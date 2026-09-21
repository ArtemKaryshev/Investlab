# InvestLab — Архитектура проекта

## Обзор системы

```
┌─────────────────────────────────────────────────────────────┐
│                     Telegram Client                          │
│  ┌──────────────────┐            ┌──────────────────┐      │
│  │   Telegram Bot   │            │    Mini App      │      │
│  │   (Inline UI)    │            │   (React PWA)    │      │
│  └────────┬─────────┘            └────────┬─────────┘      │
└───────────┼──────────────────────────────┼─────────────────┘
            │                               │
            │ Bot API                       │ HTTPS
            │ (Long Polling/Webhook)        │ (REST + WebSocket)
            │                               │
┌───────────▼───────────────────────────────▼─────────────────┐
│                    Backend Services                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Python Application Layer                 │  │
│  │  ┌──────────────┐         ┌──────────────────────┐  │  │
│  │  │ Telegram Bot │         │    FastAPI Server    │  │  │
│  │  │  (aiogram)   │         │  (REST API + Auth)   │  │  │
│  │  └──────┬───────┘         └──────────┬───────────┘  │  │
│  │         │                             │              │  │
│  │         └─────────────┬───────────────┘              │  │
│  │                       │                              │  │
│  │         ┌─────────────▼──────────────┐              │  │
│  │         │   Business Logic Layer     │              │  │
│  │         │ ┌────────────────────────┐ │              │  │
│  │         │ │  Trading Service       │ │              │  │
│  │         │ │  - Order execution     │ │              │  │
│  │         │ │  - Portfolio mgmt      │ │              │  │
│  │         │ │  - Commission calc     │ │              │  │
│  │         │ └────────────────────────┘ │              │  │
│  │         │ ┌────────────────────────┐ │              │  │
│  │         │ │  MOEX Service          │ │              │  │
│  │         │ │  - Price fetching      │ │              │  │
│  │         │ │  - History data        │ │              │  │
│  │         │ │  - Search              │ │              │  │
│  │         │ └────────────────────────┘ │              │  │
│  │         │ ┌────────────────────────┐ │              │  │
│  │         │ │  Learning Service      │ │              │  │
│  │         │ │  - Modules             │ │              │  │
│  │         │ │  - Quizzes             │ │              │  │
│  │         │ │  - Progress tracking   │ │              │  │
│  │         │ └────────────────────────┘ │              │  │
│  │         │ ┌────────────────────────┐ │              │  │
│  │         │ │  Duel Service          │ │              │  │
│  │         │ │  - Leaderboard         │ │              │  │
│  │         │ │  - Competitions        │ │              │  │
│  │         │ └────────────────────────┘ │              │  │
│  │         └────────────────────────────┘              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
┌───────────────────┐  ┌─────────────┐  ┌──────────────┐
│   PostgreSQL      │  │    Redis    │  │  MOEX ISS    │
│                   │  │             │  │   API        │
│ - Users           │  │ - Cache     │  │              │
│ - Portfolios      │  │ - Sessions  │  │ - Quotes     │
│ - Orders          │  │ - Rate      │  │ - History    │
│ - Transactions    │  │   Limit     │  │ - Search     │
│ - Learning data   │  │             │  │              │
└───────────────────┘  └─────────────┘  └──────────────┘
```

## Компоненты

### 1. Telegram Bot (aiogram)
**Ответственность:**
- Пользовательский интерфейс в Telegram
- Обработка команд и callback queries
- Inline меню и кнопки
- Онбординг новых пользователей
- Уведомления и рассылки

**Технологии:**
- Python 3.12
- aiogram 3.x
- AsyncIO

### 2. FastAPI REST API
**Ответственность:**
- REST endpoints для Mini App
- JWT/Telegram WebApp аутентификация
- Валидация входных данных
- CORS handling
- API документация (Swagger)

**Endpoints:**
- `/api/user/*` — профиль, настройки
- `/api/portfolio/*` — позиции, сводка
- `/api/market/*` — котировки, поиск
- `/api/trade/*` — исполнение ордеров
- `/api/learning/*` — модули, квизы
- `/api/leaderboard/*` — рейтинги, дуэли

