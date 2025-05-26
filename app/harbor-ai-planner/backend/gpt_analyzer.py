# gpt_analyzer.py - Enhanced version med Chain of Thought och Learning
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
import asyncio
from pathlib import Path
from dataclasses import dataclass, asdict
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletionMessage
from models import Boat, Slot, BoatStay
from config import settings

# Konfigurera loggning
logger = logging.getLogger(__name__)


@dataclass
class AnalysisMemory:
    """Strukturerad data för att spara analys-minnen"""
    timestamp: str
    problem_context: Dict[str, Any]
    reasoning_chain: List[Dict[str, Any]]
    final_recommendation: str
    confidence_level: float
    actual_outcome: Optional[Dict[str, Any]] = None


@dataclass
class LearnedPattern:
    """Mönster som AI:n har lärt sig från tidigare analyser"""
    pattern_id: str
    description: str
    confidence: float
    examples_count: int
    last_validated: str
    success_rate: float


class GPTAnalyzer:
    """
    Analyserar strategier och ger rekommendationer med hjälp av GPT.
    Enhanced version med Chain of Thought reasoning och learning från tidigare analyser.
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

        # Learning system
        self.memory_file = Path("analysis_memory.json")
        self.patterns_file = Path("learned_patterns.json")
        self.analysis_history = self._load_analysis_history()
        self.learned_patterns = self._load_learned_patterns()

    def _load_analysis_history(self) -> List[AnalysisMemory]:
        """Ladda tidigare analyser från fil"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [AnalysisMemory(**item) for item in data]
        except Exception as e:
            logger.warning(f"Could not load analysis history: {e}")
        return []

    def _save_analysis_history(self):
        """Spara analyshistorik till fil"""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(memory) for memory in self.analysis_history],
                          f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save analysis history: {e}")

    def _load_learned_patterns(self) -> List[LearnedPattern]:
        """Ladda inlärda mönster från fil"""
        try:
            if self.patterns_file.exists():
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [LearnedPattern(**item) for item in data]
        except Exception as e:
            logger.warning(f"Could not load learned patterns: {e}")
        return []

    def _save_learned_patterns(self):
        """Spara inlärda mönster till fil"""
        try:
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(pattern) for pattern in self.learned_patterns],
                          f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save learned patterns: {e}")

    async def analyze_strategies_with_learning(self, evaluation_results: List[Dict[str, Any]],
                                               boats: List[Any] = None, slots: List[Any] = None) -> Dict[str, Any]:
        """
        Enhanced analys med Chain of Thought och learning från tidigare analyser.
        """
        if not self.api_key or not self.async_client:
            logger.error(
                "OpenAI API key not configured or client initialization failed")
            return self._create_error_response("OpenAI API key not configured")

        try:
            analysis_start = datetime.now()
            logger.info("Starting Chain of Thought analysis with learning")

            # Steg 1: Förbered kontext med historisk kunskap
            context = self._prepare_enhanced_context(
                evaluation_results, boats, slots)

            # Steg 2: Kör Chain of Thought reasoning
            reasoning_chain = await self._execute_chain_of_thought_reasoning(context)

            # Steg 3: Generera slutsatser med historisk kontext
            final_analysis = await self._synthesize_conclusions_with_learning(reasoning_chain, context)

            # Steg 4: Spara för framtida lärande
            memory_entry = AnalysisMemory(
                timestamp=analysis_start.isoformat(),
                problem_context=context["current_problem"],
                reasoning_chain=reasoning_chain,
                final_recommendation=final_analysis.get(
                    "primary_recommendation", ""),
                confidence_level=final_analysis.get("confidence", 0.5)
            )

            self._add_to_memory(memory_entry)

            # Steg 5: Uppdatera inlärda mönster
            learning_update = self._update_learned_patterns(
                reasoning_chain, final_analysis)

            execution_time = (datetime.now() - analysis_start).total_seconds()

            return {
                "analysis_type": "Chain of Thought with Historical Learning",
                "timestamp": analysis_start.isoformat(),
                "execution_time_seconds": execution_time,
                "context_summary": {
                    "current_strategies": len(evaluation_results),
                    "historical_cases_used": len(context.get("similar_cases", [])),
                    "learned_patterns_applied": len(context.get("applicable_patterns", []))
                },
                "reasoning_chain": reasoning_chain,
                "final_analysis": final_analysis,
                "learning_update": learning_update,
                "confidence_assessment": self._assess_analysis_confidence(reasoning_chain, context)
            }

        except Exception as e:
            logger.exception(f"Error during enhanced GPT analysis: {str(e)}")
            return self._create_error_response(f"Error during enhanced GPT analysis: {str(e)}")

    def _prepare_enhanced_context(self, evaluation_results: List[Dict[str, Any]],
                                  boats: List[Any], slots: List[Any]) -> Dict[str, Any]:
        """Förbered kontext med både aktuell data och historisk kunskap"""

        # Grundläggande problemkontext
        summary = self._create_summary(evaluation_results)

        current_problem = {
            "total_strategies": summary["total_strategies"],
            "best_placement_rate": summary.get("best_strategy", {}).get("metrics", {}).get("placement_rate", 0),
            "average_performance": summary["average_placement_rate"],
            "problem_size": {
                "boats": len(boats) if boats else 0,
                "slots": len(slots) if slots else 0
            },
            "complexity_indicators": self._assess_problem_complexity(boats, slots)
        }

        # Hitta liknande historiska fall
        similar_cases = self._find_similar_cases(current_problem)

        # Identifiera tillämpliga mönster
        applicable_patterns = self._get_applicable_patterns(current_problem)

        return {
            "current_problem": current_problem,
            "evaluation_results": evaluation_results,
            "summary": summary,
            "similar_cases": similar_cases[:3],  # Top 3 liknande fall
            "applicable_patterns": applicable_patterns,
            "boats_stats": self._analyze_boats_stats(boats) if boats else {},
            "slots_stats": self._analyze_slots_stats(slots) if slots else {}
        }

    async def _execute_chain_of_thought_reasoning(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Utför strukturerad Chain of Thought reasoning"""

        reasoning_steps = []

        # Steg 1: Problemförståelse
        step1 = await self._reasoning_step_problem_understanding(context)
        reasoning_steps.append(step1)

        # Steg 2: Historisk kontextanalys
        step2 = await self._reasoning_step_historical_analysis(context, step1)
        reasoning_steps.append(step2)

        # Steg 3: Mönsterigenkänning
        step3 = await self._reasoning_step_pattern_recognition(context, reasoning_steps)
        reasoning_steps.append(step3)

        # Steg 4: Hypotesformulering
        step4 = await self._reasoning_step_hypothesis_formation(context, reasoning_steps)
        reasoning_steps.append(step4)

        # Steg 5: Evidensanalys
        step5 = await self._reasoning_step_evidence_analysis(context, reasoning_steps)
        reasoning_steps.append(step5)

        return reasoning_steps

    async def _reasoning_step_problem_understanding(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Steg 1: Grundläggande problemförståelse med Chain of Thought"""

        current = context["current_problem"]
        summary = context["summary"]

        prompt = f"""
        Som expert inom hamnplanering, analysera detta optimeringsproblem steg för steg:

        AKTUELLT PROBLEM:
        - Antal strategier testade: {current['total_strategies']}
        - Bästa placeringsgrad: {current['best_placement_rate']:.1%}
        - Genomsnittsprestanda: {current['average_performance']:.1%}
        - Problemstorlek: {current['problem_size']['boats']} båtar, {current['problem_size']['slots']} platser

        STRATEGIRESULTAT:
        {self._format_strategies_for_reasoning(context['evaluation_results'])}

        TANKEGÅNG STEG 1 - PROBLEMFÖRSTÅELSE:
        1. Vad är min första bedömning av denna optimeringsutmaning?
        2. Vilka är de mest uppenbara styrkorna och svagheterna i resultaten?
        3. Vad indikerar placeringsgraden om problemets svårighetsgrad?
        4. Finns det tydliga mönster i hur olika strategier presterar?

        Svara med din steg-för-steg tankegång som JSON:
        {{
            "step": "problem_understanding",
            "initial_assessment": "din första bedömning",
            "key_observations": ["observation1", "observation2", ...],
            "performance_patterns": "vad du ser i prestanda",
            "problem_difficulty": "enkel/medel/svår och varför"
        }}
        """

        response = await self._call_gpt_for_reasoning(prompt)
        return response

    async def _reasoning_step_historical_analysis(self, context: Dict[str, Any], step1: Dict[str, Any]) -> Dict[str, Any]:
        """Steg 2: Analysera historisk kontext och tidigare liknande fall"""

        similar_cases = context.get("similar_cases", [])

        historical_context = ""
        if similar_cases:
            historical_context = f"""
        HISTORISKA LIKNANDE FALL:
        {self._format_historical_cases(similar_cases)}
        """
        else:
            historical_context = "HISTORISK KONTEXT: Inga tidigare liknande fall tillgängliga."

        prompt = f"""
        Fortsätt din analys med historisk kontext:

        TIDIGARE TANKEGÅNG:
        {json.dumps(step1, indent=2)}

        {historical_context}

        TANKEGÅNG STEG 2 - HISTORISK ANALYS:
        1. Hur stämmer nuvarande resultat överens med tidigare erfarenheter?
        2. Vilka lärdomar från historiken är tillämpliga här?
        3. Ser jag några avvikelser från förväntade mönster?
        4. Vad kan historiska fall berätta om framgångsrika strategier för detta problemområde?

        Svara med din tankegång som JSON:
        {{
            "step": "historical_analysis",
            "historical_comparison": "jämförelse med tidigare fall",
            "applicable_lessons": ["lärdom1", "lärdom2", ...],
            "pattern_deviations": "avvikelser från förväntade mönster",
            "historical_insights": "vad historiken lär oss"
        }}
        """

        response = await self._call_gpt_for_reasoning(prompt)
        return response

    async def _reasoning_step_pattern_recognition(self, context: Dict[str, Any], previous_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Steg 3: Identifiera mönster baserat på inlärda patterns"""

        applicable_patterns = context.get("applicable_patterns", [])

        patterns_context = ""
        if applicable_patterns:
            patterns_context = f"""
        INLÄRDA MÖNSTER SOM KAN VARA RELEVANTA:
        {self._format_learned_patterns(applicable_patterns)}
        """
        else:
            patterns_context = "MÖNSTERIGENKÄNNING: Inga tidigare inlärda mönster tillgängliga för detta problem."

        prompt = f"""
        Fortsätt analysen med mönsterigenkänning:

        TIDIGARE TANKEGÅNGAR:
        {json.dumps(previous_steps, indent=2)}

        {patterns_context}

        TANKEGÅNG STEG 3 - MÖNSTERIGENKÄNNING:
        1. Vilka mönster kan jag identifiera i de aktuella strategiresultaten?
        2. Matchar dessa mönster något av de tidigare inlärda mönstren?
        3. Finns det nya mönster som framträder i denna analys?
        4. Hur kan erkända mönster hjälpa mig förstå varför vissa strategier fungerar bättre?

        Svara med din tankegång som JSON:
        {{
            "step": "pattern_recognition",
            "identified_patterns": ["mönster1", "mönster2", ...],
            "pattern_matching": "hur nya mönster matchar tidigare",
            "new_patterns": ["nytt_mönster1", "nytt_mönster2", ...],
            "pattern_explanations": "varför dessa mönster uppstår"
        }}
        """

        response = await self._call_gpt_for_reasoning(prompt)
        return response

    async def _reasoning_step_hypothesis_formation(self, context: Dict[str, Any], previous_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Steg 4: Formulera hypoteser baserat på analysis hittills"""

        prompt = f"""
        Baserat på din analys hittills, formulera hypoteser:

        SAMMANFATTNING AV TIDIGARE STEG:
        {json.dumps(previous_steps, indent=2)}

        TANKEGÅNG STEG 4 - HYPOTESFORMULERING:
        1. Vilka hypoteser kan jag formulera om varför vissa strategier fungerar bättre?
        2. Vad är mina teorier om de underliggande orsakerna till prestationsskillnaderna?
        3. Vilka specifika faktorer tror jag påverkar framgången mest?
        4. Hur kan jag testa eller validera dessa hypoteser?

        Svara med din tankegång som JSON:
        {{
            "step": "hypothesis_formation",
            "main_hypotheses": [
                {{"hypothesis": "hypotes1", "reasoning": "varför", "confidence": 0.8}},
                {{"hypothesis": "hypotes2", "reasoning": "varför", "confidence": 0.6}}
            ],
            "underlying_factors": ["faktor1", "faktor2", ...],
            "testable_predictions": ["prediction1", "prediction2", ...],
            "validation_methods": "hur testa hypoteserna"
        }}
        """

        response = await self._call_gpt_for_reasoning(prompt)
        return response

    async def _reasoning_step_evidence_analysis(self, context: Dict[str, Any], previous_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Steg 5: Analysera evidens för hypoteserna"""

        prompt = f"""
        Analysera evidensen för dina hypoteser:

        ALLA TIDIGARE TANKEGÅNGAR:
        {json.dumps(previous_steps, indent=2)}

        DETALJERADE STRATEGIRESULTAT:
        {json.dumps(context['evaluation_results'], indent=2)}

        TANKEGÅNG STEG 5 - EVIDENSANALYS:
        1. Vilken evidens stödjer mina huvudhypoteser?
        2. Vilken evidens motsäger eller försvagar mina hypoteser?
        3. Hur stark är evidensen för varje hypotes på en skala 1-10?
        4. Vilka slutsatser kan jag dra med hög säkerhet, och vilka är mer osäkra?

        Svara med din slutgiltiga tankegång som JSON:
        {{
            "step": "evidence_analysis",
            "supporting_evidence": [
                {{"hypothesis": "hypotes", "evidence": "evidens", "strength": 8}}
            ],
            "contradicting_evidence": [
                {{"hypothesis": "hypotes", "evidence": "motbevis", "impact": "låg/medel/hög"}}
            ],
            "confidence_ratings": {{"hypotes1": 0.9, "hypotes2": 0.6}},
            "high_confidence_conclusions": ["slutsats1", "slutsats2"],
            "uncertain_areas": ["osäkerhet1", "osäkerhet2"]
        }}
        """

        response = await self._call_gpt_for_reasoning(prompt)
        return response

    async def _synthesize_conclusions_with_learning(self, reasoning_chain: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Syntetisera slutsatser från Chain of Thought med historisk kunskap"""

        prompt = f"""
        Baserat på din fullständiga Chain of Thought-analys, ge en sammanfattande slutsats:

        FULLSTÄNDIG TANKEGÅNG:
        {json.dumps(reasoning_chain, indent=2)}

        KONTEXTSAMMANFATTNING:
        - Strategier testade: {context['current_problem']['total_strategies']}
        - Bästa resultat: {context['current_problem']['best_placement_rate']:.1%}
        - Historiska fall använda: {len(context.get('similar_cases', []))}

        SLUTGILTIG SYNTES:
        1. Vad är min huvudsakliga rekommendation baserat på hela analysen?
        2. Vilken strategi rekommenderar jag och varför?
        3. Vilka specifika förbättringar skulle jag föreslå?
        4. Vad är min förtroendenivå för denna analys?
        5. Vilka nya insikter har jag lärt mig som kan vara värdefulla framöver?

        Svara med en strukturerad slutsats som JSON:
        {{
            "primary_recommendation": "huvudrekommendation",
            "recommended_strategy": {{
                "name": "strateginamn",
                "reason": "varför denna strategi",
                "expected_improvement": "förväntad förbättring"
            }},
            "specific_improvements": ["förbättring1", "förbättring2", ...],
            "confidence": 0.85,
            "key_insights": ["insikt1", "insikt2", ...],
            "learning_for_future": ["lärdom1", "lärdom2", ...],
            "risk_factors": ["risk1", "risk2", ...],
            "next_steps": ["steg1", "steg2", ...]
        }}
        """

        response = await self._call_gpt_for_reasoning(prompt)
        return response

    async def _call_gpt_for_reasoning(self, prompt: str) -> Dict[str, Any]:
        """Anropa GPT för reasoning med error handling"""
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Du är en expert på hamnoptimering som tänker steg för steg och alltid svarar med välformatterad JSON. Visa ditt resonemang tydligt."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Lägre temperatur för mer konsekvent reasoning
                max_tokens=self.max_tokens
            )

            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Om JSON-parsing misslyckas, returnera raw content
                return {"raw_response": content, "parsing_error": True}

        except Exception as e:
            logger.error(f"Error in GPT reasoning call: {e}")
            return {"error": str(e), "step": "unknown"}

    def _find_similar_cases(self, current_problem: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Hitta liknande historiska fall"""
        similar_cases = []

        for memory in self.analysis_history:
            # Beräkna likhet baserat på problemstorlek och prestanda
            similarity_score = 0.0

            past_problem = memory.problem_context

            # Jämför problemstorlek
            if past_problem.get("problem_size"):
                size_diff = abs(past_problem["problem_size"].get(
                    "boats", 0) - current_problem["problem_size"]["boats"])
                size_similarity = max(0, 1 - size_diff / 100)  # Normalisera
                similarity_score += size_similarity * 0.4

            # Jämför prestanda
            if past_problem.get("best_placement_rate"):
                performance_diff = abs(
                    past_problem["best_placement_rate"] - current_problem["best_placement_rate"])
                perf_similarity = max(0, 1 - performance_diff)
                similarity_score += perf_similarity * 0.6

            if similarity_score > 0.5:  # Threshold för likhet
                similar_cases.append({
                    "timestamp": memory.timestamp,
                    "similarity_score": similarity_score,
                    "context": past_problem,
                    "recommendation": memory.final_recommendation,
                    "confidence": memory.confidence_level
                })

        # Sortera efter likhet
        similar_cases.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_cases[:3]

    def _get_applicable_patterns(self, current_problem: Dict[str, Any]) -> List[LearnedPattern]:
        """Hämta tillämpliga inlärda mönster"""
        applicable = []

        for pattern in self.learned_patterns:
            # Enkel matching baserat på problemstorlek och typ
            if pattern.confidence > 0.6 and pattern.success_rate > 0.7:
                applicable.append(pattern)

        return applicable[:5]  # Top 5 mönster

    def _add_to_memory(self, memory: AnalysisMemory):
        """Lägg till ny analys i minnet"""
        self.analysis_history.append(memory)

        # Begränsa historikstorlek
        if len(self.analysis_history) > 50:
            self.analysis_history = self.analysis_history[-50:]

        self._save_analysis_history()

    def _update_learned_patterns(self, reasoning_chain: List[Dict[str, Any]], final_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Uppdatera inlärda mönster baserat på ny analys"""
        new_patterns = []
        updated_patterns = []

        # Extrahera nya mönster från reasoning chain
        for step in reasoning_chain:
            if step.get("step") == "pattern_recognition":
                new_patterns_found = step.get("new_patterns", [])
                for pattern_desc in new_patterns_found:
                    # Skapa nytt mönster
                    pattern_id = f"pattern_{len(self.learned_patterns)}_{datetime.now().strftime('%Y%m%d')}"
                    new_pattern = LearnedPattern(
                        pattern_id=pattern_id,
                        description=pattern_desc,
                        confidence=0.6,  # Initial confidence
                        examples_count=1,
                        last_validated=datetime.now().isoformat(),
                        success_rate=0.7  # Initial success rate
                    )
                    self.learned_patterns.append(new_pattern)
                    new_patterns.append(pattern_desc)

        # Uppdatera befintliga mönster om de användes
        for pattern in self.learned_patterns:
            pattern.last_validated = datetime.now().isoformat()
            pattern.examples_count += 1
            updated_patterns.append(pattern.pattern_id)

        self._save_learned_patterns()

        return {
            "new_patterns_learned": new_patterns,
            "patterns_reinforced": len(updated_patterns),
            "total_patterns": len(self.learned_patterns)
        }

    def _assess_analysis_confidence(self, reasoning_chain: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Bedöm förtroendet för analysen"""
        confidence_factors = []

        # Faktorer som påverkar förtroende
        if len(context.get("similar_cases", [])) > 0:
            confidence_factors.append(
                {"factor": "historical_cases", "contribution": 0.2})

        if len(context.get("applicable_patterns", [])) > 0:
            confidence_factors.append(
                {"factor": "learned_patterns", "contribution": 0.3})

        if context["current_problem"]["total_strategies"] >= 5:
            confidence_factors.append(
                {"factor": "sufficient_strategies", "contribution": 0.2})

        # Beräkna total confidence
        total_confidence = min(1.0, sum(
            f["contribution"] for f in confidence_factors) + 0.3)  # Base confidence

        return {
            "overall_confidence": total_confidence,
            "confidence_factors": confidence_factors,
            "confidence_level": "Hög" if total_confidence > 0.8 else "Medium" if total_confidence > 0.6 else "Låg"
        }

    # Hjälpmetoder för formattering
    def _format_strategies_for_reasoning(self, evaluation_results: List[Dict[str, Any]]) -> str:
        """Formatera strategiresultat för reasoning prompts"""
        formatted = []
        for result in evaluation_results:
            name = result.get("strategy_name", "Unknown")
            metrics = result.get("metrics", {})
            placement_rate = metrics.get("placement_rate", 0)
            boats_placed = metrics.get("boats_placed", 0)

            formatted.append(
                f"- {name}: {placement_rate:.1%} placeringsgrad ({boats_placed} båtar)")

        return "\n".join(formatted)

    def _format_historical_cases(self, similar_cases: List[Dict[str, Any]]) -> str:
        """Formatera historiska fall för prompts"""
        formatted = []
        for i, case in enumerate(similar_cases):
            formatted.append(f"""
        Fall {i+1} (Likhet: {case['similarity_score']:.1%}):
        - Datum: {case['timestamp']}
        - Rekommendation: {case['recommendation']}
        - Förtroende: {case['confidence']:.1%}
            """)
        return "\n".join(formatted)

    def _format_learned_patterns(self, patterns: List[LearnedPattern]) -> str:
        """Formatera inlärda mönster för prompts"""
        formatted = []
        for pattern in patterns:
            formatted.append(f"""
        - {pattern.description}
          (Förtroende: {pattern.confidence:.1%}, Framgång: {pattern.success_rate:.1%}, Exempel: {pattern.examples_count})
            """)
        return "\n".join(formatted)

    def _assess_problem_complexity(self, boats: List[Any], slots: List[Any]) -> Dict[str, Any]:
        """Bedöm problemkomplexitet"""
        if not boats or not slots:
            return {"level": "unknown", "factors": []}

        complexity_factors = []

        # Kapacitetsratio
        capacity_ratio = len(boats) / len(slots) if slots else 0
        if capacity_ratio > 0.9:
            complexity_factors.append("hög_kapacitetsanvändning")

        # Breddvariation
        boat_widths = [b.width for b in boats if hasattr(b, 'width')]
        if boat_widths:
            width_variance = max(boat_widths) - min(boat_widths)
            if width_variance > 2.0:
                complexity_factors.append("stor_breddvariation")

        complexity_level = "hög" if len(complexity_factors) > 2 else "medel" if len(
            complexity_factors) > 0 else "låg"

        return {
            "level": complexity_level,
            "factors": complexity_factors,
            "capacity_ratio": capacity_ratio
        }

    def _analyze_boats_stats(self, boats: List[Any]) -> Dict[str, Any]:
        """Analysera båtstatistik"""
        if not boats:
            return {}

        widths = [b.width for b in boats if hasattr(b, 'width')]

        return {
            "count": len(boats),
            "width_stats": {
                "min": min(widths) if widths else 0,
                "max": max(widths) if widths else 0,
                "avg": sum(widths) / len(widths) if widths else 0
            }
        }

    def _analyze_slots_stats(self, slots: List[Any]) -> Dict[str, Any]:
        """Analysera platsstatistik"""
        if not slots:
            return {}

        max_widths = [s.max_width for s in slots if hasattr(s, 'max_width')]

        return {
            "count": len(slots),
            "max_width_stats": {
                "min": min(max_widths) if max_widths else 0,
                "max": max(max_widths) if max_widths else 0,
                "avg": sum(max_widths) / len(max_widths) if max_widths else 0
            }
        }

    # Behåll befintliga metoder för bakåtkompatibilitet
    async def analyze_strategies(self, evaluation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Standard analysmetod - nu med förbättrad Chain of Thought som standard
        """
        return await self.analyze_strategies_with_learning(evaluation_results)

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

    # Gamla metoder för bakåtkompatibilitet
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
