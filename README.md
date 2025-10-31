# 🎯 ThePred - Prediction Markets Platform

> Telegram Mini App для prediction markets с двойной валютной системой (PRED & TON)

![ThePred Banner](https://via.placeholder.com/1200x300/0A0E1A/FFD700?text=ThePred+-+Prediction+Markets)

## 📋 О проекте

**ThePred** - это инновационная платформа prediction markets в Telegram, которая позволяет пользователям делать ставки на будущие события используя внутреннюю валюту PRED или реальную криптовалюту TON.

### 🌟 Ключевые фичи

- 💎 **Двойная валютная система**: PRED (игровая) и TON (реальная)
- 🎮 **Геймификация**: ранги, миссии, достижения, лидерборды
- 🤖 **Telegram Bot**: быстрые ставки через команды
- 📱 **Mini App**: красивый веб-интерфейс с премиум дизайном
- 🎁 **Реферальная система**: 1,000 PRED за каждого приглашенного друга
- 📊 **Админ панель**: управление пользователями, маркетами, миссиями

## 🏗️ Архитектура

Проект построен на микросервисной архитектуре:

```
ThePred/
├── backend/          # FastAPI - REST API
├── bot/              # aiogram - Telegram Bot
├── webapp/           # Quart - Mini App Frontend
├── admin/            # Quart - Admin Panel
└── database/         # PostgreSQL schemas & migrations
```

### Технологический стек

**Backend:**
- FastAPI 0.109.0
- PostgreSQL 15
- Redis 7
- SQLAlchemy 2.0
- Pydantic

**Bot:**
- aiogram 3.3.0
- asyncpg
- aiohttp

**Frontend (Mini App & Admin):**
- Quart 0.19.4
- Jinja2 3.1.3
- Tailwind CSS
- Telegram Web App SDK

**Infrastructure:**
- Docker & Docker Compose
- Nginx (reverse proxy)

## 🚀 Быстрый старт

### Требования

- Python 3.13+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- Telegram Bot Token

### 1. Клонирование репозитория

```bash
git clone https://github.com/yourusername/ThePred.git
cd ThePred
```

### 2. Настройка окружения

```bash
# Копируем .env.example в .env
cp .env.example .env

# Редактируем .env и заполняем необходимые переменные
nano .env
```

**Обязательные переменные:**

```env
# Telegram
BOT_TOKEN=your_bot_token_from_botfather
WEBAPP_URL=https://your-domain.com

# Database
POSTGRES_PASSWORD=strong_password_here

# JWT
JWT_SECRET=super_secret_key_here

# Admin
ADMIN_PASSWORD=admin_password_here
```

### 3. Запуск через Docker

```bash
# Сборка и запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f
```

Сервисы будут доступны по адресам:
- Backend API: http://localhost:8000
- Mini App: http://localhost:8001
- Admin Panel: http://localhost:8002

### 4. Инициализация базы данных

База данных автоматически инициализируется при первом запуске через `database/scripts/init.sql`

Проверить можно командой:

```bash
docker-compose exec postgres psql -U thepred -d thepred -c "\dt"
```

## 📦 Локальная разработка (без Docker)

### Backend API

```bash
cd backend

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Telegram Bot

```bash
cd bot

# Установка зависимостей
pip install -r requirements.txt

# Запуск бота
python main.py
```

### Mini App

```bash
cd webapp

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
python main.py
```

### Admin Panel

```bash
cd admin

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
python main.py
```

## 📚 API Документация

После запуска Backend API документация доступна по адресам:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Основные endpoints:

**Auth:**
- `POST /auth/telegram` - Авторизация через Telegram
- `GET /auth/verify` - Проверка токена

**Users:**
- `GET /users/profile/{user_id}` - Профиль пользователя
- `GET /users/balance/{user_id}` - Баланс пользователя
- `POST /users/referral/{user_id}` - Активация реферального кода

**Markets:**
- `GET /markets` - Список маркетов
- `GET /markets/{id}` - Детали маркета
- `POST /markets` - Создание маркета

**Bets:**
- `POST /bets` - Сделать ставку
- `GET /bets/history/{user_id}` - История ставок
- `GET /bets/active/{user_id}` - Активные ставки

**Missions:**
- `GET /missions/{user_id}` - Доступные миссии
- `POST /missions/claim/{user_id}/{mission_id}` - Получить награду

## 🎮 Геймификация

### Система рангов

| Ранг | Требование | Комиссия PRED | Комиссия TON |
|------|-----------|---------------|--------------|
| 🥉 Bronze | 0-100 ставок | 1% | 5% |
| 🥈 Silver | 100-500 ставок | 0.8% | 4.5% |
| 🥇 Gold | 500-2000 ставок | 0.6% | 4% |
| 💎 Diamond | 2000-5000 ставок | 0.4% | 3% |
| 🌟 Legend | 5000+ ставок | 0.2% | 2% |

### Daily Missions

- 🎯 Make 3 Bets → +500 PRED
- 🏆 Win a Bet → +1,000 PRED
- 👥 Invite a Friend → +1,000 PRED

### Weekly Challenges

- 🔥 10 Win Streak → +5,000 PRED
- 💰 Top 10 Profit → +1,000 PRED
- 📊 Market Creator (100+ bets) → +5,000 PRED

## 🤖 Telegram Bot Commands

```
/start - Регистрация и получение 1,000 PRED
/balance - Проверить баланс
/markets - Топ-5 активных маркетов
/bet <market_id> <yes/no> <amount> - Быстрая ставка
/referral - Реферальная ссылка
/help - Помощь
```

## 🔒 Безопасность

- JWT токены для авторизации
- Rate limiting: 100 req/min per user
- SQL injection protection (SQLAlchemy ORM)
- XSS protection в Mini App
- HTTPS обязательно для production

## 📊 Мониторинг

Проект готов к интеграции с:

- Sentry (error tracking)
- Prometheus + Grafana (метрики)
- Telegram alerts для критических ошибок

## 🚢 Деплой в Production

ThePred поддерживает два режима работы:

### 🔵 Development (локальная разработка)

```bash
# Запуск локально без доменов
docker-compose up -d

# Доступ:
# - Backend: http://localhost:8000
# - WebApp: http://localhost:8001
# - Admin: http://localhost:8002
# - Landing: http://localhost:8003
```

### 🔴 Production (с доменами и SSL)

**Полная инструкция**: [DEPLOYMENT.md](./DEPLOYMENT.md)

#### Краткая версия:

**1. Подготовка**

```bash
# Скопировать production .env
cp .env.production.example .env

# Заполнить все переменные (пароли, токены, домены)
nano .env
```

**2. Настроить DNS**

Добавить A-записи для доменов:
- `thepred.com` → IP сервера (лендинг)
- `thepred.tech` → IP сервера (веб-апп)

**3. Запустить production**

```bash
# Сборка и запуск с nginx
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Проверить статус
docker-compose -f docker-compose.prod.yml ps
```

**4. Получить SSL сертификаты**

См. подробную инструкцию: [SSL_SETUP.md](./SSL_SETUP.md)

```bash
# Автоматическое получение сертификатов
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  -d thepred.com -d www.thepred.com

docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  -d thepred.tech -d www.thepred.tech
```

**5. Production URLs**

После деплоя сервисы доступны по адресам:
- 🌐 **Лендинг**: https://thepred.com
- 📱 **WebApp**: https://thepred.tech
- ⚙️ **Admin**: http://YOUR_SERVER_IP:8002
- 🔒 **Backend**: Спрятан в internal network (безопасно)

### 📚 Документация по деплою

- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Полное руководство по production деплою
- **[SSL_SETUP.md](./SSL_SETUP.md)** - Настройка SSL сертификатов
- **[CLAUDE.md](./CLAUDE.md)** - Подробная техническая документация
- **[PREDICTION_MECHANICS.md](./PREDICTION_MECHANICS.md)** - Механика предсказаний

## 🧪 Тестирование

```bash
# Backend тесты
cd backend
pytest

# Интеграционные тесты
pytest tests/integration/

# E2E тесты
pytest tests/e2e/
```

## 📈 Roadmap

**MVP (Week 1-6):**
- [x] База данных и модели
- [x] Auth через Telegram
- [x] API endpoints
- [x] Telegram Bot
- [x] Mini App
- [x] Admin Panel
- [ ] TON интеграция
- [ ] Testing & bug fixes

**V2 (Month 2-3):**
- [ ] TON deposits/withdrawals
- [ ] Создание маркетов пользователями
- [ ] Battle Mode (PvP ставки)
- [ ] Squad Predictions
- [ ] Prediction Streaks
- [ ] NFT badges для топ игроков

**V3 (Month 3-6):**
- [ ] ThePred токен (TGE)
- [ ] DEX листинг
- [ ] Staking
- [ ] DAO governance
- [ ] Mobile apps (iOS/Android)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 💬 Support

- Telegram: [@ThePredSupport](https://t.me/ThePredSupport)
- Email: support@thepred.com
- Documentation: https://docs.thepred.com

## 🙏 Acknowledgments

- Telegram Team за Web App SDK
- TON Foundation за блокчейн инфраструктуру
- Open source сообщество за отличные инструменты

---

**Made with ❤️ for the crypto community**

🚀 **Let's predict the future together!** 🚀
