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


class LargestFirstStrategy(BaseStrategy):
    """Strategi: Placera de bredaste båtarna först"""

    def __init__(self):
        super().__init__(
            "largest_first",
            "Prioriterar de bredaste båtarna först för att säkerställa att stora båtar får plats"
        )

    def place_boats(self, db: Session, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        # Sortera båtar efter bredd (störst först)
        sorted_boats = sorted(boats, key=lambda b: b.width, reverse=True)
        existing_stays = []

        for boat in sorted_boats:
            # Hitta tillgängliga platser
            available_slots = self.find_available_slots(
                boat, slots, existing_stays)

            if available_slots:
                # Hitta bästa plats
                best_slot = self.find_best_slot(boat, available_slots)

                # Skapa en ny vistelse
                stay = BoatStay(
                    boat_id=boat.id,
                    slot_id=best_slot.id,
                    start_time=boat.arrival,
                    end_time=boat.departure,
                    strategy_name=self.name
                )
                existing_stays.append(stay)

        return existing_stays


class SmallestFirstStrategy(BaseStrategy):
    """Strategi: Placera de smalaste båtarna först"""

    def __init__(self):
        super().__init__(
            "smallest_first",
            "Prioriterar de smalaste båtarna först för att maximera antalet placerade båtar"
        )

    def place_boats(self, db: Session, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        # Sortera båtar efter bredd (minst först)
        sorted_boats = sorted(boats, key=lambda b: b.width)
        existing_stays = []

        for boat in sorted_boats:
            available_slots = self.find_available_slots(
                boat, slots, existing_stays)

            if available_slots:
                # Välj den bästa platsen (minst slösad bredd)
                best_slot = self.find_best_slot(boat, available_slots)

                stay = BoatStay(
                    boat_id=boat.id,
                    slot_id=best_slot.id,
                    start_time=boat.arrival,
                    end_time=boat.departure,
                    strategy_name=self.name
                )
                existing_stays.append(stay)

        return existing_stays


class BestFitStrategy(BaseStrategy):
    """Strategi: Placera båtar i platser som ger minst slösad bredd"""

    def __init__(self):
        super().__init__(
            "best_fit",
            "Placerar varje båt på den plats som ger minst outnyttjad bredd (minimerar spillyta)"
        )

    def place_boats(self, db: Session, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        # Sortera båtar efter ankomsttid
        sorted_boats = sorted(boats, key=lambda b: b.arrival)
        existing_stays = []

        for boat in sorted_boats:
            available_slots = self.find_available_slots(
                boat, slots, existing_stays)

            if available_slots:
                # Välj den plats som ger minst slösad bredd
                best_slot = self.find_best_slot(boat, available_slots,
                                                lambda s: s.max_width - boat.width)

                stay = BoatStay(
                    boat_id=boat.id,
                    slot_id=best_slot.id,
                    start_time=boat.arrival,
                    end_time=boat.departure,
                    strategy_name=self.name
                )
                existing_stays.append(stay)

        return existing_stays


class EarliestArrivalFirstStrategy(BaseStrategy):
    """Strategi: Placera båtar baserat på ankomsttid (tidigast först)"""

    def __init__(self):
        super().__init__(
            "earliest_arrival",
            "Prioriterar båtar med tidigast ankomsttid ('först till kvarn'-princip)"
        )

    def place_boats(self, db: Session, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        # Sortera båtar efter ankomsttid (tidigast först)
        sorted_boats = sorted(boats, key=lambda b: b.arrival)
        existing_stays = []

        for boat in sorted_boats:
            available_slots = self.find_available_slots(
                boat, slots, existing_stays)

            if available_slots:
                # Välj den plats som ger minst slösad bredd
                best_slot = self.find_best_slot(boat, available_slots)

                stay = BoatStay(
                    boat_id=boat.id,
                    slot_id=best_slot.id,
                    start_time=boat.arrival,
                    end_time=boat.departure,
                    strategy_name=self.name
                )
                existing_stays.append(stay)

        return existing_stays
