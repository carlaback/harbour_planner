from typing import Dict, List
from strategy_engine import Boat, Slot

# Mäter resultat av en strategi
# Returnerar: antal båtar placerade, total oanvänd bredd


def evaluate_strategy(assignment: Dict[int, str], boats: List[Boat], slots: List[Slot]) -> Dict:
    placed_boats = len(assignment)
    used_slots = {slot_id for slot_id in assignment.values()}
    total_unused_width = 0.0
