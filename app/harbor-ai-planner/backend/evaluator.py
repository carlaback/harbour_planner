# evaluator.py - förbättrad version
from typing import List, Dict, Any, Tuple, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import asyncio
import logging
import json
from pathlib import Path

from models import Boat, Slot, BoatStay, Dock
from strategies import BaseStrategy, ALL_STRATEGIES, get_strategy_by_name, optimize_placement
from config import settings

# Konfigurera loggning
logger = logging.getLogger(__name__)


class StrategyEvaluator:
    """Utvärderar olika strategier för båtplacering med utökad funktionalitet"""

    def __init__(self, db: AsyncSession):
        """
        Initialisera utvärderaren.

        Args:
            db: Databassession för dataåtkomst
        """
        self.db = db
        self.results_dir = Path("evaluation_results")
        self.results_dir.mkdir(exist_ok=True)

    async def evaluate_strategy(self,
                                strategy: BaseStrategy,
                                boats: List[Boat],
                                slots: List[Slot]) -> Dict[str, Any]:
        """
        Utvärdera en specifik strategi med utökade mått.

        Args:
            strategy: Strategin att utvärdera
            boats: Lista med båtar att placera
            slots: Lista med tillgängliga platser

        Returns:
            Detaljerad utvärderingsrapport
        """
        start_time = datetime.now()

        try:
            # Kör strategin
            stays = await strategy.place_boats(self.db, boats, slots)

            # Beräkna mått
            metrics = await self._calculate_detailed_metrics(stays, boats, slots)

            # Beräkna exekveringstid
            execution_time = (datetime.now() - start_time).total_seconds()

            # Skapa och returnera result
            result = {
                "strategy_name": strategy.name,
                "strategy_description": strategy.description,
                "execution_time_seconds": execution_time,
                "metrics": metrics,
                "stays": [self._stay_to_dict(stay) for stay in stays],
                "timestamp": datetime.now().isoformat()
            }

            # Spara resultatet om inställningen är aktiverad
            if settings.SAVE_EVALUATION_RESULTS:
                await self._save_evaluation_result(result)

            return result

        except Exception as e:
            logger.exception(
                f"Error evaluating strategy {strategy.name}: {str(e)}")
            return {
                "strategy_name": strategy.name,
                "strategy_description": strategy.description,
                "error": str(e),
                "metrics": {},
                "stays": [],
                "timestamp": datetime.now().isoformat()
            }

    async def evaluate_all_strategies(self,
                                      boats: List[Boat],
                                      slots: List[Slot],
                                      strategy_names: List[str] = None) -> List[Dict[str, Any]]:
        """
        Utvärdera flera strategier parallellt.

        Args:
            boats: Lista med båtar att placera
            slots: Lista med tillgängliga platser
            strategy_names: Lista med namn på strategier att utvärdera (None = alla)

        Returns:
            Lista med utvärderingsrapporter för varje strategi
        """
        try:
            # Välj vilka strategier som ska utvärderas
            if strategy_names:
                strategies = [
                    s for s in ALL_STRATEGIES if s.name in strategy_names]
                if not strategies:
                    logger.warning(
                        f"No valid strategies found among: {strategy_names}")
                    return []
            else:
                strategies = ALL_STRATEGIES

            logger.info(
                f"Evaluating {len(strategies)} strategies for {len(boats)} boats and {len(slots)} slots")

            # Utvärdera strategierna parallellt för bättre prestanda
            tasks = [self.evaluate_strategy(
                strategy, boats, slots) for strategy in strategies]
            results = await asyncio.gather(*tasks)

            # Sortera efter prestanda (placeringsgrad)
            sorted_results = sorted(
                results,
                key=lambda x: (
                    x["metrics"].get("placement_rate", 0),
                    x["metrics"].get("average_width_utilization", 0)
                ),
                reverse=True
            )

            return sorted_results

        except Exception as e:
            logger.exception(f"Error in evaluate_all_strategies: {str(e)}")
            return []

    async def get_best_strategy(self,
                                boats: List[Boat],
                                slots: List[Slot],
                                weights: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Hitta den bästa strategin baserat på anpassningsbara viktningar.

        Args:
            boats: Lista med båtar att placera
            slots: Lista med tillgängliga platser
            weights: Viktning för olika mått (default: settings.EVALUATION_WEIGHTS)

        Returns:
            Den bästa strategins utvärderingsrapport
        """
        # Använd standardvikter om inga anges
        if weights is None:
            weights = {
                "placement_rate": settings.EVALUATION_WEIGHTS.get("placed_boats_weight", 50) / 100,
                "width_utilization": settings.EVALUATION_WEIGHTS.get("efficiency_weight", 30) / 100,
                "temp_slots_usage": settings.EVALUATION_WEIGHTS.get("temp_slots_usage_weight", 20) / 100
            }

        # Utvärdera alla strategier
        results = await self.evaluate_all_strategies(boats, slots)

        if not results:
            return None

        # Beräkna sammansatt poäng för varje strategi
        for result in results:
            metrics = result["metrics"]
            placement_score = metrics.get(
                "placement_rate", 0) * weights["placement_rate"]
            width_score = metrics.get(
                "average_width_utilization", 0) * weights["width_utilization"]
            temp_score = metrics.get(
                "temp_slots_usage", 0) * weights["temp_slots_usage"]

            # Sammansatt poäng
            result["composite_score"] = placement_score + \
                width_score + temp_score

        # Sortera efter sammansatt poäng
        sorted_results = sorted(
            results, key=lambda x: x["composite_score"], reverse=True)

        # Lägg till kompositpoäng för alla strategier
        best_result = sorted_results[0]
        best_result["all_scores"] = [
            {"name": r["strategy_name"], "score": r["composite_score"]}
            for r in sorted_results
        ]

        logger.info(
            f"Best strategy: {best_result['strategy_name']} with score {best_result['composite_score']:.4f}")

        return best_result

    async def optimize_with_hybrid(self, boats: List[Boat], slots: List[Slot]) -> Dict[str, Any]:
        """
        Utför optimering med hybrid och adaptiva strategier.

        Denna funktion kombinerar flera strategier för att hitta en optimal lösning,
        antingen genom att använda en hybridstrategi eller genom att hitta de bästa
        inställningarna för en adaptiv strategi.

        Args:
            boats: Lista med båtar att placera
            slots: Lista med tillgängliga platser

        Returns:
            Optimeringsresultat
        """
        try:
            # Använd optimize_placement från strategies.py
            best_strategy, stays, metrics = await optimize_placement(self.db, boats, slots)

            # Formatera resultatet
            result = {
                "strategy_name": best_strategy.name,
                "strategy_description": best_strategy.description,
                "metrics": metrics,
                "stays": [self._stay_to_dict(stay) for stay in stays],
                "timestamp": datetime.now().isoformat(),
                "optimization_method": "hybrid"
            }

            return result

        except Exception as e:
            logger.exception(f"Error in optimize_with_hybrid: {str(e)}")
            return {
                "error": str(e),
                "metrics": {},
                "stays": [],
                "timestamp": datetime.now().isoformat()
            }

    async def _calculate_detailed_metrics(self,
                                          stays: List[BoatStay],
                                          boats: List[Boat],
                                          slots: List[Slot]) -> Dict[str, Any]:
        """
        Beräkna detaljerade utvärderingsmått för en strategi.

        Args:
            stays: Lista med båtvistelser
            boats: Lista med båtar
            slots: Lista med platser

        Returns:
            Detaljerade mått om placeringens effektivitet
        """
        if not stays:
            return {
                "boats_placed": 0,
                "placement_rate": 0.0,
                "average_width_utilization": 0.0,
                "total_width_utilization": 0.0,
                "temp_slots_usage": 0.0,
                "average_stay_duration_days": 0.0,
                "max_simultaneous_occupancy": 0,
                "occupancy_rate": 0.0
            }

        # Skapa uppslagstabeller för effektivare beräkningar
        boat_dict = {boat.id: boat for boat in boats}
        slot_dict = {slot.id: slot for slot in slots}

        # Grundläggande mått
        boats_placed = len(set(stay.boat_id for stay in stays))
        placement_rate = boats_placed / len(boats) if boats else 0.0

        # Beräkna breddutnyttjande och andra mått
        total_width_utilization = 0.0
        total_stay_days = 0.0
        temp_slots_used = 0

        # Beräkna beläggning över tid
        all_dates = set()
        boat_dates = {}  # Båt-ID -> set av datum

        for stay in stays:
            boat = boat_dict.get(stay.boat_id)
            slot = slot_dict.get(stay.slot_id)

            if boat and slot:
                # Breddutnyttjande
                width_ratio = boat.width / slot.max_width
                total_width_utilization += width_ratio

                # Vistelselängd
                stay_days = (stay.end_time - stay.start_time).days + 1
                total_stay_days += stay_days

                # Temporära platser
                if slot.is_reserved and slot.available_from and slot.available_until:
                    temp_slots_used += 1

                # Beläggning över tid
                current_date = stay.start_time.date()
                end_date = stay.end_time.date()

                while current_date <= end_date:
                    all_dates.add(current_date)

                    if stay.boat_id not in boat_dates:
                        boat_dates[stay.boat_id] = set()

                    boat_dates[stay.boat_id].add(current_date)

                    current_date += timedelta(days=1)

        # Beräkna maximal samtidig beläggning
        daily_occupancy = {}
        for date in all_dates:
            daily_occupancy[date] = len(
                [b for b in boat_dates if date in boat_dates[b]])

        max_occupancy = max(daily_occupancy.values()) if daily_occupancy else 0
        avg_occupancy = sum(daily_occupancy.values()) / \
            len(daily_occupancy) if daily_occupancy else 0
        occupancy_rate = avg_occupancy / len(slots) if slots else 0

        # Beräkna genomsnittsvärden
        avg_width_utilization = total_width_utilization / \
            len(stays) if stays else 0.0
        avg_stay_duration = total_stay_days / len(stays) if stays else 0.0
        temp_slots_usage = temp_slots_used / len(stays) if stays else 0.0

        return {
            "boats_placed": boats_placed,
            "placement_rate": placement_rate,
            "average_width_utilization": avg_width_utilization,
            "total_width_utilization": total_width_utilization,
            "temp_slots_usage": temp_slots_usage,
            "average_stay_duration_days": avg_stay_duration,
            "max_simultaneous_occupancy": max_occupancy,
            "average_occupancy": avg_occupancy,
            "occupancy_rate": occupancy_rate
        }

    def _stay_to_dict(self, stay: BoatStay) -> Dict[str, Any]:
        """
        Konvertera en BoatStay till ett dict för JSON-serialisering.

        Args:
            stay: BoatStay-objekt att konvertera

        Returns:
            Dict-representation av båtvistelsen
        """
        return {
            "id": stay.id,
            "boat_id": stay.boat_id,
            "slot_id": stay.slot_id,
            "start_time": stay.start_time.isoformat() if stay.start_time else None,
            "end_time": stay.end_time.isoformat() if stay.end_time else None,
            "strategy_name": stay.strategy_name
        }

    async def _save_evaluation_result(self, result: Dict[str, Any]) -> None:
        """
        Spara utvärderingsresultat till fil.

        Args:
            result: Utvärderingsresultat att spara
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            strategy_name = result["strategy_name"]
            filename = self.results_dir / \
                f"eval_{strategy_name}_{timestamp}.json"

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)

            logger.debug(f"Evaluation result saved to {filename}")

        except Exception as e:
            logger.error(f"Failed to save evaluation result: {str(e)}")

    async def generate_comparative_report(self,
                                          boats: List[Boat],
                                          slots: List[Slot],
                                          top_n: int = 3) -> Dict[str, Any]:
        """
        Generera en jämförande rapport för de bästa strategierna.

        Args:
            boats: Lista med båtar att placera
            slots: Lista med tillgängliga platser
            top_n: Antal toppstrategier att jämföra i detalj

        Returns:
            Jämförande rapport
        """
        # Utvärdera alla strategier
        all_results = await self.evaluate_all_strategies(boats, slots)

        if not all_results:
            return {"error": "No strategies evaluated successfully"}

        # Sortera efter placeringsgrad
        sorted_results = sorted(
            all_results,
            key=lambda x: x["metrics"].get("placement_rate", 0),
            reverse=True
        )

        # Välj de bästa strategierna för detaljerad jämförelse
        top_strategies = sorted_results[:min(top_n, len(sorted_results))]

        # Skapa jämförelsetabeller
        metrics_comparison = []
        for result in all_results:
            metrics_comparison.append({
                "strategy_name": result["strategy_name"],
                "placement_rate": result["metrics"].get("placement_rate", 0),
                "width_utilization": result["metrics"].get("average_width_utilization", 0),
                "occupancy_rate": result["metrics"].get("occupancy_rate", 0),
                "execution_time": result.get("execution_time_seconds", 0)
            })

        # Skapa rapport
        report = {
            "summary": {
                "total_strategies_evaluated": len(all_results),
                "total_boats": len(boats),
                "total_slots": len(slots),
                "date_generated": datetime.now().isoformat(),
                "best_strategy": sorted_results[0]["strategy_name"] if sorted_results else None
            },
            "metrics_comparison": metrics_comparison,
            "top_strategies": top_strategies
        }

        return report
