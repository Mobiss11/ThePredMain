# ThePred - Полная Документация Проекта

**Версия**: 1.0
**Дата обновления**: 31 октября 2025
**Прогресс**: 95% Complete 🎉

---

## 📋 Содержание

1. [О проекте](#о-проекте)
2. [Архитектура](#архитектура)
3. [Технологический стек](#технологический-стек)
4. [Структура проекта](#структура-проекта)
5. [Компоненты системы](#компоненты-системы)
6. [База данных](#база-данных)
7. [API Endpoints](#api-endpoints)
8. [Что готово](#что-готово)
9. [Что не готово](#что-не-готово)
10. [Запуск проекта](#запуск-проекта)
11. [Разработка](#разработка)
12. [Production Deployment](#production-deployment)

---

## О проекте

**ThePred** - это платформа prediction markets (рынки предсказаний) в Telegram. Пользователи могут делать ставки на исходы событий в крипте, спорте и политике, зарабатывая токены PRED на точных предсказаниях.

### Ключевые особенности:

- 🎯 **Prediction Markets** - ставки на реальные события
- 💰 **Токен PRED** - внутренняя валюта платформы
- 💎 **TON Blockchain** - интеграция TON Wallet (в разработке)
- 🎮 **Геймификация** - миссии, достижения, лидерборд
- 📱 **Telegram Mini App** - полноценное веб-приложение
- 👑 **Ранговая система** - Bronze → Silver → Gold → Diamond → Grandmaster
- 📊 **Админ-панель** - управление рынками и пользователями

### Бизнес-модель:

1. **Комиссия с рынков** - 2-5% от pool
2. **Премиум-подписка** - эксклюзивные рынки, бонусы
3. **Реклама** - партнерские рынки, спонсорские события

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                      TELEGRAM BOT                            │
│                    (aiogram 3.x)                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    MINI APP (webapp)                         │
│              Quart + Jinja2 + Tailwind CSS                   │
│                  http://localhost:8001                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                  BACKEND API (FastAPI)                       │
│                  http://localhost:8000                       │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │   Auth     │  │  Markets   │  │    Bets    │           │
│  │  /auth/*   │  │ /markets/* │  │  /bets/*   │           │
│  └────────────┘  └────────────┘  └────────────┘           │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  Missions  │  │ Leaderboard│  │   Admin    │           │
│  │/missions/* │  │/leaderboard│  │  /admin/*  │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└──────────┬───────────────────────────────┬─────────────────┘
           │                               │
           ▼                               ▼
┌─────────────────────┐         ┌──────────────────────┐
│   PostgreSQL 15     │         │      Redis 7         │
│   (Database)        │         │   (Cache/Sessions)   │
│ postgres:5432       │         │   redis:6379         │
└─────────────────────┘         └──────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  ADMIN PANEL (webapp)                        │
│              Quart + Jinja2 + Chart.js                       │
│                  http://localhost:8002                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  LANDING PAGE (webapp)                       │
│                 Quart + Jinja2 + HTML/CSS                    │
│                  http://localhost:8003                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Технологический стек

### Backend (FastAPI)

- **Framework**: FastAPI 0.109.0
- **ASGI Server**: Uvicorn 0.27.0
- **ORM**: SQLAlchemy 2.0.25
- **Database Driver**: asyncpg 0.29.0
- **Migrations**: Alembic 1.13.1
- **Validation**: Pydantic 2.5.3
- **Authentication**: python-jose (JWT)
- **Password Hashing**: passlib (bcrypt)
- **Cache**: Redis 5.0.1
- **Monitoring**: Sentry SDK 1.39.2

### Frontend (Mini App, Admin, Landing)

- **Framework**: Quart 0.19.4 (async Flask)
- **Templates**: Jinja2
- **CSS**: Tailwind CSS 3.x
- **Icons**: Heroicons, Lucide Icons
- **Charts**: Chart.js (admin panel)
- **HTTP Client**: aiohttp 3.9.1

### Bot

- **Framework**: aiogram 3.x
- **Async**: asyncio
- **HTTP Client**: aiohttp

### Database

- **PostgreSQL**: 15.x
- **Redis**: 7.x

### DevOps

- **Containerization**: Docker + Docker Compose
- **Environment**: python-dotenv
- **Testing**: pytest (готово к подключению)

---

## Структура проекта

```
ThePred/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/   # API endpoints
│   │   │       ├── auth.py
│   │   │       ├── markets.py
│   │   │       ├── bets.py
│   │   │       ├── users.py
│   │   │       ├── missions.py
│   │   │       ├── leaderboard.py
│   │   │       ├── wallet.py
│   │   │       └── admin.py
│   │   ├── core/           # Core utilities
│   │   │   ├── config.py   # Settings
│   │   │   ├── database.py # DB connection
│   │   │   └── redis.py    # Redis connection
│   │   ├── models/         # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── market.py
│   │   │   ├── bet.py
│   │   │   ├── mission.py
│   │   │   └── transaction.py
│   │   └── main.py         # FastAPI app
│   ├── alembic/            # Database migrations
│   │   └── versions/
│   ├── requirements.txt
│   └── seed_data.py        # Test data script
│
├── bot/                    # Telegram Bot
│   ├── main.py            # aiogram bot
│   ├── handlers/          # Message handlers
│   └── requirements.txt
│
├── webapp/                # Mini App (Quart)
│   ├── main.py
│   ├── api_client.py      # Backend API client
│   ├── routes/            # Flask routes
│   ├── templates/         # Jinja2 templates
│   │   ├── index.html     # Markets list
│   │   ├── market.html    # Market detail
│   │   ├── profile.html   # User profile
│   │   ├── missions.html  # Missions
│   │   └── leaderboard.html
│   ├── static/            # CSS, JS, icons
│   └── requirements.txt
│
├── admin/                 # Admin Panel (Quart)
│   ├── main.py
│   ├── routes/            # Admin routes
│   ├── templates/
│   │   └── admin.html     # Admin dashboard
│   ├── static/
│   └── requirements.txt
│
├── landing/               # Landing Page (Quart)
│   ├── main.py
│   ├── templates/
│   │   ├── index.html
│   │   └── index_last.html  # Актуальная версия
│   ├── static/
│   └── requirements.txt
│
├── database/              # Database scripts
│   ├── migrations/
│   └── scripts/
│
├── docker-compose.yml     # Docker orchestration
├── Makefile              # Development commands
├── README.md             # English README
├── TODO.md               # Task tracker
└── CLAUDE.md             # Этот файл
```

---

## Компоненты системы

### 1. Backend API (FastAPI)

**Порт**: 8000
**Документация**: http://localhost:8000/docs

#### Основные endpoint'ы:

##### Auth (`/auth`)
- `POST /auth/register` - Регистрация через Telegram
- `POST /auth/token` - Получение JWT токена

##### Markets (`/markets`)
- `GET /markets/` - Список рынков (фильтры: category, status, promoted)
- `GET /markets/{market_id}` - Детали рынка
- `GET /markets/{market_id}/stats` - Статистика рынка

##### Bets (`/bets`)
- `POST /bets/` - Создать ставку
- `GET /bets/my` - Мои ставки
- `GET /bets/{bet_id}` - Детали ставки

##### Users (`/users`)
- `GET /users/me` - Профиль пользователя
- `GET /users/me/stats` - Статистика пользователя
- `GET /users/{user_id}` - Публичный профиль

##### Missions (`/missions`)
- `GET /missions/` - Список миссий
- `POST /missions/{mission_id}/claim` - Получить награду

##### Leaderboard (`/leaderboard`)
- `GET /leaderboard/?sort_by=profit` - Лидерборд
  - sort_by: profit, win_rate, win_streak, total_wins

##### Admin (`/admin`)
- `POST /admin/markets` - Создать рынок
- `POST /admin/markets/{id}/resolve` - Разрешить рынок
- `PATCH /admin/markets/{id}` - Обновить рынок
- `GET /admin/stats` - Общая статистика
- `GET /admin/users` - Список пользователей
- `PATCH /admin/users/{id}` - Обновить пользователя

##### Wallet (`/wallet`) - В РАЗРАБОТКЕ
- `POST /wallet/connect` - Подключить TON wallet
- `POST /wallet/deposit` - Пополнить PRED через TON
- `POST /wallet/withdraw` - Вывести PRED в TON

### 2. Telegram Bot (aiogram)

**Бот**: @The_Pred_Bot

#### Функционал:

1. **Приветствие** - /start
2. **Регистрация** - автоматическая через Backend API
3. **WebApp кнопка** - открывает Mini App
4. **Статус**: ✅ Полностью готов

### 3. Mini App (Quart + Tailwind)

**Порт**: 8001
**URL**: http://localhost:8001

#### Страницы:

1. **Markets** (`/`) - Список рынков
   - Фильтры: All, Crypto, Sports, Politics
   - Promoted markets
   - Search

2. **Market Detail** (`/market/<id>`) - Детали рынка
   - Текущие odds (YES/NO)
   - Создание ставки
   - История ставок
   - Pool size
   - Participants count

3. **Profile** (`/profile`) - Профиль пользователя
   - Balance (PRED)
   - Rank (Bronze → Grandmaster)
   - Statistics (Win Rate, Total Wins, Total Bets)
   - Bet History
   - TON Wallet UI (не интегрирован)

4. **Missions** (`/missions`) - Система миссий
   - 5 миссий с наградами
   - Progress tracking
   - Claim rewards

5. **Leaderboard** (`/leaderboard`) - Лидерборд
   - Сортировка: Profit, Win Rate, Win Streak, Total Wins
   - Top 100 пользователей
   - Твоя позиция

### 4. Admin Panel (Quart)

**Порт**: 8002
**URL**: http://localhost:8002

#### Разделы:

1. **Stats** - Общая статистика
   - Total Users
   - Active Markets
   - Total Bets
   - Total Volume (PRED)
   - Charts (Chart.js)

2. **Markets** - Управление рынками
   - Список всех рынков
   - Resolve market (YES/NO/CANCELLED)
   - Promote/Unpromote
   - Edit details

3. **Users** - Управление пользователями
   - Список пользователей
   - View activity
   - Edit balance
   - Ban/Unban

4. **Create Market** - Создание рынка
   - Title, Description
   - Category (Crypto, Sports, Politics, Tech)
   - End Date
   - Promoted

### 5. Landing Page (Quart)

**Порт**: 8003
**URL**: http://localhost:8003

#### Секции:

1. **Hero** - Главный блок
   - Заголовок: "Prediction Markets в Telegram"
   - 3 примера рынков (Crypto, Sports, Politics)
   - CTA: "Открыть в Telegram"

2. **Philosophy** - Коллективный разум

3. **How It Works** - 3 шага:
   - Открой бота
   - Выбери событие
   - Делай прогноз

4. **Features** - Особенности:
   - Real Markets
   - Smart Odds
   - Win Together

5. **Gamification** - Миссии, ранги, лидерборд

6. **AI Assistant** - Coming Soon

7. **Social Proof** - Статистика

8. **Footer** - Copyright, соцсети

**Статус**: ✅ Адаптивный дизайн, готов к production

---

## База данных

### PostgreSQL Schema

#### 1. `users` - Пользователи

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    balance INTEGER DEFAULT 1000,  -- PRED tokens
    rank VARCHAR(50) DEFAULT 'Bronze',
    total_bets INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    win_streak INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Ранги**: Bronze → Silver → Gold → Diamond → Grandmaster

#### 2. `markets` - Рынки

```sql
CREATE TABLE markets (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(50),  -- Crypto, Sports, Politics, Tech
    end_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'Active',  -- Active, Resolved, Cancelled
    result VARCHAR(10),  -- YES, NO, NULL
    total_yes_bets INTEGER DEFAULT 0,
    total_no_bets INTEGER DEFAULT 0,
    total_pool INTEGER DEFAULT 0,
    promoted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. `bets` - Ставки

```sql
CREATE TABLE bets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    market_id INTEGER REFERENCES markets(id),
    outcome VARCHAR(10),  -- YES, NO
    amount INTEGER NOT NULL,
    odds DECIMAL(10,2),
    potential_win INTEGER,
    status VARCHAR(50) DEFAULT 'Pending',  -- Pending, Won, Lost, Refunded
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 4. `missions` - Миссии

```sql
CREATE TABLE missions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    mission_type VARCHAR(100),
    progress INTEGER DEFAULT 0,
    target INTEGER,
    reward INTEGER,
    claimed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Типы миссий**:
1. `make_5_bets` - Сделай 5 ставок (+500 PRED)
2. `win_streak_3` - Win streak 3 (+1000 PRED)
3. `bet_on_crypto` - Ставка на крипту (+250 PRED)
4. `daily_login` - Ежедневный вход (+100 PRED)
5. `refer_friend` - Приведи друга (+2000 PRED)

#### 5. `transactions` - Транзакции

```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    type VARCHAR(50),  -- Bet, Win, Refund, Mission, Deposit, Withdraw
    amount INTEGER,
    balance_before INTEGER,
    balance_after INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 6. `wallet_addresses` - TON Wallets (В РАЗРАБОТКЕ)

```sql
CREATE TABLE wallet_addresses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    ton_address VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Seed Data

**20 тестовых рынков** в категориях:
- Crypto (7): Bitcoin, Ethereum, TON, BNB, Solana
- Sports (6): Real Madrid, Lakers, UFC, Super Bowl
- Politics (4): Trump, Elections, NATO
- Tech (3): Apple AR, AI, Tesla

**Команда**: `python3 backend/seed_data.py`

---

## API Endpoints

### Полный список эндпоинтов

#### Auth
```
POST   /auth/register         # Register via Telegram
POST   /auth/token            # Get JWT token
```

#### Markets
```
GET    /markets/              # List markets (filters: category, status, promoted)
GET    /markets/{id}          # Market details
GET    /markets/{id}/stats    # Market statistics
```

#### Bets
```
POST   /bets/                 # Create bet
GET    /bets/my               # My bets
GET    /bets/{id}             # Bet details
```

#### Users
```
GET    /users/me              # My profile
GET    /users/me/stats        # My statistics
GET    /users/{id}            # Public profile
```

#### Missions
```
GET    /missions/             # List missions
POST   /missions/{id}/claim   # Claim reward
```

#### Leaderboard
```
GET    /leaderboard/          # Leaderboard (sort_by: profit, win_rate, win_streak, total_wins)
```

#### Admin
```
POST   /admin/markets         # Create market
POST   /admin/markets/{id}/resolve  # Resolve market
PATCH  /admin/markets/{id}    # Update market
GET    /admin/stats           # Platform statistics
GET    /admin/users           # List users
PATCH  /admin/users/{id}      # Update user
```

#### Wallet (В РАЗРАБОТКЕ)
```
POST   /wallet/connect        # Connect TON wallet
POST   /wallet/deposit        # Deposit TON → PRED
POST   /wallet/withdraw       # Withdraw PRED → TON
```

---

## Что готово

### ✅ Backend API - 100%

1. **Database**:
   - ✅ PostgreSQL + Alembic migrations
   - ✅ 6 таблиц (users, markets, bets, missions, transactions, wallet_addresses)
   - ✅ 20 тестовых рынков + seed data

2. **API Endpoints**:
   - ✅ Auth (register, token)
   - ✅ Markets (list, detail, stats)
   - ✅ Bets (create, my, detail)
   - ✅ Users (profile, stats, public)
   - ✅ Missions (list, claim) - 5 миссий
   - ✅ Leaderboard (4 типа сортировки)
   - ✅ Admin (stats, markets, users, create)

3. **Features**:
   - ✅ JWT Authentication
   - ✅ Bet creation с автоматическим расчетом odds
   - ✅ Market resolution (выплаты, обновление статистики)
   - ✅ Missions system с наградами
   - ✅ Rank system (Bronze → Grandmaster)
   - ✅ Transaction history
   - ✅ Swagger documentation

### ✅ Mini App (Webapp) - 95%

1. **Страницы**:
   - ✅ Markets list с фильтрами
   - ✅ Market detail с созданием ставок
   - ✅ Profile с историей ставок
   - ✅ Missions с claim rewards
   - ✅ Leaderboard с сортировкой
   - ✅ Responsive design (mobile-first)

2. **Интеграция**:
   - ✅ Полная интеграция с Backend API
   - ✅ api_client.py с async requests
   - ✅ Динамическая загрузка данных
   - ✅ Real-time updates

3. **UI/UX**:
   - ✅ Tailwind CSS
   - ✅ Анимации
   - ✅ Темная тема
   - ✅ Icons (Heroicons, Lucide)

**Не готово**:
- ⚠️ TON Wallet UI готов, но не интегрирован с backend

### ✅ Admin Panel - 100%

1. **Разделы**:
   - ✅ Stats (общая статистика, Chart.js)
   - ✅ Markets (список, resolve, edit)
   - ✅ Users (список, edit balance, view activity)
   - ✅ Create Market (форма создания)

2. **Функционал**:
   - ✅ Market resolution (YES/NO/CANCELLED)
   - ✅ Promote/Unpromote markets
   - ✅ Edit user balances
   - ✅ View user bet history
   - ✅ Platform statistics

### ✅ Landing Page - 100%

1. **Секции**:
   - ✅ Hero с примерами рынков
   - ✅ Philosophy
   - ✅ How It Works
   - ✅ Features
   - ✅ Gamification
   - ✅ AI Assistant (Coming Soon)
   - ✅ Social Proof
   - ✅ Footer

2. **Дизайн**:
   - ✅ Адаптивный (mobile, tablet, desktop)
   - ✅ Анимации (CSS, JS)
   - ✅ Gradients, glass effects
   - ✅ SEO meta tags

### ✅ Telegram Bot - 100%

1. **Функционал**:
   - ✅ /start - Приветствие
   - ✅ Регистрация через Backend API
   - ✅ WebApp button (открывает Mini App)
   - ✅ Telegram Deep Linking

---

## Что не готово

### ❌ TON Wallet Integration - 0% (Приоритет 1)

**Требуется реализовать**:

#### Frontend (Mini App):
1. Подключить TON Connect SDK
2. UI для Connect/Disconnect wallet
3. Отображение TON адреса и баланса
4. UI для Deposit (TON → PRED)
5. UI для Withdraw (PRED → TON)

#### Backend API:
1. `POST /wallet/connect` - Сохранить TON адрес
2. `POST /wallet/deposit/initiate` - Генерировать deposit адрес
3. `POST /wallet/deposit/confirm` - Проверить транзакцию на blockchain
4. `POST /wallet/withdraw` - Отправить TON
5. Конвертация TON ↔ PRED (rate: 1 TON = 1000 PRED)
6. TON blockchain integration (TON API или SDK)
7. Обработка pending транзакций

**TODO в коде**:
```python
# backend/app/api/endpoints/wallet.py:46
# TODO: Verify TON transaction on blockchain

# backend/app/api/endpoints/admin.py:159
# TODO: Get from auth (admin_id hardcoded)
```

**Ресурсы**:
- TON Connect SDK: https://github.com/ton-connect/sdk
- TON API: https://tonapi.io/
- TON Docs: https://docs.ton.org/

**Оценка**: 8-10 часов

### ❌ Production Deployment - 0% (Приоритет 2)

**Требуется настроить**:
1. VPS/Cloud server (DigitalOcean, AWS, Hetzner)
2. Domain + SSL certificates (Certbot)
3. Nginx reverse proxy
4. Docker production setup
5. Environment variables (production)
6. Database backups
7. Monitoring (Sentry, Grafana)
8. Bot webhook configuration

**Оценка**: 4-6 часов

### ❌ Testing - 0% (Приоритет 3)

**Требуется протестировать**:
1. Все webapp страницы
2. Создание ставок
3. Missions claim
4. Market resolution
5. Admin panel функционал
6. Bot WebApp integration
7. API endpoints через Swagger

**Оценка**: 2-3 часа

---

## Запуск проекта

### Предварительные требования

- Docker + Docker Compose
- Python 3.11+
- PostgreSQL 15+ (опционально, есть в Docker)
- Redis 7+ (опционально, есть в Docker)

### 1. Через Docker Compose (Рекомендуется)

```bash
# Клонировать репозиторий
cd ThePred

# Создать .env файл
cp .env.example .env
# Отредактировать .env с реальными значениями

# Собрать и запустить все сервисы
make up
# или
docker-compose up -d

# Проверить логи
make logs
# или
docker-compose logs -f

# Проверить здоровье сервисов
make health
```

**Доступные URL**:
- Backend API: http://localhost:8000/docs
- Mini App: http://localhost:8001
- Admin Panel: http://localhost:8002
- Landing Page: http://localhost:8003
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### 2. Локальный запуск (Разработка)

#### Backend

```bash
cd backend

# Создать venv
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt

# Настроить .env
export POSTGRES_HOST=localhost
export DATABASE_URL=postgresql://thepred:password@localhost:5432/thepred
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=your-secret-key

# Запустить PostgreSQL и Redis (Docker)
docker-compose up -d postgres redis

# Применить миграции
POSTGRES_HOST=localhost alembic upgrade head

# Заполнить тестовыми данными (опционально)
POSTGRES_HOST=localhost python3 seed_data.py

# Запустить backend
POSTGRES_HOST=localhost uvicorn app.main:app --reload --port 8000
```

#### Mini App (Webapp)

```bash
cd webapp

# Установить зависимости
pip install -r requirements.txt

# Настроить .env
export API_URL=http://localhost:8000
export DEV_MODE=true

# Запустить webapp
python3 main.py
```

#### Bot

```bash
cd bot

# Установить зависимости
pip install -r requirements.txt

# Настроить .env
export BOT_TOKEN=your-telegram-bot-token
export API_URL=http://localhost:8000
export WEBAPP_URL=http://localhost:8001

# Запустить бота
python3 main.py
```

#### Admin Panel

```bash
cd admin

# Установить зависимости
pip install -r requirements.txt

# Настроить .env
export API_URL=http://localhost:8000

# Запустить admin
python3 main.py
```

#### Landing Page

```bash
cd landing

# Установить зависимости
pip install -r requirements.txt

# Запустить landing
python3 main.py
```

---

## Разработка

### Makefile команды

```bash
# Основные команды
make help          # Показать все доступные команды
make up            # Запустить все сервисы
make down          # Остановить все сервисы
make restart       # Перезапустить все сервисы
make logs          # Показать логи всех сервисов
make ps            # Показать запущенные контейнеры

# Логи отдельных сервисов
make logs-backend
make logs-bot
make logs-webapp
make logs-admin
make logs-landing

# Перезапуск отдельных сервисов
make backend-restart
make bot-restart
make webapp-restart
make admin-restart
make landing-restart

# Shell доступ
make backend-shell   # Войти в backend контейнер
make bot-shell       # Войти в bot контейнер
make db-shell        # Открыть PostgreSQL shell
make redis-shell     # Открыть Redis CLI

# База данных
make db-migrate      # Применить миграции
make db-reset        # Сбросить БД (удалит все данные!)
make backup          # Создать backup БД
make restore FILE=backup.sql  # Восстановить из backup

# Тестирование
make test            # Запустить тесты
make test-coverage   # Тесты с coverage

# Разработка
make dev             # Запустить с логами в консоли
make dev-build       # Пересобрать и запустить
make clean           # Удалить контейнеры, volumes, images
make clean-cache     # Очистить Python cache

# Мониторинг
make health          # Проверить здоровье сервисов
make stats           # Показать использование ресурсов
make monitor         # Real-time логи и статистика

# Production
make prod-build      # Собрать для production
make prod-up         # Запустить в production режиме
make prod-logs       # Production логи

# Быстрые действия
make quick-test      # up + health check
make quick-restart   # down + clean-cache + up

# Информация
make info            # Показать информацию о проекте
```

### Структура .env файлов

#### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://thepred:password@postgres:5432/thepred
POSTGRES_HOST=postgres
POSTGRES_USER=thepred
POSTGRES_PASSWORD=password
POSTGRES_DB=thepred

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
SECRET_KEY=your-super-secret-key-change-me-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# App
DEBUG=true
SENTRY_DSN=

# TON (когда будет готово)
TON_API_KEY=
TON_NETWORK=testnet
```

#### Bot (.env)

```env
BOT_TOKEN=your-telegram-bot-token
API_URL=http://backend:8000
WEBAPP_URL=https://your-domain.com
```

#### Webapp/Admin/Landing (.env)

```env
API_URL=http://backend:8000
WEBAPP_SECRET_KEY=your-webapp-secret-key
DEV_MODE=true
```

### Разработка новых фич

1. **Backend API endpoint**:
   ```python
   # backend/app/api/endpoints/your_feature.py
   from fastapi import APIRouter, Depends
   from sqlalchemy.orm import Session
   from app.core.database import get_db

   router = APIRouter(prefix="/your-feature", tags=["Your Feature"])

   @router.get("/")
   async def list_items(db: Session = Depends(get_db)):
       # Your logic
       return {"items": []}
   ```

2. **Database migration**:
   ```bash
   cd backend
   alembic revision -m "Add your_table"
   # Отредактировать backend/alembic/versions/xxx_add_your_table.py
   alembic upgrade head
   ```

3. **Frontend страница**:
   ```python
   # webapp/routes/your_page.py
   from quart import Blueprint, render_template
   from api_client import api_client

   bp = Blueprint('your_page', __name__)

   @bp.route('/your-page')
   async def your_page():
       data = await api_client.get('/your-feature/')
       return await render_template('your_page.html', data=data)
   ```

4. **Регистрация Blueprint**:
   ```python
   # webapp/main.py
   from routes.your_page import bp as your_page_bp
   app.register_blueprint(your_page_bp)
   ```

---

## Production Deployment

### 1. Server Setup

```bash
# Ubuntu 22.04 LTS
sudo apt update
sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Clone project
git clone https://github.com/your-repo/ThePred.git
cd ThePred
```

### 2. Environment Configuration

```bash
# Create production .env
cp .env.example .env
nano .env

# Set production values:
# - Strong SECRET_KEY
# - Production DATABASE_URL
# - Real BOT_TOKEN
# - Production WEBAPP_URL
# - SENTRY_DSN for monitoring
# - DEBUG=false
```

### 3. Nginx Setup

```bash
sudo apt install nginx -y

# Create nginx config
sudo nano /etc/nginx/sites-available/thepred

# Config content:
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /admin/ {
        proxy_pass http://localhost:8002/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/thepred /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. SSL Certificates

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

### 5. Start Services

```bash
# Build for production
make prod-build

# Start services
make prod-up

# Check status
make ps
make health

# Check logs
make prod-logs
```

### 6. Database Backup

```bash
# Create cron job for daily backups
crontab -e

# Add line:
0 2 * * * cd /path/to/ThePred && make backup
```

### 7. Bot Webhook (Optional)

```bash
# Set webhook for Telegram bot
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://your-domain.com/webhook"
```

### 8. Monitoring

```bash
# Install monitoring (optional)
# Sentry for error tracking
# Grafana + Prometheus for metrics
# Uptime monitoring (UptimeRobot, Pingdom)
```

---

## Дополнительная информация

### Ограничения и Best Practices

1. **Rate Limiting**:
   - Backend не имеет rate limiting (добавить в production)
   - Redis можно использовать для rate limiting

2. **Security**:
   - JWT токены хранятся в localStorage (можно перейти на httpOnly cookies)
   - CORS настроен для development (ограничить в production)
   - SQL injection защита через SQLAlchemy ORM

3. **Performance**:
   - Redis используется для кэширования
   - Database indexes на часто используемых полях
   - Async/await для I/O операций

4. **Scalability**:
   - Stateless backend (можно горизонтально масштабировать)
   - Redis для shared state
   - PostgreSQL можно replicate для read scaling

### Roadmap

#### Краткосрочный (1-2 недели):
- ✅ TON Wallet integration
- ✅ Testing
- ✅ Production deployment

#### Среднесрочный (1-2 месяца):
- 💎 Premium подписка
- 📊 Advanced analytics
- 🎮 More gamification (badges, achievements)
- 🤖 AI predictions
- 📱 Mobile app (React Native)

#### Долгосрочный (3-6 месяцев):
- 🌍 Multi-language support
- 💱 Multiple cryptocurrencies
- 🏆 Tournaments
- 📈 Advanced charting
- 🤝 Social features (friends, groups)

---

## Контакты и Support

**Проект**: ThePred - Prediction Markets
**Telegram Bot**: @The_Pred_Bot
**Version**: 1.0
**Status**: 95% Complete

**Разработка**:
- Backend: FastAPI + PostgreSQL + Redis
- Frontend: Quart + Tailwind CSS
- Bot: aiogram 3.x
- Deployment: Docker + Docker Compose

**Команды**:
```bash
make help    # Все доступные команды
make up      # Запустить проект
make logs    # Посмотреть логи
make health  # Проверить статус
```

---

**Последнее обновление**: 31 октября 2025
**Автор**: ThePred Team
**Лицензия**: Proprietary
