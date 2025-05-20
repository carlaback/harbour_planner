# test_your_analyzer_fixed.py
import asyncio
from gpt_analyzer import GPTAnalyzer
from config import settings

# Skapa en adapter som översätter attributnamn


class SettingsAdapter:
    def __init__(self, original_settings):
        self._settings = original_settings
        # Mappa OPENAI_API_KEY till openai_api_key
        self.openai_api_key = original_settings.OPENAI_API_KEY


async def test_your_analyzer():
    """Test för att bekräfta att din befintliga GPTAnalyzer-klass fungerar med en adapter"""
    print("=== TEST AV DIN BEFINTLIGA GPTANALYZER ===")

    # Skapa testdata
    evaluation_results = [
        {
            "strategy_name": "FirstFitStrategy",
            "strategy_description": "Placerar båtar på första tillgängliga plats som passar",
            "metrics": {
                "boats_placed": 40,
                "placement_rate": 0.8,
                "average_width_utilization": 0.65,
                "total_width_utilization": 0.72
            }
        },
        {
            "strategy_name": "BestFitStrategy",
            "strategy_description": "Placerar båtar på platser som minimerar överkapacitet",
            "metrics": {
                "boats_placed": 45,
                "placement_rate": 0.9,
                "average_width_utilization": 0.78,
                "total_width_utilization": 0.82
            }
        }
    ]

    try:
        # Skapa en adapter för settings
        adapter = SettingsAdapter(settings)

        # Verifiera att API-nyckeln finns
        if not adapter.openai_api_key:
            print(
                "⚠️ Varning: Ingen OpenAI API-nyckel hittades i settings.OPENAI_API_KEY!")
            print(
                "Kontrollera att OPENAI_API_KEY är korrekt konfigurerad i config.py eller .env-filen.")
            return False

        # Skapa GPTAnalyzer med adapter
        analyzer = GPTAnalyzer(settings=adapter)

        print("GPTAnalyzer skapad med settings-adapter.")
        print(
            f"Använder API-nyckel: {adapter.openai_api_key[:4]}...{adapter.openai_api_key[-4:] if len(adapter.openai_api_key) > 8 else ''}")
        print("Anropar analyze_strategies...")

        # Anropar analyze_strategies
        result = await analyzer.analyze_strategies(evaluation_results)

        print("\nResultat:")

        if "error" in result:
            print(f"Fel: {result['error']}")
            return False
        else:
            print("\nRekommendation:")
            print(result.get("recommendation", "Ingen rekommendation tillgänglig"))

            print("\nAnalys (första 500 tecken):")
            analysis = result.get("analysis", "Ingen analys tillgänglig")
            print(analysis[:500] + "..." if len(analysis) > 500 else analysis)

            print("\n✅ GODKÄND: Din GPTAnalyzer fungerar korrekt med adapter!")
            return True

    except Exception as e:
        print(f"\n❌ FEL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_your_analyzer())
