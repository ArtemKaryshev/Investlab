from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from pydantic import BaseModel
import hmac
import hashlib
import json
from urllib.parse import parse_qs
from datetime import datetime, timezone

from ..core.config import settings
from ..core.database import get_db, init_db
from ..core.models import User, Portfolio, Order, Transaction, WatchlistItem
from ..core.redis_client import redis_client
from ..services.moex_service import moex_service
from ..services.trading_service import trading_service
from ..services.learning_service import learning_service
from ..services.duel_service import duel_service


app = FastAPI(title="InvestLab API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API
class TelegramInitData(BaseModel):
    """Telegram WebApp init data."""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TradeRequest(BaseModel):
    """Trade execution request."""
    ticker: str
    side: str  # buy/sell
    shares: float
    currency: str  # USD/RUB


class WatchlistRequest(BaseModel):
    """Watchlist add/remove request."""
    ticker: str


class QuizSubmission(BaseModel):
    """Quiz answer submission."""
    module_id: int
    answers: List[int]


# Authentication
def verify_telegram_webapp_data(init_data: str) -> Optional[dict]:
    """
    Verify Telegram WebApp initData signature.
    Returns parsed user data if valid, None otherwise.
    """
    try:
        parsed = parse_qs(init_data)
        
        # Extract hash
        data_check_string_parts = []
        for key in sorted(parsed.keys()):
            if key == "hash":
                continue
            value = parsed[key][0] if isinstance(parsed[key], list) else parsed[key]
            data_check_string_parts.append(f"{key}={value}")
        
        data_check_string = "\n".join(data_check_string_parts)
        
        # Calculate hash
        secret_key = hmac.new(
            "WebAppData".encode(),
            settings.bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        received_hash = parsed.get("hash", [None])[0]
        
        if calculated_hash != received_hash:
            return None
        
        # Parse user data
        user_json = parsed.get("user", [None])[0]
        if user_json:
            return json.loads(user_json)
        
        return None
        
    except Exception as e:
        print(f"Auth error: {e}")
        return None


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user.
    Expects Authorization header with Telegram initData.
    """
    if not authorization.startswith("tma "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    init_data = authorization[4:]  # Remove "tma " prefix
    user_data = verify_telegram_webapp_data(init_data)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    # Get or create user
    result = await db.execute(
        select(User).where(User.telegram_id == user_data["id"])
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    await init_db()
    await redis_client.connect()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await redis_client.disconnect()
    await moex_service.close()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "InvestLab API"}


@app.get("/api/user/profile")
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile and portfolio summary."""
    portfolio_value = await trading_service.get_portfolio_value(db, user)
    
    return {
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "investor_category": user.investor_category.value if user.investor_category else None,
            "level": user.level,
            "xp": user.xp,
            "learning_progress": user.learning_progress,
            "streak_days": user.streak_days,
        },
        "portfolio": portfolio_value,
        "balances": {
            "usd": float(user.balance_usd),
            "rub": float(user.balance_rub),
        }
    }


@app.get("/api/portfolio/positions")
async def get_positions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's portfolio positions with current prices."""
    result = await db.execute(
        select(Portfolio).where(Portfolio.user_id == user.id)
    )
    positions = result.scalars().all()
    
    if not positions:
        return {"positions": []}
    
    # Get current prices
    tickers = [p.ticker for p in positions]
    prices = await moex_service.get_multiple_prices(tickers)
    
    positions_data = []
    for pos in positions:
        price_data = prices.get(pos.ticker, {})
        current_price = float(price_data.get("price", 0))
        
        position_value = float(pos.shares) * current_price
        profit = (current_price - float(pos.avg_price)) * float(pos.shares)
        profit_pct = ((current_price - float(pos.avg_price)) / float(pos.avg_price)) * 100 if pos.avg_price > 0 else 0
        
        positions_data.append({
            "ticker": pos.ticker,
            "name": price_data.get("name", pos.ticker),
            "shares": float(pos.shares),
            "avg_price": float(pos.avg_price),
            "current_price": current_price,
            "position_value": position_value,
            "profit": profit,
            "profit_pct": profit_pct,
            "currency": pos.currency.value,
            "change_pct": price_data.get("change_pct", 0),
        })
    
    return {"positions": positions_data}


@app.get("/api/market/stocks")
async def get_stocks(limit: int = 50):
    """Get popular stocks list."""
    stocks = await moex_service.get_popular_stocks(limit=limit)
    return {"stocks": stocks}


@app.get("/api/market/stock/{ticker}")
async def get_stock_detail(ticker: str):
    """Get detailed stock information."""
    price_data = await moex_service.get_stock_price(ticker)
    
    if not price_data:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    return {"stock": price_data}


@app.get("/api/market/stock/{ticker}/history")
async def get_stock_history(ticker: str, days: int = 365):
    """Get stock historical data."""
    history = await moex_service.get_stock_history(ticker, days=days)
    
    if not history:
        raise HTTPException(status_code=404, detail="No history data available")
    
    return {"ticker": ticker, "history": history}


@app.post("/api/trade/execute")
async def execute_trade(
    trade: TradeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute a market order."""
    from ..core.models import Currency
    
    currency = Currency.USD if trade.currency.upper() == "USD" else Currency.RUB
    
    result = await trading_service.execute_market_order(
        db=db,
        user=user,
        ticker=trade.ticker.upper(),
        side=trade.side.lower(),
        shares=trade.shares,
        currency=currency
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@app.get("/api/trading/orders")
async def get_orders(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50
):
    """Get user's order history."""
    result = await db.execute(
        select(Order)
        .where(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .limit(limit)
    )
    orders = result.scalars().all()
    
    orders_data = [
        {
            "id": order.id,
            "ticker": order.ticker,
            "order_type": order.order_type.value,
            "side": order.side,
            "shares": float(order.shares),
            "price": float(order.price) if order.price else None,
            "filled_price": float(order.filled_price) if order.filled_price else None,
            "commission": float(order.commission),
            "status": order.status.value,
            "currency": order.currency.value,
            "created_at": order.created_at.isoformat(),
            "filled_at": order.filled_at.isoformat() if order.filled_at else None,
        }
        for order in orders
    ]
    
    return {"orders": orders_data}


@app.get("/api/trading/transactions")
async def get_transactions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50
):
    """Get user's transaction history."""
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )
    transactions = result.scalars().all()
    
    transactions_data = [
        {
            "id": tx.id,
            "type": tx.transaction_type.value,
            "ticker": tx.ticker,
            "shares": float(tx.shares) if tx.shares else None,
            "price": float(tx.price) if tx.price else None,
            "amount": float(tx.amount),
            "currency": tx.currency.value,
            "description": tx.description,
            "created_at": tx.created_at.isoformat(),
        }
        for tx in transactions
    ]
    
    return {"transactions": transactions_data}


@app.get("/api/watchlist")
async def get_watchlist(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's watchlist with current prices."""
    result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.user_id == user.id)
    )
    watchlist = result.scalars().all()
    
    if not watchlist:
        return {"watchlist": []}
    
    # Get current prices
    tickers = [item.ticker for item in watchlist]
    prices = await moex_service.get_multiple_prices(tickers)
    
    watchlist_data = [
        {
            "ticker": item.ticker,
            "added_at": item.added_at.isoformat(),
            **prices.get(item.ticker, {})
        }
        for item in watchlist
    ]
    
    return {"watchlist": watchlist_data}


