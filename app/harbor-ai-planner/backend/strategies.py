# strategies.py - förbättrad version
from typing import List, Dict, Any, Tuple, Optional, Callable, Protocol
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import random
import logging
import asyncio
from functools import lru_cache

from models import Boat, Slot, BoatStay, SlotType

# Konfigurera loggning
logger = logging.getLogger(__name__)


class ScoringFunction(Protocol):
    """Protokoll för poängsättningsfunktioner för båtplatskombinationer"""

    def __call__(self, boat: Boat, slot: Slot) -> float: ...


class BaseStrategy:
    """Basstrategiimplementation för båtplacering"""

    def __init__(self, name: str, description: str = None):
        self.name = name
        self.description = description or f"{name} strategy"

    async def place_boats(self, db: AsyncSession, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        """
        Huvudfunktion som alla strategier implementerar.
        Placerar båtar på platser och returnerar en lista med båtvistelser.

        Args:
            db: Databassession
            boats: Lista med båtar att placera
            slots: Lista med tillgängliga platser

        Returns:
            Lista med BoatStay-objekt som representerar placeringarna
        """
        raise NotImplementedError("Subklasser måste implementera place_boats")

    def is_slot_available(self, slot: Slot, boat: Boat, existing_stays: List[BoatStay]) -> bool:
        """
        Kontrollera om en plats är tillgänglig för en båt under dess vistelse.

        Args:
            slot: Platsen att kontrollera
            boat: Båten som ska placeras
            existing_stays: Lista med befintliga båtvistelser

        Returns:
            True om platsen är tillgänglig, annars False
        """
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
        """
        Hitta alla tillgängliga platser för en båt.

        Args:
            boat: Båten som ska placeras
            slots: Lista med potentiella platser
            existing_stays: Lista med befintliga båtvistelser

        Returns:
            Lista med tillgängliga platser
        """
        return [slot for slot in slots if self.is_slot_available(slot, boat, existing_stays)]

    def find_best_slot(self, boat: Boat, available_slots: List[Slot],
                       scoring_fn: Optional[ScoringFunction] = None) -> Optional[Slot]:
        """
        Hitta den bästa platsen enligt angivna kriterier.

        Args:
            boat: Båten som ska placeras
            available_slots: Lista med tillgängliga platser
            scoring_fn: Valfri funktion för att poängsätta platser (lägre är bättre)

        Returns:
            Den bästa platsen eller None om ingen plats är tillgänglig
        """
        if not available_slots:
            return None

        # Använd specificerad poängsättningsfunktion eller standardkriterium
        if scoring_fn:
            return min(available_slots, key=lambda s: scoring_fn(boat, s))

        # Standardkriterium: Minimera outnyttjad bredd
        return min(available_slots, key=lambda s: s.max_width - boat.width)

    def calculate_efficiency(self, stays: List[BoatStay], boats: List[Boat], slots: List[Slot]) -> Dict[str, float]:
        """
        Beräkna effektiviteten för en given placering.

        Args:
            stays: Lista med båtvistelser
            boats: Lista med båtar
            slots: Lista med platser

        Returns:
            Statistik om placeringens effektivitet
        """
        if not stays:
            return {
                "boats_placed": 0,
                "placement_rate": 0.0,
                "width_utilization": 0.0,
                "average_stay_duration": 0.0,
                "temporary_slots_used": 0
            }

        # Hitta använda båtar och platser
        boat_dict = {boat.id: boat for boat in boats}
        slot_dict = {slot.id: slot for slot in slots}

        # Beräkna placeringsstatistik
        boats_placed = len(set(stay.boat_id for stay in stays))
        placement_rate = boats_placed / len(boats) if boats else 0.0

        # Beräkna breddutnyttjande
        total_width_ratio = 0.0
        total_stay_days = 0.0
        temp_slots_used = 0

        for stay in stays:
            boat = boat_dict.get(stay.boat_id)
            slot = slot_dict.get(stay.slot_id)

            if boat and slot:
                # Beräkna breddutnyttjande
                width_ratio = boat.width / slot.max_width
                total_width_ratio += width_ratio

                # Beräkna vistelselängd
                stay_days = (stay.end_time -
                             stay.start_time).total_seconds() / (24 * 3600)
                total_stay_days += stay_days

                # Räkna temporära platser
                if slot.is_reserved and slot.available_from and slot.available_until:
                    temp_slots_used += 1

        return {
            "boats_placed": boats_placed,
            "placement_rate": placement_rate,
            "width_utilization": total_width_ratio / len(stays) if stays else 0.0,
            "average_stay_duration": total_stay_days / len(stays) if stays else 0.0,
            "temporary_slots_used": temp_slots_used
        }


class LargestFirstStrategy(BaseStrategy):
    """Strategi: Placera de bredaste båtarna först"""

    def __init__(self):
        super().__init__(
            "largest_first",
            "Prioriterar de bredaste båtarna först för att säkerställa att stora båtar får plats"
        )

    async def place_boats(self, db: AsyncSession, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        # Sortera båtar efter bredd (störst först)
        sorted_boats = sorted(boats, key=lambda b: b.width, reverse=True)
        existing_stays = []

        for boat in sorted_boats:
            # Hitta tillgängliga platser
            available_slots = self.find_available_slots(
                boat, slots, existing_stays)

            if available_slots:
                # Hitta bästa plats (minst slösad bredd)
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

    async def place_boats(self, db: AsyncSession, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
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

    async def place_boats(self, db: AsyncSession, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        # Sortera båtar efter ankomsttid
        sorted_boats = sorted(boats, key=lambda b: b.arrival)
        existing_stays = []

        for boat in sorted_boats:
            available_slots = self.find_available_slots(
                boat, slots, existing_stays)

            if available_slots:
                # Välj den plats som ger minst slösad bredd
                best_slot = self.find_best_slot(
                    boat,
                    available_slots,
                    # Minimera skillnaden i bredd
                    lambda b, s: abs(s.max_width - b.width)
                )

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

    async def place_boats(self, db: AsyncSession, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
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


class TemporaryFirstStrategy(BaseStrategy):
    """Strategi: Prioritera temporärt tillgängliga platser först"""

    def __init__(self):
        super().__init__(
            "temporary_first",
            "Prioriterar att fylla temporärt tillgängliga platser först för att maximera nyttjandet av dessa"
        )

    async def place_boats(self, db: AsyncSession, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        # Sortera båtar efter ankomsttid
        sorted_boats = sorted(boats, key=lambda b: b.arrival)
        existing_stays = []

        for boat in sorted_boats:
            available_slots = self.find_available_slots(
                boat, slots, existing_stays)

            if available_slots:
                # Dela upp i temporära och vanliga platser
                temp_slots = [
                    s for s in available_slots if s.is_reserved and s.available_from and s.available_until]
                regular_slots = [
                    s for s in available_slots if not s.is_reserved]

                if temp_slots:
                    # Prioritera temporära platser och välj den med bäst passning
                    best_slot = self.find_best_slot(boat, temp_slots)
                elif regular_slots:
                    # Om inga temporära, använd vanliga platser
                    best_slot = self.find_best_slot(boat, regular_slots)
                else:
                    continue  # Ingen lämplig plats

                stay = BoatStay(
                    boat_id=boat.id,
                    slot_id=best_slot.id,
                    start_time=boat.arrival,
                    end_time=boat.departure,
                    strategy_name=self.name
                )
                existing_stays.append(stay)

        return existing_stays


class ShortStayFirstStrategy(BaseStrategy):
    """Strategi: Prioritera korta vistelser först"""

    def __init__(self):
        super().__init__(
            "short_stay_first",
            "Prioriterar båtar med kortare vistelser för att maximera platsomsättningen"
        )

    async def place_boats(self, db: AsyncSession, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        # Sortera båtar efter vistelselängd (kortast först)
        sorted_boats = sorted(boats, key=lambda b: (
            b.departure - b.arrival).total_seconds())
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


class LongStayFirstStrategy(BaseStrategy):
    """Strategi: Prioritera långa vistelser först"""

    def __init__(self):
        super().__init__(
            "long_stay_first",
            "Prioriterar båtar med längre vistelser för att minimera antalet platsbyten"
        )

    async def place_boats(self, db: AsyncSession, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        # Sortera båtar efter vistelselängd (längst först)
        sorted_boats = sorted(
            boats,
            key=lambda b: (b.departure - b.arrival).total_seconds(),
            reverse=True
        )
        existing_stays = []

        for boat in sorted_boats:
            available_slots = self.find_available_slots(
                boat, slots, existing_stays)

            if available_slots:
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


class RandomStrategy(BaseStrategy):
    """Strategi: Placera båtar i slumpmässig ordning"""

    def __init__(self):
        super().__init__(
            "random",
            "Placerar båtar i slumpmässig ordning (används som kontroll)"
        )

    async def place_boats(self, db: AsyncSession, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        # Slumpa ordningen på båtarna
        shuffled_boats = boats.copy()
        random.shuffle(shuffled_boats)
        existing_stays = []

        for boat in shuffled_boats:
            available_slots = self.find_available_slots(
                boat, slots, existing_stays)

            if available_slots:
                # Välj en slumpmässig plats
                best_slot = random.choice(available_slots)

                stay = BoatStay(
                    boat_id=boat.id,
                    slot_id=best_slot.id,
                    start_time=boat.arrival,
                    end_time=boat.departure,
                    strategy_name=self.name
                )
                existing_stays.append(stay)

        return existing_stays


class HybridStrategy(BaseStrategy):
    """Strategi: Kombination av flera strategier för optimal placering"""

    def __init__(self):
        super().__init__(
            "hybrid_optimal",
            "Kombinerar flera strategier för att hitta den bästa lösningen för varje båt"
        )
        # Använd dessa understrategier
        self.sub_strategies = [
            LargestFirstStrategy(),
            BestFitStrategy(),
            TemporaryFirstStrategy()
        ]

    async def place_boats(self, db: AsyncSession, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        # Sortera båtar efter komplexitet (bredd / tillgänglig tid)
        # Stora båtar med kort vistelse är svårast att placera
        sorted_boats = sorted(
            boats,
            key=lambda b: (
                b.width,
                1 / max(1, (b.departure - b.arrival).total_seconds())
            ),
            reverse=True
        )

        existing_stays = []

        # Placera varje båt med den strategi som ger bäst resultat
        for boat in sorted_boats:
            best_slot = None
            best_strategy_name = None
            min_wasted_width = float('inf')

            # Testa varje strategi för denna båt
            for strategy in self.sub_strategies:
                # Hitta tillgängliga platser enligt denna strategi
                available_slots = strategy.find_available_slots(
                    boat, slots, existing_stays)
                if not available_slots:
                    continue

                # Hitta bästa platsen enligt denna strategi
                candidate_slot = strategy.find_best_slot(boat, available_slots)

                # Beräkna slösad bredd
                wasted_width = candidate_slot.max_width - boat.width

                # Uppdatera bästa resultatet
                if wasted_width < min_wasted_width:
                    min_wasted_width = wasted_width
                    best_slot = candidate_slot
                    best_strategy_name = f"{self.name} (via {strategy.name})"

            # Om vi hittade en lämplig plats, skapa en vistelse
            if best_slot:
                stay = BoatStay(
                    boat_id=boat.id,
                    slot_id=best_slot.id,
                    start_time=boat.arrival,
                    end_time=boat.departure,
                    strategy_name=best_strategy_name
                )
                existing_stays.append(stay)

        return existing_stays


class MultiObjectiveStrategy(BaseStrategy):
    """Strategi: Använder flera mål för att optimera placeringen"""

    def __init__(self):
        super().__init__(
            "multi_objective",
            "Optimerar flera mål samtidigt: maximerar antalet båtar, minimerar outnyttjad bredd, " +
            "och prioriterar temporära platser när det är lämpligt"
        )

    async def place_boats(self, db: AsyncSession, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        # Sortera båtar efter en kombinerad prioritet:
        # 1. Bredd (stora båtar är svårare att placera)
        # 2. Vistelsens längd (kortare vistelser är lättare att placera)
        # 3. Ankomsttid (tidigare ankomster först)
        sorted_boats = sorted(
            boats,
            key=lambda b: (
                -b.width,  # Negativ för att sortera störst först
                (b.departure - b.arrival).total_seconds(),
                b.arrival
            )
        )

        existing_stays = []

        for boat in sorted_boats:
            available_slots = self.find_available_slots(
                boat, slots, existing_stays)

            if not available_slots:
                continue

            # Beräkna poäng för varje tillgänglig plats
            slot_scores = []
            for slot in available_slots:
                # Flera faktorer påverkar poängen
                # Högre för bättre passning
                width_score = 1.0 - \
                    (slot.max_width - boat.width) / slot.max_width

                # Bonus för temporära platser
                temp_bonus = 0.2 if (
                    slot.is_reserved and slot.available_from and slot.available_until) else 0.0

                # Lägre poäng för gästplatser som bör sparas till gästbåtar
                guest_penalty = 0.1 if slot.slot_type == "guest" else 0.0

                # Sammanställ poäng (högre är bättre)
                total_score = width_score + temp_bonus - guest_penalty

                slot_scores.append((slot, total_score))

            # Välj platsen med högst poäng
            if slot_scores:
                best_slot, _ = max(slot_scores, key=lambda x: x[1])

                stay = BoatStay(
                    boat_id=boat.id,
                    slot_id=best_slot.id,
                    start_time=boat.arrival,
                    end_time=boat.departure,
                    strategy_name=self.name
                )
                existing_stays.append(stay)

        return existing_stays


class SlotTypeMatchingStrategy(BaseStrategy):
    """Strategi: Placerar båtar på platser av lämplig typ"""

    def __init__(self):
        super().__init__(
            "slot_type_matching",
            "Placerar båtar på platser som bäst matchar deras behov (t.ex. gästplatser för kortare vistelser)"
        )

    async def place_boats(self, db: AsyncSession, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        # Sortera båtar efter ankomsttid
        sorted_boats = sorted(boats, key=lambda b: b.arrival)
        existing_stays = []

        for boat in sorted_boats:
            available_slots = self.find_available_slots(
                boat, slots, existing_stays)

            if not available_slots:
                continue

            # Beräkna vistelselängd i dagar
            stay_length = (boat.departure - boat.arrival).days

            # Kategorisera platser efter typ
            guest_slots = [
                s for s in available_slots if s.slot_type == "guest"]
            flex_slots = [s for s in available_slots if s.slot_type == "flex"]
            permanent_slots = [
                s for s in available_slots if s.slot_type == "permanent"]
            other_slots = [
                s for s in available_slots if s not in guest_slots + flex_slots + permanent_slots]

            # Välj platstyp baserat på vistelselängd
            target_slots = []
            if stay_length <= 7:  # Kort vistelse (upp till en vecka)
                # Föredra gästplatser för kort vistelse
                target_slots = guest_slots or flex_slots or other_slots or permanent_slots
            elif stay_length <= 30:  # Medellång vistelse (upp till en månad)
                # Föredra flexplatser för medellånga vistelser
                target_slots = flex_slots or other_slots or guest_slots or permanent_slots
            else:  # Lång vistelse
                # Föredra permanenta platser för långa vistelser
                target_slots = permanent_slots or flex_slots or other_slots or guest_slots

            if target_slots:
                # Välj den plats som ger bäst breddpassning inom den föredragna typen
                best_slot = self.find_best_slot(boat, target_slots)

                stay = BoatStay(
                    boat_id=boat.id,
                    slot_id=best_slot.id,
                    start_time=boat.arrival,
                    end_time=boat.departure,
                    strategy_name=self.name
                )
                existing_stays.append(stay)

        return existing_stays


class SeasonalStrategy(BaseStrategy):
    """Strategi: Optimerar placeringen baserat på säsong"""

    def __init__(self):
        super().__init__(
            "seasonal",
            "Anpassar placeringsstrategi baserat på säsong (högsäsong vs. lågsäsong)"
        )

    async def place_boats(self, db: AsyncSession, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        # Definiera högsäsong (t.ex. juni-augusti)
        high_season_start = datetime(datetime.now().year, 6, 1)
        high_season_end = datetime(datetime.now().year, 8, 31)

        # Sortera båtar efter ankomsttid
        sorted_boats = sorted(boats, key=lambda b: b.arrival)
        existing_stays = []

        for boat in sorted_boats:
            # Kontrollera om båten är i högsäsong (om någon del av vistelsen överlappar högsäsong)
            in_high_season = (
                (boat.arrival <= high_season_end and boat.departure >= high_season_start)
            )

            available_slots = self.find_available_slots(
                boat, slots, existing_stays)

            if not available_slots:
                continue

            best_slot = None

            if in_high_season:
                # Under högsäsong prioriterar vi att få in så många båtar som möjligt
                # Använd best-fit för att minimera slöseri med bredd
                best_slot = self.find_best_slot(
                    boat,
                    available_slots,
                    lambda b, s: s.max_width - b.width
                )
            else:
                # Under lågsäsong kan vi prioritera bekvämlighet och gruppera liknande båtar
                # Sortera platser efter bredd (största först) för att ge båtar mer utrymme
                available_slots.sort(key=lambda s: s.max_width, reverse=True)
                if available_slots:
                    best_slot = available_slots[0]

            if best_slot:
                stay = BoatStay(
                    boat_id=boat.id,
                    slot_id=best_slot.id,
                    start_time=boat.arrival,
                    end_time=boat.departure,
                    strategy_name=f"{self.name}_{'high' if in_high_season else 'low'}"
                )
                existing_stays.append(stay)

        return existing_stays


# Lista över alla tillgängliga strategier
ALL_STRATEGIES = [
    LargestFirstStrategy(),
    SmallestFirstStrategy(),
    BestFitStrategy(),
    EarliestArrivalFirstStrategy(),
    TemporaryFirstStrategy(),
    ShortStayFirstStrategy(),
    LongStayFirstStrategy(),
    RandomStrategy(),
    HybridStrategy(),
    MultiObjectiveStrategy(),
    SlotTypeMatchingStrategy(),
    SeasonalStrategy()
]

# Mappning från strateginamn till strategiinstans
STRATEGY_MAP = {strategy.name: strategy for strategy in ALL_STRATEGIES}


def get_strategy_by_name(name: str) -> Optional[BaseStrategy]:
    """
    Hämta en strategi baserat på namn.

    Args:
        name: Namn på strategin att hämta

    Returns:
        Strategiinstans eller None om strategin inte finns
    """
    strategy = STRATEGY_MAP.get(name)
    if not strategy:
        logger.warning(f"Strategy not found: {name}")
    return strategy


async def optimize_placement(db: AsyncSession, boats: List[Boat], slots: List[Slot],
                             strategy_names: List[str] = None) -> Tuple[BaseStrategy, List[BoatStay], Dict[str, Any]]:
    """
    Hitta den optimala placeringen genom att testa flera strategier.

    Args:
        db: Databassession
        boats: Lista med båtar att placera
        slots: Lista med tillgängliga platser
        strategy_names: Lista med namn på strategier att testa (None = alla)

    Returns:
        Tuple med (bästa strategi, bästa placeringar, metrics)
    """
    # Välj strategier att testa
    if not strategy_names:
        strategies = ALL_STRATEGIES
    else:
        strategies = [get_strategy_by_name(
            name) for name in strategy_names if get_strategy_by_name(name)]

    if not strategies:
        logger.warning("No valid strategies specified for optimization")
        return None, [], {}

    # Kör alla strategier parallellt för bättre prestanda
    results = await asyncio.gather(*[
        strategy.place_boats(db, boats, slots) for strategy in strategies
    ])

    # Utvärdera resultaten
    best_score = -1
    best_index = 0
    best_metrics = {}

    for i, stays in enumerate(results):
        # Beräkna effektivitet för denna strategi
        strategy = strategies[i]
        metrics = strategy.calculate_efficiency(stays, boats, slots)

        # Beräkna en sammansatt poäng (kan justeras efter behov)
        # 60% baserat på placeringsgrad, 30% baserat på breddutnyttjande, 10% baserat på temporära platser
        placement_score = metrics["placement_rate"] * 60
        efficiency_score = metrics["width_utilization"] * 30
        temp_usage_score = (
            metrics["temporary_slots_used"] / len(slots) if slots else 0) * 10

        combined_score = placement_score + efficiency_score + temp_usage_score

        logger.debug(f"Strategy {strategy.name}: score={combined_score:.2f}, "
                     f"placed={metrics['boats_placed']}/{len(boats)}, "
                     f"efficiency={metrics['width_utilization']:.2f}")

        if combined_score > best_score:
            best_score = combined_score
            best_index = i
            best_metrics = metrics

    # Returnera den bästa strategin och dess resultat
    return strategies[best_index], results[best_index], best_metrics


class ConstraintBasedStrategy(BaseStrategy):
    """
    Strategi: Använder regelbaserad optimering med begränsningar

    Denna strategi tillämpar regler och begränsningar för att hitta optimala placeringar,
    liknande hur en mänsklig hamnkapten skulle resonera.
    """

    def __init__(self):
        super().__init__(
            "constraint_based",
            "Använder regler och begränsningar för att hitta optimala placeringar "
            "baserat på båttyp, vistelselängd och tillgängliga platser"
        )

    async def place_boats(self, db: AsyncSession, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        # Sortera båtar efter en prioritetsordning:
        # 1. Först de som är svårast att placera (stora båtar)
        # 2. Sedan de med längst vistelse
        sorted_boats = sorted(
            boats,
            key=lambda b: (
                -b.width,  # Negera för att få stora båtar först
                # Negera för att få lång vistelse först
                -(b.departure - b.arrival).total_seconds()
            )
        )

        # Gruppera platser efter typ för lättare hantering
        slot_by_type = {}
        for slot in slots:
            if slot.slot_type not in slot_by_type:
                slot_by_type[slot.slot_type] = []
            slot_by_type[slot.slot_type].append(slot)

        # Förberäkna kapacitet per platstyp
        capacity_by_type = {
            slot_type: len(slots_list)
            for slot_type, slots_list in slot_by_type.items()
        }

        # Håll reda på gjorda placeringar
        existing_stays = []

        # Placera båtar enligt regelverk
        for boat in sorted_boats:
            # Beräkna vistelselängd i dagar
            stay_days = (boat.departure - boat.arrival).days

            # Hitta alla tillgängliga platser för denna båt
            available_slots = self.find_available_slots(
                boat, slots, existing_stays)

            if not available_slots:
                continue  # Ingen plats tillgänglig

            # Tillämpa placeringsregler baserat på vistelselängd och båtbredd
            best_slot = None

            # Regel 1: Mycket stora båtar går till speciella platser först
            if boat.width > 4.0:
                # Hitta breda platser
                wide_slots = [
                    s for s in available_slots if s.max_width >= boat.width + 0.5]
                if wide_slots:
                    best_slot = min(
                        wide_slots, key=lambda s: s.max_width - boat.width)

            # Regel 2: Långtidsgäster (över 30 dagar) placeras helst på permanenta platser
            elif stay_days > 30 and not best_slot:
                permanent_slots = [
                    s for s in available_slots if s.slot_type == "permanent"]
                if permanent_slots:
                    best_slot = min(permanent_slots,
                                    key=lambda s: s.max_width - boat.width)

            # Regel 3: Korttidsgäster (1-7 dagar) placeras helst på gästplatser
            elif stay_days <= 7 and not best_slot:
                guest_slots = [
                    s for s in available_slots if s.slot_type == "guest"]
                if guest_slots:
                    best_slot = min(
                        guest_slots, key=lambda s: s.max_width - boat.width)

            # Regel 4: Standardfall - använd best-fit på alla tillgängliga platser
            if not best_slot and available_slots:
                best_slot = min(available_slots,
                                key=lambda s: s.max_width - boat.width)

            # Skapa vistelsen om vi hittade en plats
            if best_slot:
                stay = BoatStay(
                    boat_id=boat.id,
                    slot_id=best_slot.id,
                    start_time=boat.arrival,
                    end_time=boat.departure,
                    strategy_name=self.name
                )
                existing_stays.append(stay)

        return existing_stays


class TimeBlockStrategy(BaseStrategy):
    """
    Strategi: Delar upp tiden i block och optimerar varje block separat

    Denna strategi hanterar fall där båtar kommer och går vid olika tider,
    genom att dela upp tiden i diskreta block och optimera varje block för sig.
    """

    def __init__(self):
        super().__init__(
            "time_block",
            "Delar upp planeringshorisonten i tidsblock och optimerar varje block separat"
        )

    async def place_boats(self, db: AsyncSession, boats: List[Boat], slots: List[Slot]) -> List[BoatStay]:
        if not boats:
            return []

        # Hitta start- och sluttider för planeringshorisonten
        min_time = min(boat.arrival for boat in boats)
        max_time = max(boat.departure for boat in boats)

        # Beräkna längden på planeringshorisonten i dagar
        horizon_days = (max_time - min_time).days + 1

        # För korta planeringar (mindre än 14 dagar), använd dagliga block
        # För medellånga (14-90 dagar), använd veckovisa block
        # För långa (över 90 dagar), använd månadsvisa block
        if horizon_days <= 14:
            block_size = timedelta(days=1)  # Dagliga block
        elif horizon_days <= 90:
            block_size = timedelta(days=7)  # Veckovisa block
        else:
            block_size = timedelta(days=30)  # Månadsvisa block

        # Skapa tidsblock
        time_blocks = []
        current_time = min_time
        while current_time < max_time:
            next_time = current_time + block_size
            time_blocks.append((current_time, next_time))
            current_time = next_time

        # Se till att sista blocket går till max_time
        if time_blocks and time_blocks[-1][1] < max_time:
            time_blocks[-1] = (time_blocks[-1][0], max_time)

        logger.debug(
            f"Created {len(time_blocks)} time blocks for planning horizon of {horizon_days} days")

        # Placera båtar i varje tidsblock
        all_stays = []
        existing_stays = []  # För att hantera överlapp mellan block

        for block_start, block_end in time_blocks:
            # Hitta båtar som är närvarande under detta block
            block_boats = [
                boat for boat in boats
                if boat.arrival < block_end and boat.departure > block_start
            ]

            if not block_boats:
                continue

            logger.debug(
                f"Processing block {block_start} to {block_end}: {len(block_boats)} boats")

            # Sortera båtar efter bredd (störst först)
            block_boats.sort(key=lambda b: b.width, reverse=True)

            # Placera båtar i detta block
            for boat in block_boats:
                # Kontrollera om båten redan har placerats
                if any(stay.boat_id == boat.id for stay in existing_stays):
                    continue

                # Hitta tillgängliga platser
                available_slots = self.find_available_slots(
                    boat, slots, existing_stays)

                if available_slots:
                    # Välj plats med best-fit
                    best_slot = self.find_best_slot(boat, available_slots)

                    stay = BoatStay(
                        boat_id=boat.id,
                        slot_id=best_slot.id,
                        start_time=boat.arrival,
                        end_time=boat.departure,
                        strategy_name=f"{self.name}_block_{block_start.strftime('%Y%m%d')}"
                    )

                    all_stays.append(stay)
                    existing_stays.append(stay)

        return all_stays


# Lägg till de nya strategierna till listan
ALL_STRATEGIES.extend([
    ConstraintBasedStrategy(),
    TimeBlockStrategy()
])

# Uppdatera mappningen
STRATEGY_MAP = {strategy.name: strategy for strategy in ALL_STRATEGIES}
