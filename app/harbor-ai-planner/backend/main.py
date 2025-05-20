# ----------------
# Importera nödvändiga moduler
# ----------------
from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import logging
import time
import random
import traceback
import os
from contextlib import asynccontextmanager
from pydantic import BaseModel
import asyncio

# ----------------
# Importera projektspecifika moduler
# ----------------
from config import settings
from models import Base, Boat, Slot, BoatStay
from strategies import ALL_STRATEGIES, STRATEGY_MAP, get_strategy_by_name
from evaluator import StrategyEvaluator
from gpt_analyzer import GPTAnalyzer

# ----------------
# Konfigurera loggning
# ----------------
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    filename=settings.LOG_FILE if settings.LOG_FILE else None
)
logger = logging.getLogger(__name__)

# ----------------
# Skapa databaskoppling
# ----------------
# Skapa async SQLAlchemy engine med asyncpg
# Ändra URL från postgresql:// till postgresql+asyncpg://
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    database_url,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=settings.DEBUG,
    future=True
)

# Skapa en async sessionfabrik
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# ----------------
# Hantera applikationens livscykel
# ----------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Livscykelhanterare för FastAPI-applikationen.
    Denna funktion körs vid start och avstängning av applikationen.
    """
    # Kod som körs vid applikationsstart
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")

    # Skapa tabeller i databasen om de inte finns
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created or verified")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        # Fortsätt ändå - tabellerna kanske redan finns

    yield  # Här körs applikationen

    # Kod som körs vid applikationsavstängning
    logger.info(f"Shutting down {settings.APP_NAME}")
    await engine.dispose()

# ----------------
# Skapa FastAPI-applikation
# ----------------
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-baserat hamnplaneringssystem med fokus på resonerande AI och hypotesprövning",
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# ----------------
# Lägg till CORS-middleware för frontend
# ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# ----------------
# Dependency för att få databassession
# ----------------


async def get_db():
    """
    Dependency-funktion för att få en databassession.
    Säkerställer att sessioner stängs korrekt även vid fel.
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# ----------------
# Hjälpfunktioner
# ----------------


def handle_exception(e: Exception) -> str:
    """
    Standardiserad felhantering för att logga undantag och returnera felmeddelanden.
    """
    logger.error(f"Exception: {str(e)}")
    logger.debug(traceback.format_exc())
    return str(e)


def serialize_datetime(dt):
    """
    Konvertera datetime-objekt till ISO-formatterade strängar.
    Hanterar även None-värden.
    """
    if dt is None:
        return None
    if hasattr(dt, 'isoformat'):
        return dt.isoformat()
    return str(dt)

# ----------------
# API-endpoints
# ----------------

# --- Generella endpoints ---


@app.get("/", tags=["General"])
async def root():
    """Root endpoint som returnerar grundläggande info om API:et"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "description": "AI-baserat hamnplaneringssystem med fokus på resonerande AI och hypotesprövning",
        "endpoints": [
            {"path": "/api/strategies",
                "description": "Lista alla tillgängliga strategier"},
            {"path": "/api/boats", "description": "Hantera båtar"},
            {"path": "/api/slots", "description": "Hantera båtplatser"},
            {"path": "/api/optimize", "description": "Kör optimering och AI-analys"},
            {"path": "/api/test-data", "description": "Skapa testdata"}
        ]
    }


@app.get("/health", tags=["General"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Hälsokontroll för att verifiera att applikationen fungerar korrekt.
    Kontrollerar databaskoppling och andra kritiska komponenter.
    """
    try:
        # Kontrollera databaskoppling med en enkel förfrågan
        await db.execute(select(1))

        # Kontrollera GPT API-nyckel
        if not settings.OPENAI_API_KEY:
            return {
                "status": "warning",
                "database": "ok",
                "gpt_api": "missing api key",
                "message": "System fungerar men GPT-analys är inte tillgänglig"
            }

        return {
            "status": "ok",
            "database": "ok",
            "gpt_api": "ok",
            "message": "System fungerar normalt"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "error",
            "message": f"System error: {str(e)}",
        }

# --- Strategi-endpoints ---


