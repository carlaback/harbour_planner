from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import random

from models import Boat, Slot, BoatStay


class BaseStrategy:
    """Basstrategiimplementation för båtplacering"""

    def __init__(self, name: str, description: str = None):
        self.name = name
        self.description = description or f"{name} strategy"

    def place_boats(self, db: Session, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        """Huvudfunktion som alla strategier implementerar"""
        raise NotImplementedError("Subklasser måste implementera place_boats")

    def is_slot_available(self, slot: Slot, boat: Boat, existing_stays: List[BoatStay]) -> bool:
        """Kontrollera om en plats är tillgänglig för en båt under dess vistelse"""
        # Breddkontroll - den kritiska faktorn
        if boat.width > slot.max_width:
            return False

        # Kontrollera om platsen är tillgänglig under båtens vistelse
        # Permanenta platser kan vara tillgängliga under sommarperioder
        if slot.is_reserved:
            # Om platsen är reserverad men har en tillgänglig period
            if slot.available_from and slot.available_until:
                if not (slot.available_from <= boat.arrival and slot.available_until >= boat.departure):
                    return False

            else:
                # Permanent plats utan tillgänglig period
                return False

                # Kontrollera om platsen redan är upptagen av en annan båt under den här perioden
        for stay in existing_stays:
            if stay.slot_id == slot.id:
                # Kolla om båtens vistelse överlappar med en befintlig vistelse
                if max(boat.arrival, stay.start_time) < min(boat.departure, stay.end_time):
                    return False
        return True

    def find_available_slots(self, boat: Boat, slots: List[Slot], existing_stays: List[BoatStay]) -> List[Slot]:
        """Hitta alla tillgängliga platser för en båt"""
        return [slot for slot in slots if self.is_slot_available(slot, boat, existing_stays)]

    def find_best_slot(self, boat: Boat, available_slots: List[Slot], criteria_fn=None) -> Slot:
        """Hitta den bästa platsen enligt angivna kriterier"""
        if not available_slots:
            return None

        if criteria_fn:
            return min(available_slots, key=criteria_fn)

        # Standardkriterium: Minimera outnyttjad bredd
        return min(available_slots, key=lambda s: s.max_width - boat.width)
