from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ── Storage Tank ─────────────────────────────────────────────────────────────

class StorageTankBase(BaseModel):
    name: str
    lat: float
    lng: float
    capacity: float = Field(..., gt=0, description="Litre cinsinden kapasite")
    current_level: float = Field(default=0.0, ge=0)
    temperature: float = Field(default=4.0, description="°C")


class StorageTankCreate(StorageTankBase):
    collection_point_id: Optional[int] = None


class StorageTankUpdate(BaseModel):
    current_level: Optional[float] = Field(default=None, ge=0)
    temperature: Optional[float] = None


class StorageTank(StorageTankBase):
    id: int
    last_updated: datetime
    collection_point_id: Optional[int] = None

    model_config = {"from_attributes": True}


# ── Logistics Fleet ───────────────────────────────────────────────────────────

class LogisticsFleetBase(BaseModel):
    vehicle_id: str
    driver_name: str
    status: str = "idle"
    current_lat: float
    current_lng: float
    speed: float = Field(default=0.0, ge=0)
    temperature: float = Field(default=4.0, description="Tank sıcaklığı °C")
    load_level: float = Field(default=0.0, ge=0)
    capacity: float = Field(default=5000.0, gt=0)


class LogisticsFleetCreate(LogisticsFleetBase):
    collection_started_at: Optional[datetime] = None


class LogisticsFleetUpdate(BaseModel):
    status: Optional[str] = None
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    speed: Optional[float] = Field(default=None, ge=0)
    temperature: Optional[float] = None
    load_level: Optional[float] = Field(default=None, ge=0)
    collection_started_at: Optional[datetime] = None


class LogisticsFleet(LogisticsFleetBase):
    id: int
    collection_started_at: Optional[datetime] = None
    last_updated: datetime

    model_config = {"from_attributes": True}


# ── Collection Point ──────────────────────────────────────────────────────────

class CollectionPointBase(BaseModel):
    name: str
    lat: float
    lng: float
    address: Optional[str] = None
    status: str = "active"


class CollectionPointCreate(CollectionPointBase):
    pass


class CollectionPoint(CollectionPointBase):
    id: int

    model_config = {"from_attributes": True}


# ── Alert ─────────────────────────────────────────────────────────────────────

class AlertBase(BaseModel):
    alert_type: str
    severity: str
    message: str
    entity_id: Optional[int] = None
    entity_type: Optional[str] = None


class AlertCreate(AlertBase):
    pass


class Alert(AlertBase):
    id: int
    resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
