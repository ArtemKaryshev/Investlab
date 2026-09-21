import aiohttp
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from ..core.redis_client import redis_client
from ..core.config import settings


class MOEXService:
    """Service for interacting with Moscow Exchange ISS API."""
    
    def __init__(self):
        self.base_url = settings.moex_api_base
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
    
    async def _fetch_json(self, url: str, params: Optional[Dict] = None) -> Dict:
        """Fetch JSON data from MOEX API."""
        await self._ensure_session()
        
        default_params = {"iss.meta": "off", "iss.json": "extended"}
        if params:
            default_params.update(params)
        
        try:
            async with self.session.get(url, params=default_params, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                return {}
        except Exception as e:
            print(f"MOEX API error: {e}")
            return {}
    
    async def get_popular_stocks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get list of popular Russian stocks.
        Returns top liquid stocks from MOEX.
        """
        cache_key = f"moex:popular_stocks:{limit}"
        cached = await redis_client.get(cache_key)
        if cached:
            return cached
        
        url = f"{self.base_url}/engines/stock/markets/shares/boards/TQBR/securities.json"
        data = await self._fetch_json(url)
        
        stocks = []
        if data and len(data) > 1:
            columns = data[1].get("securities", {}).get("columns", [])
            rows = data[1].get("securities", {}).get("data", [])
            
            for row in rows[:limit]:
                stock_dict = dict(zip(columns, row))
                
                # Filter out empty or invalid entries
                if not stock_dict.get("SECID") or not stock_dict.get("PREVPRICE"):
                    continue
                
                stocks.append({
                    "ticker": stock_dict.get("SECID"),
                    "name": stock_dict.get("SHORTNAME", stock_dict.get("SECID")),
                    "price": float(stock_dict.get("PREVPRICE", 0)),
                    "currency": "RUB",
                    "board": stock_dict.get("BOARDID", "TQBR"),
                })
        
        # Cache for 1 hour
        await redis_client.set(cache_key, stocks, expire=3600)
        return stocks
    
    async def get_stock_price(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get current stock price and details.
        """
        cache_key = f"moex:price:{ticker}"
        cached = await redis_client.get(cache_key)
        if cached:
            return cached
        
        url = f"{self.base_url}/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
        data = await self._fetch_json(url)
        
        if not data or len(data) < 2:
            return None
        
        securities_data = data[1].get("securities", {})
        marketdata = data[1].get("marketdata", {})
        
        sec_columns = securities_data.get("columns", [])
        sec_rows = securities_data.get("data", [])
        
        market_columns = marketdata.get("columns", [])
        market_rows = marketdata.get("data", [])
        
        if not sec_rows or not market_rows:
            return None
        
        sec_dict = dict(zip(sec_columns, sec_rows[0]))
        market_dict = dict(zip(market_columns, market_rows[0]))
        
        price_data = {
            "ticker": ticker,
            "name": sec_dict.get("SHORTNAME", ticker),
            "price": float(market_dict.get("LAST") or sec_dict.get("PREVPRICE") or 0),
            "open": float(market_dict.get("OPEN") or 0),
            "high": float(market_dict.get("HIGH") or 0),
            "low": float(market_dict.get("LOW") or 0),
            "prev_close": float(sec_dict.get("PREVPRICE") or 0),
            "volume": int(market_dict.get("VOLTODAY") or 0),
            "currency": "RUB",
            "change_pct": 0.0,
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        # Calculate change percentage
        if price_data["prev_close"] > 0:
            price_data["change_pct"] = round(
                ((price_data["price"] - price_data["prev_close"]) / price_data["prev_close"]) * 100, 2
            )
        
        # Cache for update interval
        await redis_client.set(cache_key, price_data, expire=settings.market_update_interval)
        return price_data
    
    async def get_stock_history(
        self, 
        ticker: str, 
        days: int = 365
    ) -> List[Dict[str, Any]]:
        """
        Get historical stock data.
        Returns OHLCV data for the specified period.
        """
        cache_key = f"moex:history:{ticker}:{days}"
        cached = await redis_client.get(cache_key)
        if cached:
            return cached
        
        from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        url = f"{self.base_url}/history/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
        params = {"from": from_date}
        
        data = await self._fetch_json(url, params)
        
        history = []
        if data and len(data) > 1:
            history_data = data[1].get("history", {})
            columns = history_data.get("columns", [])
            rows = history_data.get("data", [])
            
            for row in rows:
                candle = dict(zip(columns, row))
                
                # Skip rows without price data
                if not candle.get("CLOSE"):
                    continue
                
                history.append({
                    "date": candle.get("TRADEDATE"),
                    "open": float(candle.get("OPEN") or 0),
                    "high": float(candle.get("HIGH") or 0),
                    "low": float(candle.get("LOW") or 0),
                    "close": float(candle.get("CLOSE") or 0),
                    "volume": int(candle.get("VOLUME") or 0),
                })
        
        # Cache for 1 hour
        await redis_client.set(cache_key, history, expire=3600)
        return history
    
    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """
        Search stocks by ticker or name.
        """
        url = f"{self.base_url}/securities.json"
        params = {"q": query, "limit": 20}
        
        data = await self._fetch_json(url, params)
        
        results = []
        if data and len(data) > 1:
            securities = data[1].get("securities", {})
            columns = securities.get("columns", [])
            rows = securities.get("data", [])
            
            for row in rows:
                sec = dict(zip(columns, row))
                
                # Filter only stocks
                if sec.get("type") not in ["common_share", "preferred_share"]:
                    continue
                
                results.append({
                    "ticker": sec.get("secid"),
                    "name": sec.get("shortname", sec.get("secid")),
                    "type": sec.get("type"),
                })
        
        return results
    
    async def get_multiple_prices(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get prices for multiple tickers efficiently.
        """
        tasks = [self.get_stock_price(ticker) for ticker in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        prices = {}
        for ticker, result in zip(tickers, results):
            if isinstance(result, dict) and result:
                prices[ticker] = result
        
        return prices


# Global MOEX service instance
moex_service = MOEXService()
