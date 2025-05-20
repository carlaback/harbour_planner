# gpt_analyzer.py - uppdaterad version
from typing import Dict, Any, List
from datetime import datetime
import json
import os
from openai import OpenAI
from models import Boat, Slot
from config import Settings


class GPTAnalyzer:
    """Analyserar strategier och ger rekommendationer med hjälp av GPT"""

    def __init__(self, settings: Settings):
        self.settings = settings
        # Använd settings.OPENAI_API_KEY (notera versaler)
        self.api_key = settings.OPENAI_API_KEY if hasattr(
            settings, 'OPENAI_API_KEY') else settings.openai_api_key
        self.client = None

        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)

    async def analyze_strategies(self, evaluation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analysera resultaten från olika strategier och ge rekommendationer"""
        if not self.api_key or not self.client:
            return {
                "error": "OpenAI API key not configured",
                "recommendation": "Please configure OpenAI API key in settings"
            }

        try:
            # Skapa en sammanfattning av resultaten
            summary = self._create_summary(evaluation_results)

            # Generera prompt för GPT
            prompt = self._create_prompt(summary)

            # Anropa GPT API med det nya OpenAI API:et
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Använd en säkrare modell
                messages=[
                    {"role": "system", "content": "You are an expert in harbor management and boat placement optimization."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            # Extrahera och formatera svaret
            analysis = response.choices[0].message.content

            return {
                "analysis": analysis,
                "summary": summary,
                "recommendation": self._extract_recommendation(analysis)
            }

        except Exception as e:
            return {
                "error": f"Error communicating with OpenAI: {str(e)}",
                "recommendation": "Failed to analyze strategies"
            }

    def _create_summary(self, evaluation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Skapa en sammanfattning av utvärderingsresultaten"""
        summary = {
            "total_strategies": len(evaluation_results),
            "strategies": []
        }

        for result in evaluation_results:
            strategy_summary = {
                "name": result["strategy_name"],
                "description": result["strategy_description"],
                "metrics": result["metrics"]
            }
            summary["strategies"].append(strategy_summary)

        return summary

    def _create_prompt(self, summary: Dict[str, Any]) -> str:
        """Skapa en prompt för GPT baserad på sammanfattningen"""
        prompt = f"""Analyze the following harbor placement strategy results and provide recommendations:

Total strategies evaluated: {summary['total_strategies']}

Strategy Results:
"""

        for strategy in summary["strategies"]:
            metrics = strategy["metrics"]
            prompt += f"""
Strategy: {strategy['name']}
Description: {strategy['description']}
- Boats placed: {metrics['boats_placed']}
- Placement rate: {metrics['placement_rate']:.2%}
- Average width utilization: {metrics['average_width_utilization']:.2%}
- Total width utilization: {metrics['total_width_utilization']:.2%}
"""

        prompt += """
Please provide:
1. A detailed analysis of the results
2. Which strategy performed best and why
3. Specific recommendations for improving the harbor layout
4. Suggestions for future strategy development
"""

        return prompt

    def _extract_recommendation(self, analysis: str) -> str:
        """Extrahera den viktigaste rekommendationen från analysen"""
        # Försök hitta den första rekommendationen i texten
        lines = analysis.split('\n')
        for line in lines:
            if line.strip().startswith(('Recommendation:', 'Suggestion:', 'Best strategy:')):
                return line.strip()
        return lines[0] if lines else "No specific recommendation found"

    def analyze_strategies_old(self, strategy_evaluations: Dict[str, Dict[str, Any]],
                               boats: List[Boat], slots: List[Slot]) -> Dict[str, Any]:
        """Analyserar strategier och ger rekommendationer"""
        if not self.client:
            return {
                "error": "OpenAI API key not configured",
                "recommendation": "Please configure OpenAI API key in settings"
            }

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
            # Använd det nya API:et för att anropa OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Failed to get analysis: {str(e)}"

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extraherar JSON från GPT-svaret"""
        try:
            # Hitta JSON i svaret
            json_str = response[response.find("{"):response.rfind("}")+1]
            return json.loads(json_str)
        except:
            return {"error": "Failed to parse GPT response"}
