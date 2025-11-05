from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.models.mission import Mission, UserMission
from app.models.user import User
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

router = APIRouter()


class MissionResponse(BaseModel):
    id: int
    title: str
    description: str | None
    icon: str | None = "🎯"
    reward_amount: Decimal
    reward_currency: str
    type: str
    requirements: dict
    progress: int = 0
    completed: bool = False
    claimed: bool = False

    class Config:
        from_attributes = True


@router.get("/{user_id}", response_model=list[MissionResponse])
async def get_missions(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get available missions for user"""
    # Get active missions
    result = await db.execute(
        select(Mission).where(Mission.is_active == True)
    )
    missions = result.scalars().all()

    # Get user progress
    result = await db.execute(
        select(UserMission).where(UserMission.user_id == user_id)
    )
    user_missions = {um.mission_id: um for um in result.scalars().all()}

    # Combine data
    response = []
    for mission in missions:
        user_mission = user_missions.get(mission.id)
        response.append(MissionResponse(
            id=mission.id,
            title=mission.title,
            description=mission.description,
            icon=mission.icon or "🎯",
            reward_amount=mission.reward_amount,
            reward_currency=mission.reward_currency,
            type=mission.type,
            requirements=mission.requirements,
            progress=user_mission.progress if user_mission else 0,
            completed=user_mission.completed if user_mission else False,
            claimed=user_mission.claimed if user_mission else False
        ))

    return response


@router.post("/claim/{user_id}/{mission_id}")
async def claim_mission_reward(
    user_id: int,
    mission_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Claim mission reward"""
    # Get user mission
    result = await db.execute(
        select(UserMission).where(
            and_(
                UserMission.user_id == user_id,
                UserMission.mission_id == mission_id
            )
        )
    )
    user_mission = result.scalar_one_or_none()

    if not user_mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    if not user_mission.completed:
        raise HTTPException(status_code=400, detail="Mission not completed")

    if user_mission.claimed:
        raise HTTPException(status_code=400, detail="Reward already claimed")

    # Get mission
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    # Give reward
    if mission.reward_currency == "PRED":
        user.pred_balance += mission.reward_amount
    else:
        user.ton_balance += mission.reward_amount

    # Mark as claimed
    user_mission.claimed = True
    user_mission.claimed_at = datetime.utcnow()

    await db.commit()

    return {
        "success": True,
        "reward": {
            "amount": mission.reward_amount,
            "currency": mission.reward_currency
        }
    }
