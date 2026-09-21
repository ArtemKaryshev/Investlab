import pytest
from backend.services.moex_service import MOEXService


@pytest.mark.asyncio
async def test_get_popular_stocks():
    """Test fetching popular stocks from MOEX."""
    service = MOEXService()
    
    try:
        stocks = await service.get_popular_stocks(limit=10)
        
        assert isinstance(stocks, list)
        assert len(stocks) > 0
        
        # Check first stock has required fields
        stock = stocks[0]
        assert "ticker" in stock
        assert "name" in stock
        assert "price" in stock
        assert "currency" in stock
        
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_get_stock_price():
    """Test fetching specific stock price."""
    service = MOEXService()
    
    try:
        # Test with known ticker (Sberbank)
        price_data = await service.get_stock_price("SBER")
        
        if price_data:  # May be None if market is closed
            assert "ticker" in price_data
            assert "price" in price_data
            assert price_data["ticker"] == "SBER"
            assert isinstance(price_data["price"], float)
        
    finally:
        await service.close()
