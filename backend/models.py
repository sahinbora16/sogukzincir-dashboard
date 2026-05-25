from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class CollectionPoint(Base):
    __tablename__ = "collection_points"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    address = Column(String, nullable=True)
    status = Column(String, default="active")  # active | inactive | collecting

    tank = relationship("StorageTank", back_populates="collection_point", uselist=False)


class StorageTank(Base):
    __tablename__ = "storage_tanks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    capacity = Column(Float, nullable=False)       # litre
    current_level = Column(Float, default=0.0)     # litre
    temperature = Column(Float, default=4.0)       # °C
    last_updated = Column(DateTime, default=datetime.utcnow)
    collection_point_id = Column(Integer, ForeignKey("collection_points.id"), nullable=True)

    collection_point = relationship("CollectionPoint", back_populates="tank")


class LogisticsFleet(Base):
    __tablename__ = "logistics_fleet"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, unique=True, nullable=False)
    driver_name = Column(String, nullable=False)
    status = Column(String, default="idle")        # idle | en_route | collecting | maintenance
    current_lat = Column(Float, nullable=False)
    current_lng = Column(Float, nullable=False)
    speed = Column(Float, default=0.0)             # km/h
    temperature = Column(Float, default=4.0)       # tank °C
    load_level = Column(Float, default=0.0)        # litre
    capacity = Column(Float, default=5000.0)       # litre
    # Set when status transitions to "collecting", cleared on delivery/idle.
    # Used to compute actual elapsed time t for Bk = t * exp(0.1 * T).
    collection_started_at = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String, nullable=False)    # HIGH_RISK | MEDIUM_RISK | tank_overflow | low_tank
    severity = Column(String, nullable=False)      # critical | high | medium | low
    message = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=True)
    entity_type = Column(String, nullable=True)    # vehicle | tank
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
