"""
Trajectory API - Travel trajectory recording and commemorative card
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import TravelTrajectory
from app.schemas import (
    TrajectoryCreate, TrajectoryResponse,
    CommemorativeCardResponse,
)
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/trajectory", tags=["Trajectory"])


@router.post("/record", response_model=TrajectoryResponse)
async def record_trajectory(data: TrajectoryCreate, db: AsyncSession = Depends(get_db)):
    """Record a visitor's spot visit"""
    entry = TravelTrajectory(
        session_id=data.session_id,
        spot_name=data.spot_name,
        spot_description=data.spot_description,
        longitude=data.longitude,
        latitude=data.latitude,
        visit_order=data.visit_order,
        photo_url=data.photo_url,
        note=data.note,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.get("/list/{session_id}", response_model=list[TrajectoryResponse])
async def get_trajectory(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get a visitor's full travel trajectory"""
    result = await db.execute(
        select(TravelTrajectory)
        .where(TravelTrajectory.session_id == session_id)
        .order_by(TravelTrajectory.visit_order, TravelTrajectory.visited_at)
    )
    return result.scalars().all()


@router.get("/card/{session_id}", response_model=CommemorativeCardResponse)
async def generate_commemorative_card(session_id: str, db: AsyncSession = Depends(get_db)):
    """Generate a commemorative card for the visitor's journey"""
    result = await db.execute(
        select(TravelTrajectory)
        .where(TravelTrajectory.session_id == session_id)
        .order_by(TravelTrajectory.visit_order, TravelTrajectory.visited_at)
    )
    spots = result.scalars().all()

    if not spots:
        raise HTTPException(status_code=404, detail="该游客暂无游览记录")

    spot_names = [s.spot_name for s in spots]
    commemorative_text = await llm_service.generate_commemorative_text(spot_names)

    cover_text = f"畅游{len(spots)}景 · {spot_names[0] if spot_names else ''}之旅"

    return CommemorativeCardResponse(
        session_id=session_id,
        spots_count=len(spots),
        spots=[
            {
                "name": s.spot_name,
                "description": s.spot_description,
                "note": s.note,
                "visited_at": s.visited_at.isoformat() if s.visited_at else None,
            }
            for s in spots
        ],
        summary=commemorative_text,
        cover_text=cover_text,
    )


@router.delete("/clear/{session_id}")
async def clear_trajectory(session_id: str, db: AsyncSession = Depends(get_db)):
    """Clear a visitor's trajectory"""
    result = await db.execute(
        select(TravelTrajectory)
        .where(TravelTrajectory.session_id == session_id)
    )
    entries = result.scalars().all()
    for entry in entries:
        await db.delete(entry)
    await db.commit()
    return {"message": f"已清除 {len(entries)} 条游览记录", "success": True}
