from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models import Boat, Slot, BoatStay


class StrategyEvaluator:
    """Klass för att utvärdera resultat från olika placeringsstrategier"""

    @staticmethod
    def evaluate_strategy(db: Session, boat_stays: List[BoatStay], all_boats: List[Boat], all_slots: List[Slot]) -> Dict[str, Any]:
        """Utvärdera resultatet från en enskild strategi"""

        if not boat_stays:
            # Om inga båtar har placerats, returnera nollvärden
            return {
                "placed_boats_count": 0,
                "placed_boats_percent": 0.0,
                "used_slots_count": 0,
                "used_slots_percent": 0.0,
                "total_unused_width": 0.0,
                "average_unused_width_per_slot": 0.0,
                "efficiency": 0.0,
                "unplaced_boats_count": len(all_boats),
                "available_temporary_slots_used": 0,
                "available_temporary_slots_total": sum(1 for s in all_slots if s.is_reserved and s.available_from and s.available_until),
                "score": 0.0
            }
            # Antal placerade båtar

        placed_boat_ids = set(stay.boat_id for stay in boat_stays)
        placed_boats_count = len(placed_boat_ids)

        # Antal använda platser
        used_slot_ids = set(stay.slot_id for stay in boat_stays)
        used_slots_count = len(used_slot_ids)

        # Räkna antal tillgängliga temporära platser
        available_temporary_slots_total = sum(
            1 for s in all_slots if s.is_reserved and s.available_from and s.available_until)

        # Räkna antal använda temporära platser
        used_temporary_slots = 0
        for slot_id in used_slot_ids:
            slot = next((s for s in all_slots if s.id == slot_id), None)
            if slot and slot.is_reserved and slot.available_from and slot.available_until:
                used_temporary_slots += 1

                # Beräkna outnyttjad bredd
        total_unused_width = 0
        for stay in boat_stays:
            boat = next((b for b in all_boats if b.id == stay.boat_id), None)
            slot = next((s for s in all_slots if s.id == stay.slot_id), None)
            if boat and slot:
                unused_width = slot.max_width - boat.width
                total_unused_width += unused_width

        # Beräkna effektivitet
        efficiency = (placed_boats_count / len(all_boats)) * \
            (used_slots_count / len(all_slots))

        # Beräkna effektivitet (procent av tillgänglig bredd som används)
        total_used_width = sum(next(
            (b.width for b in all_boats if b.id == stay.boat_id), 0) for stay in boat_stays)
        total_slot_width = sum(next(
            (s.max_width for s in all_slots if s.id == stay.slot_id), 0) for stay in boat_stays)
        efficiency = total_used_width / total_slot_width if total_slot_width > 0 else 0

        # Antal oplacerade båtar
        unplaced_boats_count = len(all_boats) - placed_boats_count
        score = (
            # 50% vikt på andel placerade båtar
            (placed_boats_count / len(all_boats) * 50) +
            # 30% vikt på effektivitet (minimerad outnyttjad bredd)
            (efficiency * 30) +
            # 20% vikt på användning av temporära platser
            (used_temporary_slots / max(1, available_temporary_slots_total) * 20)
        )

        return {
            "placed_boats_count": placed_boats_count,
            "placed_boats_percent": placed_boats_count / len(all_boats) if all_boats else 0,
            "used_slots_count": used_slots_count,
            "used_slots_percent": used_slots_count / len(all_slots) if all_slots else 0,
            "total_unused_width": total_unused_width,
            "average_unused_width_per_slot": average_unused_width_per_slot,
            "efficiency": efficiency,
            "unplaced_boats_count": unplaced_boats_count,
            "available_temporary_slots_used": used_temporary_slots,
            "available_temporary_slots_total": available_temporary_slots_total,
            "score": score
        }
