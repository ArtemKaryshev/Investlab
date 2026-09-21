from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.models import (
    User, Portfolio, Order, Transaction, 
    OrderType, OrderStatus, TransactionType, Currency
)
from .moex_service import moex_service


class TradingService:
    """Service for handling trading operations."""
    
    # Commission rates (in %)
    COMMISSION_RATE = 0.0005  # 0.05% per trade
    MIN_COMMISSION_RUB = 0.04
    MIN_COMMISSION_USD = 0.01
    
    async def execute_market_order(
        self,
        db: AsyncSession,
        user: User,
        ticker: str,
        side: str,  # 'buy' or 'sell'
        shares: float,
        currency: Currency
    ) -> Dict[str, Any]:
        """
        Execute a market order immediately at current price.
        Returns execution result with filled price and commission.
        """
        # Get current market price
        price_data = await moex_service.get_stock_price(ticker)
        if not price_data:
            return {
                "success": False,
                "error": f"Не удалось получить котировку {ticker}",
            }
        
        current_price = Decimal(str(price_data["price"]))
        
        # Validate order
        validation = await self._validate_order(
            user, ticker, side, shares, current_price, currency
        )
        if not validation["valid"]:
            return {
                "success": False,
                "error": validation["error"],
            }
        
        # Calculate commission
        total_value = current_price * Decimal(str(shares))
        commission = self._calculate_commission(total_value, currency)
        
        # Execute based on side
        if side == "buy":
            result = await self._execute_buy(
                db, user, ticker, shares, current_price, commission, currency
            )
        else:
            result = await self._execute_sell(
                db, user, ticker, shares, current_price, commission, currency
            )
        
        if result["success"]:
            # Create order record
            order = Order(
                user_id=user.id,
                ticker=ticker,
                order_type=OrderType.MARKET,
                side=side,
                shares=Decimal(str(shares)),
                price=None,  # Market order has no limit price
                currency=currency,
                status=OrderStatus.FILLED,
                filled_price=current_price,
                commission=commission,
                filled_at=datetime.now(timezone.utc),
            )
            db.add(order)
            
            # Create transaction record
            transaction = Transaction(
                user_id=user.id,
                transaction_type=TransactionType.BUY if side == "buy" else TransactionType.SELL,
                ticker=ticker,
                shares=Decimal(str(shares)),
                price=current_price,
                amount=total_value + (commission if side == "buy" else -commission),
                currency=currency,
                description=f"{'Покупка' if side == 'buy' else 'Продажа'} {shares} акций {ticker} по {current_price}",
            )
            db.add(transaction)
            
            # Commission transaction
            commission_tx = Transaction(
                user_id=user.id,
                transaction_type=TransactionType.COMMISSION,
                ticker=ticker,
                amount=-commission,
                currency=currency,
                description=f"Комиссия за {'покупку' if side == 'buy' else 'продажу'} {ticker}",
            )
            db.add(commission_tx)
            
            await db.commit()
            
            return {
                "success": True,
                "order_id": order.id,
                "filled_price": float(current_price),
                "commission": float(commission),
                "total": float(total_value + commission if side == "buy" else total_value - commission),
            }
        
        return result
    
    async def _validate_order(
        self,
        user: User,
        ticker: str,
        side: str,
        shares: float,
        price: Decimal,
        currency: Currency,
    ) -> Dict[str, Any]:
        """Validate order parameters."""
        
        # Check shares
        if shares <= 0:
            return {"valid": False, "error": "Количество акций должно быть больше нуля"}
        
        # Check fractional shares (allow only whole shares)
        if shares != int(shares):
            return {"valid": False, "error": "Дробные акции не поддерживаются"}
        
        total_value = price * Decimal(str(shares))
        commission = self._calculate_commission(total_value, currency)
        
        if side == "buy":
            # Check if user has enough balance
            balance = user.balance_usd if currency == Currency.USD else user.balance_rub
            required = total_value + commission
            
            if balance < required:
                return {
                    "valid": False,
                    "error": f"Недостаточно средств. Требуется: {required:.2f} {currency.value}, доступно: {balance:.2f}",
                }
        
        return {"valid": True}
    
    def _calculate_commission(self, amount: Decimal, currency: Currency) -> Decimal:
        """Calculate trading commission."""
        commission = amount * Decimal(str(self.COMMISSION_RATE))
        min_commission = Decimal(str(
            self.MIN_COMMISSION_USD if currency == Currency.USD else self.MIN_COMMISSION_RUB
        ))
        return max(commission, min_commission)
    
    async def _execute_buy(
        self,
        db: AsyncSession,
        user: User,
        ticker: str,
        shares: float,
        price: Decimal,
        commission: Decimal,
        currency: Currency,
    ) -> Dict[str, Any]:
        """Execute buy order."""
        
        total_cost = price * Decimal(str(shares)) + commission
        
        # Deduct from balance
        if currency == Currency.USD:
            user.balance_usd -= total_cost
        else:
            user.balance_rub -= total_cost
        
        # Update or create portfolio position
        stmt = select(Portfolio).where(
            Portfolio.user_id == user.id,
            Portfolio.ticker == ticker,
        )
        result = await db.execute(stmt)
        position = result.scalar_one_or_none()
        
        if position:
            # Update existing position (weighted average price)
            total_shares = position.shares + Decimal(str(shares))
            total_value = (position.shares * position.avg_price) + (Decimal(str(shares)) * price)
            position.avg_price = total_value / total_shares
            position.shares = total_shares
        else:
            # Create new position
            position = Portfolio(
                user_id=user.id,
                ticker=ticker,
                shares=Decimal(str(shares)),
                avg_price=price,
                currency=currency,
            )
            db.add(position)
        
        return {"success": True}
    
    async def _execute_sell(
        self,
        db: AsyncSession,
        user: User,
        ticker: str,
        shares: float,
        price: Decimal,
        commission: Decimal,
        currency: Currency,
    ) -> Dict[str, Any]:
        """Execute sell order."""
        
        # Check if user has enough shares
        stmt = select(Portfolio).where(
            Portfolio.user_id == user.id,
            Portfolio.ticker == ticker,
        )
        result = await db.execute(stmt)
        position = result.scalar_one_or_none()
        
        if not position:
            return {
                "success": False,
                "error": f"У вас нет акций {ticker}",
            }
        
        if position.shares < Decimal(str(shares)):
            return {
                "success": False,
                "error": f"Недостаточно акций. Доступно: {position.shares}, требуется: {shares}",
            }
        
        # Calculate proceeds
        proceeds = price * Decimal(str(shares)) - commission
        
        # Add to balance
        if currency == Currency.USD:
            user.balance_usd += proceeds
        else:
            user.balance_rub += proceeds
        
        # Update position
        position.shares -= Decimal(str(shares))
        
        # Remove position if all shares sold
        if position.shares == 0:
            await db.delete(position)
        
        return {"success": True}
    
    async def get_portfolio_value(
        self,
        db: AsyncSession,
        user: User,
    ) -> Dict[str, Any]:
        """Calculate total portfolio value."""
        
        stmt = select(Portfolio).where(Portfolio.user_id == user.id)
        result = await db.execute(stmt)
        positions = result.scalars().all()
        
        if not positions:
            return {
                "total_value_usd": float(user.balance_usd),
                "total_value_rub": float(user.balance_rub),
                "positions_value_usd": 0.0,
                "positions_value_rub": 0.0,
                "cash_usd": float(user.balance_usd),
                "cash_rub": float(user.balance_rub),
            }
        
        # Get current prices for all tickers
        tickers = [pos.ticker for pos in positions]
        prices = await moex_service.get_multiple_prices(tickers)
        
        positions_value_rub = Decimal("0")
        positions_value_usd = Decimal("0")
        
        for position in positions:
            price_data = prices.get(position.ticker)
            if price_data:
                current_price = Decimal(str(price_data["price"]))
                position_value = position.shares * current_price
                
                if position.currency == Currency.RUB:
                    positions_value_rub += position_value
                else:
                    positions_value_usd += position_value
        
        return {
            "total_value_usd": float(user.balance_usd + positions_value_usd),
            "total_value_rub": float(user.balance_rub + positions_value_rub),
            "positions_value_usd": float(positions_value_usd),
            "positions_value_rub": float(positions_value_rub),
            "cash_usd": float(user.balance_usd),
            "cash_rub": float(user.balance_rub),
        }


# Global trading service instance
trading_service = TradingService()
