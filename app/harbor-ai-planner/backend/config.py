import os
from typing import List, Dict, Any
from pydantic import BaseSettings


class Settings(BaseSettings):

    # Applikationsnamn som visas i API-dokumentation och loggar
    APP_NAME: str = "Harbor Planning System"

    # Versionsnummer för applikationen
    VERSION: str = "1.0.0"

    # Debug-läge - påverkar loggning, felmeddelanden, och auto-reload
    # Hämtar från miljövariabeln DEBUG om den finns, annars default "true"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # ----------------
    # Databasinställningar
    # ----------------

    # Anslutningssträng till databasen
    # Format: "postgresql://användare:lösenord@host/databasnamn"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost/harbor_db"
    )

    # Antal anslutningar i pool (för hantering av många samtidiga förfrågningar)
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))

    # Max antal överflödiga anslutningar att hålla i poolen
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))

    # Timeout i sekunder innan en anslutning återanvänds
    DB_POOL_RECYCLE: int = int(
        os.getenv("DB_POOL_RECYCLE", "1800"))  # 30 minuter
