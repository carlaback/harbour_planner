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

    # API-versionsträng för versionering av endpoints
    API_V1_STR: str = "/api/v1"

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

    # Alternativ modell för enklare uppgifter (kostnadsoptimering)
    GPT_MODEL_SIMPLE: str = os.getenv("GPT_MODEL_SIMPLE", "gpt-3.5-turbo")

    # Temperatur för GPT-generering (0.0-1.0, lägre = mer deterministiskt)
    GPT_TEMPERATURE: float = float(os.getenv("GPT_TEMPERATURE", "0.2"))

    # Temperatur för kreativa uppgifter (rekommendationer, brainstorming)
    GPT_TEMPERATURE_CREATIVE: float = float(
        os.getenv("GPT_TEMPERATURE_CREATIVE", "0.7"))

    # Max antal tokens i GPT-svar
    GPT_MAX_TOKENS: int = int(os.getenv("GPT_MAX_TOKENS", "3000"))

    # Max tokens för enkla frågor
    GPT_MAX_TOKENS_SIMPLE: int = int(
        os.getenv("GPT_MAX_TOKENS_SIMPLE", "1000"))

    # Timeout i sekunder för GPT API-anrop
    GPT_TIMEOUT: int = int(os.getenv("GPT_TIMEOUT", "120"))

    # Max antal omförsök vid GPT API-fel
    GPT_MAX_RETRIES: int = int(os.getenv("GPT_MAX_RETRIES", "3"))

    # Väntetid mellan omförsök (sekunder)
    GPT_RETRY_DELAY: int = int(os.getenv("GPT_RETRY_DELAY", "2"))

    """AI-analysinställningar"""

    # Aktivera Chain of Thought reasoning för djupare analys
    AI_CHAIN_OF_THOUGHT: bool = os.getenv(
        "AI_CHAIN_OF_THOUGHT", "true").lower() == "true"

    # Aktivera learning system för förbättrad analys över tid
    AI_LEARNING_SYSTEM: bool = os.getenv(
        "AI_LEARNING_SYSTEM", "true").lower() == "true"

    # Minimalt konfidensnivå för AI-rekommendationer (0.0-1.0)
    AI_MIN_CONFIDENCE: float = float(os.getenv("AI_MIN_CONFIDENCE", "0.6"))

    # Max antal strategier att analysera i detalj samtidigt
    AI_MAX_STRATEGIES_DETAILED: int = int(
        os.getenv("AI_MAX_STRATEGIES_DETAILED", "5"))

    # Aktivera caching av AI-analyser
    AI_CACHE_ENABLED: bool = os.getenv(
        "AI_CACHE_ENABLED", "true").lower() == "true"

    # Cachetid för AI-analyser i timmar
    AI_CACHE_TTL_HOURS: int = int(os.getenv("AI_CACHE_TTL_HOURS", "24"))

    """Strategiinställningar"""

    # Lista över strateginamn som ska köras som standard om inga specifika anges
    DEFAULT_STRATEGIES: List[str] = [
        "largest_first",
        "smallest_first",
        "best_fit",
        "earliest_arrival",
        "temporary_first",
        "hybrid_optimal",
        "multi_objective",
        "constraint_based"
    ]

    # Maximal körtid i sekunder för en enskild strategi
    # Om strategin tar längre tid avbryts den (skyddar mot oändliga loopar)
    STRATEGY_TIMEOUT: int = int(os.getenv("STRATEGY_TIMEOUT", "30"))

    # Kör strategier parallellt för bättre prestanda
    STRATEGY_PARALLEL_EXECUTION: bool = os.getenv(
        "STRATEGY_PARALLEL_EXECUTION", "true").lower() == "true"

    # Max antal strategier som kan köras parallellt
    STRATEGY_MAX_PARALLEL: int = int(os.getenv("STRATEGY_MAX_PARALLEL", "4"))

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

    # Spara utvärderingsresultat till fil för senare analys
    SAVE_EVALUATION_RESULTS: bool = os.getenv(
        "SAVE_EVALUATION_RESULTS", "false").lower() == "true"

    # Katalog för sparade utvärderingsresultat
    EVALUATION_RESULTS_DIR: str = os.getenv(
        "EVALUATION_RESULTS_DIR", "evaluation_results")

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

    # Aktivera strukturerad loggning (JSON-format)
    STRUCTURED_LOGGING: bool = os.getenv(
        "STRUCTURED_LOGGING", "false").lower() == "true"

    """Säkerhetsinställningar"""

    # Secret key för JWT-tokens och andra säkerhetsfunktioner
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "your-secret-key-change-in-production")

    # Rate limiting för API-endpoints (requests per minut)
    API_RATE_LIMIT: int = int(os.getenv("API_RATE_LIMIT", "100"))

    # Rate limiting för AI-endpoints (lägre gräns p.g.a. kostnad)
    AI_RATE_LIMIT: int = int(os.getenv("AI_RATE_LIMIT", "10"))

    """Cacheinställningar"""

    # Aktivera Redis-cache för prestanda
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "false").lower() == "true"

    # Redis-anslutning
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Standard cache TTL i sekunder
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 timme

    """Testdata-inställningar"""

    # Antal båtar att skapa vid generering av testdata
    TEST_BOATS_COUNT: int = int(os.getenv("TEST_BOATS_COUNT", "50"))

    # Antal platser att skapa vid generering av testdata
    TEST_SLOTS_COUNT: int = int(os.getenv("TEST_SLOTS_COUNT", "100"))

    # Procent av platserna som ska vara temporärt tillgängliga
    TEST_TEMP_SLOTS_PERCENT: float = float(
        os.getenv("TEST_TEMP_SLOTS_PERCENT", "20.0"))

    """Utvecklingsinställningar"""

    # Aktivera automatisk dokumentationsgenerering
    AUTO_GENERATE_DOCS: bool = os.getenv(
        "AUTO_GENERATE_DOCS", "true").lower() == "true"

    # Aktivera detaljerad prestanda-profiling
    ENABLE_PROFILING: bool = os.getenv(
        "ENABLE_PROFILING", "false").lower() == "true"

    # Sökväg för exporterade profileringsresultat
    PROFILING_OUTPUT_DIR: str = os.getenv(
        "PROFILING_OUTPUT_DIR", "profiling_results")

    """Produktionsinställningar"""

    # Körmiljö (development, staging, production)
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Aktivera detaljerade felmeddelanden (inaktivera i produktion)
    SHOW_ERROR_DETAILS: bool = os.getenv(
        "SHOW_ERROR_DETAILS", "true").lower() == "true"

    # Aktivera healthcheck endpoints
    ENABLE_HEALTH_CHECKS: bool = os.getenv(
        "ENABLE_HEALTH_CHECKS", "true").lower() == "true"

    class Config:
        """Konfigurationsklass för Pydantic BaseSettings"""
        # Sökväg till .env-fil (relativ till arbetskatalogen)
        env_file = ".env"

        # Öm miljövariabelnamn ska vara skiftlägeskänsliga
        case_sensitive = True

        # Extra miljövariabler som ska ignoreras
        # Detta är användbart om det finns miljövariabler som inte är relevanta för appen
        # ignore_extra = "ignore"

    def is_production(self) -> bool:
        """Kontrollera om applikationen körs i produktionsmiljö"""
        return self.ENVIRONMENT.lower() == "production"

    def is_development(self) -> bool:
        """Kontrollera om applikationen körs i utvecklingsmiljö"""
        return self.ENVIRONMENT.lower() == "development"

    def get_gpt_model_for_task(self, task_complexity: str = "normal") -> str:
        """
        Välj lämplig GPT-modell baserat på uppgiftens komplexitet

        Args:
            task_complexity: "simple", "normal", eller "complex"

        Returns:
            Modellnamn att använda
        """
        if task_complexity == "simple":
            return self.GPT_MODEL_SIMPLE
        elif task_complexity == "complex":
            return self.GPT_MODEL
        else:
            return self.GPT_MODEL

    def get_gpt_temperature_for_task(self, task_type: str = "analytical") -> float:
        """
        Välj lämplig temperatur baserat på uppgiftstyp

        Args:
            task_type: "analytical" eller "creative"

        Returns:
            Temperatur att använda
        """
        if task_type == "creative":
            return self.GPT_TEMPERATURE_CREATIVE
        else:
            return self.GPT_TEMPERATURE


# Skapa en global instans av inställningarna
# Detta objekt importeras sedan av andra moduler för att få åtkomst till inställningarna
settings = Settings()

# Om du behöver åsidosätta specifika inställningar för testning:
if os.getenv("TESTING") == "true":
    settings.DEBUG = True
    # Använd en SQLite-databas i minnet för tester
    settings.DATABASE_URL = "sqlite:///:memory:"
    # Inaktivera AI-funktioner i tester om ingen API-nyckel finns
    if not settings.OPENAI_API_KEY:
        settings.AI_CHAIN_OF_THOUGHT = False
        settings.AI_LEARNING_SYSTEM = False
