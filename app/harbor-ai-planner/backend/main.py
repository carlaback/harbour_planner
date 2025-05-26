# ----------------
# Importera nödvändiga moduler
# ----------------
from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, update, delete, desc
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
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError

# ----------------
# Importera projektspecifika moduler
# ----------------
from config import settings
from models import Base, Boat, Slot, BoatStay, Dock, SlotType, SlotStatus
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
            {"path": "/api/docks", "description": "Hantera bryggor"},
            {"path": "/api/optimize", "description": "Kör optimering och AI-analys"},
            {"path": "/api/test-data", "description": "Skapa testdata"},
            {"path": "/api/harbor-layout", "description": "Skapa hamnlayout"},
            {"path": "/api/analyze-results",
                "description": "Kör AI-analys på resultat"},
            {"path": "/api/analysis-history", "description": "Se AI-analyshistorik"},
            {"path": "/api/ask-ai", "description": "Ställ frågor till AI:n"},
            {"path": "/api/ai-recommendations",
                "description": "Få AI-rekommendationer"}
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

# --- Dock/bryggor-endpoints ---


@app.get("/api/docks", response_model=List[Dict[str, Any]], tags=["Docks"])
async def get_docks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Hämta alla bryggor med paginering.

    Args:
        skip: Antal bryggor att hoppa över (för paginering)
        limit: Maximalt antal bryggor att returnera
    """
    try:
        docks = await db.execute(select(Dock).offset(skip).limit(limit))
        docks = docks.scalars().all()
        return [
            {
                "id": dock.id,
                "name": dock.name,
                "position_x": dock.position_x,
                "position_y": dock.position_y,
                "width": dock.width,
                "length": dock.length
            } for dock in docks
        ]
    except Exception as e:
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch docks: {error}")


@app.get("/api/docks/{dock_id}", response_model=Dict[str, Any], tags=["Docks"])
async def get_dock(dock_id: int, db: AsyncSession = Depends(get_db)):
    """
    Hämta en specifik brygga baserat på ID.

    Args:
        dock_id: ID för bryggan att hämta
    """
    try:
        dock = await db.get(Dock, dock_id)
        if not dock:
            raise HTTPException(
                status_code=404, detail=f"Dock with ID {dock_id} not found")

        return {
            "id": dock.id,
            "name": dock.name,
            "position_x": dock.position_x,
            "position_y": dock.position_y,
            "width": dock.width,
            "length": dock.length
        }
    except HTTPException:
        raise
    except Exception as e:
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch dock: {error}")


@app.post("/api/docks", response_model=Dict[str, Any], tags=["Docks"])
async def create_dock(dock_data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """
    Skapa en ny brygga.

    Args:
        dock_data: Data för den nya bryggan (namn, position, storlek)
    """
    try:
        # Validera obligatoriska fält
        required_fields = ["name", "position_x",
                           "position_y", "width", "length"]
        for field in required_fields:
            if field not in dock_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )

        # Validera att position och storlek är positiva tal
        for field in ["position_x", "position_y", "width", "length"]:
            value = dock_data.get(field)
            if not isinstance(value, (int, float)) or value < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"{field} must be a non-negative number"
                )

        # Skapa och spara bryggan
        dock = Dock(
            name=dock_data["name"],
            position_x=int(dock_data["position_x"]),
            position_y=int(dock_data["position_y"]),
            width=int(dock_data["width"]),
            length=int(dock_data["length"])
        )

        db.add(dock)
        await db.commit()
        await db.refresh(dock)

        logger.info(f"Created new dock: {dock.name} (ID: {dock.id})")

        return {
            "id": dock.id,
            "name": dock.name,
            "position_x": dock.position_x,
            "position_y": dock.position_y,
            "width": dock.width,
            "length": dock.length
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to create dock: {error}")

# --- Plats-endpoints ---


@app.get("/api/slots", response_model=List[Dict[str, Any]], tags=["Slots"])
async def get_slots(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    slot_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    dock_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Hämta alla båtplatser med paginering och filtrering.

    Args:
        skip: Antal platser att hoppa över (för paginering)
        limit: Maximalt antal platser att returnera
        slot_type: Filtrera efter platstyp (guest, flex, permanent, guest_drop_in)
        status: Filtrera efter status (available, occupied, reserved, maintenance)
        dock_id: Filtrera efter brygga-ID
    """
    try:
        query = select(Slot)

        # Tillämpa filter om de anges
        if slot_type:
            query = query.filter(Slot.slot_type == slot_type)
        if status:
            query = query.filter(Slot.status == status)
        if dock_id:
            query = query.filter(Slot.dock_id == dock_id)

        query = query.offset(skip).limit(limit)
        slots = await db.execute(query)
        slots = slots.scalars().all()

        return [
            {
                "id": slot.id,
                "name": slot.name,
                "position_x": slot.position_x,
                "position_y": slot.position_y,
                "width": slot.width,
                "length": slot.length,
                "depth": slot.depth,
                "max_width": slot.max_width,
                "slot_type": slot.slot_type,
                "status": slot.status,
                "is_reserved": slot.is_reserved,
                "price_per_day": slot.price_per_day,
                "available_from": serialize_datetime(slot.available_from),
                "available_until": serialize_datetime(slot.available_until),
                "dock_id": slot.dock_id,
                "boat_id": slot.boat_id,
                "status_text": slot.get_availability_status()
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
            "position_x": slot.position_x,
            "position_y": slot.position_y,
            "width": slot.width,
            "length": slot.length,
            "depth": slot.depth,
            "max_width": slot.max_width,
            "slot_type": slot.slot_type,
            "status": slot.status,
            "is_reserved": slot.is_reserved,
            "price_per_day": slot.price_per_day,
            "available_from": serialize_datetime(slot.available_from),
            "available_until": serialize_datetime(slot.available_until),
            "dock_id": slot.dock_id,
            "boat_id": slot.boat_id,
            "status_text": slot.get_availability_status()
        }
    except HTTPException:
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
        slot_data: Data för den nya platsen
    """
    try:
        # Validera obligatoriska fält
        required_fields = ["name", "position_x", "position_y",
                           "width", "length", "max_width", "dock_id", "slot_type"]
        for field in required_fields:
            if field not in slot_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )

        # Validera att bryggan finns
        dock = await db.get(Dock, slot_data["dock_id"])
        if not dock:
            raise HTTPException(
                status_code=400,
                detail=f"Dock with ID {slot_data['dock_id']} not found"
            )

        # Skapa plats med alla angivna fält
        slot_dict = {
            "name": slot_data["name"],
            "position_x": int(slot_data["position_x"]),
            "position_y": int(slot_data["position_y"]),
            "width": int(slot_data["width"]),
            "length": int(slot_data["length"]),
            "max_width": float(slot_data["max_width"]),
            "dock_id": int(slot_data["dock_id"]),
            "slot_type": slot_data["slot_type"],
        }

        # Hantera valfria fält
        if "depth" in slot_data:
            slot_dict["depth"] = float(slot_data["depth"])
        if "status" in slot_data:
            slot_dict["status"] = slot_data["status"]
        else:
            # Permanenta platser är upptagna som standard
            slot_dict["status"] = "occupied" if slot_data["slot_type"] == "permanent" else "available"
        if "is_reserved" in slot_data:
            slot_dict["is_reserved"] = bool(slot_data["is_reserved"])
        if "price_per_day" in slot_data:
            slot_dict["price_per_day"] = int(slot_data["price_per_day"])
        if "available_from" in slot_data and slot_data["available_from"]:
            if isinstance(slot_data["available_from"], str):
                slot_dict["available_from"] = datetime.fromisoformat(
                    slot_data["available_from"].replace("Z", "+00:00"))
            else:
                slot_dict["available_from"] = slot_data["available_from"]
        if "available_until" in slot_data and slot_data["available_until"]:
            if isinstance(slot_data["available_until"], str):
                slot_dict["available_until"] = datetime.fromisoformat(
                    slot_data["available_until"].replace("Z", "+00:00"))
            else:
                slot_dict["available_until"] = slot_data["available_until"]
        if "boat_id" in slot_data:
            slot_dict["boat_id"] = int(slot_data["boat_id"])

        # Validera datumförhållanden om båda datum anges
        if "available_from" in slot_dict and "available_until" in slot_dict:
            if slot_dict["available_from"] >= slot_dict["available_until"]:
                raise HTTPException(
                    status_code=400,
                    detail="available_until must be after available_from"
                )

        # Skapa och spara slot
        slot = Slot(**slot_dict)

        db.add(slot)
        await db.commit()
        await db.refresh(slot)

        logger.info(f"Created new slot: {slot.name} (ID: {slot.id})")

        return {
            "id": slot.id,
            "name": slot.name,
            "position_x": slot.position_x,
            "position_y": slot.position_y,
            "width": slot.width,
            "length": slot.length,
            "depth": slot.depth,
            "max_width": slot.max_width,
            "slot_type": slot.slot_type,
            "status": slot.status,
            "is_reserved": slot.is_reserved,
            "price_per_day": slot.price_per_day,
            "available_from": serialize_datetime(slot.available_from),
            "available_until": serialize_datetime(slot.available_until),
            "dock_id": slot.dock_id,
            "boat_id": slot.boat_id,
            "status_text": slot.get_availability_status()
        }
    except HTTPException:
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
        updated_fields = []

        # Uppdatera strängar och enkla värden
        for field in ["name", "slot_type", "status"]:
            if field in slot_data:
                setattr(slot, field, slot_data[field])
                updated_fields.append(field)

        # Uppdatera numeriska värden med validering
        for field in ["position_x", "position_y", "width", "length", "max_width", "depth", "price_per_day"]:
            if field in slot_data:
                try:
                    value = float(slot_data[field]) if field in [
                        "max_width", "depth"] else int(slot_data[field])
                    if value < 0:
                        raise ValueError(
                            f"{field} must be a non-negative number")
                    setattr(slot, field, value)
                    updated_fields.append(field)
                except (ValueError, TypeError) as e:
                    raise HTTPException(status_code=400, detail=str(e))

        # Uppdatera boolean-värden
        if "is_reserved" in slot_data:
            slot.is_reserved = bool(slot_data["is_reserved"])
            updated_fields.append("is_reserved")

        # Uppdatera relationsID
        if "dock_id" in slot_data:
            # Validera att bryggan finns
            dock = await db.get(Dock, slot_data["dock_id"])
            if not dock:
                raise HTTPException(
                    status_code=400,
                    detail=f"Dock with ID {slot_data['dock_id']} not found"
                )
            slot.dock_id = int(slot_data["dock_id"])
            updated_fields.append("dock_id")

        if "boat_id" in slot_data:
            if slot_data["boat_id"] is None:
                slot.boat_id = None
            else:
                # Validera att båten finns
                boat = await db.get(Boat, slot_data["boat_id"])
                if not boat:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Boat with ID {slot_data['boat_id']} not found"
                    )
                slot.boat_id = int(slot_data["boat_id"])
            updated_fields.append("boat_id")

        # Uppdatera datetime-värden
        for field in ["available_from", "available_until"]:
            if field in slot_data:
                if slot_data[field] is None:
                    setattr(slot, field, None)
                elif isinstance(slot_data[field], str):
                    try:
                        date_value = datetime.fromisoformat(
                            slot_data[field].replace("Z", "+00:00"))
                        setattr(slot, field, date_value)
                    except ValueError:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid date format for {field}. Use ISO format."
                        )
                else:
                    setattr(slot, field, slot_data[field])
                updated_fields.append(field)

        # Validera datumförhållanden om båda datum finns
        if slot.available_from and slot.available_until and slot.available_from >= slot.available_until:
            raise HTTPException(
                status_code=400,
                detail="available_until must be after available_from"
            )

        # Permanenta platser ska inte kunna sättas som tillgängliga
        if slot.slot_type == SlotType.PERMANENT and slot.status == SlotStatus.AVAILABLE:
            raise HTTPException(
                status_code=400,
                detail="Permanent slots cannot be set to available status"
            )

        # Spara ändringarna
        await db.commit()
        await db.refresh(slot)

        logger.info(
            f"Updated slot {slot.id} fields: {', '.join(updated_fields)}")

        return {
            "id": slot.id,
            "name": slot.name,
            "position_x": slot.position_x,
            "position_y": slot.position_y,
            "width": slot.width,
            "length": slot.length,
            "depth": slot.depth,
            "max_width": slot.max_width,
            "slot_type": slot.slot_type,
            "status": slot.status,
            "is_reserved": slot.is_reserved,
            "price_per_day": slot.price_per_day,
            "available_from": serialize_datetime(slot.available_from),
            "available_until": serialize_datetime(slot.available_until),
            "dock_id": slot.dock_id,
            "boat_id": slot.boat_id,
            "status_text": slot.get_availability_status()
        }
    except HTTPException:
        # Vidarebefordra HTTP-undantag
        raise
    except Exception as e:
        await db.rollback()
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to update slot: {error}")


@app.put("/api/slots/{slot_id}/status", response_model=Dict[str, Any], tags=["Slots"])
async def update_slot_status(
    slot_id: int,
    status_data: Dict[str, str],
    db: AsyncSession = Depends(get_db)
):
    """
    Uppdatera status för en specifik båtplats.

    Args:
        slot_id: ID för platsen att uppdatera
        status_data: Dictionary med ny status ("status" fältet)
    """
    try:
        # Validera indata
        if "status" not in status_data:
            raise HTTPException(
                status_code=400,
                detail="Missing required field: status"
            )

        # Validera att statusvärdet är giltigt
        new_status = status_data["status"]
        valid_statuses = [s.value for s in SlotStatus]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status value. Must be one of: {', '.join(valid_statuses)}"
            )

        # Hämta platsen
        slot = await db.get(Slot, slot_id)
        if not slot:
            raise HTTPException(
                status_code=404, detail=f"Slot with ID {slot_id} not found")

        # Kontrollera om platsen är permanent och skydda mot status-ändringar
        if slot.slot_type == SlotType.PERMANENT and new_status == SlotStatus.AVAILABLE:
            raise HTTPException(
                status_code=400,
                detail="Permanent slots cannot be set to available status"
            )

        # Uppdatera status
        slot.status = new_status
        await db.commit()
        await db.refresh(slot)

        logger.info(f"Updated status of slot {slot.id} to {new_status}")

        return {
            "id": slot.id,
            "name": slot.name,
            "slot_type": slot.slot_type,
            "status": slot.status,
            "status_text": slot.get_availability_status(),
            "message": f"Status updated to {new_status}"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to update slot status: {error}")


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
    Utför den faktiska optimeringsprocessen med förbättrad AI-analys.
    """
    try:
        start_time = time.time()
        logger.info("Starting optimization process with enhanced AI analysis")

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

        # Om inga strategier specificerats, använd alla tillgängliga
        if not strategy_names:
            strategy_names = [s.name for s in ALL_STRATEGIES]

        logger.info(f"Using strategies: {', '.join(strategy_names)}")

        # Hitta strategierna
        strategies = []
        for name in strategy_names:
            strategy = get_strategy_by_name(name)
            if strategy:
                strategies.append(strategy)
                logger.info(
                    f"✅ Loaded strategy '{name}' -> {type(strategy).__name__}")
            else:
                logger.warning(f"❌ Strategy '{name}' not found")

        if not strategies:
            raise HTTPException(
                status_code=400, detail="No valid strategies specified")

        # Kör strategierna med förbättrad utvärdering
        evaluator = StrategyEvaluator(db)
        evaluation_results = []

        for strategy in strategies:
            try:
                result = await evaluator.evaluate_strategy(strategy, boats, slots)
                evaluation_results.append(result)
                logger.info(
                    f"Strategy {strategy.name} completed - {result['metrics'].get('boats_placed', 0)} boats placed")
            except Exception as e:
                logger.error(f"Strategy {strategy.name} failed: {str(e)}")
                # Lägg till fejlresultat
                evaluation_results.append({
                    "strategy_name": strategy.name,
                    "metrics": {"boats_placed": 0, "placement_rate": 0, "error": str(e)},
                    "stays": []
                })

        # Förbättrad AI-analys med Chain of Thought och learning
        gpt_analyzer = GPTAnalyzer()

        if settings.OPENAI_API_KEY:
            try:
                logger.info(
                    "Starting enhanced AI analysis with Chain of Thought")
                ai_analysis = await gpt_analyzer.analyze_strategies_with_learning(
                    evaluation_results, boats, slots
                )
                logger.info(
                    f"AI analysis completed with confidence: {ai_analysis.get('confidence_assessment', {}).get('confidence_level', 'Unknown')}")
            except Exception as e:
                logger.error(f"AI analysis failed: {str(e)}")
                ai_analysis = {
                    "error": str(e),
                    "fallback_analysis": {
                        "message": "AI analysis unavailable, using basic evaluation",
                        "best_strategy": max(evaluation_results, key=lambda x: x['metrics'].get('boats_placed', 0))['strategy_name'] if evaluation_results else "none"
                    }
                }
        else:
            logger.info(
                "No OpenAI API key configured, using fallback analysis")
            ai_analysis = {
                "message": "OpenAI API key not configured",
                "fallback_analysis": {
                    "best_strategy": max(evaluation_results, key=lambda x: x['metrics'].get('boats_placed', 0))['strategy_name'] if evaluation_results else "none"
                }
            }

        # Konvertera resultat för kompatibilitet
        strategies_formatted = {}
        evaluations = {}

        for result in evaluation_results:
            strategy_name = result["strategy_name"]
            stays = result.get("stays", [])
            metrics = result.get("metrics", {})

            # Formatera för 'strategies' sektionen
            strategies_formatted[strategy_name] = [
                {
                    "boat_id": stay["boat_id"],
                    "boat_name": f"Boat {stay['boat_id']}",
                    "boat_width": 3.0,  # Placeholder - skulle behöva hämtas från boats
                    "slot_id": stay["slot_id"],
                    "slot_name": f"Slot {stay['slot_id']}",
                    "slot_max_width": 4.0,  # Placeholder
                    "start_time": stay["start_time"],
                    "end_time": stay["end_time"]
                }
                for stay in stays
            ]

            # Formatera för 'evaluations' sektionen
            evaluations[strategy_name] = {
                "boats_placed": metrics.get("boats_placed", 0),
                "total_boats": len(boats),
                "placement_rate": metrics.get("placement_rate", 0),
                "utilization": metrics.get("average_width_utilization", 0),
                "score": metrics.get("placement_rate", 0),
                "execution_time": result.get("execution_time_seconds", 0)
            }

        total_time = time.time() - start_time
        logger.info(
            f"Enhanced optimization process completed in {total_time:.2f}s")

        return {
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": total_time,
            "strategies": strategies_formatted,
            "evaluations": evaluations,
            "detailed_evaluation": {
                "evaluation_results": evaluation_results,
                "total_strategies_tested": len(evaluation_results),
                "successful_strategies": len([r for r in evaluation_results if r['metrics'].get('boats_placed', 0) > 0])
            },
            "ai_analysis": ai_analysis,
            "enhancement_info": {
                "chain_of_thought_enabled": bool(settings.OPENAI_API_KEY),
                "learning_system_active": True,
                "analysis_type": ai_analysis.get("analysis_type", "basic"),
                "confidence_level": ai_analysis.get("confidence_assessment", {}).get("confidence_level", "Unknown")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Enhanced optimization failed: {error}")


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

# --- AI Analysis endpoints ---


@app.post("/api/analyze-results", response_model=Dict[str, Any], tags=["AI Analysis"])
async def analyze_optimization_results(
    request_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Kör AI-analys på befintliga optimeringsresultat med Chain of Thought.

    Args:
        request_data: Dictionary med evaluation_results och optionally boats/slots data
    """
    try:
        logger.info("Starting standalone AI analysis")

        evaluation_results = request_data.get("evaluation_results", [])
        if not evaluation_results:
            raise HTTPException(
                status_code=400, detail="No evaluation results provided")

        # Hämta båtar och platser om de inte finns i request
        boats_data = request_data.get("boats")
        slots_data = request_data.get("slots")

        if not boats_data or not slots_data:
            # Hämta från databas
            boats_result = await db.execute(select(Boat))
            slots_result = await db.execute(select(Slot))
            boats_data = boats_result.scalars().all()
            slots_data = slots_result.scalars().all()

        # Kör AI-analys
        gpt_analyzer = GPTAnalyzer()

        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=400, detail="OpenAI API key not configured for AI analysis")

        ai_analysis = await gpt_analyzer.analyze_strategies_with_learning(
            evaluation_results, boats_data, slots_data
        )

        logger.info("Standalone AI analysis completed")

        return {
            "timestamp": datetime.now().isoformat(),
            "ai_analysis": ai_analysis,
            "input_summary": {
                "strategies_analyzed": len(evaluation_results),
                "boats_count": len(boats_data) if hasattr(boats_data, '__len__') else 0,
                "slots_count": len(slots_data) if hasattr(slots_data, '__len__') else 0
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"AI analysis failed: {error}")


@app.get("/api/analysis-history", response_model=List[Dict[str, Any]], tags=["AI Analysis"])
async def get_analysis_history(
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Hämta historik över AI-analyser.

    Args:
        limit: Maximalt antal analyser att returnera
    """
    try:
        # För nu returnerar vi en tom lista, men här skulle man kunna
        # implementera lagring av analyshistorik i databasen
        logger.info(f"Fetching analysis history (limit: {limit})")

        # Placeholder - i framtiden skulle vi ha en Analysis-tabell
        return []

    except Exception as e:
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch analysis history: {error}")


@app.post("/api/ask-ai", response_model=Dict[str, Any], tags=["AI Analysis"])
async def ask_ai_question(
    request_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Ställ en fråga till AI:n om hamnoptimering.

    Args:
        request_data: Dictionary med "question" och optionally context data
    """
    try:
        question = request_data.get("question")
        if not question:
            raise HTTPException(status_code=400, detail="No question provided")

        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=400, detail="OpenAI API key not configured")

        logger.info(f"Processing AI question: {question[:50]}...")

        # Hämta kontext från databasen
        boats_result = await db.execute(select(Boat))
        slots_result = await db.execute(select(Slot))
        boats = boats_result.scalars().all()
        slots = slots_result.scalars().all()

        # Använd GPT för att svara på frågan
        gpt_analyzer = GPTAnalyzer()
        response = await gpt_analyzer.answer_question(question, boats, slots, request_data.get("context"))

        logger.info("AI question answered successfully")

        return {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": response,
            "context_used": {
                "boats_count": len(boats),
                "slots_count": len(slots),
                "additional_context": bool(request_data.get("context"))
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to process AI question: {error}")


@app.get("/api/ai-recommendations", response_model=Dict[str, Any], tags=["AI Analysis"])
async def get_ai_recommendations(
    context_type: str = Query(
        "general", description="Type of recommendations: general, optimization, layout"),
    db: AsyncSession = Depends(get_db)
):
    """
    Få AI-rekommendationer för hamnoptimering.

    Args:
        context_type: Typ av rekommendationer att få
    """
    try:
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=400, detail="OpenAI API key not configured")

        logger.info(
            f"Generating AI recommendations for context: {context_type}")

        # Hämta aktuell data från databasen
        boats_result = await db.execute(select(Boat))
        slots_result = await db.execute(select(Slot))
        boats = boats_result.scalars().all()
        slots = slots_result.scalars().all()

        # Använd GPT för att generera rekommendationer
        gpt_analyzer = GPTAnalyzer()
        recommendations = await gpt_analyzer.generate_recommendations(context_type, boats, slots)

        logger.info("AI recommendations generated successfully")

        return {
            "timestamp": datetime.now().isoformat(),
            "context_type": context_type,
            "recommendations": recommendations,
            "data_summary": {
                "boats_count": len(boats),
                "slots_count": len(slots),
                "available_slots": len([s for s in slots if s.status == "available"]),
                "occupied_slots": len([s for s in slots if s.status == "occupied"])
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate AI recommendations: {error}")

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
        await db.execute(delete(Dock))

        # Skapa testdock
        dock = Dock(
            name="Test Dock",
            position_x=100,
            position_y=100,
            width=500,
            length=50
        )
        db.add(dock)
        await db.commit()
        await db.refresh(dock)

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
            slot_width = int(width * 10)  # Konvertera till pixlar för position
            slots.append(
                Slot(
                    name=f"Plats {i}",
                    position_x=100 + ((i-1) % 10) * (slot_width + 5),
                    position_y=150 + ((i-1) // 10) * 85,
                    width=slot_width,
                    length=80,
                    depth=2.5 + (i % 5) * 0.2,
                    max_width=width,
                    slot_type=SlotType.GUEST,
                    status=SlotStatus.AVAILABLE,
                    is_reserved=False,
                    price_per_day=400 + (i % 3) * 50,
                    dock_id=dock.id
                )
            )

        # Temporärt tillgängliga platser
        summer_start = datetime(2023, 6, 1)
        summer_end = datetime(2023, 8, 31)
        for i in range(regular_slots_count + 1, regular_slots_count + temp_slots_count + 1):
            width = 3.0 + (i % 7) * 0.5
            slot_width = int(width * 10)
            slots.append(
                Slot(
                    name=f"Temp {i}",
                    position_x=100 + ((i-1) % 10) * (slot_width + 5),
                    position_y=350 + ((i-1) // 10) * 85,
                    width=slot_width,
                    length=80,
                    depth=2.8 + (i % 5) * 0.2,
                    max_width=width,
                    slot_type=SlotType.FLEX,
                    status=SlotStatus.AVAILABLE,
                    is_reserved=True,
                    available_from=summer_start,
                    available_until=summer_end,
                    price_per_day=450 + (i % 3) * 50,
                    dock_id=dock.id
                )
            )

        # Permanent reserverade platser
        for i in range(regular_slots_count + temp_slots_count + 1, slots_count + 1):
            width = 3.5 + (i % 6) * 0.5
            slot_width = int(width * 10)
            slots.append(
                Slot(
                    name=f"Reserv {i}",
                    position_x=100 + ((i-1) % 10) * (slot_width + 5),
                    position_y=550 + ((i-1) // 10) * 85,
                    width=slot_width,
                    length=80,
                    depth=3.0 + (i % 5) * 0.2,
                    max_width=width,
                    slot_type=SlotType.PERMANENT,
                    status=SlotStatus.OCCUPIED,
                    is_reserved=True,
                    price_per_day=500 + (i % 3) * 50,
                    dock_id=dock.id
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


@app.post("/api/harbor-layout", response_model=Dict[str, Any], tags=["Test Data"])
async def create_harbor_layout(db: AsyncSession = Depends(get_db)):
    """
    Skapa en layout för hamnen baserad på en fördefinierad layout.
    Denna funktion skapar bryggor och båtplatser enligt en specifik layout.
    """
    try:
        logger.info("Creating harbor layout with docks and slots")

        # Rensa befintliga data
        await db.execute(delete(Slot))
        await db.execute(delete(Dock))

        # Skapa bryggorna
        docks = [
            # Översta bryggorna (501-530)
            Dock(name="Brygga A", position_x=300,
                 position_y=70, width=320, length=40),
            Dock(name="Brygga B", position_x=300,
                 position_y=130, width=280, length=40),

            # Mittenområdet (401-455)
            Dock(name="Brygga C", position_x=280,
                 position_y=270, width=40, length=440),
            Dock(name="Brygga D", position_x=370,
                 position_y=340, width=40, length=140),
            Dock(name="Brygga E", position_x=460,
                 position_y=340, width=40, length=300),
            Dock(name="Brygga F", position_x=550,
                 position_y=340, width=40, length=300),

            # Nedre bryggorna (301-346)
            Dock(name="Brygga G", position_x=280,
                 position_y=750, width=450, length=40),
            Dock(name="Brygga H", position_x=280,
                 position_y=810, width=450, length=40),

            # Gästhamn (201-246)
            Dock(name="Gästhamn", position_x=150,
                 position_y=990, width=600, length=40),

            # Nedersta bryggorna (101-181)
            Dock(name="Brygga J", position_x=150,
                 position_y=1190, width=600, length=40),
            Dock(name="Brygga K", position_x=150,
                 position_y=1280, width=600, length=40),

            # Udden (50-59)
            Dock(name="Udden", position_x=75,
                 position_y=1330, width=30, length=200)
        ]

        await db.add_all(docks)
        await db.commit()

        # Hämta de nya bryggorna för att få deras IDs
        result = await db.execute(select(Dock))
        saved_docks = {dock.name: dock for dock in result.scalars().all()}

        # Skapa platserna
        slots = []

        # Hjälpfunktion för att skapa en rad med platser
        def create_slot_row(start_id, count, start_x, start_y, width, length, is_vertical, spacing,
                            dock_name, slot_type, status="available", depth=2.5, price=400):
            dock = saved_docks[dock_name]
            row_slots = []
            for i in range(count):
                slot_id = start_id + i
                x = start_x if is_vertical else start_x + i * (width + spacing)
                y = start_y + i * \
                    (length + spacing) if is_vertical else start_y

                # Certain slot IDs are available based on image
                special_status = status
                if slot_id in [407, 403, 314, 437] and slot_type == "permanent":
                    special_status = "available"

                row_slots.append(
                    Slot(
                        id=slot_id,
                        name=str(slot_id),
                        position_x=x,
                        position_y=y,
                        width=width,
                        length=length,
                        depth=depth + (i % 5) * 0.2,  # Variera djupet lite
                        max_width=width * 0.9,  # Maxbredd något mindre än faktisk bredd
                        slot_type=slot_type,
                        status=special_status,
                        is_reserved=(slot_type != "guest"),
                        # Variera priset lite
                        price_per_day=price + (i % 3) * 50,
                        dock_id=dock.id
                    )
                )
            return row_slots

        # Översta bryggorna (501-530)
        slots.extend(create_slot_row(501, 5, 310, 80, 30,
                     30, False, 5, "Brygga A", "flex"))
        slots.extend(create_slot_row(510, 10, 310, 140,
                     25, 30, False, 5, "Brygga B", "flex"))

        # Mittenområdet (401-456)
        slots.extend(create_slot_row(401, 17, 250, 320, 25, 30,
                     True, 5, "Brygga C", "permanent", "occupied"))
        slots.extend(create_slot_row(420, 10, 340, 360,
                     25, 30, True, 5, "Brygga D", "flex"))
        slots.extend(create_slot_row(430, 10, 430, 360,
                     25, 30, True, 5, "Brygga E", "flex"))
        slots.extend(create_slot_row(440, 10, 520, 360,
                     25, 30, True, 5, "Brygga F", "flex"))

        # Nedre bryggorna (301-346)
        slots.extend(create_slot_row(301, 23, 290, 720,
                     20, 30, False, 3, "Brygga G", "flex"))
        slots.extend(create_slot_row(324, 23, 290, 780,
                     20, 30, False, 3, "Brygga H", "flex"))

        # Gästhamn (201-246)
        slots.extend(create_slot_row(201, 25, 160, 960, 20,
                     30, False, 3, "Gästhamn", "guest"))

        # Nedersta bryggorna (101-181)
        slots.extend(create_slot_row(101, 40, 160, 1160, 15, 30,
                     False, 2, "Brygga J", "permanent", "occupied"))
        slots.extend(create_slot_row(141, 40, 160, 1250, 15, 30,
                     False, 2, "Brygga K", "permanent", "occupied"))

        # Udden (50-59)
        slots.extend(create_slot_row(50, 10, 45, 1340,
                     20, 18, True, 2, "Udden", "guest"))

        # Drop-in områden
        slots.append(
            Slot(
                id=901,
                name="Gästhamn DROP-IN 1",
                position_x=250,
                position_y=990,
                width=200,
                length=40,
                depth=3.0,
                max_width=10.0,
                slot_type="guest_drop_in",
                status="available",
                price_per_day=250,
                dock_id=saved_docks["Gästhamn"].id
            )
        )

        slots.append(
            Slot(
                id=902,
                name="Gästhamn DROP-IN 2",
                position_x=460,
                position_y=990,
                width=180,
                length=40,
                depth=3.0,
                max_width=10.0,
                slot_type="guest_drop_in",
                status="available",
                price_per_day=250,
                dock_id=saved_docks["Gästhamn"].id
            )
        )

        # Båstupläggning (text i högerkant på bilden)
        slots.append(
            Slot(
                id=903,
                name="Båstupläggning",
                position_x=700,
                position_y=990,
                width=40,
                length=100,
                depth=0,
                max_width=0,
                slot_type="other",
                status="available",
                price_per_day=0,
                dock_id=saved_docks["Gästhamn"].id
            )
        )

        # Spara alla platser
        await db.add_all(slots)
        await db.commit()

        logger.info(
            f"Harbor layout created with {len(docks)} docks and {len(slots)} slots")

        return {
            "message": "Harbor layout created successfully",
            "docks_count": len(docks),
            "slots_count": len(slots),
            "slot_types": {
                "guest": len([s for s in slots if s.slot_type == "guest"]),
                "flex": len([s for s in slots if s.slot_type == "flex"]),
                "permanent": len([s for s in slots if s.slot_type == "permanent"]),
                "guest_drop_in": len([s for s in slots if s.slot_type == "guest_drop_in"]),
                "other": len([s for s in slots if s.slot_type == "other"])
            }
        }
    except Exception as e:
        await db.rollback()
        error = handle_exception(e)
        raise HTTPException(
            status_code=500, detail=f"Failed to create harbor layout: {error}")

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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Hantera valideringsfel med detaljerade meddelanden"""
    error_detail = {"errors": []}
    for error in exc.errors():
        error_detail["errors"].append({
            "location": error["loc"],
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(f"Validation error: {error_detail}")
    return await request_validation_exception_handler(request, exc)

# Kör servern om denna fil körs direkt
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    uvicorn.run(app, host="0.0.0.0", port=8001)
