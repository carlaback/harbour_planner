from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from models import Boat, Slot, BoatStay
from strategies import BaseStrategy, ALL_STRATEGIES


class StrategyEvaluator:
    """Utvärderar olika strategier för båtplacering"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_strategy(self, strategy: BaseStrategy, boats: List[Boat], slots: List[Slot]) -> Dict[str, Any]:
        """Utvärdera en specifik strategi"""
        # Kör strategin
        stays = await strategy.place_boats(self.db, boats, slots)

        # Beräkna mått
        metrics = await self._calculate_metrics(stays, boats, slots)

        return {
            "strategy_name": strategy.name,
            "strategy_description": strategy.description,
            "metrics": metrics,
            "stays": stays
        }

    async def evaluate_all_strategies(self, boats: List[Boat], slots: List[Slot]) -> List[Dict[str, Any]]:
        """Utvärdera alla tillgängliga strategier"""
        results = []
        for strategy in ALL_STRATEGIES:
            result = await self.evaluate_strategy(strategy, boats, slots)
            results.append(result)
        return results

    async def _calculate_metrics(self, stays: List[BoatStay], boats: List[Boat], slots: List[Slot]) -> Dict[str, Any]:
        """Beräkna utvärderingsmått för en strategi"""
        if not stays:
            return {
                "boats_placed": 0,
                "placement_rate": 0.0,
                "average_width_utilization": 0.0,
                "total_width_utilization": 0.0
            }

        # Antal placerade båtar
        boats_placed = len(stays)
        placement_rate = boats_placed / len(boats) if boats else 0.0

        # Beräkna breddutnyttjande
        total_width_utilization = 0.0
        for stay in stays:
            boat = next((b for b in boats if b.id == stay.boat_id), None)
            slot = next((s for s in slots if s.id == stay.slot_id), None)
            if boat and slot:
                total_width_utilization += boat.width / slot.max_width

        average_width_utilization = total_width_utilization / \
            len(stays) if stays else 0.0

        return {
            "boats_placed": boats_placed,
            "placement_rate": placement_rate,
            "average_width_utilization": average_width_utilization,
            "total_width_utilization": total_width_utilization
        }

    async def get_best_strategy(self, boats: List[Boat], slots: List[Slot]) -> Dict[str, Any]:
        """Hitta den bästa strategin baserat på utvärderingsmått"""
        results = await self.evaluate_all_strategies(boats, slots)

        # Sortera baserat på placement_rate och average_width_utilization
        sorted_results = sorted(
            results,
            key=lambda x: (
                x["metrics"]["placement_rate"],
                x["metrics"]["average_width_utilization"]
            ),
            reverse=True
        )

        return sorted_results[0] if sorted_results else None
