# gpt_analyzer.py - omarbetad version
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import logging
import asyncio
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletionMessage
from models import Boat, Slot
from config import settings

# Konfigurera loggning
logger = logging.getLogger(__name__)


class GPTAnalyzer:
    """
    Analyserar strategier och ger rekommendationer med hjälp av GPT.
    Förbättrad version med asynkron hantering, bättre felhantering och mer nyanserade analyser.
    """

    def __init__(self, settings_obj=None):
        """
        Initierar GPT-analysatorn med konfiguration.

        Args:
            settings_obj: Konfigurationsobjekt (använder global settings om None)
        """
        self.settings = settings_obj or settings
        self.api_key = self.settings.OPENAI_API_KEY
        self.model = self.settings.GPT_MODEL
        self.temperature = self.settings.GPT_TEMPERATURE
        self.max_tokens = self.settings.GPT_MAX_TOKENS
        self.timeout = self.settings.GPT_TIMEOUT

        # Initiera klienter om API-nyckel finns
        self.client = None
        self.async_client = None

        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, timeout=self.timeout)
            self.async_client = AsyncOpenAI(
                api_key=self.api_key, timeout=self.timeout)
            logger.info(f"GPT API initialized with model {self.model}")
        else:
            logger.warning(
                "No OpenAI API key configured, GPT analysis unavailable")

    async def analyze_strategies(self, evaluation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analysera resultaten från olika strategier och ge rekommendationer.

        Args:
            evaluation_results: Lista med utvärderingsresultat för olika strategier

        Returns:
            Analys och rekommendationer från GPT
        """
        if not self.api_key or not self.async_client:
            logger.error(
                "OpenAI API key not configured or client initialization failed")
            return self._create_error_response("OpenAI API key not configured")

        try:
            # Skapa en detaljerad sammanfattning av resultaten
            summary = self._create_summary(evaluation_results)

            # Skapa en mer nyanserad prompt för GPT
            prompt = self._create_enhanced_prompt(summary)

            # Anropa GPT-API asynkront
            response = await self._async_call_gpt(prompt)

            # Extrahera och formatera svaret
            if not response:
                return self._create_error_response("Failed to get response from GPT API")

            analysis = response.content

            # Strukturera och tolka analysen för att förse bättre insikter
            structured_analysis = self._structure_analysis(analysis)

            return {
                "analysis": analysis,
                "summary": summary,
                "structured_analysis": structured_analysis,
                "recommendation": self._extract_recommendation(analysis),
                "top_strategy": self._extract_top_strategy(analysis, summary),
                "improvement_suggestions": self._extract_improvement_suggestions(analysis)
            }

        except Exception as e:
            logger.exception(f"Error during GPT analysis: {str(e)}")
            return self._create_error_response(f"Error during GPT analysis: {str(e)}")

    def _create_summary(self, evaluation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Skapa en detaljerad sammanfattning av utvärderingsresultaten.

        Args:
            evaluation_results: Lista med utvärderingsresultat

        Returns:
            Strukturerad sammanfattning av resultaten
        """
        try:
            # Grundläggande sammanfattning
            summary = {
                "total_strategies": len(evaluation_results),
                "strategies": [],
                "best_strategy": None,
                "worst_strategy": None,
                "average_placement_rate": 0.0,
                "average_width_utilization": 0.0,
                "total_stays": 0
            }

            # Samla strategidata
            placement_rates = []
            width_utilizations = []

            for result in evaluation_results:
                metrics = result.get("metrics", {})
                placement_rate = metrics.get("placement_rate", 0.0)
                width_util = metrics.get("average_width_utilization", 0.0)
                boats_placed = metrics.get("boats_placed", 0)

                strategy_summary = {
                    "name": result.get("strategy_name", "Unknown"),
                    "description": result.get("strategy_description", ""),
                    "metrics": metrics,
                    "stays_count": len(result.get("stays", [])),
                    "relative_performance": 0.0  # Beräknas senare
                }

                summary["strategies"].append(strategy_summary)
                placement_rates.append(placement_rate)
                width_utilizations.append(width_util)
                summary["total_stays"] += strategy_summary["stays_count"]

            # Beräkna genomsnitt om det finns data
            if placement_rates:
                summary["average_placement_rate"] = sum(
                    placement_rates) / len(placement_rates)
            if width_utilizations:
                summary["average_width_utilization"] = sum(
                    width_utilizations) / len(width_utilizations)

            # Hitta bästa och sämsta strategin baserat på en kombinerad poäng
            if summary["strategies"]:
                for strategy in summary["strategies"]:
                    metrics = strategy["metrics"]
                    # Kombinerad poäng: 60% placeringsgrad, 40% breddutnyttjande
                    combined_score = 0.6 * \
                        metrics.get("placement_rate", 0.0) + 0.4 * \
                        metrics.get("average_width_utilization", 0.0)
                    strategy["combined_score"] = combined_score

                # Sortera efter kombinerad poäng
                sorted_strategies = sorted(
                    summary["strategies"],
                    key=lambda x: x["combined_score"],
                    reverse=True
                )

                # Sätt relativ prestanda jämfört med bästa strategin
                best_score = sorted_strategies[0]["combined_score"] if sorted_strategies else 0
                for strategy in summary["strategies"]:
                    if best_score > 0:
                        strategy["relative_performance"] = strategy["combined_score"] / best_score

                # Spara bästa och sämsta strategi
                summary["best_strategy"] = sorted_strategies[0] if sorted_strategies else None
                summary["worst_strategy"] = sorted_strategies[-1] if len(
                    sorted_strategies) > 1 else None

            return summary

        except Exception as e:
            logger.exception(f"Error creating result summary: {str(e)}")
            return {"total_strategies": len(evaluation_results), "strategies": [], "error": str(e)}

    def _create_enhanced_prompt(self, summary: Dict[str, Any]) -> str:
        """
        Skapa en mer nyanserad prompt för GPT baserad på sammanfattningen.

        Args:
            summary: Sammanfattning av strategiresultat

        Returns:
            Prompt för GPT
        """
        prompt = f"""Analysera följande resultat från ett hamnplaneringssystem. 
Du är en expert på optimering av hamnplatser och båtplacering.

Antal utvärderade strategier: {summary['total_strategies']}

Sammanfattning:
- Genomsnittlig placeringsgrad: {summary['average_placement_rate']:.2%}
- Genomsnittligt breddutnyttjande: {summary['average_width_utilization']:.2%}
- Totalt antal placeringar: {summary['total_stays']}

Strategiresultat:
"""

        # Lägg till data för varje strategi
        for i, strategy in enumerate(summary["strategies"]):
            metrics = strategy["metrics"]
            relative_performance = strategy["relative_performance"] * 100

            prompt += f"""
Strategi {i+1}: {strategy['name']}
Beskrivning: {strategy['description']}
- Antal placerade båtar: {metrics.get('boats_placed', 0)}
- Placeringsgrad: {metrics.get('placement_rate', 0.0):.2%}
- Genomsnittligt breddutnyttjande: {metrics.get('average_width_utilization', 0.0):.2%}
- Antal placeringar: {strategy['stays_count']}
- Relativ prestanda: {relative_performance:.1f}% av bästa strategin
"""

        # Lägg till bästa och sämsta strategier om de finns
        if summary.get("best_strategy"):
            best = summary["best_strategy"]
            prompt += f"\nBästa strategin verkar vara: {best['name']} med placeringsgrad {best['metrics'].get('placement_rate', 0.0):.2%} och breddutnyttjande {best['metrics'].get('average_width_utilization', 0.0):.2%}.\n"

        prompt += """
Vänligen analysera resultaten och fokusera på:
1. Vilken strategi presterar bäst och varför? Analysera både placeringsgrad och effektivitet.
2. Vad är de viktigaste styrkorna och svagheterna för varje strategi?
3. Finns det mönster eller insikter från resultaten som kan användas för att förbättra hamnplaneringen?
4. Specifika rekommendationer för att förbättra båtplaceringen och maximera hamnens kapacitet.
5. Skulle en hybridstrategi potentiellt kunna prestera bättre än någon av de enskilda strategierna?

Svara i tydliga punkter som kan användas av hamnoperatörerna. Avsluta med en sammanfattande rekommendation.
"""

        return prompt

    async def _async_call_gpt(self, prompt: str) -> Optional[ChatCompletionMessage]:
        """
        Anropa GPT-API asynkront.

        Args:
            prompt: Prompt att skicka till GPT

        Returns:
            GPT-svar eller None vid fel
        """
        if not self.async_client:
            logger.error("AsyncOpenAI client not initialized")
            return None

        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Du är en expert på hamnoptimering och båtplaceringsstrategier. Ge specifika, detaljerade och praktiska råd."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            return response.choices[0].message if response.choices else None

        except asyncio.TimeoutError:
            logger.error(
                f"GPT API call timed out after {self.timeout} seconds")
            return None
        except Exception as e:
            logger.exception(f"Error calling GPT API: {str(e)}")
            return None

    def _structure_analysis(self, analysis: str) -> Dict[str, Any]:
        """
        Strukturera GPT-analysen i kategorier för lättare användning.

        Args:
            analysis: Textanalys från GPT

        Returns:
            Strukturerad analys indelad i kategorier
        """
        categories = {
            "best_strategy": "",
            "strategy_insights": [],
            "improvement_suggestions": [],
            "hybrid_approach": "",
            "conclusion": ""
        }

        # Enkel parsning av sektioner baserat på nyckelord
        lines = analysis.split('\n')
        current_category = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Identifiera sektioner baserat på innehåll
            lower_line = line.lower()
            if "bäst" in lower_line and "strategi" in lower_line and len(line) < 100:
                current_category = "best_strategy"
                categories[current_category] = line
            elif "förbättr" in lower_line or "rekommend" in lower_line:
                current_category = "improvement_suggestions"
                if line not in categories[current_category]:
                    categories[current_category].append(line)
            elif "hybrid" in lower_line or "kombination" in lower_line:
                current_category = "hybrid_approach"
                categories[current_category] = line
            elif "sammanfattning" in lower_line or "slutsats" in lower_line or "avslutningsvis" in lower_line:
                current_category = "conclusion"
                categories[current_category] = line
            elif line.startswith(('-', '•', '*', '1.', '2.', '3.')) and current_category:
                # Lägg till punkter till aktuell kategori
                if current_category == "improvement_suggestions":
                    if line not in categories[current_category]:
                        categories[current_category].append(line)
                elif current_category == "strategy_insights":
                    categories[current_category].append(line)
            elif "strategi" in lower_line and len(line) < 100 and not current_category:
                current_category = "strategy_insights"
                categories[current_category].append(line)

        return categories

    def _extract_recommendation(self, analysis: str) -> str:
        """
        Extrahera den viktigaste rekommendationen från analysen.

        Args:
            analysis: Textanalys från GPT

        Returns:
            Den viktigaste rekommendationen som hittats i texten
        """
        # Sök efter rekommendationer i texten
        recommendation_keywords = [
            "rekommendation:", "rekommenderar", "bästa alternativet är",
            "slutsats:", "sammantaget", "sammanfattningsvis",
            "avslutningsvis", "viktigaste åtgärden"
        ]

        lines = analysis.split('\n')

        # Först, leta efter tydliga rekommendationsrader
        for line in lines:
            line = line.strip()
            if not line:
                continue

            lower_line = line.lower()
            for keyword in recommendation_keywords:
                if keyword in lower_line and len(line) > 20:
                    return line

        # Leta efter sista stycket eller sista meningen
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        if non_empty_lines:
            # Försök med sista stycket först
            last_paragraph = non_empty_lines[-1]
            if len(last_paragraph) > 20:
                return last_paragraph

            # Om sista stycket är för kort, ta de tre sista icke-tomma raderna
            if len(non_empty_lines) >= 3:
                return " ".join(non_empty_lines[-3:])

        return "Ingen specifik rekommendation hittad."

    def _extract_top_strategy(self, analysis: str, summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrahera information om den bästa strategin från analysen.

        Args:
            analysis: Textanalys från GPT
            summary: Sammanfattning av strategiresultat

        Returns:
            Information om den bästa strategin
        """
        # Standardvärde - använd den statistiskt bästa strategin från sammanfattningen
        best_strategy = {
            "name": summary.get("best_strategy", {}).get("name", "Unknown"),
            "reason": "Högst kombinerad poäng (placeringsgrad och breddutnyttjande)."
        }

        # Försök hitta GPT:s analys av bästa strategin
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            lower_line = line.lower()

            if ("bäst" in lower_line and "strategi" in lower_line) or \
               ("perform" in lower_line and "best" in lower_line):
                best_strategy["gpt_analysis"] = line.strip()

                # Försök hitta motivering på efterföljande rader
                if i + 1 < len(lines) and lines[i+1].strip():
                    best_strategy["reason"] = lines[i+1].strip()

                # Kontrollera om namnet på strategin nämns
                for strategy in summary.get("strategies", []):
                    if strategy["name"].lower() in lower_line:
                        best_strategy["name"] = strategy["name"]
                        break

                break

        return best_strategy

    def _extract_improvement_suggestions(self, analysis: str) -> List[str]:
        """
        Extrahera specifika förbättringsförslag från analysen.

        Args:
            analysis: Textanalys från GPT

        Returns:
            Lista med förbättringsförslag
        """
        suggestions = []

        lines = analysis.split('\n')
        in_suggestions_section = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            lower_line = line.lower()

            # Identifiera förbättringssektioner
            if ("förbättr" in lower_line or "rekommend" in lower_line) and \
               ("hamn" in lower_line or "layout" in lower_line or "strategi" in lower_line):
                in_suggestions_section = True
                continue

            # Samla punkter i förbättringssektionen
            if in_suggestions_section and line.startswith(('-', '•', '*', '1.', '2.', '3.')):
                suggestions.append(line)
            elif in_suggestions_section and len(suggestions) > 0 and not any(c.isdigit() for c in line[:2]):
                # Avsluta sektionen om vi har samlat några förslag och kommit till en ny sektion
                in_suggestions_section = False

        # Om inga specifika förslag hittades, analysera hela texten för förslag
        if not suggestions:
            for line in lines:
                if "bör" in line.lower() or "kan" in line.lower() or "skulle" in line.lower():
                    # Tillräckligt lång för att vara ett meningsfullt förslag
                    if len(line.strip()) > 30:
                        suggestions.append(line.strip())

            # Begränsa till 3 förslag om vi hittade många
            suggestions = suggestions[:3]

        return suggestions

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """
        Skapa ett standardiserat felsvar.

        Args:
            error_message: Felmeddelande

        Returns:
            Formaterat felsvar
        """
        logger.error(error_message)
        return {
            "error": error_message,
            "recommendation": "Kontakta systemadministratören om problemet kvarstår.",
            "timestamp": datetime.now().isoformat()
        }

    # Behåll den gamla metoden för bakåtkompatibilitet, men märk som föråldrad
    def analyze_strategies_old(self, strategy_evaluations: Dict[str, Dict[str, Any]],
                               boats: List[Boat], slots: List[Slot]) -> Dict[str, Any]:
        """
        FÖRÅLDRAD: Analyserar strategier och ger rekommendationer.
        Behållen för bakåtkompatibilitet.
        """
        logger.warning(
            "Using deprecated analyze_strategies_old method. Please update to analyze_strategies.")

        if not self.client:
            return self._create_error_response("OpenAI API key not configured")

        try:
            # Samla grundläggande data
            analysis_data = {
                "boats": self._summarize_boats(boats),
                "slots": self._summarize_slots(slots),
                "strategies": strategy_evaluations,
                "bottlenecks": self._find_bottlenecks(boats, slots)
            }

            # Skapa prompt och få GPT-svar
            prompt = self._create_analysis_prompt(analysis_data)
            gpt_response = self._get_gpt_response(prompt)

            return self._extract_json_from_response(gpt_response)

        except Exception as e:
            return self._create_error_response(f"Error in analyze_strategies_old: {str(e)}")

    # Behåll hjälpmetoder för bakåtkompatibilitet
    def _summarize_boats(self, boats: List[Boat]) -> Dict[str, Any]:
        """Sammanfattar båtdata"""
        return {
            "total": len(boats),
            "widths": {
                "min": min(b.width for b in boats) if boats else 0,
                "max": max(b.width for b in boats) if boats else 0,
                "avg": sum(b.width for b in boats) / len(boats) if boats else 0
            },
            "time_range": {
                "earliest": min(b.arrival for b in boats) if boats else None,
                "latest": max(b.departure for b in boats) if boats else None
            }
        }

    def _summarize_slots(self, slots: List[Slot]) -> Dict[str, Any]:
        """Sammanfattar platsdata"""
        return {
            "total": len(slots),
            "widths": {
                "min": min(s.max_width for s in slots) if slots else 0,
                "max": max(s.max_width for s in slots) if slots else 0,
                "avg": sum(s.max_width for s in slots) / len(slots) if slots else 0
            }
        }

    def _find_bottlenecks(self, boats: List[Boat], slots: List[Slot]) -> Dict[str, Any]:
        """Identifierar potentiella flaskhalsar"""
        return {
            "width_mismatch": max(b.width for b in boats) > max(s.max_width for s in slots) if boats and slots else False,
            "capacity_issue": len(boats) > len(slots),
            "time_conflict": self._check_time_conflicts(boats)
        }

    def _check_time_conflicts(self, boats: List[Boat]) -> bool:
        """Kontrollerar om det finns tidskonflikter"""
        if not boats or len(boats) < 2:
            return False

        time_slots = [(b.arrival, b.departure) for b in boats]
        time_slots.sort(key=lambda x: x[0])

        for i in range(len(time_slots)-1):
            if time_slots[i][1] > time_slots[i+1][0]:
                return True
        return False

    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Skapar en prompt för GPT-analys"""
        return f"""
        Analysera följande hamndata och ge rekommendationer:
        
        Båtar: {data['boats']['total']} st
        - Bredd: {data['boats']['widths']['min']:.1f}m - {data['boats']['widths']['max']:.1f}m
        - Tidsperiod: {data['boats']['time_range']['earliest']} till {data['boats']['time_range']['latest']}
        
        Platser: {data['slots']['total']} st
        - Bredd: {data['slots']['widths']['min']:.1f}m - {data['slots']['widths']['max']:.1f}m
        
        Flaskhalsar:
        - Breddmismatch: {'Ja' if data['bottlenecks']['width_mismatch'] else 'Nej'}
        - Kapacitetsproblem: {'Ja' if data['bottlenecks']['capacity_issue'] else 'Nej'}
        - Tidskonflikter: {'Ja' if data['bottlenecks']['time_conflict'] else 'Nej'}
        
        Strategier:
        {self._format_strategies(data['strategies'])}
        
        Ge en detaljerad analys och rekommendationer i JSON-format.
        """

    def _format_strategies(self, strategies: Dict[str, Dict[str, Any]]) -> str:
        """Formaterar strategidata för prompten"""
        return "\n".join(
            f"- {name}: {data.get('placed_boats_percent', 0):.1%} placerade båtar"
            for name, data in strategies.items()
        )

    def _get_gpt_response(self, prompt: str) -> str:
        """Hämtar svar från GPT"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.exception(f"Error getting GPT response: {str(e)}")
            return f"Failed to get analysis: {str(e)}"

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extraherar JSON från GPT-svaret"""
        try:
            # Hitta JSON i svaret
            json_str = response[response.find("{"):response.rfind("}")+1]
            return json.loads(json_str)
        except Exception as e:
            logger.exception(f"Error parsing GPT response: {str(e)}")
            return {"error": f"Failed to parse GPT response: {str(e)}"}
