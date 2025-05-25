import asyncio
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, delete

# Importera databas-modeller
from models import Base, Boat

# ===== KONFIGURATION =====
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://", 1)

async_engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Realistiska båtnamn för demo
BOAT_NAMES = [
    "Sjöfarten", "Vindkraft", "Havsbris", "Kattegatt", "Skärgård", "Maritim",
    "Neptun", "Poseidon", "Triton", "Oceania", "Atlantis", "Pacific Dream",
    "Nordic Star", "Baltic Queen", "Gotland", "Öresund", "Mälardrottning",
    "Archipelago", "Coastline", "Seaside", "Marina", "Anchorage", "Harbor",
    "Sailor's Dream", "Captain's Pride", "First Mate", "Compass Rose",
    "Sunset Cruise", "Dawn Patrol", "Midnight Sun", "Aurora", "Stella Maris",
    "Sea Eagle", "Storm Petrel", "Cormorant", "Seagull", "Albatross"
]


async def clear_boats():
    """Rensa befintliga båtar"""
    async with async_session() as db:
        try:
            result = await db.execute(delete(Boat))
            await db.commit()
            print(f"🗑️  Rensade {result.rowcount} befintliga båtar")
        except Exception as e:
            print(f"❌ Fel vid rensning: {e}")
            await db.rollback()


async def add_demo_boats():
    """Lägg till realistiska demo-båtar för AI-optimering"""
    async with async_session() as db:
        try:
            # Kontrollera om det redan finns båtar
            boat_count = await db.execute(select(func.count()).select_from(Boat))
            existing_boats = boat_count.scalar()

            if existing_boats > 0:
                print(
                    f"ℹ️  Det finns redan {existing_boats} båtar i databasen")
                choice = input(
                    "Vill du rensa och skapa nya? (ja/nej): ").lower()
                if choice in ['ja', 'j', 'yes', 'y']:
                    await clear_boats()
                else:
                    print("✅ Behåller befintliga båtar")
                    return

            test_boats = []
            today = datetime.now().date()

            print("🔧 Genererar demo-båtar...")

            # Småbåtar (många, korta vistelser)
            for i in range(15):
                test_boats.append(Boat(
                    name=f"{random.choice(BOAT_NAMES)} {i+1}",
                    width=round(random.uniform(1.5, 2.2), 1),
                    arrival=today + timedelta(days=random.randint(0, 5)),
                    departure=today + timedelta(days=random.randint(2, 8))
                ))

            # Medelstora båtar (vanligast typ)
            for i in range(18):
                test_boats.append(Boat(
                    name=f"{random.choice(BOAT_NAMES)} Express {i+1}",
                    width=round(random.uniform(2.2, 2.8), 1),
                    arrival=today + timedelta(days=random.randint(0, 7)),
                    departure=today + timedelta(days=random.randint(4, 12))
                ))

            # Stora båtar (färre, längre vistelser)
            for i in range(10):
                test_boats.append(Boat(
                    name=f"{random.choice(BOAT_NAMES)} Cruiser {i+1}",
                    width=round(random.uniform(2.8, 3.5), 1),
                    arrival=today + timedelta(days=random.randint(0, 10)),
                    departure=today + timedelta(days=random.randint(8, 20))
                ))

            # Extra stora båtar (få, riktigt utmanande)
            for i in range(5):
                test_boats.append(Boat(
                    name=f"{random.choice(BOAT_NAMES)} Mega {i+1}",
                    width=round(random.uniform(3.5, 4.5), 1),
                    arrival=today + timedelta(days=random.randint(0, 8)),
                    departure=today + timedelta(days=random.randint(10, 25))
                ))

            # Problem-båtar (verkligt stora, skapar utmaning för AI)
            for i in range(3):
                test_boats.append(Boat(
                    name=f"Superbåt {i+1}",
                    width=round(random.uniform(4.5, 5.2), 1),
                    arrival=today + timedelta(days=random.randint(1, 6)),
                    departure=today + timedelta(days=random.randint(15, 30))
                ))

            # Samma-dag båtar (skapar konkurrens)
            conflict_day = today + timedelta(days=3)
            for i in range(6):
                test_boats.append(Boat(
                    name=f"Konflikt {i+1}",
                    width=round(random.uniform(2.0, 3.2), 1),
                    arrival=conflict_day,
                    departure=conflict_day +
                    timedelta(days=random.randint(3, 10))
                ))

            # Spara alla testbåtar
            db.add_all(test_boats)
            await db.commit()

            print(f"✅ {len(test_boats)} demo-båtar har skapats!")

            # Visa statistik
            small = sum(1 for b in test_boats if b.width < 2.2)
            medium = sum(1 for b in test_boats if 2.2 <= b.width < 2.8)
            large = sum(1 for b in test_boats if 2.8 <= b.width < 3.5)
            xl = sum(1 for b in test_boats if b.width >= 3.5)

            print(f"\n📊 Storleksfördelning:")
            print(f"   🚤 Små (< 2.2m): {small} båtar")
            print(f"   🛥️  Medium (2.2-2.8m): {medium} båtar")
            print(f"   🚢 Stora (2.8-3.5m): {large} båtar")
            print(f"   🛳️  Extra stora (> 3.5m): {xl} båtar")

            stays = [(b.departure - b.arrival).days for b in test_boats]
            avg_stay = sum(stays) / len(stays)
            print(f"\n⏱️  Genomsnittlig vistelse: {avg_stay:.1f} dagar")

            arriving_soon = sum(1 for b in test_boats if 0 <=
                                (b.arrival - today).days <= 7)
            print(f"📅 Ankomster nästa vecka: {arriving_soon} båtar")

            print(f"\n🎯 REDO FÖR AI-OPTIMERING!")
            print(
                f"   Nu kan du testa optimeringen med {len(test_boats)} olika båtar!")

        except Exception as e:
            print(f"❌ Fel vid skapande av testbåtar: {str(e)}")
            await db.rollback()
            raise


async def verify_boats():
    """Verifiera att båtar finns i databasen"""
    async with async_session() as db:
        try:
            boat_count = await db.execute(select(func.count()).select_from(Boat))
            total_boats = boat_count.scalar()

            print(f"✓ Totalt antal båtar i databasen: {total_boats}")

            if total_boats > 0:
                boats = await db.execute(select(Boat).limit(5))
                print("\nExempel på båtar:")
                for boat in boats.scalars():
                    days = (boat.departure - boat.arrival).days
                    print(
                        f"  - {boat.name}: {boat.width}m bred, {days} dagars vistelse")

            return total_boats

        except Exception as e:
            print(f"❌ Fel vid verifiering: {str(e)}")
            return 0


async def main():
    """Huvudfunktion"""
    try:
        print("===== DEMO-BÅTAR FÖR AI-OPTIMERING =====")

        # Lägg till demo-båtar
        await add_demo_boats()

        # Verifiera att de lagts till
        total_boats = await verify_boats()

        if total_boats > 0:
            print(
                f"\n🎉 Klart! Nu kan du testa AI-optimeringen med {total_boats} båtar.")
            print("   Gå till frontend och klicka 'Starta Automatisk Optimering'!")
        else:
            print("\n❌ Inga båtar hittades. Något gick fel.")

    except Exception as e:
        print(f"\n❌ PROCESSEN MISSLYCKADES: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