@app.get("/api/strategies", response_model=List[Dict[str, Any]], tags=["Strategies"])
async def get_strategies():
    """
    Lista alla tillgängliga strategier.

    Returnerar information om varje implementerad strategi, inklusive namn och beskrivning.
    """
    try:
        return [
            {
                "name": strategy.name,
                "description": strategy.description
            } for strategy in ALL_STRATEGIES
        ]
    except Exception as e:
        logger.error(f"Failed to list strategies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list strategies: {str(e)}"
        )

# --- Båt-endpoints ---


@app.get("/api/boats", response_model=List[Dict[str, Any]], tags=["Boats"])
async def get_boats(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Hämta alla båtar med paginering.

    Args:
        skip: Antal båtar att hoppa över (för paginering)
        limit: Maximalt antal båtar att returnera
    """
    try:
        boats = await db.execute(select(Boat).offset(skip).limit(limit))
        boats = boats.scalars().all()
        return [
            {
                "id": boat.id,
                "name": boat.name,
                "width": boat.width,
                "arrival": serialize_datetime(boat.arrival),
                "departure": serialize_datetime(boat.departure)
            } for boat in boats
        ]
    except Exception as e:
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch boats: {error}")


@app.get("/api/boats/{boat_id}", response_model=Dict[str, Any], tags=["Boats"])
async def get_boat(boat_id: int, db: AsyncSession = Depends(get_db)):
    """
    Hämta en specifik båt baserat på ID.

    Args:
        boat_id: ID för båten att hämta
    """
    try:
        boat = await db.get(Boat, boat_id)
        if not boat:
            raise HTTPException(
                status_code=404, detail=f"Boat with ID {boat_id} not found")

        return {
            "id": boat.id,
            "name": boat.name,
            "width": boat.width,
            "arrival": serialize_datetime(boat.arrival),
            "departure": serialize_datetime(boat.departure)
        }
    except HTTPException:
        # Vidarebefordra HTTP-undantag
        raise
    except Exception as e:
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch boat: {error}")


@app.post("/api/boats", response_model=Dict[str, Any], tags=["Boats"])
async def create_boat(boat_data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """
    Skapa en ny båt.

    Args:
        boat_data: Data för den nya båten (namn, bredd, ankomst, avresa)
    """
    try:
        # Validera obligatoriska fält
        required_fields = ["name", "width", "arrival", "departure"]
        for field in required_fields:
            if field not in boat_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )

        # Konvertera strängar till datetime om de inte redan är det
        if isinstance(boat_data["arrival"], str):
            boat_data["arrival"] = datetime.fromisoformat(
                boat_data["arrival"].replace("Z", "+00:00"))
        if isinstance(boat_data["departure"], str):
            boat_data["departure"] = datetime.fromisoformat(
                boat_data["departure"].replace("Z", "+00:00"))

        # Validera datumförhållanden
        if boat_data["arrival"] >= boat_data["departure"]:
            raise HTTPException(
                status_code=400,
                detail="Departure time must be after arrival time"
            )

        # Validera bredd
        if not isinstance(boat_data["width"], (int, float)) or boat_data["width"] <= 0:
            raise HTTPException(
                status_code=400,
                detail="Width must be a positive number"
            )

        # Skapa och spara båten
        boat = Boat(
            name=boat_data["name"],
            width=float(boat_data["width"]),
            arrival=boat_data["arrival"],
            departure=boat_data["departure"]
        )

        db.add(boat)
        await db.commit()
        await db.refresh(boat)

        logger.info(f"Created new boat: {boat.name} (ID: {boat.id})")

        return {
            "id": boat.id,
            "name": boat.name,
            "width": boat.width,
            "arrival": serialize_datetime(boat.arrival),
            "departure": serialize_datetime(boat.departure)
        }
    except HTTPException:
        # Vidarebefordra HTTP-undantag
        raise
    except Exception as e:
        await db.rollback()
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to create boat: {error}")


@app.put("/api/boats/{boat_id}", response_model=Dict[str, Any], tags=["Boats"])
async def update_boat(boat_id: int, boat_data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """
    Uppdatera en befintlig båt.

    Args:
        boat_id: ID för båten att uppdatera
        boat_data: Nya data för båten
    """
    try:
        # Hämta båten
        boat = await db.get(Boat, boat_id)
        if not boat:
            raise HTTPException(
                status_code=404, detail=f"Boat with ID {boat_id} not found")

        # Uppdatera fält om de finns i indata
        if "name" in boat_data:
            boat.name = boat_data["name"]

        if "width" in boat_data:
            if not isinstance(boat_data["width"], (int, float)) or boat_data["width"] <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Width must be a positive number"
                )
            boat.width = float(boat_data["width"])

        if "arrival" in boat_data:
            if isinstance(boat_data["arrival"], str):
                boat_data["arrival"] = datetime.fromisoformat(
                    boat_data["arrival"].replace("Z", "+00:00"))
            boat.arrival = boat_data["arrival"]

        if "departure" in boat_data:
            if isinstance(boat_data["departure"], str):
                boat_data["departure"] = datetime.fromisoformat(
                    boat_data["departure"].replace("Z", "+00:00"))
            boat.departure = boat_data["departure"]

        # Validera datumförhållanden
        if boat.arrival >= boat.departure:
            raise HTTPException(
                status_code=400,
                detail="Departure time must be after arrival time"
            )

        # Spara ändringarna
        await db.commit()
        await db.refresh(boat)

        logger.info(f"Updated boat: {boat.name} (ID: {boat.id})")

        return {
            "id": boat.id,
            "name": boat.name,
            "width": boat.width,
            "arrival": serialize_datetime(boat.arrival),
            "departure": serialize_datetime(boat.departure)
        }
    except HTTPException:
        # Vidarebefordra HTTP-undantag
        raise
    except Exception as e:
        await db.rollback()
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to update boat: {error}")


@app.delete("/api/boats/{boat_id}", response_model=Dict[str, Any], tags=["Boats"])
async def delete_boat(boat_id: int, db: AsyncSession = Depends(get_db)):
    """
    Ta bort en båt.

    Args:
        boat_id: ID för båten att ta bort
    """
    try:
        # Hämta båten
        boat = await db.get(Boat, boat_id)
        if not boat:
            raise HTTPException(status_code=404, detail="Boat not found")

        # Ta bort båten
        await db.delete(boat)
        await db.commit()

        logger.info(f"Deleted boat: {boat.name} (ID: {boat.id})")

        return {"message": f"Boat {boat_id} deleted successfully"}
    except HTTPException:
        # Vidarebefordra HTTP-undantag
        raise
    except Exception as e:
        await db.rollback()
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to delete boat: {error}")

# --- Plats-endpoints ---


@app.get("/api/slots", response_model=List[Dict[str, Any]], tags=["Slots"])
async def get_slots(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Hämta alla båtplatser med paginering.

    Args:
        skip: Antal platser att hoppa över (för paginering)
        limit: Maximalt antal platser att returnera
    """
    try:
        slots = await db.execute(select(Slot).offset(skip).limit(limit))
        slots = slots.scalars().all()
        return [
            {
                "id": slot.id,
                "name": slot.name,
                "max_width": slot.max_width,
                "is_reserved": slot.is_reserved,
                "available_from": serialize_datetime(slot.available_from),
                "available_until": serialize_datetime(slot.available_until),
                "status": slot.get_availability_status()
            } for slot in slots
        ]
    except Exception as e:
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch slots: {error}")


@app.get("/api/slots/{slot_id}", response_model=Dict[str, Any], tags=["Slots"])
async def get_slot(slot_id: int, db: AsyncSession = Depends(get_db)):
    """
    Hämta en specifik båtplats baserat på ID.

    Args:
        slot_id: ID för platsen att hämta
    """
    try:
        slot = await db.get(Slot, slot_id)
        if not slot:
            raise HTTPException(
                status_code=404, detail=f"Slot with ID {slot_id} not found")

        return {
            "id": slot.id,
            "name": slot.name,
            "max_width": slot.max_width,
            "is_reserved": slot.is_reserved,
            "available_from": serialize_datetime(slot.available_from),
            "available_until": serialize_datetime(slot.available_until),
            "status": slot.get_availability_status()
        }
    except HTTPException:
        # Vidarebefordra HTTP-undantag
        raise
    except Exception as e:
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch slot: {error}")


@app.post("/api/slots", response_model=Dict[str, Any], tags=["Slots"])
async def create_slot(slot_data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """
    Skapa en ny båtplats.

    Args:
        slot_data: Data för den nya platsen (namn, maxbredd, reservationsstatus, etc.)
    """
    try:
        # Validera obligatoriska fält
        required_fields = ["name", "max_width"]
        for field in required_fields:
            if field not in slot_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )

        # Validera maxbredd
        if not isinstance(slot_data["max_width"], (int, float)) or slot_data["max_width"] <= 0:
            raise HTTPException(
                status_code=400,
                detail="Max width must be a positive number"
            )

        # Konvertera strängar till datetime om de anges och inte redan är datetime
        available_from = None
        if "available_from" in slot_data and slot_data["available_from"]:
            if isinstance(slot_data["available_from"], str):
                available_from = datetime.fromisoformat(
                    slot_data["available_from"].replace("Z", "+00:00"))
            else:
                available_from = slot_data["available_from"]

        available_until = None
        if "available_until" in slot_data and slot_data["available_until"]:
            if isinstance(slot_data["available_until"], str):
                available_until = datetime.fromisoformat(
                    slot_data["available_until"].replace("Z", "+00:00"))
            else:
                available_until = slot_data["available_until"]

        # Validera datumförhållanden om båda datum anges
        if available_from and available_until and available_from >= available_until:
            raise HTTPException(
                status_code=400,
                detail="available_until must be after available_from"
            )

        # Skapa och spara platsen
        slot = Slot(
            name=slot_data["name"],
            max_width=float(slot_data["max_width"]),
            is_reserved=bool(slot_data.get("is_reserved", False)),
            available_from=available_from,
            available_until=available_until
        )

        db.add(slot)
        await db.commit()
        await db.refresh(slot)

        logger.info(f"Created new slot: {slot.name} (ID: {slot.id})")

        return {
            "id": slot.id,
            "name": slot.name,
            "max_width": slot.max_width,
            "is_reserved": slot.is_reserved,
            "available_from": serialize_datetime(slot.available_from),
            "available_until": serialize_datetime(slot.available_until),
            "status": slot.get_availability_status()
        }
    except HTTPException:
        # Vidarebefordra HTTP-undantag
        raise
    except Exception as e:
        await db.rollback()
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to create slot: {error}")


@app.put("/api/slots/{slot_id}", response_model=Dict[str, Any], tags=["Slots"])
async def update_slot(slot_id: int, slot_data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """
    Uppdatera en befintlig båtplats.

    Args:
        slot_id: ID för platsen att uppdatera
        slot_data: Nya data för platsen
    """
    try:
        # Hämta platsen
        slot = await db.get(Slot, slot_id)
        if not slot:
            raise HTTPException(
                status_code=404, detail=f"Slot with ID {slot_id} not found")

        # Uppdatera fält om de finns i indata
        if "name" in slot_data:
            slot.name = slot_data["name"]

        if "max_width" in slot_data:
            if not isinstance(slot_data["max_width"], (int, float)) or slot_data["max_width"] <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Max width must be a positive number"
                )
            slot.max_width = float(slot_data["max_width"])

        if "is_reserved" in slot_data:
            slot.is_reserved = bool(slot_data["is_reserved"])

        # Hantera available_from
        if "available_from" in slot_data:
            if slot_data["available_from"] is None:
                slot.available_from = None
            elif isinstance(slot_data["available_from"], str):
                slot.available_from = datetime.fromisoformat(
                    slot_data["available_from"].replace("Z", "+00:00"))
            else:
                slot.available_from = slot_data["available_from"]

        # Hantera available_until
        if "available_until" in slot_data:
            if slot_data["available_until"] is None:
                slot.available_until = None
            elif isinstance(slot_data["available_until"], str):
                slot.available_until = datetime.fromisoformat(
                    slot_data["available_until"].replace("Z", "+00:00"))
            else:
                slot.available_until = slot_data["available_until"]

        # Validera datumförhållanden om båda datum finns
        if slot.available_from and slot.available_until and slot.available_from >= slot.available_until:
            raise HTTPException(
                status_code=400,
                detail="available_until must be after available_from"
            )

        # Spara ändringarna
        await db.commit()
        await db.refresh(slot)

        logger.info(f"Updated slot: {slot.name} (ID: {slot.id})")

        return {
            "id": slot.id,
            "name": slot.name,
            "max_width": slot.max_width,
            "is_reserved": slot.is_reserved,
            "available_from": serialize_datetime(slot.available_from),
            "available_until": serialize_datetime(slot.available_until),
            "status": slot.get_availability_status()
        }
    except HTTPException:
        # Vidarebefordra HTTP-undantag
        raise
    except Exception as e:
        await db.rollback()
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to update slot: {error}")


@app.delete("/api/slots/{slot_id}", response_model=Dict[str, Any], tags=["Slots"])
async def delete_slot(slot_id: int, db: AsyncSession = Depends(get_db)):
    """
    Ta bort en båtplats.

    Args:
        slot_id: ID för platsen att ta bort
    """
    try:
        # Hämta platsen
        slot = await db.get(Slot, slot_id)
        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found")

        # Ta bort platsen
        await db.delete(slot)
        await db.commit()

        logger.info(f"Deleted slot: {slot.name} (ID: {slot.id})")

        return {"message": f"Slot {slot_id} deleted successfully"}
    except HTTPException:
        # Vidarebefordra HTTP-undantag
        raise
    except Exception as e:
        await db.rollback()
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to delete slot: {error}")

# --- Optimerings-endpoints ---


@app.post("/api/optimize", response_model=Dict[str, Any], tags=["Optimization"])
async def optimize_harbor(
    background_tasks: BackgroundTasks,
    strategy_names: List[str] = Query(None),
    run_in_background: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """
    Kör optimering med valda strategier och utför AI-analys.

    Args:
        strategy_names: Lista över strategier att köra (om tom används alla tillgängliga)
        run_in_background: Om optimeringen ska köras som en bakgrundsuppgift

    Returns:
        Resultat av optimering och AI-analys, eller jobb-ID om körning i bakgrunden
    """
    # Förbered jobbet
    job_id = f"optimize_{int(time.time())}"

    # Skapa en funktion för att utföra optimeringen
    async def run_optimization():
        try:
            # Använd en ny databassession för bakgrundsuppgiften
            async with async_session() as async_db:
                try:
                    result = await _perform_optimization(async_db, strategy_names)

                    # Spara resultatet för senare hämtning
                    with open(f"{job_id}.json", "w") as f:
                        json.dump(result, f, default=str)

                    logger.info(f"Background optimization completed: {job_id}")
                finally:
                    await async_db.close()
        except Exception as e:
            logger.error(f"Background optimization failed: {str(e)}")
            # Spara fel för senare hämtning
            with open(f"{job_id}.error", "w") as f:
                f.write(str(e))

    # Om användaren begär bakgrundskörning
    if run_in_background:
        background_tasks.add_task(run_optimization)
        return {
            "status": "processing",
            "job_id": job_id,
            "message": "Optimization started in background"
        }

    # Annars kör synkront
    return await _perform_optimization(db, strategy_names)


async def _perform_optimization(db: AsyncSession, strategy_names: List[str] = None) -> Dict[str, Any]:
    """
    Utför den faktiska optimeringsprocessen.

    Args:
        db: Databassession
        strategy_names: Lista över strategier att köra

    Returns:
        Resultat av optimering och AI-analys
    """
    try:
        start_time = time.time()
        logger.info("Starting optimization process")

        # Hämta alla båtar och platser från databasen
        boats_query = select(Boat).options(selectinload(Boat.boat_stays))
        slots_query = select(Slot).options(selectinload(Slot.boat_stays))

        boats_result = await db.execute(boats_query)
        slots_result = await db.execute(slots_query)

        boats = boats_result.scalars().all()
        slots = slots_result.scalars().all()

        if not boats:
            raise HTTPException(status_code=400, detail="No boats in database")

        if not slots:
            raise HTTPException(status_code=400, detail="No slots in database")

        logger.info(
            f"Optimizing placement for {len(boats)} boats and {len(slots)} slots")

        # Om inga strategier specificerats, använd standardstrategierna
        if not strategy_names:
            strategy_names = settings.DEFAULT_STRATEGIES

        logger.info(f"Using strategies: {', '.join(strategy_names)}")

        # Hitta strategierna
        strategies = []
        for name in strategy_names:
            strategy = get_strategy_by_name(name)
            if strategy:
                strategies.append(strategy)

        if not strategies:
            raise HTTPException(
                status_code=400, detail="No valid strategies specified")

        # Kör alla valda strategier
        all_results = {}
        for strategy in strategies:
            strategy_start = time.time()
            logger.info(f"Running strategy: {strategy.name}")

            # Implementera timeout-skydd
            boat_stays = await strategy.place_boats(db, boats, slots)

            all_results[strategy.name] = boat_stays

            strategy_time = time.time() - strategy_start
            logger.info(
                f"Strategy {strategy.name} completed in {strategy_time:.2f}s with {len(boat_stays)} placements")

        # Utvärdera resultaten från alla strategier
        logger.info("Evaluating strategy results")
        evaluations = await StrategyEvaluator.evaluate_all_strategies(
            db, all_results, boats, slots)

        # Skapa en detaljerad utvärdering med mer information
        detailed_evaluation = await StrategyEvaluator.get_detailed_evaluation(
            db, all_results, boats, slots)

        # Använd GPT för att analysera resultaten om API-nyckel finns
        if settings.OPENAI_API_KEY:
            logger.info("Starting GPT analysis")
            try:
                gpt_analyzer = GPTAnalyzer(api_key=settings.OPENAI_API_KEY)
                gpt_analysis = await gpt_analyzer.analyze_strategies(
                    evaluations, boats, slots
                )
                logger.info("GPT analysis completed successfully")
            except Exception as e:
                logger.error(f"GPT analysis failed: {str(e)}")
                # Fallback om GPT-analys misslyckas
                gpt_analysis = {
                    "error": f"Failed to analyze with GPT: {str(e)}",
                    "best_strategy": max(evaluations.items(), key=lambda x: x[1].get('score', 0))[0],
                    "recommendations": []
                }
        else:
            logger.warning("No OpenAI API key provided, skipping GPT analysis")
            gpt_analysis = {
                "error": "No OpenAI API key configured",
                "best_strategy": max(evaluations.items(), key=lambda x: x[1].get('score', 0))[0],
                "recommendations": []
            }

        total_time = time.time() - start_time
        logger.info(f"Optimization process completed in {total_time:.2f}s")

        # Returnera resultaten
        return {
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": total_time,
            "strategies": {
                name: [
                    {
                        "boat_id": stay.boat_id,
                        "boat_name": next((b.name for b in boats if b.id == stay.boat_id), "Unknown"),
                        "boat_width": next((b.width for b in boats if b.id == stay.boat_id), 0),
                        "slot_id": stay.slot_id,
                        "slot_name": next((s.name for s in slots if s.id == stay.slot_id), "Unknown"),
                        "slot_max_width": next((s.max_width for s in slots if s.id == stay.slot_id), 0),
                        "start_time": serialize_datetime(stay.start_time),
                        "end_time": serialize_datetime(stay.end_time)
                    }
                    for stay in stays
                ]
                for name, stays in all_results.items()
            },
            "evaluations": evaluations,
            "detailed_evaluation": detailed_evaluation,
            "gpt_analysis": gpt_analysis
        }
    except HTTPException:
        # Vidarebefordra HTTP-undantag
        raise
    except Exception as e:
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Optimization failed: {error}")


@app.get("/api/optimize/{job_id}", response_model=Dict[str, Any], tags=["Optimization"])
async def get_optimization_result(job_id: str):
    """
    Hämta resultatet av en bakgrundsoptimering.

    Args:
        job_id: ID för optimeringsjobbet

    Returns:
        Resultat av optimeringen, eller statusuppdatering om den fortfarande körs
    """
    try:
        # Kontrollera om resultatet finns
        if os.path.exists(f"{job_id}.json"):
            with open(f"{job_id}.json", "r") as f:
                return json.load(f)

        # Kontrollera om det finns ett felmeddelande
        if os.path.exists(f"{job_id}.error"):
            with open(f"{job_id}.error", "r") as f:
                error_message = f.read()
            raise HTTPException(
                status_code=500, detail=f"Optimization failed: {error_message}")

        # Annars antar vi att jobbet fortfarande körs
        return {
            "status": "processing",
            "job_id": job_id,
            "message": "Optimization is still running"
        }
    except HTTPException:
        # Vidarebefordra HTTP-undantag
        raise
    except Exception as e:
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve optimization result: {error}")

# --- Testdata-endpoint ---


@app.post("/api/test-data", response_model=Dict[str, Any], tags=["Test Data"])
async def create_test_data(
    boats_count: int = Query(settings.TEST_BOATS_COUNT, ge=1, le=1000),
    slots_count: int = Query(settings.TEST_SLOTS_COUNT, ge=1, le=1000),
    temp_slots_percent: float = Query(
        settings.TEST_TEMP_SLOTS_PERCENT, ge=0, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Skapa testdata med båtar och platser.

    Args:
        boats_count: Antal båtar att skapa
        slots_count: Antal platser att skapa
        temp_slots_percent: Procent av platserna som ska vara temporärt tillgängliga
    """
    try:
        logger.info(
            f"Creating test data: {boats_count} boats, {slots_count} slots, {temp_slots_percent}% temp slots")

        # Rensa befintliga data
        await db.execute(delete(BoatStay))
        await db.execute(delete(Boat))
        await db.execute(delete(Slot))

        # Beräkna antal platser av varje typ
        regular_slots_count = int(
            # 10% permanenta
            slots_count * (100 - temp_slots_percent - 10) / 100)
        temp_slots_count = int(slots_count * temp_slots_percent / 100)
        perm_slots_count = slots_count - regular_slots_count - temp_slots_count

        # Skapa platser med varierande bredd
        slots = []

        # Vanliga platser
        for i in range(1, regular_slots_count + 1):
            # Varierande bredder mellan 2.5m och 6.0m
            # Ger bredder från 2.5, 3.0, 3.5... till 6.0
            width = 2.5 + (i % 8) * 0.5
            slots.append(
                Slot(name=f"Plats {i}", max_width=width, is_reserved=False)
            )

        # Temporärt tillgängliga platser
        summer_start = datetime(2023, 6, 1)
        summer_end = datetime(2023, 8, 31)
        for i in range(regular_slots_count + 1, regular_slots_count + temp_slots_count + 1):
            width = 3.0 + (i % 7) * 0.5
            slots.append(
                Slot(
                    name=f"Temp {i}",
                    max_width=width,
                    is_reserved=True,
                    available_from=summer_start,
                    available_until=summer_end
                )
            )

        # Permanent reserverade platser
        for i in range(regular_slots_count + temp_slots_count + 1, slots_count + 1):
            width = 3.5 + (i % 6) * 0.5
            slots.append(
                Slot(
                    name=f"Reserv {i}",
                    max_width=width,
                    is_reserved=True
                )
            )

        # Skapa båtar med varierande bredd och vistelserlängd
        boats = []
        for i in range(1, boats_count + 1):
            # Variera båtarnas bredd
            width = 2.0 + (i % 9) * 0.5  # Bredder från 2.0 till 6.0m

            # Variera ankomst- och avresedatum under sommaren
            arrival_day = random.randint(1, 80)  # 1 juni till 19 augusti
            stay_length = random.randint(3, 14)  # 3 till 14 dagars vistelse

            arrival = datetime(2023, 6, 1) + timedelta(days=arrival_day)
            departure = arrival + timedelta(days=stay_length)

            boat_name = f"Båt {i}"
            # Lägg till mer beskrivande namn för vissa båtar
            if i % 10 == 0:
                boat_name = f"Yacht {i}"
            elif i % 7 == 0:
                boat_name = f"Segelbåt {i}"
            elif i % 5 == 0:
                boat_name = f"Motorbåt {i}"

            boats.append(
                Boat(
                    name=boat_name,
                    width=width,
                    arrival=arrival,
                    departure=departure
                )
            )

        # Spara till databasen
        await db.add_all(slots)
        await db.add_all(boats)
        await db.commit()

        logger.info(
            f"Test data created successfully: {len(slots)} slots, {len(boats)} boats")

        return {
            "message": f"Skapade {len(slots)} platser och {len(boats)} båtar som testdata",
            "slots_created": len(slots),
            "boats_created": len(boats),
            "slot_types": {
                "regular": regular_slots_count,
                "temporary": temp_slots_count,
                "permanent": perm_slots_count
            }
        }

    except Exception as e:
        await db.rollback()
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to create test data: {error}")

# --- Vistelse-endpoints ---


@app.get("/api/stays", response_model=List[Dict[str, Any]], tags=["Stays"])
async def get_stays(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    strategy: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Hämta alla båtvistelser med paginering och filtrering.

    Args:
        skip: Antal vistelser att hoppa över (för paginering)
        limit: Maximalt antal vistelser att returnera
        strategy: Filtrera efter strategi
    """
    try:
        # Skapa en basförfrågan
        query = select(BoatStay)

        # Lägg till filter om strategi anges
        if strategy:
            query = query.filter(BoatStay.strategy_name == strategy)

        # Hämta vistelser med paginering
        result = await db.execute(query.offset(skip).limit(limit))
        stays = result.scalars().all()

        # Hämta relaterad information för båtar och platser
        boat_ids = {stay.boat_id for stay in stays}
        slot_ids = {stay.slot_id for stay in stays}

        boats_query = select(Boat).filter(Boat.id.in_(boat_ids))
        slots_query = select(Slot).filter(Slot.id.in_(slot_ids))

        boats_result = await db.execute(boats_query)
        slots_result = await db.execute(slots_query)

        boats = {boat.id: boat for boat in boats_result.scalars().all()}
        slots = {slot.id: slot for slot in slots_result.scalars().all()}

        # Formatera resultat
        result = []
        for stay in stays:
            boat = boats.get(stay.boat_id)
            slot = slots.get(stay.slot_id)

            result.append({
                "id": stay.id,
                "boat": {
                    "id": boat.id,
                    "name": boat.name,
                    "width": boat.width
                } if boat else None,
                "slot": {
                    "id": slot.id,
                    "name": slot.name,
                    "max_width": slot.max_width
                } if slot else None,
                "start_time": serialize_datetime(stay.start_time),
                "end_time": serialize_datetime(stay.end_time),
                "strategy_name": stay.strategy_name
            })

        return result
    except Exception as e:
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch stays: {error}")


class BoatStayData(BaseModel):
    boat_id: int
    slot_id: int
    start_time: datetime
    end_time: datetime


class SaveSolutionRequest(BaseModel):
    strategy_name: str
    boat_stays: List[BoatStayData]


@app.post("/api/save-solution", response_model=Dict[str, Any], tags=["Optimization"])
async def save_solution(
    request: SaveSolutionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Spara en specifik lösning (placeringar) till databasen.

    Args:
        request: Request data containing strategy name and boat stays
    """
    try:
        logger.info(f"Saving solution for strategy: {request.strategy_name}")

        # Ta bort befintliga vistelser med denna strategi
        await db.execute(delete(BoatStay).filter(
            BoatStay.strategy_name == request.strategy_name))

        # Validera indata
        for stay_data in request.boat_stays:
            # Kontrollera att båten och platsen finns
            boat = await db.get(Boat, stay_data.boat_id)
            if not boat:
                raise HTTPException(
                    status_code=400,
                    detail=f"Boat with ID {stay_data.boat_id} not found"
                )

            slot = await db.get(Slot, stay_data.slot_id)
            if not slot:
                raise HTTPException(
                    status_code=400,
                    detail=f"Slot with ID {stay_data.slot_id} not found"
                )

            # Kontrollera att båten passar på platsen
            if boat.width > slot.max_width:
                raise HTTPException(
                    status_code=400,
                    detail=f"Boat width ({boat.width}) exceeds slot max width ({slot.max_width})"
                )

        # Skapa nya boat_stays-poster
        new_stays = []
        for stay_data in request.boat_stays:
            stay = BoatStay(
                boat_id=stay_data.boat_id,
                slot_id=stay_data.slot_id,
                start_time=stay_data.start_time,
                end_time=stay_data.end_time,
                strategy_name=request.strategy_name
            )
            new_stays.append(stay)

        await db.add_all(new_stays)
        await db.commit()

        logger.info(
            f"Saved {len(new_stays)} boat placements for strategy '{request.strategy_name}'")

        return {
            "message": f"Saved {len(new_stays)} boat placements for strategy '{request.strategy_name}'",
            "stays_count": len(new_stays)
        }
    except HTTPException:
        # Vidarebefordra HTTP-undantag
        raise
    except Exception as e:
        await db.rollback()
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to save solution: {error}")

# Kör servern om denna fil körs direkt
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    uvicorn.run(app, host="0.0.0.0", port=8001)
