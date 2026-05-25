from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import List

from database import get_db
from models import StorageTank as TankModel, CollectionPoint as CPModel, Alert as AlertModel
from schemas import (
    StorageTank,
    StorageTankCreate,
    StorageTankUpdate,
    CollectionPoint,
    CollectionPointCreate,
)
from utils import check_tank_level_alert, check_cold_chain_alert

router = APIRouter()


@router.get("/collection-points/", response_model=List[CollectionPoint])
async def list_collection_points(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CPModel))
    return result.scalars().all()


@router.post("/collection-points/", response_model=CollectionPoint, status_code=201)
async def create_collection_point(
    data: CollectionPointCreate, db: AsyncSession = Depends(get_db)
):
    cp = CPModel(**data.model_dump())
    db.add(cp)
    await db.commit()
    await db.refresh(cp)
    return cp


@router.get("/", response_model=List[StorageTank])
async def list_tanks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TankModel))
    return result.scalars().all()


@router.get("/{tank_id}", response_model=StorageTank)
async def get_tank(tank_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TankModel).where(TankModel.id == tank_id))
    tank = result.scalar_one_or_none()
    if not tank:
        raise HTTPException(status_code=404, detail="Tank not found")
    return tank


@router.post("/", response_model=StorageTank, status_code=201)
async def create_tank(data: StorageTankCreate, db: AsyncSession = Depends(get_db)):
    tank = TankModel(**data.model_dump())
    db.add(tank)
    await db.commit()
    await db.refresh(tank)
    return tank


@router.patch("/{tank_id}/level", response_model=StorageTank)
async def update_tank_level(
    tank_id: int,
    data: StorageTankUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TankModel).where(TankModel.id == tank_id))
    tank = result.scalar_one_or_none()
    if not tank:
        raise HTTPException(status_code=404, detail="Tank not found")

    if data.current_level is not None:
        tank.current_level = data.current_level
    if data.temperature is not None:
        tank.temperature = data.temperature
    tank.last_updated = datetime.utcnow()

    level_alert = check_tank_level_alert(tank.id, tank.current_level, tank.capacity)
    if level_alert:
        db.add(AlertModel(**level_alert))

    cold_alert = check_cold_chain_alert(tank.id, "tank", tank.temperature)
    if cold_alert:
        db.add(AlertModel(**cold_alert))

    await db.commit()
    await db.refresh(tank)

    ws_manager = request.app.state.ws_manager
    await ws_manager.broadcast({
        "type": "tank_update",
        "data": {
            "id": tank.id,
            "name": tank.name,
            "current_level": tank.current_level,
            "capacity": tank.capacity,
            "temperature": tank.temperature,
            "last_updated": tank.last_updated.isoformat(),
        },
    })

    return tank
