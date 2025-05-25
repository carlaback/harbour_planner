import asyncio
import traceback
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, delete

# Importera databas-modeller
from models import Base, Dock, Slot, SlotType, SlotStatus

# ===== KONFIGURATION =====
# Ladda miljövariabler från .env
load_dotenv()

# Använd DATABASE_URL från .env-filen
DATABASE_URL = os.getenv("DATABASE_URL")

# Konvertera från PostgreSQL till PostgreSQL+asyncpg om det behövs
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://", 1)

print(f"Använder databasanslutning: {DATABASE_URL}")

# Skapa engine för att ansluta till databasen
async_engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def clear_existing_data():
    """Rensa bort befintlig data från databasen"""
    async with async_session() as db:
        try:
            # Ta bort alla rader i slots och docks tabellerna
            await db.execute(delete(Slot))
            await db.execute(delete(Dock))
            await db.commit()
            print("✓ Tidigare data har rensats från databasen")
        except Exception as e:
            print(f"✗ Fel vid rensning av data: {str(e)}")
            await db.rollback()


async def create_tables():
    """Skapa databastabeller om de inte finns"""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✓ Databastabeller har skapats eller verifierats")
    except Exception as e:
        print(f"✗ Fel vid skapande av tabeller: {str(e)}")
        raise


