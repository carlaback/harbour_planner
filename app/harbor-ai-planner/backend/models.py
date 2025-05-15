from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


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

    stays = relationship("BoatStay", back_populates="boat",
                         cascade="all, delete-orphan")

    def __repr__(self):
        return f"Boat(id={self.id}, name={self.name}, width={self.width}, arrival={self.arrival}, departure={self.departure})"

    def is_present_at(self, date_time):
        """Kontrollera om båten är i hamnen vid given tidpunkt"""
        return self.arrival <= date_time <= self.departure


class Slot(Base):
    """
    Modell för båtplatser.
    Representerar platser i hamnen där båtar kan förtöjas.
    """
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    # Maxbredd för båtar på denna plats
    max_width = Column(Float, nullable=False)
    is_reserved = Column(Boolean, default=False)  # Om platsen är reserverad
    # Om temporärt tillgänglig, från när
    available_from = Column(DateTime, nullable=True)
    # Om temporärt tillgänglig, till när
    available_until = Column(DateTime, nullable=True)

    stays = relationship("BoatStay", back_populates="slot",
                         cascade="all, delete-orphan")

    def __repr__(self):
        if self.is_reserved and self.available_from and self.available_until:
            return f"Slot(id={self.id}, name={self.name}, max_width={self.max_width}, reserved but available {self.available_from} to {self.available_until})"
        elif self.is_reserved:
            return f"Slot(id={self.id}, name={self.name}, max_width={self.max_width}, permanently reserved)"
        else:
            return f"Slot(id={self.id}, name={self.name}, max_width={self.max_width}, available)"

    def is_available(self, from_time, until_time):
        """
        Kontrollera om platsen är tillgänglig under en viss period.

        Args:
            from_time: Periodens starttid
            until_time: Periodens sluttid

        Returns:
            bool: True om platsen är tillgänglig under hela perioden, annars False
        """
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

        if not self.is_reserved:
            return "Tillgänglig"
        elif self.is_reserved and not (self.available_from and self.available_until):
            return "Permanent reserverad"
        elif (self.available_from and self.available_until and
              self.available_from <= current_date <= self.available_until):
            return f"Temporärt tillgänglig till {self.available_until.strftime('%Y-%m-%d')}"
        else:
            return "Reserverad"


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

    boat = relationship("Boat", back_populates="stays")
    slot = relationship("Slot", back_populates="stays")

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
                min(self.end_time, other_stay.end_time))

    def duration_days(self):
        """Beräkna vistelsens längd i dagar"""
        delta = self.end_time - self.start_time
        # Konvertera sekunder till dagar
        return delta.days + (delta.seconds / 86400)
