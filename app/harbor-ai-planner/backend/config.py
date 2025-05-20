import os
from typing import List, Dict, Any
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # Applikationsnamn som visas i API-dokumentation och loggar
    APP_NAME: str = "Harbor Planning System"

    # Versionsnummer för applikationen
    VERSION: str = "1.0.0"

    # Debug-läge - påverkar loggning, felmeddelanden, och auto-reload
    # Hämtar från miljövariabeln DEBUG om den finns, annars default "true"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    """Databasinställningar"""

    # Anslutningssträng till databasen
    # Format: "postgresql+asyncpg://användare:lösenord@host/databasnamn"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/harbor_planner"
    )

    # Antal anslutningar i pool (för hantering av många samtidiga förfrågningar)
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))

    # Max antal överflödiga anslutningar att hålla i poolen
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))

    # Timeout i sekunder innan en anslutning återanvänds
    DB_POOL_RECYCLE: int = int(
        os.getenv("DB_POOL_RECYCLE", "1800"))  # 30 minuter

    """API-inställningar"""

    # Prefix för alla API-endpoints, t.ex. "/api/boats" istället för bara "/boats"
    API_PREFIX: str = "/api"

    # Maximalt antal resultat per sida för paginerade endpoints
    API_PAGE_SIZE: int = int(os.getenv("API_PAGE_SIZE", "100"))

    # Timeout i sekunder för API-förfrågningar
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "60"))

    """OpenAI/GPT-inställningar"""

    # API-nyckel för OpenAI, krävs för GPT-analys
    # MYCKET VIKTIGT: Lägg inte API-nyckeln direkt i koden, använd miljövariabler!
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Vilken GPT-modell att använda
    GPT_MODEL: str = os.getenv("GPT_MODEL", "gpt-4-turbo")

    # Temperatur för GPT-generering (0.0-1.0, lägre = mer deterministiskt)
    GPT_TEMPERATURE: float = float(os.getenv("GPT_TEMPERATURE", "0.2"))

    # Max antal tokens i GPT-svar
    GPT_MAX_TOKENS: int = int(os.getenv("GPT_MAX_TOKENS", "3000"))

    # Timeout i sekunder för GPT API-anrop
    GPT_TIMEOUT: int = int(os.getenv("GPT_TIMEOUT", "120"))

    """Strategiinställningar"""

    # Lista över strateginamn som ska köras som standard om inga specifika anges
    DEFAULT_STRATEGIES: List[str] = [
        "largest_first",
        "smallest_first",
        "best_fit",
        "earliest_arrival",
        "temporary_first",
        "optimal_width",
        "random"
    ]

    # Maximal körtid i sekunder för en enskild strategi
    # Om strategin tar längre tid avbryts den (skyddar mot oändliga loopar)
    STRATEGY_TIMEOUT: int = int(os.getenv("STRATEGY_TIMEOUT", "30"))

    """Utvärderingsparametrar"""

    # Viktning för sammansatt poäng (i procent)
    EVALUATION_WEIGHTS: Dict[str, float] = {
        # Vikt för antal placerade båtar (%)
        "placed_boats_weight": 50.0,
        # Vikt för effektivitet i breddanvändning (%)
        "efficiency_weight": 30.0,
        # Vikt för användning av temporära platser (%)
        "temp_slots_usage_weight": 20.0
    }

    """CORS-inställningar (Cross-Origin Resource Sharing)"""

    # Lista över tillåtna origins för CORS
    # "*" tillåter alla origins (bör begränsas i produktion)
    CORS_ORIGINS: List[str] = ["*"]

    # Tillåtna HTTP-metoder för CORS
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

    # Tillåtna HTTP-headers för CORS
    CORS_HEADERS: List[str] = ["*"]

    """Tidsinställningar"""

    # Tidszon för systemet
    TIMEZONE: str = "Europe/Stockholm"

    # Format för datum i API-svar
    DATE_FORMAT: str = "%Y-%m-%d"

    # Format för tid i API-svar
    TIME_FORMAT: str = "%H:%M:%S"

    # Format för datum och tid i API-svar
    DATETIME_FORMAT: str = "%Y-%m-%dT%H:%M:%S"

    """Loggningsinställningar"""

    # Loggnivå (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Sökväg till loggfil (om tom loggas endast till konsol)
    LOG_FILE: str = os.getenv("LOG_FILE", "")

    # Format för loggmeddelanden
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    """Testdata-inställningar"""

    # Antal båtar att skapa vid generering av testdata
    TEST_BOATS_COUNT: int = int(os.getenv("TEST_BOATS_COUNT", "50"))

    # Antal platser att skapa vid generering av testdata
    TEST_SLOTS_COUNT: int = int(os.getenv("TEST_SLOTS_COUNT", "100"))

    # Procent av platserna som ska vara temporärt tillgängliga
    TEST_TEMP_SLOTS_PERCENT: float = float(
        os.getenv("TEST_TEMP_SLOTS_PERCENT", "20.0"))

    class Config:
        """Konfigurationsklass för Pydantic BaseSettings"""
        # Sökväg till .env-fil (relativ till arbetskatalogen)
        env_file = ".env"

        # Öm miljövariabelnamn ska vara skiftlägeskänsliga
        case_sensitive = True

        # Extra miljövariabler som ska ignoreras
        # Detta är användbart om det finns miljövariabler som inte är relevanta för appen
        # ignore_extra = "ignore"


# Skapa en global instans av inställningarna
# Detta objekt importeras sedan av andra moduler för att få åtkomst till inställningarna
settings = Settings()

# Om du behöver åsidosätta specifika inställningar för testning:
if os.getenv("TESTING") == "true":
    settings.DEBUG = True
    # Använd en SQLite-databas i minnet för tester
    settings.DATABASE_URL = "sqlite:///:memory:"