### 3. Services Layer

#### Trading Service
```python
class TradingService:
    - execute_market_order()      # Исполнение рыночных ордеров
    - execute_limit_order()       # Лимитные ордера (TODO)
    - calculate_commission()      # Расчёт комиссии
    - update_portfolio()          # Обновление позиций
    - get_portfolio_value()       # Расчёт стоимости портфеля
```

#### MOEX Service
```python
class MOEXService:
    - get_popular_stocks()        # Топ акций
    - get_stock_price()           # Текущая цена
    - get_stock_history()         # История
    - search_stocks()             # Поиск
    - get_multiple_prices()       # Batch запрос
```

#### Learning Service
```python
class LearningService:
    - get_modules_for_user()      # Модули для категории
    - complete_lesson()           # Завершение урока
    - submit_quiz()               # Проверка квиза
    - award_achievement()         # Выдача достижений
    - calculate_progress()        # Подсчёт прогресса
```

#### Duel Service
```python
class DuelService:
    - create_duel()               # Создание соревнования
    - join_duel()                 # Присоединение
    - get_duel_leaderboard()      # Таблица результатов
    - update_participants()       # Обновление балансов
```

### 4. Data Layer

#### PostgreSQL Schema
```sql
users
├── id (PK)
├── telegram_id (UNIQUE)
├── investor_category (enum)
├── balance_usd, balance_rub
├── learning_progress
├── xp, level, achievements
└── timestamps

portfolios
├── id (PK)
├── user_id (FK)
├── ticker
├── shares
├── avg_price
└── currency

orders
├── id (PK)
├── user_id (FK)
├── ticker
├── order_type (market/limit)
├── status (pending/filled/cancelled)
├── price, filled_price
└── timestamps

transactions
├── id (PK)
├── user_id (FK)
├── type (buy/sell/deposit/commission)
├── ticker, shares, price
└── amount, currency

learning_modules
├── id (PK)
├── order, title, description
├── category (investor type)
├── content (JSON)
├── quiz (JSON)
└── xp_reward

duels
├── id (PK)
├── name, duration_days
├── start_balance, currency
└── started_at, ends_at

duel_participants
├── id (PK)
├── duel_id (FK)
├── user_id (FK)
├── starting_balance
├── current_balance
└── return_pct
```

#### Redis Cache Structure
```
Key Pattern                    TTL      Description
─────────────────────────────  ───────  ─────────────────────────
moex:price:{ticker}            30s      Текущая цена
moex:history:{ticker}:{days}   1h       Исторические данные
moex:popular_stocks:{limit}    1h       Топ акций
user:{telegram_id}:session     24h      Сессия пользователя
rate_limit:{user_id}:{action}  1m       Rate limiting
```

### 5. Frontend (React Mini App)

**Структура:**
```
src/
├── api/
│   └── client.ts              # HTTP client + auth
├── components/
│   └── Layout.tsx             # Навигация
├── pages/
│   ├── Portfolio.tsx          # Главный экран
│   ├── Market.tsx             # Список акций
│   ├── StockDetail.tsx        # Детали + торговля
│   ├── Learning.tsx           # Обучение
│   ├── Leaderboard.tsx        # Рейтинг
│   └── Profile.tsx            # Профиль
├── App.tsx                    # Роутинг
└── main.tsx                   # Entry point
```

**State Management:**
- React Query для серверного стейта
- Local state через useState/useReducer
- Context для глобальных настроек (тема, язык)

## Потоки данных

### 1. Торговля (покупка акции)
```
User (Mini App)
    │
    ├─ Click "Купить" на StockDetail
    │
    ▼
POST /api/trade/execute
    │
    ├─ Валидация Telegram initData
    ├─ Получение user из БД
    │
    ▼
TradingService.execute_market_order()
    │
    ├─ Получение цены из MOEX (cache/API)
    ├─ Валидация баланса
    ├─ Расчёт комиссии
    ├─ Обновление user.balance
    ├─ Создание/обновление Portfolio
    ├─ Создание Order (status=filled)
    ├─ Создание Transaction записей
    │
    ▼
Response → Frontend
    │
    ├─ Invalidate queries (profile, positions)
    └─ Показать успех/ошибку
```

