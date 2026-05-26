"""
Avatar API - Digital human configuration management
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AvatarConfig
from app.schemas import AvatarCreate, AvatarResponse, AvatarUpdate, MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/avatar", tags=["Avatar"])


@router.get("", response_model=list[AvatarResponse])
async def list_avatars(db: AsyncSession = Depends(get_db)):
    """List all avatar configurations"""
    result = await db.execute(
        select(AvatarConfig).order_by(AvatarConfig.created_at.desc())
    )
    return result.scalars().all()


@router.get("/active", response_model=AvatarResponse)
async def get_active_avatar(db: AsyncSession = Depends(get_db)):
    """Get currently active avatar configuration"""
    result = await db.execute(
        select(AvatarConfig).where(AvatarConfig.is_active == True)
    )
    avatar = result.scalar_one_or_none()
    if not avatar:
        raise HTTPException(404, "No active avatar configured")
    return avatar


@router.post("", response_model=AvatarResponse)
async def create_avatar(data: AvatarCreate, db: AsyncSession = Depends(get_db)):
    """Create a new avatar configuration"""
    avatar = AvatarConfig(**data.model_dump())
    db.add(avatar)
    await db.commit()
    await db.refresh(avatar)
    return avatar


@router.put("/{avatar_id}", response_model=AvatarResponse)
async def update_avatar(
    avatar_id: int,
    data: AvatarUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update avatar configuration"""
    avatar = await db.get(AvatarConfig, avatar_id)
    if not avatar:
        raise HTTPException(404, "Avatar not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(avatar, key, value)

    await db.commit()
    await db.refresh(avatar)
    return avatar


@router.post("/{avatar_id}/activate", response_model=MessageResponse)
async def activate_avatar(avatar_id: int, db: AsyncSession = Depends(get_db)):
    """Set an avatar as the active one"""
    # Deactivate all
    result = await db.execute(
        select(AvatarConfig).where(AvatarConfig.is_active == True)
    )
    for active in result.scalars().all():
        active.is_active = False

    # Activate target
    avatar = await db.get(AvatarConfig, avatar_id)
    if not avatar:
        raise HTTPException(404, "Avatar not found")
    avatar.is_active = True

    await db.commit()
    return MessageResponse(message=f"Avatar '{avatar.name}' activated")


@router.delete("/{avatar_id}", response_model=MessageResponse)
async def delete_avatar(avatar_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an avatar configuration"""
    avatar = await db.get(AvatarConfig, avatar_id)
    if not avatar:
        raise HTTPException(404, "Avatar not found")
    if avatar.is_active:
        raise HTTPException(400, "Cannot delete active avatar")

    await db.delete(avatar)
    await db.commit()
    return MessageResponse(message="Avatar deleted")
