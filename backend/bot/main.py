import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from decimal import Decimal

from ..core.config import settings
from ..core.database import AsyncSessionLocal, init_db
from ..core.models import User, InvestorCategory, Currency
from ..core.redis_client import redis_client
from ..services.moex_service import moex_service
from ..services.trading_service import trading_service
from ..services.learning_service import learning_service
from ..services.duel_service import duel_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=settings.bot_token)
dp = Dispatcher()
router = Router()


class OnboardingStates(StatesGroup):
    """States for user onboarding flow."""
    choosing_category = State()
    initial_deposit = State()


class TradingStates(StatesGroup):
    """States for trading operations."""
    entering_ticker = State()
    entering_shares = State()
    confirming_order = State()


# Starting balances by investor category
STARTING_BALANCES = {
    InvestorCategory.CONSERVATIVE: {"usd": 50000, "rub": 500000},
    InvestorCategory.MODERATE: {"usd": 100000, "rub": 1000000},
    InvestorCategory.AGGRESSIVE: {"usd": 200000, "rub": 2000000},
}


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Build main menu keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📱 Открыть Mini App", web_app=WebAppInfo(url=settings.webapp_url))
    builder.button(text="📚 Обучение", callback_data="learning_menu")
    builder.button(text="💼 Портфель", callback_data="portfolio")
    builder.button(text="📊 Рынок", callback_data="market")
    builder.button(text="💰 Баланс", callback_data="balance")
    builder.button(text="🏆 Лидерборд", callback_data="leaderboard")
    builder.button(text="⚔️ Дуэли", callback_data="duels")
    builder.button(text="⚙️ Настройки", callback_data="settings")
    
    builder.adjust(1, 2, 2, 2, 1)
    return builder.as_markup()


def get_category_keyboard() -> InlineKeyboardMarkup:
    """Build investor category selection keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🛡 Консервативный", callback_data="category_conservative")
    builder.button(text="⚖️ Умеренный", callback_data="category_moderate")
    builder.button(text="🚀 Агрессивный", callback_data="category_aggressive")
    
    builder.adjust(1)
    return builder.as_markup()


async def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None, last_name: str = None) -> User:
    """Get existing user or create new one."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        return user


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command."""
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    
    # Check if user completed onboarding
    if not user.investor_category:
        await message.answer(
            "🎓 <b>Добро пожаловать в InvestLab!</b>\n\n"
            "Премиум-симулятор биржи для обучения инвестированию.\n\n"
            "⚠️ <i>Это виртуальный симулятор. Все операции проводятся с виртуальными деньгами "
            "и не несут реальных финансовых рисков. Данный бот не предоставляет инвестиционных "
            "рекомендаций.</i>\n\n"
            "Для начала выберите свою категорию инвестора:",
            reply_markup=get_category_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(OnboardingStates.choosing_category)
    else:
        await message.answer(
            f"👋 С возвращением, {user.first_name or 'инвестор'}!\n\n"
            f"💼 Ваш профиль:\n"
            f"• Категория: {user.investor_category.value.title()}\n"
            f"• Уровень: {user.level}\n"
            f"• Прогресс обучения: {user.learning_progress}%\n\n"
            f"Выберите действие:",
            reply_markup=get_main_menu_keyboard(),
        )


@router.callback_query(F.data.startswith("category_"), OnboardingStates.choosing_category)
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    """Process investor category selection."""
    category_map = {
        "category_conservative": InvestorCategory.CONSERVATIVE,
        "category_moderate": InvestorCategory.MODERATE,
        "category_aggressive": InvestorCategory.AGGRESSIVE,
    }
    
    category = category_map.get(callback.data)
    if not category:
        await callback.answer("Ошибка выбора категории")
        return
    
    # Update user
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one()
        
        user.investor_category = category
        balances = STARTING_BALANCES[category]
        user.balance_usd = balances["usd"]
        user.balance_rub = balances["rub"]
        
        await session.commit()
    
    category_descriptions = {
        InvestorCategory.CONSERVATIVE: "🛡 <b>Консервативный инвестор</b>\n\nВы предпочитаете стабильность и минимальные риски. Ваша цель — сохранить капитал и получать стабильный доход.",
        InvestorCategory.MODERATE: "⚖️ <b>Умеренный инвестор</b>\n\nВы готовы к разумным рискам ради роста капитала. Баланс между стабильностью и доходностью.",
        InvestorCategory.AGGRESSIVE: "🚀 <b>Агрессивный инвестор</b>\n\nВы готовы к высоким рискам ради максимальной прибыли. Ваша цель — быстрый рост капитала.",
    }
    
    await callback.message.edit_text(
        f"{category_descriptions[category]}\n\n"
        f"💰 Стартовый капитал:\n"
        f"• ${balances['usd']:,}\n"
        f"• ₽{balances['rub']:,}\n\n"
        f"✅ Отлично! Теперь вы готовы начать обучение и торговлю.\n\n"
        f"Рекомендуем начать с обучающих модулей 👇",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "learning_menu")
async def show_learning_menu(callback: CallbackQuery):
    """Show learning modules menu."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one()
        
        modules = await learning_service.get_modules_for_user(session, user)
        
        text = f"📚 <b>Обучающие модули</b>\n\n"
        text += f"📊 Прогресс: {user.learning_progress}%\n"
        text += f"⭐️ Уровень: {user.level}\n"
        text += f"🎯 XP: {user.xp}\n\n"
        
        builder = InlineKeyboardBuilder()
        
        for module in modules:
            status = "✅" if module["completed"] else "📖"
            builder.button(
                text=f"{status} {module['order']}. {module['title']}", 
                callback_data=f"module_{module['id']}"
            )
        
        builder.button(text="🔙 Назад", callback_data="main_menu")
        builder.adjust(1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("module_"))