### 2. Обучение (прохождение модуля)
```
User (Bot)
    │
    ├─ /start → onboarding
    ├─ Выбор категории инвестора
    ├─ Присвоение стартового баланса
    │
    ▼
Меню "Обучение"
    │
    ├─ LearningService.get_modules_for_user()
    ├─ Показ списка модулей
    │
    ▼
User открывает модуль
    │
    ├─ Показ контента
    ├─ User проходит квиз
    │
    ▼
LearningService.submit_quiz()
    │
    ├─ Проверка ответов
    ├─ Расчёт score
    ├─ Обновление user.quiz_scores
    │
    ▼
LearningService.complete_lesson()
    │
    ├─ Добавление в user.completed_lessons
    ├─ Начисление XP
    ├─ Проверка level up
    ├─ Обновление learning_progress
    │
    ▼
Response → User
    └─ Показ результата + XP
```

### 3. Обновление котировок (фоновый процесс)
```
Scheduled Task (каждые 30 сек)
    │
    ▼
MOEXService.get_multiple_prices(watchlist_tickers)
    │
    ├─ Проверка Redis cache
    │   └─ Если есть → return cached
    │
    ├─ MOEX ISS API requests
    │   └─ GET /iss/engines/stock/markets/shares/...
    │
    ├─ Parse JSON response
    ├─ Сохранение в Redis (TTL=30s)
    │
    ▼
WebSocket broadcast (опционально, TODO)
    └─ Push обновлений в Mini App
```

## Безопасность

### Authentication Flow (Mini App)
```
1. User открывает Mini App в Telegram
   ↓
2. Telegram передаёт initData (HMAC-signed)
   ↓
3. Frontend отправляет в Authorization header:
   "tma <initData>"
   ↓
4. Backend проверяет:
   - Распарсить initData
   - Вычислить HMAC с BOT_TOKEN
   - Сравнить с полученным hash
   ↓
5. Если валидно → извлечь user_id
   ↓
6. Загрузить User из БД
   ↓
7. Вернуть данные
```

### Input Validation
```python
# Pydantic models
class TradeRequest(BaseModel):
    ticker: str               # Валидация формата
    side: str                 # Enum (buy/sell)
    shares: float            # Положительное число
    currency: str            # Enum (USD/RUB)

# SQLAlchemy ORM (параметризованные запросы)
session.execute(
    select(User).where(User.telegram_id == user_id)
)
# ✅ Защита от SQL injection
```

## Масштабирование

### Горизонтальное
- **Bot:** Несколько инстансов с webhook (через nginx load balancer)
- **API:** FastAPI за Gunicorn/Uvicorn workers
- **Database:** PostgreSQL read replicas
- **Redis:** Redis Cluster для sharding

### Вертикальное
- Увеличение CPU/RAM для API workers
- Индексы БД на часто используемые поля
- Connection pooling (SQLAlchemy pool_size)

### Кэширование
- Redis для котировок (TTL=30s)
- CDN для статических файлов frontend
- HTTP cache headers для API responses

## Мониторинг

### Метрики
- **Bot:** Messages/sec, response time, errors
- **API:** Request rate, latency p50/p95/p99, 5xx errors
- **DB:** Query time, connection pool usage, locks
- **Redis:** Hit rate, memory usage, evictions

### Логирование
- Структурированные логи (JSON)
- Уровни: DEBUG, INFO, WARNING, ERROR
- Aggregation: Sentry для ошибок, CloudWatch/ELK для метрик

### Алерты
- API latency > 1s
- Error rate > 1%
- Database connection pool > 80%
- Redis memory > 90%

---

**Документ обновлён:** 2024