@app.post("/api/watchlist/add")
async def add_to_watchlist(
    request: WatchlistRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add stock to watchlist."""
    # Check if already in watchlist
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user.id,
            WatchlistItem.ticker == request.ticker.upper()
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already in watchlist")
    
    # Add to watchlist
    item = WatchlistItem(
        user_id=user.id,
        ticker=request.ticker.upper()
    )
    db.add(item)
    await db.commit()
    
    return {"success": True}


@app.delete("/api/watchlist/remove/{ticker}")
async def remove_from_watchlist(
    ticker: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove stock from watchlist."""
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user.id,
            WatchlistItem.ticker == ticker.upper()
        )
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Not in watchlist")
    
    await db.delete(item)
    await db.commit()
    
    return {"success": True}


@app.get("/api/learning/modules")
async def get_learning_modules(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get learning modules for user."""
    modules = await learning_service.get_modules_for_user(db, user)
    return {"modules": modules}


@app.post("/api/learning/quiz/submit")
async def submit_quiz(
    submission: QuizSubmission,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit quiz answers."""
    result = await learning_service.submit_quiz(
        db, user, submission.module_id, submission.answers
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@app.get("/api/leaderboard/global")
async def get_global_leaderboard(
    db: AsyncSession = Depends(get_db),
    limit: int = 50
):
    """Get global leaderboard."""
    leaderboard = await duel_service.get_global_leaderboard(db, limit=limit)
    return {"leaderboard": leaderboard}


@app.get("/api/duels/active")
async def get_active_duels(db: AsyncSession = Depends(get_db)):
    """Get list of active duels."""
    duels = await duel_service.get_active_duels(db)
    return {"duels": duels}


@app.get("/api/duels/{duel_id}/leaderboard")
async def get_duel_leaderboard(
    duel_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get leaderboard for a specific duel."""
    leaderboard = await duel_service.get_duel_leaderboard(db, duel_id)
    return {"leaderboard": leaderboard}


@app.post("/api/duels/{duel_id}/join")
async def join_duel(
    duel_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Join a duel."""
    result = await duel_service.join_duel(db, user, duel_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


# Admin endpoints (simplified - should have proper admin auth)
@app.post("/api/admin/duels/create")
async def admin_create_duel(
    name: str,
    duration_days: int,
    start_balance: float,
    currency: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Create a new duel."""
    # Check if user is admin
    if user.telegram_id not in settings.admin_ids:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from ..core.models import Currency as CurrencyEnum
    currency_enum = CurrencyEnum.USD if currency.upper() == "USD" else CurrencyEnum.RUB
    
    duel = await duel_service.create_duel(
        db, name, duration_days, start_balance, currency_enum
    )
    
    return {
        "success": True,
        "duel_id": duel.id,
        "name": duel.name,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
