from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import List, Optional

from database import get_db
from models import Alert as AlertModel
from schemas import Alert, AlertCreate

router = APIRouter()


@router.get("/", response_model=List[Alert])
async def list_alerts(
    resolved: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(AlertModel).order_by(AlertModel.created_at.desc())
    if resolved is not None:
        query = query.where(AlertModel.resolved == resolved)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=Alert, status_code=201)
async def create_alert(data: AlertCreate, db: AsyncSession = Depends(get_db)):
    alert = AlertModel(**data.model_dump())
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.patch("/{alert_id}/resolve", response_model=Alert)
async def resolve_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertModel).where(AlertModel.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.resolved = True
    alert.resolved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertModel).where(AlertModel.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.delete(alert)
    await db.commit()
