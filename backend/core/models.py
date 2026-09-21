from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, JSON, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from typing import Optional, List
from decimal import Decimal
import enum
from .database import Base


class InvestorCategory(str, enum.Enum):
    """Investor risk profile categories."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class OrderType(str, enum.Enum):
    """Order types for trading."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"


class OrderStatus(str, enum.Enum):
    """Order execution status."""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class TransactionType(str, enum.Enum):
    """Types of transactions."""
    DEPOSIT = "deposit"
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    COMMISSION = "commission"


class Currency(str, enum.Enum):
    """Supported currencies."""
    USD = "USD"
    RUB = "RUB"


class User(Base):
    """User model with profile and progress tracking."""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Profile
    investor_category: Mapped[Optional[InvestorCategory]] = mapped_column(Enum(InvestorCategory))
    balance_usd: Mapped[Decimal] = mapped_column(Float, default=0.0)
    balance_rub: Mapped[Decimal] = mapped_column(Float, default=0.0)
    
    # Learning progress
    learning_progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100%
    completed_lessons: Mapped[List] = mapped_column(JSON, default=list)
    quiz_scores: Mapped[dict] = mapped_column(JSON, default=dict)
    practical_tasks: Mapped[List] = mapped_column(JSON, default=list)
    
    # Gamification
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    achievements: Mapped[List] = mapped_column(JSON, default=list)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Settings
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    language: Mapped[str] = mapped_column(String(10), default="ru")
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    portfolios: Mapped[List["Portfolio"]] = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    watchlist: Mapped[List["WatchlistItem"]] = relationship("WatchlistItem", back_populates="user", cascade="all, delete-orphan")
    duel_participations: Mapped[List["DuelParticipant"]] = relationship("DuelParticipant", back_populates="user")


class Portfolio(Base):
    """User's portfolio holdings."""
    __tablename__ = "portfolios"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    shares: Mapped[Decimal] = mapped_column(Float, nullable=False)
    avg_price: Mapped[Decimal] = mapped_column(Float, nullable=False)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="portfolios")
    
    __table_args__ = (
        Index("idx_portfolio_user_ticker", "user_id", "ticker", unique=True),
    )


class Order(Base):
    """Trading orders."""
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    order_type: Mapped[OrderType] = mapped_column(Enum(OrderType), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # buy/sell
    shares: Mapped[Decimal] = mapped_column(Float, nullable=False)
    price: Mapped[Optional[Decimal]] = mapped_column(Float)  # None for market orders
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING)
    filled_price: Mapped[Optional[Decimal]] = mapped_column(Float)
    commission: Mapped[Decimal] = mapped_column(Float, default=0.0)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    filled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")


class Transaction(Base):
    """Transaction history."""
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    ticker: Mapped[Optional[str]] = mapped_column(String(20))
    shares: Mapped[Optional[Decimal]] = mapped_column(Float)
    price: Mapped[Optional[Decimal]] = mapped_column(Float)
    amount: Mapped[Decimal] = mapped_column(Float, nullable=False)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="transactions")


class WatchlistItem(Base):
    """User's watchlist."""
    __tablename__ = "watchlist"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="watchlist")
    
    __table_args__ = (
        Index("idx_watchlist_user_ticker", "user_id", "ticker", unique=True),
    )


class Duel(Base):
    """Portfolio duels between users."""
    __tablename__ = "duels"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    start_balance: Mapped[Decimal] = mapped_column(Float, nullable=False)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    participants: Mapped[List["DuelParticipant"]] = relationship("DuelParticipant", back_populates="duel", cascade="all, delete-orphan")


class DuelParticipant(Base):
    """Participants in duels."""
    __tablename__ = "duel_participants"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    duel_id: Mapped[int] = mapped_column(Integer, ForeignKey("duels.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    starting_balance: Mapped[Decimal] = mapped_column(Float, nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(Float, nullable=False)
    return_pct: Mapped[Decimal] = mapped_column(Float, default=0.0)
    
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    duel: Mapped["Duel"] = relationship("Duel", back_populates="participants")
    user: Mapped["User"] = relationship("User", back_populates="duel_participations")
    
    __table_args__ = (
        Index("idx_duel_user", "duel_id", "user_id", unique=True),
    )


class LearningModule(Base):
    """Learning curriculum modules."""
    __tablename__ = "learning_modules"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[Optional[InvestorCategory]] = mapped_column(Enum(InvestorCategory))  # None = all categories
    
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    quiz: Mapped[Optional[dict]] = mapped_column(JSON)
    practical_task: Mapped[Optional[dict]] = mapped_column(JSON)
    
    xp_reward: Mapped[int] = mapped_column(Integer, default=100)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
