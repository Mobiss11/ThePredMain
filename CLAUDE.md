# ThePred - Полная Документация Проекта

**Версия**: 1.2
**Дата обновления**: 8 ноября 2025
**Прогресс**: 97% Complete 🎉

---

## 📋 Содержание

1. [О проекте](#о-проекте)
2. [Архитектура](#архитектура)
3. [Технологический стек](#технологический-стек)
4. [Структура проекта](#структура-проекта)
5. [Компоненты системы](#компоненты-системы)
6. [База данных](#база-данных)
7. [API Endpoints](#api-endpoints)
8. [Система очередей и уведомлений](#система-очередей-и-уведомлений)
9. [Broadcast система](#broadcast-система)
10. [Что готово](#что-готово)
11. [Что не готово](#что-не-готово)
12. [Запуск проекта](#запуск-проекта)
13. [Разработка](#разработка)
14. [Production Deployment](#production-deployment)

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
- 📢 **Broadcast система** - массовые рассылки с rate limiting
- 🎫 **Support система** - тикеты поддержки (в разработке)

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
│                 @The_Pred_Bot                                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    MINI APP (webapp)                         │
│              Quart + Jinja2 + Tailwind CSS                   │
│                  https://thepred.tech                        │
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
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │   Wallet   │  │  Support   │  │  Broadcast │           │
│  │ /wallet/*  │  │ /support/* │  │/admin/bcast│           │
│  └────────────┘  └────────────┘  └────────────┘           │
└──────────┬───────────────────────────────┬─────────────────┘
           │                               │
           ▼                               ▼
┌─────────────────────┐         ┌──────────────────────┐
│   PostgreSQL 15     │         │      Redis 7         │
│   (Database)        │         │   (Cache/Sessions)   │
│ postgres:5432       │         │   redis:6379         │
└─────────────────────┘         └──────────────────────┘
           │
           ▼
┌─────────────────────┐
│   MinIO S3          │
│  (File Storage)     │
│ https://thepred.store│
└─────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  TELEGRAM WORKER                             │
│            Notification Queue Processor                      │
│         Rate Limiting: 30 msg/sec (Telegram API)            │
└─────────────────────────────────────────────────────────────┘

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
- **ORM**: SQLAlchemy 2.0.25 (async)
- **Database Driver**: asyncpg 0.29.0
- **Migrations**: Alembic 1.13.1
- **Validation**: Pydantic 2.5.3
- **Authentication**: python-jose (JWT)
- **Password Hashing**: passlib (bcrypt)
- **Cache**: Redis 5.0.1
- **File Storage**: boto3 (S3/MinIO)
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
- **Worker**: Standalone notification processor

### Database

- **PostgreSQL**: 15.x
- **Redis**: 7.x
- **S3 Storage**: MinIO (S3-compatible)

### DevOps

- **Containerization**: Docker + Docker Compose
- **Process Manager**: PM2 (production)
- **Web Server**: Nginx (reverse proxy, production)
- **SSL**: Let's Encrypt (Certbot)
- **Environment**: python-dotenv
- **Testing**: pytest (готово к подключению)

---

## Структура проекта

```
ThePred/
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/            # API endpoints
│   │   │       ├── auth.py           # Аутентификация (register, token)
│   │   │       ├── markets.py        # Рынки (list, detail, stats)
│   │   │       ├── bets.py           # Ставки (create, my, detail)
│   │   │       ├── users.py          # Пользователи (profile, stats, ban)
│   │   │       ├── missions.py       # Миссии (list, claim, progress)
│   │   │       ├── leaderboard.py    # Лидерборд (rankings, filters)
│   │   │       ├── wallet.py         # TON кошелек (connect, deposit, withdraw)
│   │   │       ├── admin.py          # Админка (markets, users, broadcast, stats)
│   │   │       ├── support.py        # Поддержка (tickets, messages)
│   │   │       └── scheduler.py      # Планировщик (weekly rewards, cleanup)
│   │   ├── core/                     # Core utilities
│   │   │   ├── config.py             # Settings (env variables)
│   │   │   ├── database.py           # DB connection pool
│   │   │   ├── redis.py              # Redis connection
│   │   │   └── security.py           # JWT, password hashing
│   │   ├── models/                   # SQLAlchemy models
│   │   │   ├── user.py               # User (profile, balance, rank, ban)
│   │   │   ├── market.py             # Market (title, odds, pool, status)
│   │   │   ├── bet.py                # Bet (user, market, amount, outcome)
│   │   │   ├── mission.py            # Mission (type, progress, reward)
│   │   │   ├── transaction.py        # Transaction (type, amount, balance)
│   │   │   ├── wallet.py             # WalletAddress (TON address)
│   │   │   ├── support.py            # SupportTicket, SupportMessage
│   │   │   ├── telegram_notification.py  # TelegramNotification (queue)
│   │   │   └── user_mission.py       # UserMission (progress tracking)
│   │   ├── services/                 # Business logic services
│   │   │   ├── telegram_queue_service.py  # Queue management (add, get, mark)
│   │   │   ├── mission_service.py    # Mission progress tracking
│   │   │   └── market_service.py     # Market resolution logic
│   │   └── main.py                   # FastAPI app entry point
│   ├── alembic/                      # Database migrations
│   │   ├── versions/                 # Migration files
│   │   │   ├── xxx_create_tables.py
│   │   │   ├── xxx_add_ban_system.py
│   │   │   ├── xxx_add_support_tickets.py
│   │   │   ├── xxx_add_notification_queue.py
│   │   │   └── xxx_add_broadcast_type.py
│   │   └── env.py                    # Alembic config
│   ├── telegram_worker.py            # Telegram notification worker (NEW)
│   ├── requirements.txt              # Python dependencies
│   └── seed_data.py                  # Test data seeding script
│
├── bot/                              # Telegram Bot
│   ├── main.py                       # aiogram bot entry point
│   ├── handlers/                     # Message handlers
│   │   ├── start.py                  # /start command
│   │   ├── support.py                # Support tickets
│   │   └── common.py                 # Common handlers
│   ├── keyboards/                    # Telegram keyboards
│   │   └── inline.py                 # Inline keyboards
│   ├── notification_worker.py        # Alternative worker (standalone)
│   └── requirements.txt              # Bot dependencies
│
├── webapp/                           # Mini App (Quart)
│   ├── main.py                       # Quart app entry point
│   ├── api_client.py                 # Backend API client (async)
│   ├── routes/                       # Flask routes
│   │   ├── markets.py                # Markets pages
│   │   ├── profile.py                # User profile
│   │   ├── missions.py               # Missions page
│   │   ├── leaderboard.py            # Leaderboard page
│   │   └── support.py                # Support tickets
│   ├── templates/                    # Jinja2 templates
│   │   ├── base.html                 # Base template
│   │   ├── index.html                # Markets list
│   │   ├── market.html               # Market detail + betting
│   │   ├── profile.html              # User profile + stats
│   │   ├── missions.html             # Missions + claim
│   │   ├── leaderboard.html          # Rankings
│   │   └── support.html              # Support tickets
│   ├── static/                       # Static files
│   │   ├── css/                      # Custom CSS
│   │   ├── js/                       # Custom JavaScript
│   │   └── icons/                    # Icons, images
│   └── requirements.txt              # Webapp dependencies
│
├── admin/                            # Admin Panel (Quart)
│   ├── main.py                       # Quart admin app
│   ├── routes/                       # Admin routes
│   │   ├── dashboard.py              # Dashboard stats
│   │   ├── markets.py                # Market management
│   │   ├── users.py                  # User management
│   │   ├── broadcast.py              # Broadcast system
│   │   └── support.py                # Support ticket management
│   ├── templates/                    # Admin templates
│   │   ├── base.html                 # Admin base template
│   │   ├── dashboard.html            # Stats dashboard
│   │   ├── markets.html              # Markets CRUD
│   │   ├── users.html                # Users management
│   │   ├── broadcast.html            # Broadcast interface (NEW)
│   │   └── support.html              # Support tickets
│   ├── static/                       # Admin static files
│   │   ├── css/
│   │   └── js/
│   └── requirements.txt              # Admin dependencies
│
├── landing/                          # Landing Page (Quart)
│   ├── main.py                       # Landing app
│   ├── templates/
│   │   ├── index.html                # Main landing
│   │   └── index_last.html           # Latest version
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── requirements.txt
│
├── database/                         # Database scripts
│   ├── migrations/                   # Manual migrations
│   └── scripts/                      # Utility scripts
│       └── cleanup.sql               # Database cleanup
│
├── документация/                     # Documentation
│   ├── polymarket/                   # Polymarket research
│   │   ├── main.md                   # Polymarket analysis
│   │   └── example.md                # Examples
│   └── architecture/                 # Architecture docs
│
├── docker-compose.yml                # Docker orchestration (dev)
├── docker-compose.prod.yml           # Docker production config
├── Makefile                          # Development commands
├── .env                              # Environment variables
├── .env.example                      # Environment template
├── README.md                         # English README
├── TODO.md                           # Task tracker
└── CLAUDE.md                         # This file (Russian docs)
```

---

## Компоненты системы

### 1. Backend API (FastAPI)

**Порт**: 8000
**Production**: Запускается через PM2
**Документация**: http://localhost:8000/docs

#### Основные модули:

##### 1.1 Auth (`/auth`)
```python
# backend/app/api/endpoints/auth.py
POST /auth/register         # Регистрация через Telegram
POST /auth/token            # Получение JWT токена
```

**Функционал**:
- Регистрация пользователей через Telegram ID
- JWT токены (24h expiration)
- Начальный баланс: 10,000 PRED
- Автоматическое создание 19 миссий при регистрации

##### 1.2 Markets (`/markets`)
```python
# backend/app/api/endpoints/markets.py
GET  /markets/              # Список рынков (фильтры, поиск)
GET  /markets/{id}          # Детали рынка
GET  /markets/{id}/stats    # Статистика рынка
```

**Параметры фильтрации**:
- `category`: Crypto, Sports, Politics, Tech
- `status`: Active, Resolved, Cancelled
- `promoted`: true/false
- `search`: поиск по названию

**Возвращаемые данные**:
- Текущие odds (YES/NO)
- Total pool size
- Количество участников
- Ваши ставки на рынке
- История активности

##### 1.3 Bets (`/bets`)
```python
# backend/app/api/endpoints/bets.py
POST /bets/                 # Создать ставку
GET  /bets/my               # Мои ставки (фильтры)
GET  /bets/{id}             # Детали ставки
```

**Создание ставки**:
- Автоматический расчет odds на основе AMM (Automated Market Maker)
- Formula: `odds = total_pool / (outcome_pool + amount)`
- Potential win рассчитывается заранее
- Транзакция в БД (списание PRED)
- Обновление статистики пользователя

**Статусы ставки**:
- `Pending` - рынок активен
- `Won` - ставка выиграла
- `Lost` - ставка проиграла
- `Refunded` - рынок отменен

##### 1.4 Users (`/users`)
```python
# backend/app/api/endpoints/users.py
GET  /users/me              # Мой профиль
GET  /users/me/stats        # Моя статистика
GET  /users/{id}            # Публичный профиль
```

**Профиль содержит**:
- Balance (PRED, TON)
- Rank (Bronze → Grandmaster)
- Statistics (Win Rate, Total Wins, Win Streak)
- Bet history
- Referral info
- Ban status

**Ранговая система**:
- Bronze: 0-10 wins
- Silver: 11-25 wins
- Gold: 26-50 wins
- Diamond: 51-100 wins
- Grandmaster: 100+ wins

##### 1.5 Missions (`/missions`)
```python
# backend/app/api/endpoints/missions.py
GET  /missions/             # Список миссий пользователя
POST /missions/{id}/claim   # Получить награду
```

**19 типов миссий**:

1. **First Bet** - Сделай первую ставку (+500 PRED)
2. **5 Bets** - Сделай 5 ставок (+1000 PRED)
3. **10 Bets** - Сделай 10 ставок (+2000 PRED)
4. **Win Streak 3** - Выиграй 3 подряд (+1500 PRED)
5. **Win Streak 5** - Выиграй 5 подряд (+3000 PRED)
6. **Bet on Crypto** - Ставка на крипту (+500 PRED)
7. **Bet on Sports** - Ставка на спорт (+500 PRED)
8. **Bet on Politics** - Ставка на политику (+500 PRED)
9. **High Roller** - Ставка 1000+ PRED (+1000 PRED)
10. **Lucky 7** - Выиграй 7 ставок (+2500 PRED)
11. **Daily Active** - 7 дней активности (+1500 PRED)
12. **Referral** - Приведи друга (+2000 PRED)
13. **Silver Rank** - Достигни Silver (+1000 PRED)
14. **Gold Rank** - Достигни Gold (+2500 PRED)
15. **Diamond Rank** - Достигни Diamond (+5000 PRED)
16. **Grandmaster Rank** - Достигни Grandmaster (+10000 PRED)
17. **Total Volume 10k** - 10k PRED объем (+3000 PRED)
18. **Total Volume 50k** - 50k PRED объем (+10000 PRED)
19. **Total Volume 100k** - 100k PRED объем (+25000 PRED)

**Механика**:
- Автоматическое обновление прогресса
- Claim награды когда прогресс == target
- Одноразовые миссии

##### 1.6 Leaderboard (`/leaderboard`)
```python
# backend/app/api/endpoints/leaderboard.py
GET /leaderboard/           # Топ пользователей
```

**Типы сортировки**:
- `profit` - по заработанным PRED (default)
- `win_rate` - по проценту побед
- `win_streak` - по текущей серии побед
- `total_wins` - по общему количеству побед

**Параметры**:
- `limit`: количество (default: 100)
- `offset`: смещение для пагинации
- `sort_by`: тип сортировки

##### 1.7 Wallet (`/wallet`) - В РАЗРАБОТКЕ
```python
# backend/app/api/endpoints/wallet.py
POST /wallet/connect        # Подключить TON wallet
POST /wallet/deposit        # Пополнить PRED через TON
POST /wallet/withdraw       # Вывести PRED в TON
```

**Планируемый функционал**:
- Подключение TON Connect
- Конвертация: 1 TON = 1000 PRED
- Минимальный депозит: 0.1 TON
- Минимальный вывод: 100 PRED
- Комиссия вывода: 5%

##### 1.8 Admin (`/admin`)
```python
# backend/app/api/endpoints/admin.py
# Markets
POST   /admin/markets                  # Создать рынок
POST   /admin/markets/{id}/resolve     # Разрешить рынок
PATCH  /admin/markets/{id}             # Обновить рынок
DELETE /admin/markets/{id}             # Удалить рынок

# Users
GET    /admin/users                    # Список пользователей
PATCH  /admin/users/{id}               # Обновить пользователя
POST   /admin/users/{id}/ban           # Забанить пользователя
POST   /admin/users/{id}/unban         # Разбанить пользователя

# Broadcast (NEW)
POST   /admin/broadcast                # Массовая рассылка

# Stats
GET    /admin/stats                    # Общая статистика
```

**Broadcast система**:
- Отправка с изображением (до 1000 символов)
- Отправка без изображения (до 4096 символов)
- Загрузка изображений в S3/MinIO
- Очередь через TelegramQueueService
- Rate limiting через Telegram Worker
- Форматирование: HTML, Markdown
- Target: все пользователи или конкретный ID

**Market Resolution**:
- Выбор исхода: YES, NO, CANCELLED
- Автоматический расчет выплат
- Обновление балансов победителей
- Создание транзакций
- Обновление статистики пользователей
- Уведомления через очередь

##### 1.9 Support (`/support`)
```python
# backend/app/api/endpoints/support.py
GET  /support/tickets                  # Мои тикеты
POST /support/tickets                  # Создать тикет
GET  /support/tickets/{id}             # Детали тикета
POST /support/tickets/{id}/messages    # Отправить сообщение
POST /support/tickets/{id}/close       # Закрыть тикет

# Admin
GET  /admin/support/tickets            # Все тикеты
POST /admin/support/tickets/{id}/reply # Ответить на тикет
```

**Функционал**:
- Приоритеты: Low, Medium, High, Urgent
- Статусы: Open, In Progress, Waiting User, Closed
- Вложения (фото через S3)
- История сообщений
- Отслеживание ответа админа

##### 1.10 Scheduler (`/scheduler`)
```python
# backend/app/api/endpoints/scheduler.py
# Автоматические задачи (APScheduler)

Weekly Leaderboard Rewards (Понедельник 00:00 UTC):
- Топ 10 получают награды
- Уведомления через очередь
- Сброс weekly stats

Cleanup Old Data (Ежедневно 03:00 UTC):
- Удаление старых уведомлений (>30 дней)
- Архивация закрытых тикетов
```

---

### 2. Telegram Bot (aiogram)

**Файл**: `bot/main.py`
**Бот**: @The_Pred_Bot

#### Функционал:

##### 2.1 Команды
```python
/start              # Приветствие + регистрация
/help               # Помощь
/support            # Создать тикет поддержки
/balance            # Показать баланс
/stats              # Статистика
```

##### 2.2 WebApp Integration
```python
# Кнопка "🎯 Open Markets" открывает Mini App
webapp_url = f"{WEBAPP_URL}?telegram_id={user.id}&username={user.username}"
```

##### 2.3 Support Tickets
```python
# Создание тикета через FSM (Finite State Machine)
1. /support - начало диалога
2. Выбор приоритета (Low/Medium/High/Urgent)
3. Ввод темы тикета
4. Ввод описания проблемы
5. Опционально: отправка фото
6. Создание тикета в backend
7. Уведомление админам
```

##### 2.4 Notifications
```python
# Бот получает уведомления из очереди
- Market Resolved (твой рынок закрылся)
- Bet Won/Lost (результат ставки)
- Mission Completed (миссия выполнена)
- Leaderboard Reward (награда за место)
- Broadcast (массовая рассылка от админа)
- Support Reply (ответ админа в тикете)
```

---

### 3. Telegram Worker

**Файл**: `backend/telegram_worker.py`
**Тип**: Standalone process (PM2)

#### Архитектура:

```python
class TelegramWorker:
    """
    Обработчик очереди Telegram уведомлений

    Характеристики:
    - Rate limiting: 30 сообщений/секунду (лимит Telegram)
    - Batch processing: обрабатывает до 30 сообщений за раз
    - Error handling: временные и постоянные ошибки
    - Retry logic: до 5 попыток на сообщение
    - Sleep: 1 сек с сообщениями, 5 сек без сообщений
    """
```

#### Основные методы:

##### 3.1 Process Loop
```python
async def _process_loop(self):
    """
    Главный цикл обработки

    1. Получить pending сообщения из БД (SKIP LOCKED)
    2. Обработать параллельно (asyncio.gather)
    3. Sleep для соблюдения rate limit
    4. Повторить
    """
```

##### 3.2 Send Message
```python
async def _send_message(self, notification):
    """
    Отправка одного уведомления

    Поддержка:
    - Text messages (HTML, Markdown)
    - Photo with caption
    - Метаданные из notification_metadata

    Обработка ошибок:
    - TelegramForbiddenError -> PERMANENT_FAILURE (user blocked bot)
    - TelegramBadRequest -> PERMANENT_FAILURE (invalid data)
    - TelegramAPIError -> FAILED (retry)
    - Other errors -> FAILED (retry)
    """
```

##### 3.3 Status Updates
```python
# Статусы уведомлений
PENDING -> PROCESSING -> SENT      # Успешно
PENDING -> PROCESSING -> FAILED -> ... -> SENT  # С retry
PENDING -> PROCESSING -> PERMANENT_FAILURE  # Нет retry
```

#### Integration:

```python
# backend/app/services/telegram_queue_service.py
class TelegramQueueService:
    """
    Сервис управления очередью

    Методы:
    - add_notification(): добавить уведомление в очередь
    - get_pending_messages(): получить pending (FOR UPDATE SKIP LOCKED)
    - mark_processing(): пометить как обрабатывается
    - mark_sent(): пометить как отправлено
    - mark_failed(): пометить как ошибка (с/без retry)
    """
```

#### Запуск:

```bash
# Development
cd backend
BOT_TOKEN="your_token" python telegram_worker.py

# Production (PM2)
pm2 start telegram_worker.py --name telegram-worker --interpreter python3
pm2 logs telegram-worker
```

---

### 4. Mini App (Webapp)

**Порт**: 8001
**Production**: https://thepred.tech
**Framework**: Quart (async Flask)

#### Страницы:

##### 4.1 Markets (`/`)
```html
<!-- webapp/templates/index.html -->
Функционал:
- Список всех рынков
- Фильтры: All, Crypto, Sports, Politics, Tech
- Promoted markets (выделены)
- Поиск по названию
- Sorting: Latest, Ending Soon, Most Popular
- Infinite scroll (pagination)
```

##### 4.2 Market Detail (`/market/<id>`)
```html
<!-- webapp/templates/market.html -->
Функционал:
- Полная информация о рынке
- Текущие odds (YES/NO с процентами)
- Pool size, participants count
- Betting interface:
  - Выбор исхода (YES/NO)
  - Ввод суммы
  - Расчет potential win
  - Подтверждение ставки
- Твои ставки на этом рынке
- История активности (последние ставки других)
```

##### 4.3 Profile (`/profile`)
```html
<!-- webapp/templates/profile.html -->
Секции:
1. Balance Card
   - PRED balance (с анимацией)
   - TON balance (если подключен)
   - Connect Wallet button (в разработке)

2. Stats Card
   - Current Rank (с иконкой)
   - Win Rate (цветной прогресс-бар)
   - Total Wins / Total Bets
   - Win Streak (огонь если >0)

3. Bet History
   - Фильтры: All, Pending, Won, Lost
   - Карточки ставок с детальной инфо
   - Pagination
```

##### 4.4 Missions (`/missions`)
```html
<!-- webapp/templates/missions.html -->
Функционал:
- Grid карточек миссий (19 штук)
- Progress bar для каждой миссии
- Claim button (когда выполнена)
- Claimed badge (когда получена награда)
- Группировка по типам:
  - Betting Missions
  - Streak Missions
  - Category Missions
  - Rank Missions
  - Volume Missions
```

##### 4.5 Leaderboard (`/leaderboard`)
```html
<!-- webapp/templates/leaderboard.html -->
Функционал:
- Tabs для сортировки:
  - 💰 Profit Leaders
  - 🎯 Win Rate Leaders
  - 🔥 Win Streak Leaders
  - 🏆 Most Wins Leaders
- Top 3 с большими медалями
- Список с позициями 4-100
- "Your Position" card внизу
- Real-time updates
```

#### API Client:

```python
# webapp/api_client.py
class APIClient:
    """
    Async HTTP client для взаимодействия с Backend API

    Методы для всех endpoints:
    - auth (register, token)
    - markets (list, detail, stats)
    - bets (create, my, detail)
    - users (profile, stats)
    - missions (list, claim)
    - leaderboard (get)
    - wallet (connect, deposit, withdraw)
    """
```

---

### 5. Admin Panel

**Порт**: 8002
**Production**: Доступна через Nginx proxy
**Framework**: Quart + Chart.js

#### Разделы:

##### 5.1 Dashboard (`/admin`)
```html
<!-- admin/templates/dashboard.html -->
Статистика:
- Total Users (с ростом)
- Active Markets
- Total Bets (за все время)
- Total Volume (PRED)

Графики (Chart.js):
- Users Growth (линейный график)
- Bets by Category (круговая диаграмма)
- Daily Volume (столбчатая диаграмма)
- Top Markets (горизонтальная диаграмма)
```

##### 5.2 Markets Management (`/admin/markets`)
```html
<!-- admin/templates/markets.html -->
Функционал:
- Таблица всех рынков
- Фильтры: Status, Category
- Действия:
  - ✏️ Edit (modal)
  - ✅ Resolve (выбор исхода)
  - 🔝 Promote/Unpromote
  - 🗑️ Delete (с подтверждением)

Create Market Modal:
- Title (max 500 chars)
- Description (rich text)
- Category (select)
- End Date (datepicker)
- Promoted (checkbox)
```

##### 5.3 Users Management (`/admin/users`)
```html
<!-- admin/templates/users.html -->
Функционал:
- Таблица пользователей
- Search by telegram_id, username
- Фильтры: Rank, Banned
- Сортировка: Balance, Total Bets, Win Rate

Действия:
- 👁️ View Activity (modal с историей)
- ✏️ Edit Balance (modal)
- 🚫 Ban/Unban
- 📊 View Stats

User Activity Modal:
- Recent bets
- Mission progress
- Transaction history
- Support tickets
```

##### 5.4 Broadcast System (`/admin/broadcast`) - NEW
```html
<!-- admin/templates/broadcast.html -->
Секции:

1. Rich Text Editor
   - Formatting toolbar:
     - Bold, Italic, Underline, Strikethrough
     - Code, Link, Unordered List, Ordered List
   - Emoji Picker (32 emojis):
     - 😊🔥💎🎯💰📈🚀⚡️✨🎉
     - 🎁💪🏆👑💯🌟⭐️🎮📊
     - 💸🤑💵💴💷💶🪙📉📈
     - ❤️👍👏🙌🤝
   - Character counter:
     - 0 / 4096 (без изображения)
     - 0 / 1000 (с изображением)
   - Visual warning при превышении лимита

2. Image Upload
   - Drag & drop zone
   - File picker (images only)
   - Preview с возможностью удаления
   - Auto-upload to S3/MinIO

3. Settings
   - Parse Mode: HTML / Markdown
   - Target:
     - All Users (broadcast)
     - Specific User (by telegram_id)

4. Preview
   - Live preview сообщения
   - Preview изображения
   - HTML rendering

5. Send Button
   - Validation перед отправкой
   - Success toast с количеством получателей
   - Estimated delivery time

После отправки:
- Сообщения добавляются в очередь
- Telegram Worker обрабатывает с rate limiting
- Показывается количество queued сообщений
```

**Технические детали**:
```javascript
// Динамический лимит символов
function updateCharCounter() {
    const message = document.getElementById('message').value;
    const charCount = message.length;
    const maxChars = uploadedImageFile ? 1000 : 4096;

    counter.textContent = `${charCount} / ${maxChars} characters`;

    if (charCount > maxChars) {
        counter.classList.add('text-red-400');
        warning.classList.remove('hidden');
    } else {
        counter.classList.remove('text-red-400');
        warning.classList.add('hidden');
    }
}

// FormData submission
const formData = new FormData();
formData.append('message', message);
formData.append('target', target);
formData.append('parse_mode', parseMode);
if (telegram_id) formData.append('telegram_id', telegram_id);
if (uploadedImageFile) formData.append('image', uploadedImageFile);
```

##### 5.5 Support Tickets (`/admin/support`)
```html
<!-- admin/templates/support.html -->
Функционал:
- Список всех тикетов
- Фильтры: Status, Priority
- Badge цвета по статусу/приоритету

Ticket Detail Modal:
- User info
- Ticket subject, description
- Attached photo (если есть)
- Message thread
- Reply form (с возможностью фото)
- Actions: Close Ticket, Change Status
```

---

### 6. Landing Page

**Порт**: 8003
**Файл**: `landing/templates/index_last.html`

#### Секции:

```html
1. Hero Section
   - Gradient background
   - Заголовок: "Prediction Markets в Telegram"
   - 3 примера рынков (Crypto, Sports, Politics)
   - CTA button: "Открыть в Telegram"

2. Philosophy Section
   - "Сила коллективного разума"
   - Описание концепции prediction markets
   - Анимированные карточки

3. How It Works (3 шага)
   - Открой бота → Выбери событие → Делай прогноз
   - Step-by-step анимация

4. Features Grid
   - Real Markets
   - Smart Odds
   - Win Together
   - Каждая feature с иконкой и описанием

5. Gamification Section
   - Миссии, Ранги, Лидерборд
   - Скриншоты интерфейса

6. AI Assistant (Coming Soon)
   - Будущая функциональность
   - Тизер

7. Social Proof
   - Статистика (users, markets, volume)
   - Счетчики с анимацией

8. Footer
   - Copyright
   - Social links (Telegram, Twitter, GitHub)
```

**Дизайн**:
- Полностью адаптивный (mobile, tablet, desktop)
- Градиенты, glass effects
- Smooth scroll animations (AOS.js)
- Темная тема
- SEO оптимизация

---

## База данных

### PostgreSQL Schema (11 таблиц)

#### 1. `users` - Пользователи

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    photo_url VARCHAR(500),

    -- Balances
    pred_balance DECIMAL(20,2) DEFAULT 10000.00 NOT NULL,
    ton_balance DECIMAL(20,2) DEFAULT 0.00 NOT NULL,

    -- Gamification
    rank VARCHAR(50) DEFAULT 'Bronze' NOT NULL,
    total_bets BIGINT DEFAULT 0 NOT NULL,
    total_wins BIGINT DEFAULT 0 NOT NULL,
    total_losses BIGINT DEFAULT 0 NOT NULL,
    win_streak BIGINT DEFAULT 0 NOT NULL,

    -- Referral
    referrer_id BIGINT REFERENCES users(id),
    referral_code VARCHAR(50) UNIQUE,

    -- Ban system
    is_banned BOOLEAN DEFAULT FALSE NOT NULL,
    ban_reason TEXT,
    banned_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_referral_code ON users(referral_code);
CREATE INDEX idx_users_is_banned ON users(is_banned);
```

**Ранги**:
- Bronze: 0-10 wins
- Silver: 11-25 wins
- Gold: 26-50 wins
- Diamond: 51-100 wins
- Grandmaster: 100+ wins

#### 2. `markets` - Рынки

```sql
CREATE TABLE markets (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,  -- Crypto, Sports, Politics, Tech
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) DEFAULT 'Active' NOT NULL,  -- Active, Resolved, Cancelled
    result VARCHAR(10),  -- YES, NO, NULL

    -- Pool tracking
    total_yes_bets BIGINT DEFAULT 0 NOT NULL,
    total_no_bets BIGINT DEFAULT 0 NOT NULL,
    total_pool BIGINT DEFAULT 0 NOT NULL,

    -- Admin
    promoted BOOLEAN DEFAULT FALSE NOT NULL,
    created_by INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_markets_category ON markets(category);
CREATE INDEX idx_markets_status ON markets(status);
CREATE INDEX idx_markets_end_date ON markets(end_date);
CREATE INDEX idx_markets_promoted ON markets(promoted);
```

**Categories**:
- Crypto: Bitcoin, Ethereum, TON, altcoins
- Sports: Football, Basketball, UFC, etc.
- Politics: Elections, referendums, appointments
- Tech: Product launches, IPOs, acquisitions

#### 3. `bets` - Ставки

```sql
CREATE TABLE bets (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) NOT NULL,
    market_id INTEGER REFERENCES markets(id) NOT NULL,

    -- Bet details
    outcome VARCHAR(10) NOT NULL,  -- YES, NO
    amount BIGINT NOT NULL,
    odds DECIMAL(10,2) NOT NULL,
    potential_win BIGINT NOT NULL,

    -- Status
    status VARCHAR(50) DEFAULT 'Pending' NOT NULL,  -- Pending, Won, Lost, Refunded

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_bets_user_id ON bets(user_id);
CREATE INDEX idx_bets_market_id ON bets(market_id);
CREATE INDEX idx_bets_status ON bets(status);
CREATE INDEX idx_bets_created_at ON bets(created_at DESC);
```

**Odds calculation (AMM)**:
```python
# Automated Market Maker formula
total_pool = market.total_yes_bets + market.total_no_bets
outcome_pool = market.total_yes_bets if outcome == "YES" else market.total_no_bets

odds = (total_pool + amount) / (outcome_pool + amount)
potential_win = amount * odds
```

#### 4. `missions` - Миссии (шаблоны)

```sql
CREATE TABLE missions (
    id SERIAL PRIMARY KEY,
    mission_type VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    icon VARCHAR(50),  -- Emoji или название иконки
    target INTEGER NOT NULL,
    reward INTEGER NOT NULL,
    category VARCHAR(50),  -- Betting, Streak, Category, Rank, Volume

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
```

**19 миссий** (детали см. в разделе Missions выше)

#### 5. `user_missions` - Прогресс миссий пользователя

```sql
CREATE TABLE user_missions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) NOT NULL,
    mission_id INTEGER REFERENCES missions(id) NOT NULL,

    -- Progress tracking
    progress INTEGER DEFAULT 0 NOT NULL,
    claimed BOOLEAN DEFAULT FALSE NOT NULL,
    claimed_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    UNIQUE(user_id, mission_id)
);

CREATE INDEX idx_user_missions_user_id ON user_missions(user_id);
CREATE INDEX idx_user_missions_claimed ON user_missions(claimed);
```

**Механика**:
- При регистрации создаются 19 записей (по одной на каждую миссию)
- progress обновляется автоматически при различных событиях
- claimed = true после получения награды

#### 6. `transactions` - История транзакций

```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) NOT NULL,

    -- Transaction details
    type VARCHAR(50) NOT NULL,  -- Bet, Win, Refund, Mission, Deposit, Withdraw, LeaderboardReward
    amount BIGINT NOT NULL,
    balance_before BIGINT NOT NULL,
    balance_after BIGINT NOT NULL,
    description TEXT,

    -- Related entities
    bet_id INTEGER REFERENCES bets(id),
    mission_id INTEGER REFERENCES missions(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_type ON transactions(type);
CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);
```

**Типы транзакций**:
- Bet: списание при создании ставки
- Win: выплата при выигрыше
- Refund: возврат при отмене рынка
- Mission: награда за миссию
- LeaderboardReward: награда за место в лидерборде
- Deposit: пополнение через TON (в разработке)
- Withdraw: вывод в TON (в разработке)

#### 7. `wallet_addresses` - TON кошельки (в разработке)

```sql
CREATE TABLE wallet_addresses (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) UNIQUE NOT NULL,
    ton_address VARCHAR(255) NOT NULL,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_wallet_addresses_ton_address ON wallet_addresses(ton_address);
```

#### 8. `support_tickets` - Тикеты поддержки

```sql
CREATE TYPE ticketstatus AS ENUM ('open', 'in_progress', 'waiting_user', 'closed');
CREATE TYPE ticketpriority AS ENUM ('low', 'medium', 'high', 'urgent');

CREATE TABLE support_tickets (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    priority ticketpriority DEFAULT 'medium' NOT NULL,
    status ticketstatus DEFAULT 'open' NOT NULL,
    admin_replied BOOLEAN DEFAULT FALSE NOT NULL,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    closed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_support_tickets_user_id ON support_tickets(user_id);
CREATE INDEX idx_support_tickets_status ON support_tickets(status);
CREATE INDEX idx_support_tickets_priority ON support_tickets(priority);
```

#### 9. `support_messages` - Сообщения в тикетах

```sql
CREATE TABLE support_messages (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER REFERENCES support_tickets(id) NOT NULL,
    user_id BIGINT REFERENCES users(id),  -- NULL если от админа
    is_admin BOOLEAN DEFAULT FALSE NOT NULL,
    message TEXT NOT NULL,
    attachment_url VARCHAR(500),  -- S3 URL для фото

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_support_messages_ticket_id ON support_messages(ticket_id);
CREATE INDEX idx_support_messages_created_at ON support_messages(created_at);
```

#### 10. `telegram_notifications_queue` - Очередь уведомлений

```sql
CREATE TYPE notificationstatus AS ENUM (
    'PENDING',           -- Ожидает отправки
    'PROCESSING',        -- В процессе отправки
    'SENT',              -- Успешно отправлено
    'FAILED',            -- Ошибка (будет retry)
    'PERMANENT_FAILURE'  -- Необратимая ошибка (без retry)
);

CREATE TYPE notificationtype AS ENUM (
    'LEADERBOARD_REWARD',
    'MARKET_RESOLVED',
    'BET_WON',
    'BET_LOST',
    'MISSION_COMPLETED',
    'BROADCAST',         -- NEW: массовая рассылка
    'SYSTEM'
);

CREATE TABLE telegram_notifications_queue (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    user_id BIGINT REFERENCES users(id),

    -- Message content
    message_text TEXT NOT NULL,
    parse_mode VARCHAR(10) DEFAULT 'HTML',  -- HTML или Markdown
    notification_type notificationtype NOT NULL,
    notification_metadata TEXT,  -- JSON для доп. данных (например, photo_url)

    -- Status tracking
    status notificationstatus DEFAULT 'PENDING' NOT NULL,
    attempts INTEGER DEFAULT 0 NOT NULL,
    max_attempts INTEGER DEFAULT 5 NOT NULL,

    -- Scheduling
    scheduled_at TIMESTAMP WITH TIME ZONE,  -- Когда отправить
    processing_at TIMESTAMP WITH TIME ZONE, -- Когда началась обработка
    sent_at TIMESTAMP WITH TIME ZONE,       -- Когда отправлено

    -- Errors
    error_message TEXT,
    last_error_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_notifications_status ON telegram_notifications_queue(status);
CREATE INDEX idx_notifications_telegram_id ON telegram_notifications_queue(telegram_id);
CREATE INDEX idx_notifications_scheduled_at ON telegram_notifications_queue(scheduled_at);
CREATE INDEX idx_notifications_created_at ON telegram_notifications_queue(created_at);
```

**Metadata examples**:
```json
// Broadcast с изображением
{
  "broadcast": true,
  "photo_url": "https://thepred.store/thepred-events/broadcast/20251108_123456_image.jpg"
}

// Результат рынка
{
  "market_id": 123,
  "market_title": "Will Bitcoin reach $100k by end of 2025?",
  "result": "YES"
}

// Выигрыш ставки
{
  "bet_id": 456,
  "market_id": 123,
  "amount_won": 2500
}
```

#### 11. `leaderboard_snapshots` - Снимки лидерборда (опционально)

```sql
CREATE TABLE leaderboard_snapshots (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) NOT NULL,
    period VARCHAR(50) NOT NULL,  -- weekly, monthly, all_time

    -- Metrics
    position INTEGER NOT NULL,
    total_profit BIGINT NOT NULL,
    win_rate DECIMAL(5,2),
    win_streak INTEGER,
    total_wins INTEGER,

    -- Reward (если получил)
    reward_amount INTEGER,
    rewarded BOOLEAN DEFAULT FALSE,

    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_snapshots_period_date ON leaderboard_snapshots(period, snapshot_date);
CREATE INDEX idx_snapshots_user_period ON leaderboard_snapshots(user_id, period);
```

### Seed Data

**Файл**: `backend/seed_data.py`

**20 тестовых рынков**:
- 7 Crypto: Bitcoin $100k, Ethereum $10k, TON $15, BNB $1000, Solana $500
- 6 Sports: Real Madrid win, Lakers championship, Ronaldo goals, UFC 300
- 4 Politics: Trump reelection, Russia-Ukraine, NATO expansion, UK elections
- 3 Tech: Apple AR glasses, AI surpass humans, Tesla $500

**Команда запуска**:
```bash
cd backend
POSTGRES_HOST=localhost python3 seed_data.py
```

---

## API Endpoints

### Полный список (40+ endpoints)

#### Auth
```
POST   /auth/register                 # Регистрация через Telegram
POST   /auth/token                    # Получение JWT токена
```

#### Markets
```
GET    /markets/                      # Список рынков
  ?category=Crypto                    # Фильтр по категории
  &status=Active                      # Фильтр по статусу
  &promoted=true                      # Только promoted
  &search=bitcoin                     # Поиск по названию
  &limit=20&offset=0                  # Pagination

GET    /markets/{id}                  # Детали рынка
GET    /markets/{id}/stats            # Статистика рынка
```

#### Bets
```
POST   /bets/                         # Создать ставку
  Body: {
    "market_id": 1,
    "outcome": "YES",
    "amount": 100
  }

GET    /bets/my                       # Мои ставки
  ?status=Pending                     # Фильтр по статусу
  &market_id=1                        # Фильтр по рынку
  &limit=50&offset=0

GET    /bets/{id}                     # Детали ставки
```

#### Users
```
GET    /users/me                      # Мой профиль
GET    /users/me/stats                # Моя статистика
GET    /users/{id}                    # Публичный профиль
```

#### Missions
```
GET    /missions/                     # Список моих миссий
POST   /missions/{id}/claim           # Получить награду
```

#### Leaderboard
```
GET    /leaderboard/                  # Топ пользователей
  ?sort_by=profit                     # profit, win_rate, win_streak, total_wins
  &limit=100&offset=0
```

#### Wallet (В РАЗРАБОТКЕ)
```
POST   /wallet/connect                # Подключить TON wallet
  Body: {"ton_address": "EQ..."}

POST   /wallet/deposit                # Депозит TON → PRED
  Body: {"amount_ton": 1.5}

POST   /wallet/withdraw               # Вывод PRED → TON
  Body: {"amount_pred": 1500}
```

#### Support
```
# User endpoints
GET    /support/tickets               # Мои тикеты
POST   /support/tickets               # Создать тикет
  Body: {
    "subject": "Не могу сделать ставку",
    "priority": "high",
    "message": "Описание проблемы",
    "attachment": <file>
  }

GET    /support/tickets/{id}          # Детали тикета
POST   /support/tickets/{id}/messages # Отправить сообщение
POST   /support/tickets/{id}/close    # Закрыть тикет

# Admin endpoints
GET    /admin/support/tickets         # Все тикеты
  ?status=open&priority=high

POST   /admin/support/tickets/{id}/reply  # Ответить
POST   /admin/support/tickets/{id}/status # Изменить статус
```

#### Admin - Markets
```
POST   /admin/markets                 # Создать рынок
  Body: {
    "title": "Will Bitcoin reach $100k?",
    "description": "...",
    "category": "Crypto",
    "end_date": "2025-12-31T23:59:59Z",
    "promoted": false
  }

PATCH  /admin/markets/{id}            # Обновить рынок
POST   /admin/markets/{id}/resolve    # Разрешить рынок
  Body: {"result": "YES"}             # YES, NO, CANCELLED

DELETE /admin/markets/{id}            # Удалить рынок
```

#### Admin - Users
```
GET    /admin/users                   # Список пользователей
  ?limit=50&offset=0
  &search=username
  &rank=Diamond
  &is_banned=false

PATCH  /admin/users/{id}              # Обновить пользователя
  Body: {
    "pred_balance": 5000,
    "rank": "Gold"
  }

POST   /admin/users/{id}/ban          # Забанить
  Body: {"reason": "Cheating"}

POST   /admin/users/{id}/unban        # Разбанить
```

#### Admin - Broadcast (NEW)
```
POST   /admin/broadcast               # Массовая рассылка
  Content-Type: multipart/form-data

  Fields:
    message: "Текст сообщения"
    target: "all" | "specific"
    telegram_id: 123456 (если target=specific)
    parse_mode: "HTML" | "Markdown"
    image: <file> (опционально)

  Response: {
    "total_recipients": 150,
    "queued": 150,
    "message": "Broadcast queued for 150 users"
  }
```

#### Admin - Stats
```
GET    /admin/stats                   # Общая статистика
  Response: {
    "total_users": 150,
    "active_markets": 12,
    "total_bets": 543,
    "total_volume": 125000,
    "users_growth": [...],
    "bets_by_category": {...},
    "daily_volume": [...]
  }
```

---

## Система очередей и уведомлений

### Архитектура

```
┌──────────────────────────────────────────────────────────┐
│                    APPLICATION EVENTS                     │
│   (Bet Won, Market Resolved, Mission Completed, etc.)    │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│              TelegramQueueService.add_notification()      │
│                                                           │
│  await TelegramQueueService.add_notification(             │
│      db=db,                                               │
│      telegram_id=user.telegram_id,                        │
│      message_text="🎉 Поздравляем! Ваша ставка выиграла!" │
│      notification_type=NotificationType.BET_WON,          │
│      user_id=user.id,                                     │
│      metadata={"bet_id": 123, "amount_won": 2500}         │
│  )                                                        │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│            telegram_notifications_queue (PostgreSQL)      │
│                                                           │
│  Status: PENDING → PROCESSING → SENT/FAILED              │
│  FOR UPDATE SKIP LOCKED (concurrent processing)          │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                   TELEGRAM WORKER                         │
│                                                           │
│  While True:                                              │
│    1. Get pending messages (limit=30, SKIP LOCKED)       │
│    2. Process in parallel (asyncio.gather)               │
│    3. Send via aiogram Bot.send_message()                │
│    4. Update status (SENT/FAILED)                        │
│    5. Sleep 1s (rate limiting)                           │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                   TELEGRAM API                            │
│                 (30 messages/second max)                  │
└──────────────────────────────────────────────────────────┘
```

### TelegramQueueService

**Файл**: `backend/app/services/telegram_queue_service.py`

```python
class TelegramQueueService:
    """Сервис управления очередью Telegram уведомлений"""

    @staticmethod
    async def add_notification(
        db: AsyncSession,
        telegram_id: int,
        message_text: str,
        notification_type: NotificationType,
        user_id: Optional[int] = None,
        parse_mode: str = "HTML",
        scheduled_at: Optional[datetime] = None,
        metadata: Optional[dict] = None
    ) -> TelegramNotification:
        """
        Добавить уведомление в очередь

        Args:
            telegram_id: Telegram ID получателя
            message_text: Текст сообщения
            notification_type: Тип уведомления (enum)
            user_id: ID пользователя в БД (опционально)
            parse_mode: HTML или Markdown
            scheduled_at: Когда отправить (None = немедленно)
            metadata: Доп. данные (JSON)

        Returns:
            TelegramNotification: Созданная запись
        """

    @staticmethod
    async def get_pending_messages(
        db: AsyncSession,
        limit: int = 30,
        include_scheduled: bool = True
    ) -> List[TelegramNotification]:
        """
        Получить pending сообщения для отправки

        Uses FOR UPDATE SKIP LOCKED для безопасной конкурентной обработки
        """

    @staticmethod
    async def mark_processing(db: AsyncSession, notification_id: int):
        """Пометить как обрабатывается"""

    @staticmethod
    async def mark_sent(db: AsyncSession, notification_id: int):
        """Пометить как отправлено"""

    @staticmethod
    async def mark_failed(
        db: AsyncSession,
        notification_id: int,
        error_message: str,
        permanent_failure: bool = False
    ):
        """
        Пометить как ошибка

        Args:
            permanent_failure: True = PERMANENT_FAILURE (без retry)
                              False = FAILED (будет retry)
        """
```

### Типы уведомлений

```python
class NotificationType(str, enum.Enum):
    LEADERBOARD_REWARD = "LEADERBOARD_REWARD"
    # Текст: "🏆 Поздравляем! Вы заняли {position} место в недельном лидерборде"
    # Metadata: {"position": 3, "reward": 5000}

    MARKET_RESOLVED = "MARKET_RESOLVED"
    # Текст: "📊 Рынок '{market_title}' закрыт. Результат: {result}"
    # Metadata: {"market_id": 123, "result": "YES"}

    BET_WON = "BET_WON"
    # Текст: "🎉 Ваша ставка выиграла! +{amount} PRED"
    # Metadata: {"bet_id": 456, "amount_won": 2500}

    BET_LOST = "BET_LOST"
    # Текст: "😔 Ваша ставка проиграла"
    # Metadata: {"bet_id": 789}

    MISSION_COMPLETED = "MISSION_COMPLETED"
    # Текст: "✅ Миссия '{mission_title}' выполнена! +{reward} PRED"
    # Metadata: {"mission_id": 5, "reward": 1000}

    BROADCAST = "BROADCAST"
    # Текст: любой (от админа)
    # Metadata: {"broadcast": true, "photo_url": "..."}

    SYSTEM = "SYSTEM"
    # Текст: системное уведомление
    # Metadata: любые данные
```

### Примеры использования

#### 1. Уведомление о выигрыше ставки

```python
# backend/app/api/endpoints/admin.py (market resolution)

for bet in winning_bets:
    # Начислить выигрыш
    user.pred_balance += bet.potential_win
    bet.status = BetStatus.WON

    # Добавить в очередь уведомление
    await TelegramQueueService.add_notification(
        db=db,
        telegram_id=user.telegram_id,
        message_text=f"🎉 Поздравляем! Ваша ставка на рынке '{market.title}' выиграла!\n\n"
                     f"💰 Выигрыш: +{bet.potential_win} PRED",
        notification_type=NotificationType.BET_WON,
        user_id=user.id,
        metadata={
            "bet_id": bet.id,
            "market_id": market.id,
            "amount_won": bet.potential_win
        }
    )
```

#### 2. Broadcast с изображением

```python
# backend/app/api/endpoints/admin.py (broadcast)

# Upload image to S3
photo_url = f"{settings.S3_PUBLIC_URL}/{settings.S3_BUCKET}/{filename}"

# Add to queue for each user
for telegram_id, user_id in recipients:
    await TelegramQueueService.add_notification(
        db=db,
        telegram_id=telegram_id,
        message_text=message,
        notification_type=NotificationType.BROADCAST,
        user_id=user_id,
        parse_mode=parse_mode,
        metadata={
            "broadcast": True,
            "photo_url": photo_url
        }
    )
```

#### 3. Weekly Leaderboard Rewards

```python
# backend/app/api/endpoints/scheduler.py (weekly job)

top_users = await get_top_leaderboard()

for position, user in enumerate(top_users[:10], start=1):
    reward = REWARDS[position]

    # Начислить награду
    user.pred_balance += reward

    # Уведомление
    await TelegramQueueService.add_notification(
        db=db,
        telegram_id=user.telegram_id,
        message_text=f"🏆 Поздравляем! Вы заняли {position} место в недельном лидерборде!\n\n"
                     f"💰 Награда: +{reward} PRED",
        notification_type=NotificationType.LEADERBOARD_REWARD,
        user_id=user.id,
        metadata={
            "position": position,
            "reward": reward,
            "period": "weekly"
        }
    )
```

### Rate Limiting

**Telegram API лимиты**:
- 30 сообщений в секунду разным пользователям
- 20 сообщений в минуту одному пользователю
- 1 сообщение в секунду в один чат (для ботов)

**Наша реализация**:
```python
# backend/telegram_worker.py

class TelegramWorker:
    def __init__(self, batch_size: int = 30):
        self.batch_size = min(batch_size, 30)  # Max 30 msg/sec

    async def _process_loop(self):
        while self.is_running:
            start_time = datetime.now()

            # Process batch (up to 30 messages)
            messages = await self._get_pending_messages(limit=self.batch_size)
            await asyncio.gather(*[self._send_message(msg) for msg in messages])

            # Calculate sleep to maintain 1 second per batch
            elapsed = (datetime.now() - start_time).total_seconds()
            sleep_time = max(0, 1.0 - elapsed)

            if len(messages) == 0:
                await asyncio.sleep(5)  # No messages - sleep longer
            else:
                await asyncio.sleep(sleep_time)
```

---

## Broadcast система

### Полный workflow

#### 1. Frontend (Admin Panel)

**Файл**: `admin/templates/broadcast.html`

```javascript
// Rich Text Editor
const editor = document.getElementById('message');

// Formatting buttons
function formatText(command) {
    const selection = window.getSelection().toString();
    const formatted = {
        'bold': `<b>${selection}</b>`,
        'italic': `<i>${selection}</i>`,
        'code': `<code>${selection}</code>`,
        'link': `<a href="URL">${selection}</a>`
    }[command];

    insertAtCursor(formatted);
}

// Emoji picker
function insertEmoji(emoji) {
    insertAtCursor(emoji);
}

// Image upload
async function handleImageUpload(event) {
    const file = event.target.files[0];
    uploadedImageFile = file;

    // Preview
    const reader = new FileReader();
    reader.onload = (e) => {
        preview.src = e.target.result;
    };
    reader.readAsDataURL(file);

    // Update character limit
    updateCharCounter(); // 4096 → 1000
}

// Send broadcast
async function sendBroadcast() {
    const formData = new FormData();
    formData.append('message', message);
    formData.append('target', target);
    formData.append('parse_mode', parseMode);
    if (telegram_id) formData.append('telegram_id', telegram_id);
    if (uploadedImageFile) formData.append('image', uploadedImageFile);

    const response = await fetch('/admin/broadcast', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();
    // Show success: "Broadcast queued for 150 users"
}
```

#### 2. Admin Proxy

**Файл**: `admin/main.py`

```python
@app.route('/admin/broadcast', methods=['POST'])
@login_required
async def api_admin_broadcast():
    """Proxy broadcast request to backend API"""
    form = await request.form
    files = await request.files

    # Build FormData
    data = aiohttp.FormData()
    data.add_field('message', form.get('message'))
    data.add_field('target', form.get('target', 'all'))
    data.add_field('parse_mode', form.get('parse_mode', 'HTML'))

    if form.get('telegram_id'):
        data.add_field('telegram_id', form.get('telegram_id'))

    # Add image if uploaded
    if 'image' in files and files['image'].filename:
        image = files['image']
        image_bytes = image.read()
        data.add_field(
            'image',
            image_bytes,
            filename=image.filename,
            content_type=image.content_type
        )

    # Forward to backend
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{app.config['API_URL']}/admin/broadcast",
            data=data
        ) as response:
            result = await response.json()
            return jsonify(result)
```

#### 3. Backend API

**Файл**: `backend/app/api/endpoints/admin.py`

```python
@router.post("/broadcast")
async def broadcast_message(
    message: str = Form(...),
    target: str = Form("all"),
    parse_mode: str = Form("HTML"),
    telegram_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Массовая рассылка сообщений

    Поддержка:
    - Текст до 4096 символов (без изображения)
    - Текст до 1000 символов (с изображением)
    - Загрузка изображений в S3
    - Отправка всем или конкретному пользователю
    """

    # Validate message length
    max_length = 1000 if image else 4096
    if len(message) > max_length:
        raise HTTPException(400, f"Message too long! Max {max_length} characters")

    # Upload image to S3 if provided
    photo_url = None
    if image:
        image_data = await image.read()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"broadcast/{timestamp}_{image.filename}"

        s3_client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY
        )

        s3_client.put_object(
            Bucket=settings.S3_BUCKET,
            Key=filename,
            Body=image_data,
            ContentType=image.content_type,
            ACL='public-read'
        )

        photo_url = f"{settings.S3_PUBLIC_URL}/{settings.S3_BUCKET}/{filename}"

    # Get recipients
    if target == "all":
        query = select(User.telegram_id, User.id).where(User.is_banned == False)
        result = await db.execute(query)
        recipients = [(row[0], row[1]) for row in result.all()]
    elif target == "specific" and telegram_id:
        query = select(User.telegram_id, User.id).where(User.telegram_id == telegram_id)
        result = await db.execute(query)
        row = result.first()
        recipients = [(row[0], row[1])] if row else []
    else:
        raise HTTPException(400, "Invalid target")

    # Add messages to queue
    queued_count = 0
    for tg_id, user_id in recipients:
        try:
            metadata = {"broadcast": True}
            if photo_url:
                metadata["photo_url"] = photo_url

            await TelegramQueueService.add_notification(
                db=db,
                telegram_id=tg_id,
                message_text=message,
                notification_type=NotificationType.BROADCAST,
                user_id=user_id,
                parse_mode=parse_mode,
                metadata=metadata
            )
            queued_count += 1

        except Exception as e:
            logger.error(f"[Broadcast] Failed to queue for {tg_id}: {e}")
            continue

    await db.commit()

    return {
        "total_recipients": len(recipients),
        "queued": queued_count,
        "message": f"Broadcast queued for {queued_count} users"
    }
```

#### 4. Queue Processing

**TelegramQueueService** добавляет записи в БД:

```sql
INSERT INTO telegram_notifications_queue (
    telegram_id,
    user_id,
    message_text,
    notification_type,
    parse_mode,
    notification_metadata,
    status
) VALUES (
    792818131,
    1,
    'Привет! Это тестовая рассылка с картинкой 🚀',
    'BROADCAST',
    'HTML',
    '{"broadcast": true, "photo_url": "https://thepred.store/..."}',
    'PENDING'
);
```

#### 5. Worker Processing

**Файл**: `backend/telegram_worker.py`

```python
async def _send_message(self, notification: TelegramNotification):
    """Отправка одного уведомления"""
    try:
        # Mark as processing
        await self._update_status(
            notification.id,
            NotificationStatus.PROCESSING
        )

        # Parse metadata
        metadata = json.loads(notification.notification_metadata or '{}')
        photo_url = metadata.get('photo_url')

        # Send message
        if photo_url:
            # Send photo with caption
            await self.bot.send_photo(
                chat_id=notification.telegram_id,
                photo=photo_url,
                caption=notification.message_text,
                parse_mode=notification.parse_mode
            )
        else:
            # Send text message
            await self.bot.send_message(
                chat_id=notification.telegram_id,
                text=notification.message_text,
                parse_mode=notification.parse_mode
            )

        # Mark as sent
        await self._update_status(
            notification.id,
            NotificationStatus.SENT
        )

        logger.info(f"✓ Sent #{notification.id} to {notification.telegram_id}")

    except TelegramForbiddenError:
        # User blocked bot - permanent failure
        await self._update_status(
            notification.id,
            NotificationStatus.PERMANENT_FAILURE,
            error="User blocked bot"
        )

    except Exception as e:
        # Temporary error - will retry
        await self._update_status(
            notification.id,
            NotificationStatus.FAILED,
            error=str(e)
        )
```

#### 6. Delivery

Сообщения доставляются пользователям:
- С изображением → `Bot.send_photo(caption=...)`
- Без изображения → `Bot.send_message(text=...)`
- Rate limiting: максимум 30 сообщений в секунду

---

## Что готово

### ✅ Backend API - 100%

1. **Database**:
   - ✅ PostgreSQL + Alembic migrations
   - ✅ 11 таблиц (users, markets, bets, missions, user_missions, transactions, wallet_addresses, support_tickets, support_messages, telegram_notifications_queue, leaderboard_snapshots)
   - ✅ 20 тестовых рынков + seed data
   - ✅ 19 миссий

2. **API Endpoints**:
   - ✅ Auth (register, token)
   - ✅ Markets (list, detail, stats)
   - ✅ Bets (create, my, detail)
   - ✅ Users (profile, stats, public, ban/unban)
   - ✅ Missions (list, claim) - 19 миссий
   - ✅ Leaderboard (4 типа сортировки)
   - ✅ Admin (stats, markets CRUD, users management, broadcast)
   - ✅ Support (tickets, messages, admin replies)
   - ✅ Scheduler (weekly rewards, cleanup)

3. **Features**:
   - ✅ JWT Authentication
   - ✅ Bet creation с автоматическим расчетом odds (AMM)
   - ✅ Market resolution (выплаты, обновление статистики)
   - ✅ Missions system с наградами (19 типов)
   - ✅ Rank system (Bronze → Grandmaster)
   - ✅ Transaction history
   - ✅ Ban system (ban/unban users)
   - ✅ Support tickets (create, reply, close)
   - ✅ Notification queue (TelegramQueueService)
   - ✅ Broadcast system (text + images, rate limiting)
   - ✅ S3/MinIO integration (image storage)
   - ✅ Swagger documentation

### ✅ Telegram Worker - 100%

1. **Функционал**:
   - ✅ Queue processing (30 msg/sec rate limit)
   - ✅ Error handling (temporary vs permanent failures)
   - ✅ Retry logic (до 5 попыток)
   - ✅ Photo support (send_photo with caption)
   - ✅ Metadata parsing (JSON)
   - ✅ Status updates (PENDING → PROCESSING → SENT/FAILED)
   - ✅ Logging
   - ✅ Graceful shutdown

2. **Deployment**:
   - ✅ Standalone process
   - ✅ PM2 integration
   - ✅ Production-ready

### ✅ Telegram Bot - 100%

1. **Функционал**:
   - ✅ /start - Приветствие + регистрация
   - ✅ WebApp button (открывает Mini App)
   - ✅ Support tickets через FSM
   - ✅ Deep linking
   - ✅ Команды: /help, /support, /balance, /stats

2. **Integration**:
   - ✅ Backend API integration
   - ✅ Автоматическая регистрация
   - ✅ WebApp URL generation

### ✅ Mini App (Webapp) - 95%

1. **Страницы**:
   - ✅ Markets list с фильтрами
   - ✅ Market detail с созданием ставок
   - ✅ Profile с историей ставок
   - ✅ Missions с claim rewards
   - ✅ Leaderboard с сортировкой
   - ✅ Support tickets (в разработке UI)
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
- ⚠️ Support tickets UI (базовая версия)

### ✅ Admin Panel - 100%

1. **Разделы**:
   - ✅ Dashboard (статистика, Chart.js графики)
   - ✅ Markets (список, create, edit, resolve, delete)
   - ✅ Users (список, edit balance, ban/unban, view activity)
   - ✅ Broadcast (rich editor, emoji picker, image upload, queue) - NEW
   - ✅ Support (tickets list, reply, close)

2. **Broadcast Features**:
   - ✅ Rich text editor с форматированием
   - ✅ 32 emoji picker
   - ✅ Image upload с preview
   - ✅ Character counter (динамический лимит)
   - ✅ Target selection (all/specific user)
   - ✅ Parse mode (HTML/Markdown)
   - ✅ Queue integration
   - ✅ Success feedback

3. **Функционал**:
   - ✅ Market resolution (YES/NO/CANCELLED)
   - ✅ Promote/Unpromote markets
   - ✅ Edit user balances
   - ✅ Ban/Unban users с причиной
   - ✅ View user bet history
   - ✅ Platform statistics
   - ✅ Support ticket management

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

**Ресурсы**:
- TON Connect SDK: https://github.com/ton-connect/sdk
- TON API: https://tonapi.io/
- TON Docs: https://docs.ton.org/

**Оценка**: 12-16 часов

### ⚠️ Support Tickets UI - 50% (Приоритет 2)

**Что готово**:
- ✅ Backend API (create, list, messages, reply)
- ✅ Database models
- ✅ Admin panel UI

**Что требуется**:
- ❌ Mini App UI для пользователей
- ❌ Telegram bot integration (inline создание тикетов)
- ❌ Push уведомления о новых сообщениях

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
8. Broadcast system (text + images)
9. Support tickets workflow

**Оценка**: 6-8 часов

### ⚠️ Production Monitoring - 20% (Приоритет 4)

**Что готово**:
- ✅ PM2 process manager
- ✅ Nginx reverse proxy
- ✅ SSL certificates

**Что требуется**:
- ❌ Sentry integration (error tracking)
- ❌ Grafana + Prometheus (metrics)
- ❌ Uptime monitoring (UptimeRobot)
- ❌ Database backups automation
- ❌ Alerts (Telegram bot)

**Оценка**: 4-6 часов

---

## Запуск проекта

### Предварительные требования

- Docker + Docker Compose
- Python 3.11+
- PostgreSQL 15+ (опционально, есть в Docker)
- Redis 7+ (опционально, есть в Docker)
- MinIO (опционально, есть в Docker)

### 1. Через Docker Compose (Рекомендуется для Development)

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
- MinIO: localhost:9000

### 2. Production Setup (PM2)

**На production сервере используется PM2 для управления процессами**

#### Установка зависимостей:

```bash
cd /home/ThePredMain

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Bot
cd ../bot
pip install -r requirements.txt

# Webapp
cd ../webapp
pip install -r requirements.txt

# Admin
cd ../admin
pip install -r requirements.txt

# Landing
cd ../landing
pip install -r requirements.txt
```

#### PM2 Configuration:

```javascript
// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'backend',
      script: 'venv/bin/uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8000',
      cwd: '/home/ThePredMain/backend',
      env: {
        POSTGRES_HOST: 'localhost',
        DATABASE_URL: 'postgresql://...',
        ...
      }
    },
    {
      name: 'telegram-worker',
      script: 'venv/bin/python',
      args: 'telegram_worker.py',
      cwd: '/home/ThePredMain/backend',
      env: {
        BOT_TOKEN: '...',
        POSTGRES_HOST: 'localhost',
        ...
      }
    },
    {
      name: 'bot',
      script: 'python',
      args: 'main.py',
      cwd: '/home/ThePredMain/bot',
      env: {
        BOT_TOKEN: '...',
        API_URL: 'http://localhost:8000',
        ...
      }
    },
    {
      name: 'webapp',
      script: 'python',
      args: 'main.py',
      cwd: '/home/ThePredMain/webapp'
    },
    {
      name: 'admin',
      script: 'python',
      args: 'main.py',
      cwd: '/home/ThePredMain/admin'
    },
    {
      name: 'landing',
      script: 'python',
      args: 'main.py',
      cwd: '/home/ThePredMain/landing'
    }
  ]
};
```

#### Команды PM2:

```bash
# Запустить все сервисы
pm2 start ecosystem.config.js

# Проверить статус
pm2 status

# Логи
pm2 logs
pm2 logs backend
pm2 logs telegram-worker

# Перезапуск
pm2 restart all
pm2 restart backend
pm2 restart telegram-worker

# Остановка
pm2 stop all
pm2 delete all
```

### 3. Database Migrations

```bash
# Development
cd backend
POSTGRES_HOST=localhost alembic upgrade head

# Production (через Docker)
docker exec -it thepredmain-backend-1 alembic upgrade head

# Создать новую миграцию
alembic revision -m "Description"

# Показать текущую версию
alembic current

# История миграций
alembic history
```

### 4. Seed Data

```bash
# Development
cd backend
POSTGRES_HOST=localhost python3 seed_data.py

# Production
docker exec -it thepredmain-backend-1 python seed_data.py
```

---

## Разработка

### Environment Variables

**Главный .env файл** (в корне проекта):

```env
# ============ Database ============
POSTGRES_DB=thepred
POSTGRES_USER=thepred
POSTGRES_PASSWORD=SUPER_STRONG_PASSWORD_CHANGE_ME_123!@#
POSTGRES_HOST=localhost  # или postgres для Docker

# ============ JWT ============
JWT_SECRET=YOUR_SUPER_SECRET_JWT_KEY_MINIMUM_32_CHARS_RANDOM
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# ============ Application ============
DEBUG=false
INITIAL_PRED_BALANCE=10000
REFERRAL_BONUS_PRED=1000

# ============ Telegram Bot ============
BOT_TOKEN=8067436515:AAGHg6_ojgsnBmREI1U9Sr_iibgXYGInml0
BOT_USERNAME=The_Pred_Bot

# ============ WebApp ============
WEBAPP_URL=https://thepred.tech
WEBAPP_SECRET_KEY=WEBAPP_SECRET_KEY_RANDOM_STRING_32_CHARS
DEV_MODE=false

# ============ Admin ============
ADMIN_PASSWORD=STRONG_ADMIN_PASSWORD_CHANGE_ME
ADMIN_SECRET_KEY=ADMIN_SECRET_KEY_RANDOM_32_CHARS

# ============ MinIO S3 Storage ============
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=Ivanbunin110818
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=admin
S3_SECRET_KEY=Ivanbunin110818
S3_BUCKET=thepred-events
S3_PUBLIC_URL=https://thepred.store

# ============ API URL ============
API_URL=http://localhost:8000

# ============ Redis ============
REDIS_HOST=localhost
REDIS_PORT=6379
```

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

# Production
make prod-build      # Собрать для production
make prod-up         # Запустить в production режиме
make prod-rebuild-app # Пересобрать app сервисы
make prod-status     # Показать статус production
make prod-logs       # Production логи
```

### Git Workflow

```bash
# Проверить статус
git status

# Добавить изменения
git add .

# Коммит
git commit -m "Description"

# Push
git push origin main

# Pull последние изменения
git pull origin main
```

### Debugging

**Backend (FastAPI)**:
```bash
# Включить debug режим
DEBUG=true uvicorn app.main:app --reload

# Swagger UI
http://localhost:8000/docs

# Логи SQL запросов
# В config.py установить echo=True в create_async_engine
```

**Telegram Worker**:
```bash
# Запустить с подробными логами
BOT_TOKEN="..." python telegram_worker.py

# PM2 логи
pm2 logs telegram-worker --lines 100
```

**Database queries**:
```bash
# PostgreSQL shell
psql -U thepred -d thepred

# Проверить очередь
SELECT id, telegram_id, status, notification_type, created_at
FROM telegram_notifications_queue
ORDER BY created_at DESC
LIMIT 10;

# Проверить pending сообщения
SELECT COUNT(*)
FROM telegram_notifications_queue
WHERE status = 'PENDING';
```

---

## Production Deployment

### 1. Server Requirements

- Ubuntu 22.04 LTS (рекомендуется)
- 2 CPU cores minimum
- 4 GB RAM minimum
- 20 GB SSD storage
- Domain с SSL

### 2. Initial Setup

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Install Node.js + PM2
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2

# Install PostgreSQL client tools
sudo apt install postgresql-client -y

# Clone project
git clone https://github.com/Mobiss11/ThePredMain.git
cd ThePredMain
```

### 3. Environment Configuration

```bash
# Create production .env
cp .env.example .env
nano .env

# Set production values:
# - Strong passwords
# - Production URLs
# - Real BOT_TOKEN
# - Production S3_PUBLIC_URL
# - DEBUG=false
```

### 4. Database Setup

```bash
# Start PostgreSQL via Docker
docker-compose up -d postgres

# Wait for startup
sleep 10

# Run migrations
cd backend
source venv/bin/activate
POSTGRES_HOST=localhost alembic upgrade head

# Seed initial data (optional)
POSTGRES_HOST=localhost python seed_data.py
```

### 5. Nginx Configuration

```bash
sudo apt install nginx -y

# Create nginx config
sudo nano /etc/nginx/sites-available/thepred
```

**Nginx config**:
```nginx
# Main webapp
server {
    listen 80;
    server_name thepred.tech www.thepred.tech;

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
}

# Admin panel (subdomain or path)
server {
    listen 80;
    server_name admin.thepred.tech;

    location / {
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Landing page
server {
    listen 80;
    server_name landing.thepred.tech;

    location / {
        proxy_pass http://localhost:8003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# MinIO S3 (for images)
server {
    listen 80;
    server_name thepred.store;

    location / {
        proxy_pass http://localhost:9000;
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

### 6. SSL Certificates

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d thepred.tech -d www.thepred.tech -d admin.thepred.tech -d thepred.store
```

### 7. Start Services

```bash
# Start via PM2
pm2 start ecosystem.config.js

# Check status
pm2 status

# Save PM2 config
pm2 save

# Enable PM2 on startup
pm2 startup
# Follow instructions to enable startup
```

### 8. Monitoring

```bash
# PM2 monitoring
pm2 monit

# Logs
pm2 logs

# Restart all
pm2 restart all

# Stop all
pm2 stop all

# Delete all
pm2 delete all
```

### 9. Database Backups

```bash
# Create backup directory
mkdir -p /home/ThePredMain/backups

# Backup script
cat > /home/ThePredMain/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec -it thepredmain-postgres-1 pg_dump -U thepred thepred > /home/ThePredMain/backups/backup_$DATE.sql
# Keep only last 7 days
find /home/ThePredMain/backups -name "backup_*.sql" -mtime +7 -delete
EOF

chmod +x /home/ThePredMain/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add line:
0 2 * * * /home/ThePredMain/backup.sh
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

## Заключение

**ThePred** - это комплексная платформа prediction markets с полной интеграцией в Telegram экосистему.

### Текущий статус: 97% Complete

**Готово**:
- ✅ Backend API (FastAPI) - 100%
- ✅ Telegram Bot (aiogram) - 100%
- ✅ Telegram Worker (queue processor) - 100%
- ✅ Mini App (Quart) - 95%
- ✅ Admin Panel (Quart) - 100%
- ✅ Landing Page - 100%
- ✅ Broadcast System - 100%
- ✅ Support Tickets (backend) - 100%
- ✅ Database Schema - 100%
- ✅ Migrations - 100%

**В разработке**:
- ⚠️ TON Wallet Integration - 0%
- ⚠️ Support Tickets UI (user) - 50%
- ⚠️ Testing - 0%
- ⚠️ Production Monitoring - 20%

### Контакты

- **Telegram Bot**: @The_Pred_Bot
- **Website**: https://thepred.tech
- **Admin Panel**: https://admin.thepred.tech (internal)
- **GitHub**: https://github.com/Mobiss11/ThePredMain

### Команды

```bash
make help    # Все доступные команды
make up      # Запустить проект
make logs    # Посмотреть логи
make health  # Проверить статус
```

---

**Последнее обновление**: 8 ноября 2025
**Автор**: ThePred Team
**Версия**: 1.2
