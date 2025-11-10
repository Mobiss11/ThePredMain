# ThePred - Документация Проекта

**Версия**: 1.4
**Дата обновления**: 10 ноября 2025
**Прогресс**: 98% Complete 🎉

> **⚡️ ВАЖНО**:
> - Для быстрого старта работы читай **[CONTEXT.md](CONTEXT.md)** - текущие задачи, статус компонентов, известные проблемы
> - Для детальной технической документации см. разделы ниже
> - После перерыва ВСЕГДА начинай с CONTEXT.md

---

## 📋 Содержание

1. [О проекте](#о-проекте)
2. [Архитектура](#архитектура)
3. [Технологический стек](#технологический-стек)
4. [Структура проекта](#структура-проекта)
5. [Основные компоненты](#основные-компоненты)
6. [База данных](#база-данных)
7. [Запуск проекта](#запуск-проекта)
8. [Разработка](#разработка)
9. [Production Deployment](#production-deployment)

---

## О проекте

**ThePred** - платформа prediction markets (рынки предсказаний) в Telegram. Пользователи делают ставки на исходы событий в крипте, спорте и политике, зарабатывая токены PRED.

### Ключевые особенности:

- 🎯 **Prediction Markets** - ставки на реальные события
- 💰 **Токен PRED** - внутренняя валюта (начальный баланс: 10,000 PRED)
- 💎 **TON Blockchain** - интеграция TON Wallet (в разработке)
- 🎮 **Геймификация** - 19 миссий, достижения, лидерборд
- 📱 **Telegram Mini App** - полноценное веб-приложение
- 👑 **Ранговая система** - Bronze → Silver → Gold → Diamond → Grandmaster
- 📊 **Админ-панель** - управление рынками, пользователями, broadcast
- 📢 **Broadcast система** - массовые рассылки с rate limiting (30 msg/sec)
- 📅 **Scheduled Broadcasts** - запланированные рассылки с datetime picker
- 🎫 **Support система** - тикеты поддержки

### Бизнес-модель:

1. **Комиссия с рынков** - 2-5% от pool
2. **Премиум-подписка** - эксклюзивные рынки, бонусы
3. **Реклама** - партнерские рынки, спонсорские события

---

## Архитектура

```
┌─────────────────────────────────────────────────────┐
│              TELEGRAM BOT (@The_Pred_Bot)            │
│                    aiogram 3.x                       │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│         MINI APP (https://thepred.tech)              │
│         Quart + Jinja2 + Tailwind CSS                │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│           BACKEND API (FastAPI:8000)                 │
│                                                      │
│  Auth | Markets | Bets | Users | Missions           │
│  Leaderboard | Wallet | Admin | Support             │
└─────┬──────────────────────────────┬────────────────┘
      │                              │
      ▼                              ▼
┌──────────────┐              ┌─────────────┐
│ PostgreSQL 15│              │   Redis 7   │
│  (Database)  │              │   (Cache)   │
└──────┬───────┘              └─────────────┘
       │
       ▼
┌──────────────┐
│  MinIO S3    │
│(thepred.store│
└──────────────┘

┌─────────────────────────────────────────────────────┐
│          TELEGRAM WORKER (notification queue)        │
│          Rate Limiting: 30 msg/sec                   │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│     BROADCAST SCHEDULER (scheduled broadcasts)       │
│          Checks every 60 seconds                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│         ADMIN PANEL (Quart:8002)                     │
│  Dashboard | Markets | Users | Broadcast | Support  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│         LANDING PAGE (Quart:8003)                    │
└─────────────────────────────────────────────────────┘
```

---

## Технологический стек

### Backend
- **FastAPI** 0.109.0 - REST API
- **SQLAlchemy** 2.0.25 - ORM (async)
- **Alembic** 1.13.1 - Database migrations
- **PostgreSQL** 15.x - Primary database
- **Redis** 7.x - Cache & sessions
- **JWT** - Authentication (24h expiration)
- **boto3** - S3/MinIO integration

### Frontend
- **Quart** 0.19.4 - Async Flask (Mini App, Admin, Landing)
- **Jinja2** - Templates
- **Tailwind CSS** 3.x - Styling
- **Chart.js** - Admin dashboard charts
- **aiohttp** - API client

### Bot & Worker
- **aiogram** 3.x - Telegram Bot framework
- **asyncio** - Async processing
- **APScheduler** - Scheduled tasks

### DevOps
- **Docker** + **Docker Compose** - Containerization
- **PM2** - Process management (production)
- **Nginx** - Reverse proxy
- **Let's Encrypt** - SSL certificates

---

## Структура проекта

```
ThePred/
├── backend/                    # FastAPI Backend (порт 8000)
│   ├── app/
│   │   ├── api/endpoints/      # 40+ API endpoints
│   │   │   ├── auth.py
│   │   │   ├── markets.py
│   │   │   ├── bets.py
│   │   │   ├── users.py
│   │   │   ├── missions.py
│   │   │   ├── leaderboard.py
│   │   │   ├── wallet.py       # В разработке
│   │   │   ├── admin.py
│   │   │   ├── support.py
│   │   │   └── scheduler.py
│   │   ├── core/               # Config, Database, Security
│   │   ├── models/             # 12 SQLAlchemy моделей
│   │   └── services/           # Business logic
│   ├── alembic/                # Database migrations
│   ├── telegram_worker.py      # Notification queue processor
│   ├── broadcast_scheduler.py  # Scheduled broadcasts processor
│   └── seed_data.py            # Test data (20 markets, 19 missions)
│
├── bot/                        # Telegram Bot
│   ├── main.py                 # aiogram bot
│   └── handlers/               # /start, /support, etc.
│
├── webapp/                     # Mini App (порт 8001)
│   ├── main.py                 # Quart app
│   ├── templates/              # Markets, Profile, Missions, Leaderboard
│   └── api_client.py           # Async Backend API client
│
├── admin/                      # Admin Panel (порт 8002)
│   ├── main.py                 # Admin interface
│   └── templates/              # Dashboard, Markets, Users, Broadcast, Support
│
├── landing/                    # Landing Page (порт 8003)
│   └── templates/              # Marketing site
│
├── docker-compose.yml          # Development setup
├── .env                        # Environment variables
├── Makefile                    # Development commands
├── CLAUDE.md                   # Этот файл (главная документация)
├── CONTEXT.md                  # Текущий статус, задачи, детали
└── README.md                   # English documentation
```

---

## Основные компоненты

### 1. Backend API (FastAPI)

**Порт**: 8000 | **Swagger**: http://localhost:8000/docs

#### API Endpoints (основные):

```python
# Authentication
POST   /auth/register              # Регистрация через Telegram ID
POST   /auth/token                 # JWT токен (24h)

# Markets
GET    /markets/                   # Список рынков (фильтры, поиск)
GET    /markets/{id}               # Детали рынка
GET    /markets/{id}/stats         # Статистика рынка

# Bets
POST   /bets/                      # Создать ставку (AMM odds calculation)
GET    /bets/my                    # Мои ставки
GET    /bets/{id}                  # Детали ставки

# Users
GET    /users/me                   # Мой профиль
GET    /users/me/stats             # Моя статистика

# Missions (19 types)
GET    /missions/                  # Список миссий
POST   /missions/{id}/claim        # Получить награду

# Leaderboard
GET    /leaderboard/               # Топ пользователей (profit, win_rate, win_streak, total_wins)

# Admin - Markets
POST   /admin/markets              # Создать рынок
POST   /admin/markets/{id}/resolve # Разрешить рынок (YES/NO/CANCELLED)
PATCH  /admin/markets/{id}         # Обновить рынок
DELETE /admin/markets/{id}         # Удалить рынок

# Admin - Users
GET    /admin/users                # Список пользователей
PATCH  /admin/users/{id}           # Обновить пользователя
POST   /admin/users/{id}/ban       # Забанить
POST   /admin/users/{id}/unban     # Разбанить

# Admin - Broadcast
POST   /admin/broadcast                     # Массовая рассылка (немедленная)
POST   /admin/broadcast/schedule            # Запланированная рассылка (NEW)
GET    /admin/broadcast/scheduled           # Список запланированных (NEW)
DELETE /admin/broadcast/scheduled/{id}      # Отменить запланированную (NEW)

# Admin - Stats
GET    /admin/stats                # Статистика платформы

# Support
POST   /support/tickets            # Создать тикет
GET    /support/tickets            # Мои тикеты
POST   /support/tickets/{id}/messages # Отправить сообщение
```

**Детали см. в**: [CONTEXT.md - API Endpoints](#)

### 2. Telegram Bot (aiogram)

**Бот**: @The_Pred_Bot

```python
/start     # Приветствие + регистрация (автоматически создает 19 миссий)
/help      # Помощь
/support   # Создать тикет поддержки (FSM)
/balance   # Показать баланс
/stats     # Статистика

# WebApp button - открывает Mini App
```

### 3. Telegram Worker

**Файл**: `backend/telegram_worker.py`

- Обработка очереди уведомлений (telegram_notifications_queue)
- Rate limiting: 30 msg/sec (Telegram API limit)
- Batch processing (asyncio.gather)
- Error handling (temporary vs permanent failures)
- Retry logic (до 5 попыток)
- Photo support (send_photo with caption)

**Deployment**: PM2 process `telegram-worker`

### 4. Broadcast Scheduler

**Файл**: `backend/broadcast_scheduler.py`

- Автоматическая проверка scheduled broadcasts каждые 60 секунд
- Обработка PENDING broadcasts по времени
- Создание уведомлений через TelegramQueueService
- Поддержка target: all или specific user
- Статусы: PENDING → PROCESSING → COMPLETED

**Deployment**: PM2 process `broadcast-scheduler`

### 5. Mini App (Quart)

**URL**: https://thepred.tech | **Port**: 8001

**Страницы**:
- `/` - Список рынков (фильтры, поиск, сортировка)
- `/market/<id>` - Детали рынка + betting interface
- `/profile` - Профиль пользователя + bet history
- `/missions` - 19 миссий + claim rewards
- `/leaderboard` - Топ пользователей (4 типа сортировки)
- `/support` - Support tickets (в разработке UI)

### 6. Admin Panel (Quart)

**URL**: https://admin.thepred.tech (internal) | **Port**: 8002

**Разделы**:
- **Dashboard** - Статистика (users, markets, bets, volume) + Chart.js графики
- **Markets** - CRUD, resolve (YES/NO/CANCELLED), promote
- **Users** - Управление пользователями, ban/unban, edit balance
- **Broadcast** - Rich editor, emoji picker, image upload, **scheduled broadcasts**
- **Support** - Ticket management, replies

**Broadcast Features** (NEW):
- Rich text editor (Bold, Italic, Code, Links, Lists)
- 32 emoji picker
- Image upload (до 5MB) → S3
- Character counter (1000 с изображением, 4096 без)
- Parse mode: HTML / Markdown
- Target: all users / specific telegram_id
- **DateTime picker для scheduled broadcasts** (UTC + Moscow time preview)
- **Real-time clock** (UTC + Moscow)
- **Validation**: min 5 minutes from now
- **Scheduled broadcasts table** (status, time, cancel button)

### 7. Landing Page (Quart)

**URL**: https://landing.thepred.tech | **Port**: 8003

- Hero section
- How it works
- Features
- Gamification preview
- Social proof
- SEO optimized

---

## База данных

### PostgreSQL 15 (12 таблиц)

```sql
1.  users                          # Пользователи (balance, rank, stats, ban)
2.  markets                        # Рынки (title, category, pool, status)
3.  bets                          # Ставки (user, market, amount, odds, status)
4.  missions                      # Миссии (19 типов)
5.  user_missions                 # Прогресс миссий пользователя
6.  transactions                  # История транзакций
7.  wallet_addresses              # TON кошельки (в разработке)
8.  support_tickets               # Тикеты поддержки
9.  support_messages              # Сообщения в тикетах
10. telegram_notifications_queue  # Очередь уведомлений
11. leaderboard_snapshots         # Снимки лидерборда (опционально)
12. scheduled_broadcasts          # Запланированные рассылки (NEW)
```

**Детальные схемы см. в**: [CONTEXT.md - Database Schema](#)

### Миграции (Alembic)

```bash
# Применить миграции
cd backend
alembic upgrade head

# Создать новую миграцию
alembic revision -m "Description"

# История миграций
alembic history

# Текущая версия
alembic current
```

---

## Запуск проекта

### Development (Docker Compose)

```bash
# 1. Клонировать репозиторий
cd ThePred

# 2. Создать .env
cp .env.example .env
# Отредактировать .env с реальными значениями

# 3. Запустить все сервисы
make up
# или
docker-compose up -d

# 4. Применить миграции
make db-migrate
# или
docker exec -it thepredmain-backend-1 alembic upgrade head

# 5. Загрузить тестовые данные (опционально)
docker exec -it thepredmain-backend-1 python seed_data.py

# 6. Проверить статус
make ps
make logs

# Доступные URL:
# Backend API: http://localhost:8000/docs
# Mini App:    http://localhost:8001
# Admin Panel: http://localhost:8002
# Landing:     http://localhost:8003
```

### Production (PM2)

```bash
# 1. Установить зависимости
cd /home/ThePredMain

# Создать venv для каждого сервиса
cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd ../bot && pip install -r requirements.txt
cd ../webapp && pip install -r requirements.txt
cd ../admin && pip install -r requirements.txt
cd ../landing && pip install -r requirements.txt

# 2. Применить миграции
cd /home/ThePredMain/backend
source venv/bin/activate
POSTGRES_HOST=localhost alembic upgrade head

# 3. Запустить через PM2
pm2 start ecosystem.config.js

# 4. Проверить статус
pm2 status
pm2 logs --lines 50

# 5. Сохранить PM2 config
pm2 save
pm2 startup

# Процессы:
# - backend (FastAPI:8000)
# - bot (aiogram)
# - telegram-worker (notification queue)
# - broadcast-scheduler (scheduled broadcasts)
# - webapp (Quart:8001)
# - admin (Quart:8002)
# - landing (Quart:8003)
```

---

## Разработка

### Makefile команды

```bash
# Основные
make help          # Показать все команды
make up            # Запустить все сервисы
make down          # Остановить все сервисы
make restart       # Перезапустить все
make logs          # Логи всех сервисов
make ps            # Статус контейнеров

# Логи отдельных сервисов
make logs-backend
make logs-bot
make logs-webapp

# Shell доступ
make backend-shell # Войти в backend контейнер
make db-shell      # PostgreSQL shell

# База данных
make db-migrate    # Применить миграции
make db-reset      # Сбросить БД (ОПАСНО!)
make backup        # Создать backup
```

### Environment Variables (.env)

```env
# Database
POSTGRES_DB=thepred
POSTGRES_USER=thepred
POSTGRES_PASSWORD=SUPER_STRONG_PASSWORD
POSTGRES_HOST=localhost  # или postgres для Docker

# JWT
JWT_SECRET=YOUR_SUPER_SECRET_JWT_KEY_32_CHARS
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# Telegram
BOT_TOKEN=your_bot_token_here
BOT_USERNAME=The_Pred_Bot

# WebApp
WEBAPP_URL=https://thepred.tech
WEBAPP_SECRET_KEY=RANDOM_32_CHARS

# MinIO S3
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=admin
S3_SECRET_KEY=your_password
S3_BUCKET=thepred-events
S3_PUBLIC_URL=https://thepred.store

# API
API_URL=http://localhost:8000

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Git Workflow

```bash
# Проверить статус
git status

# Добавить изменения
git add .

# Коммит (с Claude signature)
git commit -m "Description

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push
git push origin main

# Pull последние изменения
git pull origin main
```

### Debugging

```bash
# Backend API - проверить endpoint
curl http://localhost:8000/docs

# Database - проверить очередь уведомлений
docker exec -it thepredmain-postgres-1 psql -U thepred -d thepred \
  -c "SELECT COUNT(*) FROM telegram_notifications_queue WHERE status = 'PENDING';"

# Telegram Worker - логи
pm2 logs telegram-worker --lines 100

# Broadcast Scheduler - логи
pm2 logs broadcast-scheduler --lines 100

# PM2 статус всех процессов
pm2 status

# PM2 мониторинг
pm2 monit
```

---

## Production Deployment

### 1. Server Requirements
- Ubuntu 22.04 LTS
- 2 CPU cores minimum
- 4 GB RAM minimum
- 20 GB SSD storage
- Domain с SSL

### 2. Initial Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Install Node.js + PM2
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2

# Install PostgreSQL client
sudo apt install postgresql-client -y

# Clone project
git clone https://github.com/Mobiss11/ThePredMain.git
cd ThePredMain
```

### 3. Configure Environment

```bash
# Create production .env
cp .env.example .env
nano .env

# Set production values:
# - Strong passwords
# - Production URLs (https://thepred.tech)
# - Real BOT_TOKEN
# - Production S3_PUBLIC_URL
# - DEBUG=false
```

### 4. Database & Migrations

```bash
# Start PostgreSQL via Docker
docker-compose up -d postgres

# Run migrations
cd backend
source venv/bin/activate
POSTGRES_HOST=localhost alembic upgrade head

# Seed data (optional)
POSTGRES_HOST=localhost python seed_data.py
```

### 5. Nginx Configuration

```bash
sudo apt install nginx -y

# Create config
sudo nano /etc/nginx/sites-available/thepred
```

**Nginx config example**:
```nginx
server {
    listen 80;
    server_name thepred.tech www.thepred.tech;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
    }
}

server {
    listen 80;
    server_name admin.thepred.tech;
    location / {
        proxy_pass http://localhost:8002;
    }
}

server {
    listen 80;
    server_name thepred.store;
    location / {
        proxy_pass http://localhost:9000;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/thepred /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. SSL Certificates

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d thepred.tech -d www.thepred.tech -d admin.thepred.tech -d thepred.store
```

### 7. Start Services (PM2)

```bash
# Start all services
pm2 start ecosystem.config.js

# Check status
pm2 status

# Save config
pm2 save

# Enable on startup
pm2 startup
```

### 8. Monitoring

```bash
# PM2 monitoring
pm2 monit

# Logs
pm2 logs
pm2 logs backend
pm2 logs telegram-worker
pm2 logs broadcast-scheduler

# Restart
pm2 restart all
```

### 9. Database Backups

```bash
# Create backup script
cat > /home/ThePredMain/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec -it thepredmain-postgres-1 pg_dump -U thepred thepred > /home/ThePredMain/backups/backup_$DATE.sql
find /home/ThePredMain/backups -name "backup_*.sql" -mtime +7 -delete
EOF

chmod +x /home/ThePredMain/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /home/ThePredMain/backup.sh
```

### 10. Updates

```bash
# Pull latest changes
cd /home/ThePredMain
git pull origin main

# Run migrations
cd backend
source venv/bin/activate
alembic upgrade head

# Restart services
pm2 restart all

# Check logs
pm2 logs --lines 50
```

---

## Что готово / Не готово

### ✅ Готово (98%)

**Backend API** - 100%
- 40+ endpoints (auth, markets, bets, users, missions, leaderboard, admin, support)
- JWT authentication
- AMM odds calculation
- Market resolution logic
- 19 missions system
- Rank system (Bronze → Grandmaster)
- Ban system
- Notification queue
- Broadcast система (text + images)
- **Scheduled broadcasts** (datetime picker, auto-send)

**Telegram Worker** - 100%
- Queue processing (30 msg/sec)
- Error handling + retry logic
- Photo support

**Broadcast Scheduler** - 100%
- Auto-check every 60 seconds
- PENDING → PROCESSING → COMPLETED

**Telegram Bot** - 100%
- /start, /support, WebApp integration

**Mini App** - 95%
- Markets, Profile, Missions, Leaderboard
- Support tickets UI (в разработке)

**Admin Panel** - 100%
- Dashboard, Markets, Users, **Broadcast**, Support
- Rich editor, emoji picker, image upload
- **Scheduled broadcasts table**
- **DateTime picker (UTC + Moscow preview)**

**Landing Page** - 100%
- Marketing site

**Database** - 100%
- 12 таблиц
- Миграции
- Seed data (20 markets, 19 missions)

**Production** - 100%
- PM2 deployment
- Nginx reverse proxy
- SSL certificates
- Database backups

### ❌ Не готово (2%)

**TON Wallet Integration** - 0%
- TON Connect SDK
- Deposit/Withdraw UI
- TON blockchain API
- Конвертация TON ↔ PRED

**Support Tickets UI** - 50%
- Mini App UI для пользователей
- Push уведомления

**Testing** - 0%
- Unit tests
- Integration tests
- E2E tests

**Monitoring** - 20%
- Sentry (error tracking)
- Grafana + Prometheus
- Alerts

---

## Заключение

**ThePred** - полнофункциональная платформа prediction markets с Telegram интеграцией.

### Текущий статус: 98% Complete ✅

**Следующие шаги**:
1. TON Wallet Integration (Приоритет 1)
2. Testing (Приоритет 1)
3. Support Tickets UI (Приоритет 2)
4. Monitoring (Приоритет 2)

### Быстрые команды

```bash
# Development
make up            # Запустить все
make logs          # Логи
make db-migrate    # Миграции

# Production
pm2 status         # Статус всех процессов
pm2 logs --lines 50 # Логи
pm2 restart all    # Перезапуск

# Git
git status
git add .
git commit -m "Description"
git push origin main
```

### Важные ссылки

- **Main App**: https://thepred.tech
- **Admin Panel**: https://admin.thepred.tech
- **Bot**: @The_Pred_Bot
- **GitHub**: https://github.com/Mobiss11/ThePredMain
- **Backend API**: http://localhost:8000/docs

### Контакты

- **CONTEXT.md** - текущий статус, задачи, детали
- **TODO.md** - task tracker
- **README.md** - English documentation

---

**Последнее обновление**: 10 ноября 2025
**Версия**: 1.4
**Автор**: ThePred Team