async def show_module_content(callback: CallbackQuery):
    """Show specific module content."""
    module_id = int(callback.data.split("_")[1])
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one()
        
        modules = await learning_service.get_modules_for_user(session, user)
        module = next((m for m in modules if m["id"] == module_id), None)
        
        if not module:
            await callback.answer("Модуль не найден")
            return
        
        # Build content text
        text = f"📖 <b>{module['title']}</b>\n\n"
        text += f"{module['description']}\n\n"
        
        for section in module["content"]["sections"]:
            text += f"<b>{section['title']}</b>\n{section['text']}\n\n"
        
        builder = InlineKeyboardBuilder()
        
        if module["quiz"] and not module["completed"]:
            builder.button(text="📝 Пройти квиз", callback_data=f"quiz_{module_id}")
        
        if not module["completed"]:
            builder.button(text="✅ Завершить урок", callback_data=f"complete_{module_id}")
        else:
            builder.button(text="✅ Урок пройден", callback_data="noop")
        
        builder.button(text="🔙 К модулям", callback_data="learning_menu")
        builder.adjust(1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("complete_"))
async def complete_module(callback: CallbackQuery):
    """Complete a learning module."""
    module_id = int(callback.data.split("_")[1])
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one()
        
        completion = await learning_service.complete_lesson(session, user, module_id)
        
        if completion["success"]:
            text = f"🎉 <b>Урок пройден!</b>\n\n"
            text += f"⭐️ +{completion['xp_earned']} XP\n"
            text += f"📊 Прогресс: {completion['progress']}%\n"
            
            if completion["leveled_up"]:
                text += f"\n🎊 <b>Новый уровень: {completion['level']}!</b>"
            
            await callback.message.answer(text, parse_mode="HTML")
        else:
            await callback.message.answer(f"❌ {completion['error']}")
    
    await callback.answer()


