# InvestLab — Краткая инструкция

## 🚀 Быстрый запуск

### 1. Настройка окружения

```bash
# Скопировать пример конфига
cp .env.example .env

# Отредактировать .env:
# BOT_TOKEN - получить у @BotFather
# WEBAPP_URL - URL вашего Mini App
# API_SECRET_KEY - сгенерировать: openssl rand -hex 32
```

### 2. Запуск backend

```bash
# Запустить все сервисы через Docker
docker-compose up -d --build

# Проверить статус
docker-compose ps

# Логи бота
docker-compose logs -f bot

# Логи API
docker-compose logs -f api
```

### 3. Запуск frontend (разработка)

```bash
cd frontend
npm install
npm run dev
# Откроется на http://localhost:5173
```

### 4. Production сборка frontend

```bash
cd frontend
npm run build
# Загрузить dist/ на Vercel/Netlify/CloudFlare Pages
# Обновить WEBAPP_URL в .env на production URL
```

## 📊 Структура БД

### Основные таблицы:
- **users** — профили пользователей
- **portfolios** — позиции в портфеле
- **orders** — история ордеров
- **transactions** — история транзакций
- **watchlist** — избранные акции
- **learning_modules** — обучающие модули
- **duels** — соревнования
- **duel_participants** — участники дуэлей

## 🔑 Основные команды

### Docker
```bash
docker-compose up -d          # Запустить
docker-compose down           # Остановить
docker-compose logs -f bot    # Логи бота
docker-compose restart bot    # Перезапустить бота
docker-compose exec postgres psql -U investlab  # Подключиться к БД
```

### Тестирование
```bash
cd backend
pytest tests/ -v
pytest tests/ -v --cov
```

### База данных
```bash
# Подключиться к PostgreSQL
docker-compose exec postgres psql -U investlab investlab

# Бэкап
docker-compose exec postgres pg_dump -U investlab investlab > backup.sql

# Восстановление
docker-compose exec -T postgres psql -U investlab investlab < backup.sql
```

## 🎯 Частые задачи

### Создать дуэль (через API)
```bash
curl -X POST http://localhost:8000/api/admin/duels/create \
  -H "Authorization: tma <telegram_init_data>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Недельная дуэль",
    "duration_days": 7,
    "start_balance": 1000000,
    "currency": "RUB"
  }'
```

### Добавить админа
```bash
# В .env добавить telegram user ID:
ADMIN_USER_IDS=123456789,987654321
```

### Обновить стартовый баланс
Редактировать `backend/bot/main.py`:
```python
STARTING_BALANCES = {
    InvestorCategory.CONSERVATIVE: {"usd": 50000, "rub": 500000},
    InvestorCategory.MODERATE: {"usd": 100000, "rub": 1000000},
    InvestorCategory.AGGRESSIVE: {"usd": 200000, "rub": 2000000},
}
```

## 🐛 Устранение проблем

### Бот не отвечает
```bash
# Проверить логи
docker-compose logs bot --tail=50

# Перезапустить
docker-compose restart bot

# Проверить BOT_TOKEN
docker-compose exec bot env | grep BOT_TOKEN
```

### API не работает
```bash
# Проверить порт 8000
curl http://localhost:8000/

# Проверить логи
docker-compose logs api --tail=50
```

### База данных не подключается
```bash
# Проверить статус
docker-compose ps postgres

# Переподключиться
docker-compose restart postgres

# Проверить логи
docker-compose logs postgres
```

### Frontend не загружает данные
1. Проверить `VITE_API_URL` в `frontend/.env`
2. Проверить CORS в `backend/api/main.py`
3. Проверить Telegram initData (работает только внутри Telegram WebApp)

## 📈 Мониторинг

### Метрики Redis
```bash
docker-compose exec redis redis-cli INFO stats
docker-compose exec redis redis-cli DBSIZE
```

### Метрики PostgreSQL
```bash
docker-compose exec postgres psql -U investlab -c "SELECT COUNT(*) FROM users;"
docker-compose exec postgres psql -U investlab -c "SELECT COUNT(*) FROM portfolios;"
```

## 🔒 Безопасность

### Ротация секретов
```bash
# Сгенерировать новый API_SECRET_KEY
openssl rand -hex 32

# Обновить в .env
# Перезапустить сервисы
docker-compose restart
```

### Бэкап БД (Production)
```bash
# Ежедневный бэкап
0 2 * * * docker-compose exec postgres pg_dump -U investlab investlab | gzip > /backups/investlab_$(date +\%Y\%m\%d).sql.gz
```

## 📱 Настройка Telegram Bot

1. Создать бота у @BotFather → получить токен
2. Включить Inline Mode (опционально)
3. Установить команды:
```
start - Запустить бота
```
4. Создать Mini App у @BotFather → `/newapp`
5. Указать URL Mini App (после деплоя frontend)

## 🌐 Деплой на Railway

```bash
# Установить CLI
npm install -g @railway/cli

# Логин
railway login

# Инициализация
railway init

# Добавить переменные окружения
railway variables set BOT_TOKEN=your_token
railway variables set WEBAPP_URL=https://your-frontend.vercel.app

# Деплой
railway up
```

## 📊 Полезные SQL запросы

```sql
-- Топ-10 инвесторов
SELECT first_name, balance_usd + balance_rub as total, level, xp
FROM users
ORDER BY total DESC
LIMIT 10;

-- Самые популярные акции
SELECT ticker, COUNT(*) as holders, SUM(shares) as total_shares
FROM portfolios
GROUP BY ticker
ORDER BY holders DESC;

-- Статистика по обучению
SELECT 
  investor_category,
  AVG(learning_progress) as avg_progress,
  AVG(level) as avg_level
FROM users
GROUP BY investor_category;
```

---

**Нужна помощь?** Создайте Issue на GitHub или напишите в Telegram
