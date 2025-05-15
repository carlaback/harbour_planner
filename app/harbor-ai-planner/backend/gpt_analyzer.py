from typing import Dict, Any, List
from datetime import datetime
import openai
import json
import os
from models import Boat, Slot


class GPTAnalyzer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        openai.api_key = self.api_key

    def analyze_strategies(self, strategy_evaluations: Dict[str, Dict[str, Any]],
                           boats: List[Boat], slots: List[Slot]) -> Dict[str, Any]:
        """Analyserar strategier och ger rekommendationer"""

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
                "min": min(b.width for b in boats),
                "max": max(b.width for b in boats),
                "avg": sum(b.width for b in boats) / len(boats)
            },
            "time_range": {
                "earliest": min(b.arrival for b in boats),
                "latest": max(b.departure for b in boats)
            }
        }

    def _summarize_slots(self, slots: List[Slot]) -> Dict[str, Any]:
        """Sammanfattar platsdata"""
        return {
            "total": len(slots),
            "widths": {
                "min": min(s.max_width for s in slots),
                "max": max(s.max_width for s in slots),
                "avg": sum(s.max_width for s in slots) / len(slots)
            }
        }

    def _find_bottlenecks(self, boats: List[Boat], slots: List[Slot]) -> Dict[str, Any]:
        """Identifierar potentiella flaskhalsar"""
        return {
            "width_mismatch": max(b.width for b in boats) > max(s.max_width for s in slots),
            "capacity_issue": len(boats) > len(slots),
            "time_conflict": self._check_time_conflicts(boats)
        }

    def _check_time_conflicts(self, boats: List[Boat]) -> bool:
        """Kontrollerar om det finns tidskonflikter"""
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
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=3000
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
