from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from sqlalchemy import Index

Base = declarative_base()


class SlotType(str, Enum):
    """Enum för olika typer av båtplatser"""
    GUEST = "guest"
    FLEX = "flex"
    PERMANENT = "permanent"
    GUEST_DROP_IN = "guest_drop_in"
    OTHER = "other"


class SlotStatus(str, Enum):
    """Enum för båtplatsernas status"""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"


class Boat(Base):
    """
    Modell för båtar.
    Representerar båtar som ska placeras på platser i hamnen.
    """
    __tablename__ = "boats"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    width = Column(Float, nullable=False)  # Båtens bredd i meter
    arrival = Column(DateTime, nullable=False)  # Ankomsttid
    departure = Column(DateTime, nullable=False)  # Avgångstid

    boat_stays = relationship("BoatStay", back_populates="boat",
                              cascade="all, delete-orphan")

    def __repr__(self):
        return f"Boat(id={self.id}, name={self.name}, width={self.width}, arrival={self.arrival}, departure={self.departure})"

    def is_present_at(self, date_time):
        """Kontrollera om båten är i hamnen vid given tidpunkt"""
        return self.arrival <= date_time <= self.departure


class Dock(Base):
    """
    Modell för bryggor.
    Representerar bryggor i hamnen där båtplatser är placerade.
    """
    __tablename__ = "docks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    position_x = Column(Integer, nullable=False)
    position_y = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    length = Column(Integer, nullable=False)

    # Relationer
    slots = relationship("Slot", back_populates="dock",
                         cascade="all, delete-orphan")

    def __repr__(self):
        return f"Dock(id={self.id}, name={self.name}, pos=({self.position_x},{self.position_y}), size={self.width}x{self.length})"


class Slot(Base):
    """
    Modell för båtplatser.
    Representerar platser i hamnen där båtar kan förtöjas.
    """
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    position_x = Column(Integer, nullable=False)
    position_y = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    length = Column(Integer, nullable=False)
    depth = Column(Float, nullable=True)
    # Maxbredd för båtar på denna plats
    max_width = Column(Float, nullable=False)
    slot_type = Column(String, nullable=False,
                       default=SlotType.GUEST)  # Typ av plats
    status = Column(String, nullable=False,
                    default=SlotStatus.AVAILABLE)  # Status
    is_reserved = Column(Boolean, default=False)  # Om platsen är reserverad
    price_per_day = Column(Integer, nullable=True)  # Pris per dag
    # Om temporärt tillgänglig, från när
    available_from = Column(DateTime, nullable=True)
    # Om temporärt tillgänglig, till när
    available_until = Column(DateTime, nullable=True)
    dock_id = Column(Integer, ForeignKey("docks.id"), nullable=False)
    # Aktuell båt på platsen, om någon
    boat_id = Column(Integer, ForeignKey("boats.id"), nullable=True)

    # Relationer
    boat_stays = relationship(
        "BoatStay", back_populates="slot", cascade="all, delete-orphan")
    dock = relationship("Dock", back_populates="slots")
    boat = relationship("Boat", foreign_keys=[boat_id])

    def __repr__(self):
        status_str = f"status: {self.status}"
        if self.is_reserved and self.available_from and self.available_until:
            reserved_str = f"reserved but available {self.available_from} to {self.available_until}"
        elif self.is_reserved:
            reserved_str = "permanently reserved"
        else:
            reserved_str = "available"

        return f"Slot(id={self.id}, name={self.name}, type={self.slot_type}, {status_str}, {reserved_str}, pos=({self.position_x},{self.position_y}))"

    def is_available(self, from_time, until_time):
        """
        Kontrollera om platsen är tillgänglig under en viss period.

        Args:
            from_time: Periodens starttid
            until_time: Periodens sluttid

        Returns:
            bool: True om platsen är tillgänglig under hela perioden, annars False
        """
        # Om platsen har en status som inte är tillgänglig, returnera False
        if self.status != SlotStatus.AVAILABLE:
            return False

        # Om platsen är reserverad, måste vi kontrollera tillgänglighetsperioden
        if self.is_reserved:
            # Om platsen är permanent reserverad (utan tillgänglighetsperiod)
            if not self.available_from or not self.available_until:
                return False

            # Om platsen är temporärt tillgänglig, kontrollera om den begärda perioden
            # ligger helt inom tillgänglighetsperioden
            return self.available_from <= from_time and self.available_until >= until_time

        # Om platsen inte är reserverad, är den alltid tillgänglig
        # (förutsatt att ingen annan båt är där, vilket kontrolleras på annat ställe)
        return True

    def get_availability_status(self, current_date=None):
        """
        Returnera en beskrivning av platsens tillgänglighetsstatus.

        Args:
            current_date: Datum att kontrollera status för (default: aktuellt datum)

        Returns:
            str: Beskrivning av tillgänglighetsstatus
        """
        if current_date is None:
            current_date = datetime.now()

        # Returnera aktuell status
        if self.status == SlotStatus.AVAILABLE:
            if self.slot_type == SlotType.PERMANENT:
                return "Permanent plats (ledig)"
            elif self.slot_type == SlotType.FLEX:
                return "Flexplats (ledig)"
            elif self.slot_type == SlotType.GUEST_DROP_IN:
                return "Gästhamn drop-in (ledig)"
            else:
                return "Gästplats (ledig)"
        elif self.status == SlotStatus.OCCUPIED:
            return "Upptagen"
        elif self.status == SlotStatus.RESERVED:
            return "Reserverad"
        elif self.status == SlotStatus.MAINTENANCE:
            return "Underhåll"
        else:
            return "Okänd status"


class BoatStay(Base):
    """
    Modell för båtvistelser.
    Representerar koppling mellan en båt och en plats under en specifik period.
    """
    __tablename__ = "boat_stays"

    id = Column(Integer, primary_key=True, index=True)
    boat_id = Column(Integer, ForeignKey("boats.id"), nullable=False)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    # Vilken strategi som genererade denna placering
    strategy_name = Column(String, nullable=True)

    boat = relationship("Boat", back_populates="boat_stays")
    slot = relationship("Slot", back_populates="boat_stays")

    def __repr__(self):
        return f"BoatStay(id={self.id}, boat_id={self.boat_id}, slot_id={self.slot_id}, start={self.start_time}, end={self.end_time})"

    def overlaps_with(self, other_stay):
        """
        Kontrollera om denna vistelse överlappar med en annan vistelse.

        Args:
            other_stay: En annan BoatStay-instans att jämföra med

        Returns:
            bool: True om vistelserna överlappar i tid, annars False
        """
        # Överlappning sker om en vistelse börjar innan den andra slutar
        # och slutar efter att den andra börjar
        return (max(self.start_time, other_stay.start_time)
                < min(self.end_time, other_stay.end_time))

    def duration_days(self):
        """Beräkna vistelsens längd i dagar"""
        delta = self.end_time - self.start_time
        # Konvertera sekunder till dagar
        return delta.days + (delta.seconds / 86400)
