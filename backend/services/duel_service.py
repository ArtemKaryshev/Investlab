from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.models import User, Duel, DuelParticipant, Currency
from .trading_service import trading_service


class DuelService:
    """Service for managing portfolio duels and leaderboards."""
    
    async def create_duel(
        self,
        db: AsyncSession,
        name: str,
        duration_days: int,
        start_balance: float,
        currency: Currency
    ) -> Duel:
        """Create a new portfolio duel."""
        
        duel = Duel(
            name=name,
            duration_days=duration_days,
            start_balance=start_balance,
            currency=currency,
            started_at=datetime.now(timezone.utc),
            ends_at=datetime.now(timezone.utc) + timedelta(days=duration_days),
            is_active=True,
        )
        
        db.add(duel)
        await db.commit()
        await db.refresh(duel)
        
        return duel
    
    async def join_duel(
        self,
        db: AsyncSession,
        user: User,
        duel_id: int
    ) -> Dict[str, Any]:
        """Join an active duel."""
        
        # Get duel
        result = await db.execute(
            select(Duel).where(Duel.id == duel_id)
        )
        duel = result.scalar_one_or_none()
        
        if not duel:
            return {"success": False, "error": "Дуэль не найдена"}
        
        if not duel.is_active:
            return {"success": False, "error": "Дуэль завершена"}
        
        # Check if already participating
        existing = await db.execute(
            select(DuelParticipant).where(
                DuelParticipant.duel_id == duel_id,
                DuelParticipant.user_id == user.id
            )
        )
        if existing.scalar_one_or_none():
            return {"success": False, "error": "Вы уже участвуете в этой дуэли"}
        
        # Create participant
        participant = DuelParticipant(
            duel_id=duel_id,
            user_id=user.id,
            starting_balance=duel.start_balance,
            current_balance=duel.start_balance,
            return_pct=0.0,
        )
        
        db.add(participant)
        await db.commit()
        
        return {
            "success": True,
            "duel_id": duel_id,
            "starts_at": duel.started_at.isoformat(),
            "ends_at": duel.ends_at.isoformat(),
        }
    
    async def get_active_duels(
        self,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get list of active duels."""
        
        now = datetime.now(timezone.utc)
        
        result = await db.execute(
            select(Duel).where(
                Duel.is_active == True,
                Duel.ends_at > now
            ).order_by(Duel.started_at.desc())
        )
        duels = result.scalars().all()
        
        duel_list = []
        for duel in duels:
            # Count participants
            participant_count = await db.execute(
                select(func.count(DuelParticipant.id)).where(
                    DuelParticipant.duel_id == duel.id
                )
            )
            count = participant_count.scalar()
            
            duel_list.append({
                "id": duel.id,
                "name": duel.name,
                "duration_days": duel.duration_days,
                "start_balance": float(duel.start_balance),
                "currency": duel.currency.value,
                "participants": count,
                "started_at": duel.started_at.isoformat(),
                "ends_at": duel.ends_at.isoformat(),
                "time_left_hours": int((duel.ends_at - now).total_seconds() / 3600),
            })
        
        return duel_list
    
    async def get_duel_leaderboard(
        self,
        db: AsyncSession,
        duel_id: int
    ) -> List[Dict[str, Any]]:
        """Get leaderboard for a specific duel."""
        
        result = await db.execute(
            select(DuelParticipant, User).join(User).where(
                DuelParticipant.duel_id == duel_id
            ).order_by(DuelParticipant.return_pct.desc())
        )
        
        rows = result.all()
        
        leaderboard = []
        for rank, (participant, user) in enumerate(rows, 1):
            leaderboard.append({
                "rank": rank,
                "user_id": user.id,
                "username": user.username or user.first_name or f"Пользователь {user.id}",
                "return_pct": float(participant.return_pct),
                "current_balance": float(participant.current_balance),
                "profit": float(participant.current_balance - participant.starting_balance),
            })
        
        return leaderboard
    
    async def get_global_leaderboard(
        self,
        db: AsyncSession,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get global leaderboard by total portfolio value."""
        
        result = await db.execute(
            select(User).order_by(
                (User.balance_usd + User.balance_rub).desc()
            ).limit(limit)
        )
        users = result.scalars().all()
        
        leaderboard = []
        for rank, user in enumerate(users, 1):
            # Calculate total portfolio value
            portfolio_value = await trading_service.get_portfolio_value(db, user)
            
            leaderboard.append({
                "rank": rank,
                "user_id": user.id,
                "username": user.username or user.first_name or f"Пользователь {user.id}",
                "level": user.level,
                "xp": user.xp,
                "total_value_rub": portfolio_value["total_value_rub"],
                "total_value_usd": portfolio_value["total_value_usd"],
                "learning_progress": user.learning_progress,
            })
        
        return leaderboard
    
    async def update_duel_participants(
        self,
        db: AsyncSession,
        duel_id: int
    ):
        """Update all participants' current balances for a duel."""
        
        result = await db.execute(
            select(DuelParticipant, User).join(User).where(
                DuelParticipant.duel_id == duel_id
            )
        )
        
        rows = result.all()
        
        for participant, user in rows:
            # Calculate current portfolio value
            portfolio_value = await trading_service.get_portfolio_value(db, user)
            
            # Get duel currency
            duel_result = await db.execute(
                select(Duel).where(Duel.id == duel_id)
            )
            duel = duel_result.scalar_one()
            
            if duel.currency == Currency.USD:
                current_value = portfolio_value["total_value_usd"]
            else:
                current_value = portfolio_value["total_value_rub"]
            
            participant.current_balance = current_value
            participant.return_pct = (
                ((current_value - participant.starting_balance) / participant.starting_balance) * 100
                if participant.starting_balance > 0 else 0
            )
        
        await db.commit()


# Global duel service instance
duel_service = DuelService()