async def create_harbor_layout():
    """Skapa hamnlayouten enligt definierad layout"""
    async with async_session() as db:
        try:
            # För att hålla koll på vilka ID:n vi redan har använt
            used_slot_ids = set()

            # ===== SKAPA BRYGGORNA =====
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
                     position_y=290, width=40, length=220),
                Dock(name="Brygga E", position_x=460,
                     position_y=350, width=40, length=330),
                Dock(name="Brygga F", position_x=550,
                     position_y=350, width=40, length=330),

                # Nedre bryggorna (301-346)
                Dock(name="Brygga G", position_x=280,
                     position_y=750, width=450, length=30),
                Dock(name="Brygga H", position_x=280,
                     position_y=810, width=450, length=30),

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

            # Spara bryggorna
            db.add_all(docks)
            await db.commit()
            print(f"✓ {len(docks)} bryggor har skapats")

            # Hämta de skapade bryggorna för att få deras IDs
            result = await db.execute(select(Dock))
            saved_docks = {dock.name: dock for dock in result.scalars().all()}

            # ===== SKAPA PLATSER =====
            slots = []

            # Översta bryggorna (501-530)
            # Brygga A
            for i in range(5):
                slot_id = 501 + i*2
                if slot_id in used_slot_ids:
                    print(
                        f"⚠️ Varning: ID {slot_id} har redan använts. Hoppar över.")
                    continue

                used_slot_ids.add(slot_id)
                slots.append(Slot(
                    id=slot_id,
                    name=str(slot_id),
                    position_x=310 + i*60,
                    position_y=80,
                    width=30,
                    length=30,
                    depth=2.5 + (i % 5) * 0.2,
                    max_width=3.0,
                    slot_type="flex",
                    status="occupied",
                    dock_id=saved_docks["Brygga A"].id
                ))

            # Brygga B
            for i in range(12):
                slot_id = 510 + i*2
                if slot_id in used_slot_ids:
                    print(
                        f"⚠️ Varning: ID {slot_id} har redan använts. Hoppar över.")
                    continue

                used_slot_ids.add(slot_id)
                slots.append(Slot(
                    id=slot_id,
                    name=str(slot_id),
                    position_x=310 + i*23,
                    position_y=140,
                    width=20,
                    length=30,
                    depth=2.5,
                    max_width=2.5,
                    slot_type="flex",
                    status="occupied",
                    dock_id=saved_docks["Brygga B"].id
                ))

            # Mittenområdet (401-455)
            # Brygga C (vertikal brygga med platser på västsidan)
            for i in range(17):
                slot_id = 401 + i
                if slot_id in used_slot_ids:
                    print(
                        f"⚠️ Varning: ID {slot_id} har redan använts. Hoppar över.")
                    continue

                used_slot_ids.add(slot_id)
                # Platser 403 och 407 är lediga (gröna)
                status = "available" if slot_id in [403, 407] else "occupied"
                slots.append(Slot(
                    id=slot_id,
                    name=str(slot_id),
                    position_x=250,
                    position_y=290 + i*25,
                    width=25,
                    length=30,
                    depth=2.8,
                    max_width=2.5,
                    slot_type="permanent",
                    status=status,
                    dock_id=saved_docks["Brygga C"].id
                ))

            # Brygga D (första vertikala bryggan i mitten)
            for i in range(3):
                slot_id = 418 + i
                if slot_id in used_slot_ids:
                    print(
                        f"⚠️ Varning: ID {slot_id} har redan använts. Hoppar över.")
                    continue

                used_slot_ids.add(slot_id)
                slots.append(Slot(
                    id=slot_id,
                    name=str(slot_id),
                    position_x=340,
                    position_y=290 + i*25,
                    width=25,
                    length=30,
                    depth=2.8,
                    max_width=2.5,
                    slot_type="flex",
                    status="occupied",
                    dock_id=saved_docks["Brygga D"].id
                ))

            # Fortsättning Brygga D
            for i in range(4):
                slot_id = 421 + i
                if slot_id in used_slot_ids:
                    print(
                        f"⚠️ Varning: ID {slot_id} har redan använts. Hoppar över.")
                    continue

                used_slot_ids.add(slot_id)
                slots.append(Slot(
                    id=slot_id,
                    name=str(slot_id),
                    position_x=340,
                    position_y=370 + i*25,
                    width=25,
                    length=30,
                    depth=2.8,
                    max_width=2.5,
                    slot_type="flex",
                    status="occupied",
                    dock_id=saved_docks["Brygga D"].id
                ))

            # Brygga E (andra vertikala bryggan i mitten)
            for i in range(10):
                slot_id = 430 + i
                if slot_id in used_slot_ids:
                    print(
                        f"⚠️ Varning: ID {slot_id} har redan använts. Hoppar över.")
                    continue

                used_slot_ids.add(slot_id)
                # Plats 437 är ledig (grön)
                status = "available" if slot_id == 437 else "occupied"
                slots.append(Slot(
                    id=slot_id,
                    name=str(slot_id),
                    position_x=430,
                    position_y=370 + i*25,
                    width=25,
                    length=30,
                    depth=2.8,
                    max_width=2.5,
                    slot_type="flex",
                    status=status,
                    dock_id=saved_docks["Brygga E"].id
                ))

            # Fortsättning Brygga E
            for i in range(3):
                slot_id = 440 + i*2
                if slot_id in used_slot_ids:
                    print(
                        f"⚠️ Varning: ID {slot_id} har redan använts. Hoppar över.")
                    continue

                used_slot_ids.add(slot_id)
                slots.append(Slot(
                    id=slot_id,
                    name=str(slot_id),
                    position_x=430,
                    position_y=530 + i*25,
                    width=25,
                    length=30,
                    depth=2.8,
                    max_width=2.5,
                    slot_type="flex",
                    status="occupied",
                    dock_id=saved_docks["Brygga E"].id
                ))

            for i in range(3):
                slot_id = 446 + i*2
                if slot_id in used_slot_ids:
                    print(
                        f"⚠️ Varning: ID {slot_id} har redan använts. Hoppar över.")
                    continue

                used_slot_ids.add(slot_id)
                slots.append(Slot(
                    id=slot_id,
                    name=str(slot_id),
                    position_x=430,
                    position_y=605 + i*25,
                    width=25,
                    length=30,
                    depth=2.8,
                    max_width=2.5,
                    slot_type="flex",
                    status="occupied",
                    dock_id=saved_docks["Brygga E"].id
                ))

            # Brygga F (tredje vertikala bryggan i mitten)
            # Ändrat från 430+100+i till 550+i för att undvika krock med ID 530
            for i in range(11):
                slot_id = 550 + i  # Ändrat från 430+100+i till 550+i
                if slot_id in used_slot_ids:
                    print(
                        f"⚠️ Varning: ID {slot_id} har redan använts. Hoppar över.")
                    continue

                used_slot_ids.add(slot_id)
                slots.append(Slot(
                    id=slot_id,
                    name=str(slot_id),
                    position_x=520,
                    position_y=370 + i*25,
                    width=25,
                    length=30,
                    depth=2.8,
                    max_width=2.5,
                    slot_type="flex",
                    status="occupied",
                    dock_id=saved_docks["Brygga F"].id
                ))

            # Nedre bryggorna (301-346)
            # Brygga G (första horisontella bryggan i nedre området)
            for i in range(24):
                slot_id = 300 + i
                if slot_id in used_slot_ids:
                    print(
                        f"⚠️ Varning: ID {slot_id} har redan använts. Hoppar över.")
                    continue

                used_slot_ids.add(slot_id)
                # Plats 314 är ledig (grön)
                status = "available" if slot_id == 314 else "occupied"
                slots.append(Slot(
                    id=slot_id,
                    name=str(slot_id),
                    position_x=281 + i*19,
                    position_y=720,
                    width=18,
                    length=25,
                    depth=2.5,
                    max_width=2.0,
                    slot_type="flex",
                    status=status,
                    dock_id=saved_docks["Brygga G"].id
                ))

            # Brygga H (andra horisontella bryggan i nedre området)
            for i in range(24):
                slot_id = 324 + i
                if slot_id in used_slot_ids:
                    print(
                        f"⚠️ Varning: ID {slot_id} har redan använts. Hoppar över.")
                    continue

                used_slot_ids.add(slot_id)
                # Plats 336 är ledig (grön)
                status = "available" if slot_id == 336 else "occupied"
                slots.append(Slot(
                    id=slot_id,
                    name=str(slot_id),
                    position_x=281 + i*19,
                    position_y=780,
                    width=18,
                    length=25,
                    depth=2.5,
                    max_width=2.0,
                    slot_type="flex",
                    status=status,
                    dock_id=saved_docks["Brygga H"].id
                ))

            # Gästhamn (201-246)
            for i in range(25):
                slot_id = 201 + i
                if slot_id in used_slot_ids:
                    print(
                        f"⚠️ Varning: ID {slot_id} har redan använts. Hoppar över.")
                    continue

                used_slot_ids.add(slot_id)
                # För platser 203-207 (gröna platser)
                status = "available" if slot_id in range(
                    203, 208) else "occupied"
                slots.append(Slot(
                    id=slot_id,
                    name=str(slot_id),
                    position_x=160 + i*20,
                    position_y=960,
                    width=20,
                    length=30,
                    depth=3.0,
                    max_width=2.2,
                    slot_type="guest",
                    status=status,
                    dock_id=saved_docks["Gästhamn"].id
                ))

            # Drop-in områden
            special_ids = [901, 902, 903]
            for slot_id in special_ids:
                if slot_id in used_slot_ids:
                    print(
                        f"⚠️ Varning: ID {slot_id} har redan använts. Hoppar över.")
                    continue

                used_slot_ids.add(slot_id)

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

            # Båtupläggning (på högersidan)
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

            # Nedersta bryggorna (101-181)
            # Brygga J (första nedre bryggan med lägre nummer)
            for i in range(40):
                slot_id = 101 + i*2
                if slot_id in used_slot_ids:
                    print(
                        f" Varning: ID {slot_id} har redan använts. Hoppar över.")
                    continue

                used_slot_ids.add(slot_id)
                slots.append(Slot(
                    id=slot_id,
                    name=str(slot_id),
                    position_x=160 + i*15,
                    position_y=1160,
                    width=15,
                    length=30,
                    depth=3.0,
                    max_width=1.8,
                    slot_type="permanent",
                    status="occupied",
                    dock_id=saved_docks["Brygga J"].id
                ))

            # Brygga K (andra nedre bryggan med högre nummer)
            for i in range(40):
                slot_id = 141 + i*2
                if slot_id in used_slot_ids:
                    print(
                        f"⚠️ Varning: ID {slot_id} har redan använts. Hoppar över.")
                    continue

                used_slot_ids.add(slot_id)
                slots.append(Slot(
                    id=slot_id,
                    name=str(slot_id),
                    position_x=160 + i*15,
                    position_y=1250,
                    width=15,
                    length=30,
                    depth=3.0,
                    max_width=1.8,
                    slot_type="permanent",
                    status="occupied",
                    dock_id=saved_docks["Brygga K"].id
                ))

            # Udden (50-59)
            for i in range(10):
                slot_id = 50 + i
                if slot_id in used_slot_ids:
                    print(
                        f"⚠️ Varning: ID {slot_id} har redan använts. Hoppar över.")
                    continue

                used_slot_ids.add(slot_id)
                slots.append(Slot(
                    id=slot_id,
                    name=str(slot_id),
                    position_x=45,
                    position_y=1340 + i*20,
                    width=20,
                    length=18,
                    depth=3.0,
                    max_width=2.0,
                    slot_type="guest",
                    status="occupied",
                    dock_id=saved_docks["Udden"].id
                ))

            # Spara alla platser - använd executemany för bättre prestanda om många platser
            if slots:
                print(f"Sparar {len(slots)} båtplatser...")
                db.add_all(slots)
                await db.commit()
                print(f"✓ {len(slots)} båtplatser har skapats")

            return {
                "status": "success",
                "message": "Hamnlayout skapad framgångsrikt",
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
            print(f"✗ Fel vid skapande av hamnlayout: {str(e)}")
            traceback.print_exc()
            await db.rollback()
            raise


async def verify_data():
    """Verifiera att data har skapats korrekt"""
    async with async_session() as db:
        try:
            # Räkna bryggor
            dock_count = await db.execute(select(func.count()).select_from(Dock))
            dock_count = dock_count.scalar()

            # Räkna platser
            slot_count = await db.execute(select(func.count()).select_from(Slot))
            slot_count = slot_count.scalar()

            print(
                f"✓ Verifiering av data: {dock_count} bryggor och {slot_count} båtplatser finns i databasen")

            # Visa några exempel
            if dock_count > 0:
                docks = await db.execute(select(Dock).limit(2))
                print("Exempel på bryggor:", [
                      f"ID: {d.id}, Namn: {d.name}" for d in docks.scalars()])

            if slot_count > 0:
                slots = await db.execute(select(Slot).limit(2))
                print("Exempel på platser:", [
                      f"ID: {s.id}, Namn: {s.name}, Typ: {s.slot_type}" for s in slots.scalars()])

            return {
                "dock_count": dock_count,
                "slot_count": slot_count
            }
        except Exception as e:
            print(f"✗ Fel vid verifiering av data: {str(e)}")
            traceback.print_exc()
            return {
                "error": str(e)
            }


async def main():
    """Huvudfunktion för att köra hela processen"""
    try:
        print("\n===== SKAPAR HAMNLAYOUT =====")

        # Steg 1: Skapa tabeller
        await create_tables()

        # Steg 2: Rensa befintlig data
        await clear_existing_data()

        # Steg 3: Skapa hamnlayout
        result = await create_harbor_layout()
        print(f"Resultat: {result}")

        # Steg 4: Verifiera data
        verification = await verify_data()
        print(f"Verifiering: {verification}")

        print("\n✅ PROCESS SLUTFÖRD FRAMGÅNGSRIKT!")
        print("===============================")
    except Exception as e:
        print(f"\n❌ PROCESSEN MISSLYCKADES: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
