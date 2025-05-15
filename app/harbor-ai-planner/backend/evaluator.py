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


@staticmethod
def evaluate_all_strategies(db: Session, all_strategies_results: Dict[str, List[BoatStay]],
                            all_boats: List[Boat], all_slots: List[Slot]) -> Dict[str, Dict[str, Any]]:
    """Utvärdera alla strategier och returnera en jämförelse"""

    results = {}

    for strategy_name, boat_stays in all_strategies_results.items():
        results[strategy_name] = StrategyEvaluator.evaluate_strategy(
            db, boat_stays, all_boats, all_slots)

    # Lägg till vilket strategi som är bäst enligt vårt score
    best_strategy = max(
        results.items(), key=lambda x: x[1]["score"], default=(None, None))
    if best_strategy[0]:
        for strategy_name, eval_results in results.items():
            eval_results["is_best_by_score"] = (
                strategy_name == best_strategy[0])

    return results

    @staticmethod
    def get_detailed_evaluation(db: Session, all_strategies_results: Dict[str, List[BoatStay]],
                                all_boats: List[Boat], all_slots: List[Slot]) -> Dict[str, Any]:
        """Gör en djupare utvärdering som inkluderar olika mätvärden och jämförelser"""

        # Grundläggande utvärdering av alla strategier
        basic_eval = StrategyEvaluator.evaluate_all_strategies(
            db, all_strategies_results, all_boats, all_slots)

        # Identifiera de bästa strategierna enligt olika mått
        best_by_placed_boats = max(basic_eval.items(
        ), key=lambda x: x[1]["placed_boats_count"], default=(None, None))
        best_by_efficiency = max(
            basic_eval.items(), key=lambda x: x[1]["efficiency"], default=(None, None))
        best_by_temp_slots = max(basic_eval.items(
        ), key=lambda x: x[1]["available_temporary_slots_used"], default=(None, None))
        best_by_score = max(basic_eval.items(),
                            key=lambda x: x[1]["score"], default=(None, None))

        # Skapa en detaljerad sammanfattning
        detailed_summary = {
            "total_boats": len(all_boats),
            "total_slots": len(all_slots),
            "temporary_slots": sum(1 for s in all_slots if s.is_reserved and s.available_from and s.available_until),
            "permanent_slots": sum(1 for s in all_slots if s.is_reserved and (not s.available_from or not s.available_until)),
            "regular_slots": sum(1 for s in all_slots if not s.is_reserved),
            "best_strategy": {
                "by_placed_boats": best_by_placed_boats[0],
                "by_efficiency": best_by_efficiency[0],
                "by_temp_slots": best_by_temp_slots[0],
                "by_score": best_by_score[0]
            },
            "strategy_evaluations": basic_eval
        }

        # Analysera breddfördelning - viktigt för att förstå hur bra matchning av bredder
        boat_width_distribution = {}
        for boat in all_boats:
            width_category = round(boat.width * 2) / \
                2  # Avrunda till närmaste 0.5
            if width_category not in boat_width_distribution:
                boat_width_distribution[width_category] = 0
            boat_width_distribution[width_category] += 1

        slot_width_distribution = {}
        for slot in all_slots:
            width_category = round(slot.max_width * 2) / \
                2  # Avrunda till närmaste 0.5
            if width_category not in slot_width_distribution:
                slot_width_distribution[width_category] = 0
            slot_width_distribution[width_category] += 1

        detailed_summary["width_distribution"] = {
            "boats": {str(k): v for k, v in sorted(boat_width_distribution.items())},
            "slots": {str(k): v for k, v in sorted(slot_width_distribution.items())}
        }

        # Analys av vilka typer av båtar som inte fick plats
        unplaced_analysis = {}
        for strategy_name, boat_stays in all_strategies_results.items():
            placed_boat_ids = {stay.boat_id for stay in boat_stays}
            unplaced_boats = [
                b for b in all_boats if b.id not in placed_boat_ids]

            # Gruppera oplacerade båtar efter bredd
            unplaced_by_width = {}
            for boat in unplaced_boats:
                # Avrunda till närmaste 0.5
                width_category = round(boat.width * 2) / 2
                if width_category not in unplaced_by_width:
                    unplaced_by_width[width_category] = 0
                unplaced_by_width[width_category] += 1

            unplaced_analysis[strategy_name] = {
                "total_unplaced": len(unplaced_boats),
                "unplaced_by_width": {str(k): v for k, v in sorted(unplaced_by_width.items())},
                "average_width": sum(b.width for b in unplaced_boats) / len(unplaced_boats) if unplaced_boats else 0
            }

        detailed_summary["unplaced_analysis"] = unplaced_analysis

        return detailed_summary
