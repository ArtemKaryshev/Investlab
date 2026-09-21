# InvestLab — Премиум-симулятор биржи для Telegram

![InvestLab](https://img.shields.io/badge/Status-Production%20Ready-success)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![React](https://img.shields.io/badge/React-18.2-61dafb)
![License](https://img.shields.io/badge/License-MIT-green)

**InvestLab** — полноценный виртуальный симулятор торговли ценными бумагами на Московской бирже (MOEX) для Telegram. Предназначен для обучения начинающих инвесторов принципам работы фондового рынка без финансовых рисков.

## 🎯 Возможности

### 📱 Telegram Bot
- ✅ Онбординг с выбором категории инвестора (Консервативный / Умеренный / Агрессивный)
- ✅ Виртуальное пополнение счёта (USD/RUB)
- ✅ Просмотр портфеля, баланса, позиций
- ✅ Торговые операции (покупка/продажа акций)
- ✅ Обучающие модули (7 уроков с квизами и практическими заданиями)
- ✅ Лидерборд и рейтинг пользователей
- ✅ Система геймификации (XP, уровни, достижения, стрики)

### 🌐 Mini App (React)
- ✅ Детальный просмотр портфеля с P&L в реальном времени
- ✅ Графики котировок (исторические данные за год)
- ✅ Торговый интерфейс с валидацией
- ✅ Отслеживание прогресса обучения
- ✅ Лидерборд с подиумом топ-3
- ✅ Профиль пользователя с метриками

### 📊 Рыночные данные
- ✅ Реальные котировки MOEX через ISS API (без регистрации)
- ✅ Кэширование в Redis с автообновлением каждые 30 секунд
- ✅ Исторические данные за год
- ✅ Поиск акций по тикеру и названию

### 💼 Торговля
- ✅ Рыночные ордера (market orders)
- ✅ Автоматический расчёт комиссий (0.05% + минимум)
- ✅ Управление позициями (средневзвешенная цена)
- ✅ Мультивалютность (USD/RUB)
- ✅ История транзакций и ордеров
- ✅ Валидация баланса и количества акций

### 🎓 Обучение
- ✅ 7 структурированных модулей
- ✅ Квизы с подсчётом результатов
- ✅ Практические задания
- ✅ Прогресс-бар (60% уроки + 30% квизы + 10% практика)
- ✅ Награды XP за завершение модулей

### 🏆 Соревнования
- ✅ Глобальный лидерборд по стоимости портфеля
- ✅ Дуэли портфелей (создание, участие, таблица результатов)
- ✅ Автоматический подсчёт доходности (return %)

---

## 🛠 Технологический стек

### Backend
- **Python 3.12**
- **aiogram 3.x** — Telegram Bot API
- **FastAPI** — REST API для Mini App
- **SQLAlchemy 2.0** (async) — ORM
- **PostgreSQL** — основная БД
- **Redis** — кэш котировок и rate-limiting
- **Alembic** — миграции БД
- **aiohttp** — асинхронные HTTP-запросы к MOEX API

### Frontend (Mini App)
- **React 18** + **TypeScript**
- **Vite** — сборка
- **TailwindCSS** — стилизация
- **React Query** — state management и кэширование
- **Recharts** — графики
- **Axios** — HTTP-клиент
- **React Router** — навигация

### Infrastructure
- **Docker + Docker Compose** — контейнеризация
- **MOEX ISS API** — бесплатный источник котировок

---

## 🚀 Быстрый старт

### 1. Требования
- Docker & Docker Compose
- Telegram Bot Token (получить у [@BotFather](https://t.me/botfather))
- Домен с HTTPS (для Mini App) или локальная разработка

### 2. Клонирование репозитория
```bash
git clone <your-repo-url> investlab
cd investlab
```

### 3. Конфигурация
Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
```

**Обязательные переменные:**
```env
# Telegram
BOT_TOKEN=1234567890:ABCDEF...  # От @BotFather
WEBAPP_URL=https://your-domain.com  # URL Mini App

# Database
DATABASE_URL=postgresql+asyncpg://investlab:password@postgres:5432/investlab

# Redis
REDIS_URL=redis://redis:6379/0

# API
API_SECRET_KEY=your-random-secret-key-here  # Генерируйте openssl rand -hex 32
API_HOST=0.0.0.0
API_PORT=8000

# Admin (telegram user IDs через запятую)
ADMIN_USER_IDS=123456789,987654321
```

### 4. Запуск через Docker Compose

```bash
docker-compose up -d --build
```

Сервисы:
- **Bot** — порт не открыт (long polling или webhook)
- **API** — http://localhost:8000
- **PostgreSQL** — localhost:5432
- **Redis** — localhost:6379

### 5. Frontend (Mini App)

#### Локальная разработка
```bash
cd frontend
npm install
npm run dev
```

Откроется на `http://localhost:5173`

#### Production сборка
```bash
npm run build
# Папка dist/ содержит статические файлы для хостинга
```

**Деплой Mini App:**
- Залейте `dist/` на любой статический хостинг (Vercel, Netlify, Cloudflare Pages, или свой NGINX)
- Укажите URL в `WEBAPP_URL`

### 6. Создание Telegram Bot

1. Создайте бота у [@BotFather](https://t.me/botfather)
2. Включите Inline Mode (опционально)
3. Установите Mini App:
   ```
   /newapp
   # Выберите бота
   # Название: InvestLab
   # Описание: Симулятор биржи
   # URL: https://your-domain.com
   # Загрузите иконку 640x360
   ```
4. Установите команды:
   ```
   /setcommands
   start - Запустить бота
   ```

---

## 📁 Структура проекта

```
investlab/
├── backend/
│   ├── bot/
│   │   └── main.py              # Telegram Bot (aiogram)
│   ├── api/
│   │   └── main.py              # FastAPI REST API
│   ├── core/
│   │   ├── config.py            # Настройки
│   │   ├── database.py          # Async SQLAlchemy setup
│   │   ├── models.py            # Модели БД
│   │   └── redis_client.py      # Redis wrapper
│   └── services/
│       ├── moex_service.py      # MOEX API интеграция
│       ├── trading_service.py   # Торговый движок
│       ├── learning_service.py  # Обучающая система
│       └── duel_service.py      # Дуэли и лидерборд
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts        # Axios + auth
│   │   ├── components/
│   │   │   └── Layout.tsx       # Навигация
│   │   ├── pages/
│   │   │   ├── Portfolio.tsx
│   │   │   ├── Market.tsx
│   │   │   ├── StockDetail.tsx
│   │   │   ├── Learning.tsx
│   │   │   ├── Leaderboard.tsx
│   │   │   └── Profile.tsx
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   └── package.json
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

---

## 🔒 Безопасность

### Реализованные меры
✅ **Валидация Telegram WebApp initData** через HMAC-SHA256  
✅ **Параметризованные SQL-запросы** (SQLAlchemy ORM)  
✅ **Input validation** (Pydantic models)  
✅ **Rate limiting** готов через Redis (требует реализации middleware)  
✅ **Секреты через environment variables**  
✅ **CORS настроен** (в production укажите точные origins)  
✅ **Хэширование токенов** для auth  
✅ **Нет SQL injection** — используется ORM  
✅ **Нет XSS** — React экранирует вывод автоматически

### Рекомендации для production
- [ ] Включите HTTPS для API
- [ ] Настройте CORS на конкретные домены
- [ ] Добавьте rate limiting middleware в FastAPI
- [ ] Ротация API_SECRET_KEY
- [ ] Логирование с Sentry/CloudWatch
- [ ] Регулярные бэкапы PostgreSQL
- [ ] Мониторинг (Prometheus + Grafana)

---

## 🎨 Дизайн

**Палитра (тёмная премиум-тема):**
- Background: `#0F1117`
- Surface: `#171A23`
- Elevated: `#1E222E`
- Border: `#2A2E3A`
- Accent (Gold): `#FBBF24`
- Success: `#10B981`
- Danger: `#EF4444`

**Типографика:** System UI stack (-apple-system, Segoe UI)

---

## 🎯 Roadmap

### Фаза 1 (Текущая) ✅
- [x] Базовый функционал торговли
- [x] Обучающие модули
- [x] Mini App с портфелем
- [x] Лидерборд

### Фаза 2 (Следующая)
- [ ] Лимитные ордера (Limit orders)
- [ ] Стоп-лоссы (Stop-loss orders)
- [ ] Push-уведомления о ценах
- [ ] Уведомления о исполнении ордеров
- [ ] Дивиденды и сплиты
- [ ] Экспорт отчётов (PDF)
- [ ] Социальные функции (копирование сделок)

### Фаза 3
- [ ] Опционы и фьючерсы (симуляция)
- [ ] Технический анализ (индикаторы RSI, MACD)
- [ ] AI-ассистент для рекомендаций
- [ ] Интеграция с Tinkoff Invest API
- [ ] Поддержка NYSE/NASDAQ акций

---

## 📊 API Эндпоинты

### Аутентификация
Все запросы требуют заголовок:
```
Authorization: tma <telegram_init_data>
```

### Основные эндпоинты

**User & Portfolio**
- `GET /api/user/profile` — профиль и сводка портфеля
- `GET /api/portfolio/positions` — позиции с текущими ценами

**Market**
- `GET /api/market/stocks?limit=50` — список акций
- `GET /api/market/stock/{ticker}` — детали акции
- `GET /api/market/stock/{ticker}/history?days=365` — история

**Trading**
- `POST /api/trade/execute` — исполнить ордер
- `GET /api/trading/orders?limit=50` — история ордеров
- `GET /api/trading/transactions?limit=50` — транзакции

**Watchlist**
- `GET /api/watchlist` — избранное
- `POST /api/watchlist/add` — добавить
- `DELETE /api/watchlist/remove/{ticker}` — удалить

**Learning**
- `GET /api/learning/modules` — модули обучения
- `POST /api/learning/quiz/submit` — отправить квиз

**Leaderboard**
- `GET /api/leaderboard/global?limit=50` — топ инвесторов
- `GET /api/duels/active` — активные дуэли
- `GET /api/duels/{id}/leaderboard` — результаты дуэли
- `POST /api/duels/{id}/join` — присоединиться

**Admin** (требуется telegram_id в ADMIN_USER_IDS)
- `POST /api/admin/duels/create` — создать дуэль

---

## 🧪 Тестирование

```bash
cd backend
pip install pytest pytest-asyncio pytest-cov
pytest tests/ -v --cov
```

---

## 📦 Хостинг

### Рекомендации для бесплатного старта

**Backend (Bot + API):**
1. **Railway.app** (500 часов/месяц бесплатно)
   - PostgreSQL + Redis включены
   - Deploy через GitHub
   - Автоматические HTTPS

2. **Fly.io** (3 VM бесплатно)
   - Postgres + Redis addons
   - `flyctl launch`

**Frontend (Mini App):**
1. **Vercel** (бесплатный tier)
   - `vercel --prod`
   - Автоматический HTTPS

2. **Cloudflare Pages**
   - GitHub integration
   - Глобальный CDN

**Database:**
- Railway PostgreSQL (бесплатно)
- Supabase (бесплатно до 500MB)

---

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature-ветку: `git checkout -b feature/amazing-feature`
3. Commit изменения: `git commit -m 'Add amazing feature'`
4. Push в ветку: `git push origin feature/amazing-feature`
5. Откройте Pull Request

---

## 📄 Лицензия

MIT License — используйте свободно для коммерческих и некоммерческих проектов.

---

## ⚠️ Дисклеймер

**InvestLab** — образовательный симулятор. Все операции проводятся с виртуальными средствами. Данные не являются инвестиционной рекомендацией. Авторы не несут ответственности за финансовые решения пользователей на реальных рынках.

---

## 📧 Контакты

- **Issues:** [GitHub Issues](https://github.com/your-repo/issues)
- **Telegram:** [@your_channel](https://t.me/your_channel)

---

**Создано с 💛 для обучения инвесторов**

