from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Any, Callable, List, Optional

from database import get_db
from models import LogisticsFleet as FleetModel, Alert as AlertModel
from schemas import LogisticsFleet, LogisticsFleetCreate, LogisticsFleetUpdate
from utils import check_spoilage_alert, check_cold_chain_alert

router = APIRouter()


class TelemetryIn(BaseModel):
    gps_lat: float
    gps_lng: float
    current_temp_c: float
    speed: Optional[float] = None
    load_level: Optional[float] = None
    # When the vehicle reports a status change the endpoint reacts to it:
    # idle/en_route → clears collection_started_at
    # collecting    → sets collection_started_at if not already set
    status: Optional[str] = None


async def evaluate_and_alert(
    vehicle_id: int,
    temperature: float,
    ws_manager: Any,
    collection_started_at: Optional[datetime] = None,
    db_factory: Optional[Callable] = None,
) -> None:
    """
    Background task — evaluates cold-chain and Bk-based spoilage rules,
    persists any alerts, then broadcasts them via WebSocket.

    collection_started_at drives the real t in Bk = t * exp(0.1 * T).
    If absent we fall back to a conservative 0.5 h so the first push after
    collection begins can still surface a MEDIUM_RISK at elevated temps.
    db_factory is injected in tests; defaults to database.AsyncSessionLocal.
    """
    if db_factory is None:
        import database  # lazy import — tests patch database.AsyncSessionLocal
        db_factory = database.AsyncSessionLocal

    # ── Calculate elapsed collection time ────────────────────────────────────
    if collection_started_at is not None:
        t_hours = max(
            0.0,
            (datetime.utcnow() - collection_started_at).total_seconds() / 3600,
        )
    else:
        t_hours = 0.5  # conservative default when tracking not yet started

    pending: list[dict] = []

    # Cold-chain check fires regardless of Bk (immediate boundary breach)
    cold = check_cold_chain_alert(vehicle_id, "vehicle", temperature)
    if cold:
        pending.append(cold)

    # Bk-based spoilage check — only if cold chain is not already violated
    # (avoids duplicate HIGH_RISK for the same temperature event)
    if not cold:
        spoilage = check_spoilage_alert(t_hours, temperature, vehicle_id, "vehicle")
        if spoilage:
            pending.append(spoilage)

    if not pending:
        return

    async with db_factory() as db:
        for alert_data in pending:
            db.add(AlertModel(**alert_data))
        await db.commit()

    for alert_data in pending:
        await ws_manager.broadcast({"type": "alert", "data": alert_data})


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[LogisticsFleet])
async def list_vehicles(db: AsyncSession = Depends(get_db)) -> list[FleetModel]:
    result = await db.execute(select(FleetModel))
    return result.scalars().all()


@router.get("/{vehicle_id}", response_model=LogisticsFleet)
async def get_vehicle(
    vehicle_id: int, db: AsyncSession = Depends(get_db)
) -> FleetModel:
    result = await db.execute(select(FleetModel).where(FleetModel.id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.post("/", response_model=LogisticsFleet, status_code=201)
async def create_vehicle(
    data: LogisticsFleetCreate, db: AsyncSession = Depends(get_db)
) -> FleetModel:
    vehicle = FleetModel(**data.model_dump())
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


# ── Telemetry endpoints ───────────────────────────────────────────────────────

def _build_fleet_event(v: FleetModel) -> dict:
    return {
        "type": "fleet_update",
        "data": {
            "id": v.id,
            "vehicle_id": v.vehicle_id,
            "status": v.status,
            "current_lat": v.current_lat,
            "current_lng": v.current_lng,
            "speed": v.speed,
            "temperature": v.temperature,
            "load_level": v.load_level,
            "capacity": v.capacity,
            "collection_started_at": (
                v.collection_started_at.isoformat() if v.collection_started_at else None
            ),
            "last_updated": v.last_updated.isoformat(),
        },
    }


@router.patch("/{vehicle_id}/telemetry", response_model=LogisticsFleet)
async def update_telemetry(
    vehicle_id: int,
    data: LogisticsFleetUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> FleetModel:
    """Internal PATCH endpoint for dashboard / operator updates."""
    result = await db.execute(select(FleetModel).where(FleetModel.id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    incoming = data.model_dump(exclude_none=True)

    # Auto-manage collection_started_at on status transitions
    if "status" in incoming:
        new_status: str = incoming["status"]
        if new_status == "collecting" and vehicle.status != "collecting":
            vehicle.collection_started_at = datetime.utcnow()
        elif new_status in ("idle", "en_route") and vehicle.status == "collecting":
            vehicle.collection_started_at = None

    for field, value in incoming.items():
        setattr(vehicle, field, value)
    vehicle.last_updated = datetime.utcnow()

    ws_manager = request.app.state.ws_manager

    # Cold-chain check is synchronous and inline (immediate alert requirement)
    if vehicle.temperature is not None:
        cold_alert = check_cold_chain_alert(vehicle.id, "vehicle", vehicle.temperature)
        if cold_alert:
            db.add(AlertModel(**cold_alert))
            await ws_manager.broadcast({"type": "alert", "data": cold_alert})

    await db.commit()
    await db.refresh(vehicle)
    await ws_manager.broadcast(_build_fleet_event(vehicle))
    return vehicle


@router.post("/{vehicle_id}/telemetry", response_model=LogisticsFleet)
async def post_telemetry(
    vehicle_id: int,
    data: TelemetryIn,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> FleetModel:
    """
    Vehicle-push telemetry endpoint.
    GPS + temperature update is persisted immediately; spoilage / alert
    evaluation runs as a background task so the vehicle gets a fast 200.
    """
    result = await db.execute(select(FleetModel).where(FleetModel.id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    vehicle.current_lat = data.gps_lat
    vehicle.current_lng = data.gps_lng
    vehicle.temperature = data.current_temp_c
    if data.speed is not None:
        vehicle.speed = data.speed
    if data.load_level is not None:
        vehicle.load_level = data.load_level

    # Status transition → manage collection_started_at
    if data.status is not None:
        if data.status == "collecting" and vehicle.status != "collecting":
            vehicle.collection_started_at = datetime.utcnow()
        elif data.status in ("idle", "en_route") and vehicle.status == "collecting":
            vehicle.collection_started_at = None
        vehicle.status = data.status

    vehicle.last_updated = datetime.utcnow()
    await db.commit()
    await db.refresh(vehicle)

    ws_manager = request.app.state.ws_manager
    background_tasks.add_task(
        evaluate_and_alert,
        vehicle_id,
        data.current_temp_c,
        ws_manager,
        vehicle.collection_started_at,
    )
    await ws_manager.broadcast(_build_fleet_event(vehicle))
    return vehicle


@router.delete("/{vehicle_id}", status_code=204)
async def delete_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db)) -> None:
    result = await db.execute(select(FleetModel).where(FleetModel.id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    await db.delete(vehicle)
    await db.commit()
