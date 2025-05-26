from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Table, Text, JSON
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


class AnalysisType(str, Enum):
    """Enum för olika typer av AI-analyser"""
    STRATEGY_COMPARISON = "strategy_comparison"
    OPTIMIZATION = "optimization"
    RECOMMENDATION = "recommendation"
    QUESTION_ANSWER = "question_answer"
    PERFORMANCE_ANALYSIS = "performance_analysis"


class ConfidenceLevel(str, Enum):
    """Enum för AI-konfidensnivåer"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


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


class OptimizationRun(Base):
    """
    Modell för optimeringskörninngar.
    Sparar metadata om varje optimering som utförs.
    """
    __tablename__ = "optimization_runs"

    id = Column(Integer, primary_key=True, index=True)

    # Grundläggande metadata
    timestamp = Column(DateTime, nullable=False,
                       default=datetime.utcnow, index=True)
    execution_time_seconds = Column(Float, nullable=False)

    # Input-parametrar
    boats_count = Column(Integer, nullable=False)
    slots_count = Column(Integer, nullable=False)
    strategies_used = Column(JSON, nullable=False)  # Lista med strateginamn

    # Resultat-metadata
    best_strategy = Column(String, nullable=True)
    boats_placed = Column(Integer, nullable=False, default=0)
    placement_rate = Column(Float, nullable=False, default=0.0)

    # Koppla till AI-analys
    ai_analysis_id = Column(Integer, ForeignKey(
        "ai_analyses.id"), nullable=True)

    # Relationer
    ai_analysis = relationship(
        "AIAnalysis", back_populates="optimization_runs")
    strategy_results = relationship(
        "StrategyResult", back_populates="optimization_run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"OptimizationRun(id={self.id}, timestamp={self.timestamp}, best_strategy={self.best_strategy}, boats_placed={self.boats_placed})"


class StrategyResult(Base):
    """
    Modell för strategiresultat.
    Sparar detaljerade resultat för varje strategi i en optimering.
    """
    __tablename__ = "strategy_results"

    id = Column(Integer, primary_key=True, index=True)
    optimization_run_id = Column(Integer, ForeignKey(
        "optimization_runs.id"), nullable=False)

    # Strategiinformation
    strategy_name = Column(String, nullable=False, index=True)
    strategy_description = Column(Text, nullable=True)

    # Prestanda-mått
    boats_placed = Column(Integer, nullable=False, default=0)
    placement_rate = Column(Float, nullable=False, default=0.0)
    width_utilization = Column(Float, nullable=False, default=0.0)
    execution_time_seconds = Column(Float, nullable=False)

    # Detaljerade mått (JSON för flexibilitet)
    detailed_metrics = Column(JSON, nullable=True)

    # Eventuella fel
    error_message = Column(Text, nullable=True)

    # Relationer
    optimization_run = relationship(
        "OptimizationRun", back_populates="strategy_results")

    def __repr__(self):
        return f"StrategyResult(id={self.id}, strategy={self.strategy_name}, boats_placed={self.boats_placed})"


class AIAnalysis(Base):
    """
    Modell för AI-analyser.
    Sparar resultat från GPT-analyser för framtida referens och lärande.
    """
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True)

    # Grundläggande metadata
    timestamp = Column(DateTime, nullable=False,
                       default=datetime.utcnow, index=True)
    analysis_type = Column(String, nullable=False,
                           index=True)  # AnalysisType enum

    # AI-modell som användes
    model_used = Column(String, nullable=False)
    temperature = Column(Float, nullable=True)

    # Input-data (hashar för att undvika duplicering)
    input_hash = Column(String, nullable=True, index=True)
    input_summary = Column(JSON, nullable=True)  # Sammanfattning av input-data

    # AI-analys resultat
    analysis_result = Column(JSON, nullable=False)  # Fullständig AI-analys
    confidence_level = Column(String, nullable=True)  # ConfidenceLevel enum
    confidence_score = Column(Float, nullable=True)  # 0.0-1.0

    # Rekommendationer och insikter
    recommendations = Column(JSON, nullable=True)
    key_insights = Column(JSON, nullable=True)

    # Chain of Thought reasoning (om aktiverat)
    reasoning_steps = Column(JSON, nullable=True)

    # Performance-mått
    processing_time_seconds = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True)

    # Kvalitetsbedömning (kan fyllas i senare)
    human_feedback_rating = Column(Integer, nullable=True)  # 1-5 skala
    human_feedback_comments = Column(Text, nullable=True)

    # Relationer
    optimization_runs = relationship(
        "OptimizationRun", back_populates="ai_analysis")

    def __repr__(self):
        return f"AIAnalysis(id={self.id}, type={self.analysis_type}, timestamp={self.timestamp}, confidence={self.confidence_level})"


class AIQuestion(Base):
    """
    Modell för AI-frågor.
    Sparar frågor som ställts till AI:n och deras svar.
    """
    __tablename__ = "ai_questions"

    id = Column(Integer, primary_key=True, index=True)

    # Fråga och svar
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)

    # Metadata
    timestamp = Column(DateTime, nullable=False,
                       default=datetime.utcnow, index=True)
    model_used = Column(String, nullable=False)

    # Kontext som användes för att besvara frågan
    context_summary = Column(JSON, nullable=True)

    # Prestanda
    processing_time_seconds = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True)

    # Kvalitetsbedömning
    user_rating = Column(Integer, nullable=True)  # 1-5 skala
    user_feedback = Column(Text, nullable=True)

    def __repr__(self):
        return f"AIQuestion(id={self.id}, question='{self.question[:50]}...', timestamp={self.timestamp})"


class SystemMetrics(Base):
    """
    Modell för systemmått.
    Sparar prestanda- och användningsstatistik.
    """
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)

    # Tidsstämpel
    timestamp = Column(DateTime, nullable=False,
                       default=datetime.utcnow, index=True)
    metric_date = Column(DateTime, nullable=False,
                         index=True)  # Datum för måttet

    # API-användning
    api_requests_total = Column(Integer, nullable=False, default=0)
    api_requests_ai = Column(Integer, nullable=False, default=0)
    api_requests_optimization = Column(Integer, nullable=False, default=0)

    # Optimeringsstatistik
    optimizations_run = Column(Integer, nullable=False, default=0)
    average_boats_placed = Column(Float, nullable=True)
    average_execution_time = Column(Float, nullable=True)

    # AI-användning
    ai_analyses_run = Column(Integer, nullable=False, default=0)
    ai_questions_asked = Column(Integer, nullable=False, default=0)
    ai_tokens_used = Column(Integer, nullable=False, default=0)
    ai_cost_estimate = Column(Float, nullable=True)  # Uppskattad kostnad i USD

    # Systemresurser
    memory_usage_mb = Column(Float, nullable=True)
    cpu_usage_percent = Column(Float, nullable=True)

    # Databas-mått
    database_connections_active = Column(Integer, nullable=True)
    database_query_time_avg = Column(Float, nullable=True)

    def __repr__(self):
        return f"SystemMetrics(date={self.metric_date}, api_requests={self.api_requests_total}, optimizations={self.optimizations_run})"


class UserPreferences(Base):
    """
    Modell för användarpreferenser.
    Sparar användarspecifika inställningar och preferenser.
    """
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)

    # Användaridentifiering (kan utökas senare med riktig autentisering)
    user_identifier = Column(String, nullable=False, unique=True, index=True)

    # Preferenser för strategier
    # Lista med föredragda strategier
    preferred_strategies = Column(JSON, nullable=True)
    strategy_weights = Column(JSON, nullable=True)  # Anpassade viktningar

    # AI-preferenser
    ai_detail_level = Column(String, nullable=False,
                             default="medium")  # low, medium, high
    ai_confidence_threshold = Column(Float, nullable=False, default=0.6)

    # UI-preferenser
    default_view = Column(String, nullable=True)
    theme = Column(String, nullable=False, default="light")

    # Notifieringsinställningar
    email_notifications = Column(Boolean, nullable=False, default=False)
    notification_frequency = Column(String, nullable=False, default="weekly")

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False,
                        default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"UserPreferences(user={self.user_identifier}, ai_detail={self.ai_detail_level})"


# Indexer för bättre prestanda
Index('idx_boat_stays_boat_time', BoatStay.boat_id, BoatStay.start_time)
Index('idx_boat_stays_slot_time', BoatStay.slot_id, BoatStay.start_time)
Index('idx_boats_arrival', Boat.arrival)
Index('idx_slots_type_status', Slot.slot_type, Slot.status)
Index('idx_ai_analyses_type_timestamp',
      AIAnalysis.analysis_type, AIAnalysis.timestamp)
Index('idx_optimization_runs_timestamp', OptimizationRun.timestamp)
Index('idx_strategy_results_strategy', StrategyResult.strategy_name)
Index('idx_system_metrics_date', SystemMetrics.metric_date)