@router.callback_query(F.data == "portfolio")
async def show_portfolio(callback: CallbackQuery):
    """Show user's portfolio."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one()
        
        portfolio_value = await trading_service.get_portfolio_value(session, user)
        
        # Get positions
        from ..core.models import Portfolio
        positions_result = await session.execute(
            select(Portfolio).where(Portfolio.user_id == user.id)
        )
        positions = positions_result.scalars().all()
        
        text = f"💼 <b>Ваш портфель</b>\n\n"
        text += f"💰 Общая стоимость:\n"
        text += f"• ${portfolio_value['total_value_usd']:,.2f}\n"
        text += f"• ₽{portfolio_value['total_value_rub']:,.2f}\n\n"
        text += f"💵 Наличные:\n"
        text += f"• ${portfolio_value['cash_usd']:,.2f}\n"
        text += f"• ₽{portfolio_value['cash_rub']:,.2f}\n\n"
        
        if positions:
            text += f"📊 <b>Позиции:</b>\n\n"
            
            # Get current prices
            tickers = [p.ticker for p in positions]
            prices = await moex_service.get_multiple_prices(tickers)
            
            for pos in positions:
                price_data = prices.get(pos.ticker)
                if price_data:
                    current_price = Decimal(str(price_data["price"]))
                    position_value = pos.shares * current_price
                    profit = (current_price - pos.avg_price) * pos.shares
                    profit_pct = ((current_price - pos.avg_price) / pos.avg_price) * 100
                    
                    profit_emoji = "🟢" if profit > 0 else "🔴" if profit < 0 else "⚪️"
                    
                    text += f"{profit_emoji} <b>{pos.ticker}</b>\n"
                    text += f"  Акций: {pos.shares} × {current_price:.2f} {pos.currency.value}\n"
                    text += f"  Стоимость: {position_value:.2f} {pos.currency.value}\n"
                    text += f"  P&L: {profit:+.2f} ({profit_pct:+.2f}%)\n\n"
        else:
            text += "📭 Позиций пока нет. Начните торговать!"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="📈 Купить", callback_data="trade_buy")
        builder.button(text="📉 Продать", callback_data="trade_sell")
        builder.button(text="💰 Пополнить", callback_data="deposit")
        builder.button(text="🔙 Назад", callback_data="main_menu")
        builder.adjust(2, 1, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data == "market")
async def show_market(callback: CallbackQuery):
    """Show market overview with popular stocks."""
    stocks = await moex_service.get_popular_stocks(limit=10)
    
    text = "📊 <b>Популярные акции MOEX</b>\n\n"
    
    for stock in stocks:
        text += f"<b>{stock['ticker']}</b> — {stock['name']}\n"
        text += f"  Цена: {stock['price']:.2f} {stock['currency']}\n\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Поиск акций", callback_data="search_stocks")
    builder.button(text="📈 Купить", callback_data="trade_buy")
    builder.button(text="🔙 Назад", callback_data="main_menu")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    await callback.answer()


@router.callback_query(F.data == "balance")
async def show_balance(callback: CallbackQuery):
    """Show user balance with deposit option."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one()
        
        text = f"💰 <b>Ваш баланс</b>\n\n"
        text += f"💵 Доллары: ${user.balance_usd:,.2f}\n"
        text += f"💴 Рубли: ₽{user.balance_rub:,.2f}\n\n"
        text += f"<i>Используйте кнопки ниже для пополнения виртуального счёта</i>"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="💵 +$10,000", callback_data="deposit_usd_10000")
        builder.button(text="💴 +₽100,000", callback_data="deposit_rub_100000")
        builder.button(text="💵 +$50,000", callback_data="deposit_usd_50000")
        builder.button(text="💴 +₽500,000", callback_data="deposit_rub_500000")
        builder.button(text="🔙 Назад", callback_data="main_menu")
        builder.adjust(2, 2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("deposit_"))
async def process_deposit(callback: CallbackQuery):
    """Process virtual balance deposit."""
    parts = callback.data.split("_")
    currency = parts[1]
    amount = int(parts[2])
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one()
        
        if currency == "usd":
            user.balance_usd += amount
            currency_symbol = "$"
        else:
            user.balance_rub += amount
            currency_symbol = "₽"
        
        # Create transaction
        from ..core.models import Transaction, TransactionType, Currency as CurrencyEnum
        transaction = Transaction(
            user_id=user.id,
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            currency=CurrencyEnum.USD if currency == "usd" else CurrencyEnum.RUB,
            description=f"Виртуальное пополнение счёта",
        )
        session.add(transaction)
        
        await session.commit()
        
        await callback.message.answer(
            f"✅ Счёт пополнен на {currency_symbol}{amount:,}",
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data == "leaderboard")
async def show_leaderboard(callback: CallbackQuery):
    """Show global leaderboard."""
    async with AsyncSessionLocal() as session:
        leaderboard = await duel_service.get_global_leaderboard(session, limit=10)
        
        text = "🏆 <b>Топ инвесторов</b>\n\n"
        
        medals = ["🥇", "🥈", "🥉"]
        
        for entry in leaderboard:
            medal = medals[entry["rank"] - 1] if entry["rank"] <= 3 else f"{entry['rank']}."
            text += f"{medal} <b>{entry['username']}</b>\n"
            text += f"  Уровень {entry['level']} | Капитал: ₽{entry['total_value_rub']:,.0f}\n\n"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Назад", callback_data="main_menu")
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery):
    """Return to main menu."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one()
        
        await callback.message.edit_text(
            f"👋 Главное меню\n\n"
            f"Уровень: {user.level} | XP: {user.xp} | Прогресс: {user.learning_progress}%",
            reply_markup=get_main_menu_keyboard(),
        )
    
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    """No-op handler for disabled buttons."""
    await callback.answer()


async def on_startup():
    """Initialize on startup."""
    logger.info("Starting InvestLab bot...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Connect to Redis
    await redis_client.connect()
    logger.info("Redis connected")
    
    # Initialize learning modules
    async with AsyncSessionLocal() as session:
        await learning_service.initialize_modules(session)
    logger.info("Learning modules initialized")
    
    logger.info("Bot started successfully!")


async def on_shutdown():
    """Cleanup on shutdown."""
    logger.info("Shutting down bot...")
    
    await redis_client.disconnect()
    await moex_service.close()
    await bot.session.close()
    
    logger.info("Bot stopped")


async def main():
    """Main bot entry point."""
    dp.include_router(router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
