# ThePred - Remaining Tasks

**Last Updated**: 31 октября 2025
**Current Progress**: 95% Complete 🎉

---

## ✅ Что готово:

### Backend API - 100%
- ✅ PostgreSQL + Alembic migrations
- ✅ 6 таблиц (users, markets, bets, missions, transactions, wallet_addresses)
- ✅ 20 тестовых рынков + seed data
- ✅ Auth, Markets, Bets, Users APIs
- ✅ Missions system (5 missions)
- ✅ Leaderboard API (profit, win_rate, win_streak, total_wins sorting)
- ✅ Admin Panel API (stats, market management, user management)

### Webapp - 95%
- ✅ Quart + Jinja2 + Tailwind CSS
- ✅ Полная интеграция с Backend API
- ✅ Динамическая загрузка рынков
- ✅ Создание ставок
- ✅ Профиль пользователя
- ✅ Система миссий с claim rewards
- ✅ Leaderboard с сортировкой
- ✅ Admin Panel UI (4 таба: Stats, Markets, Users, Create)
- ⚠️ TON Wallet UI готов, но не интегрирован

### Bot - 100%
- ✅ Упрощен до приветствия + webapp button
- ✅ Регистрация через Backend API
- ✅ WebApp integration

---

## 🚀 Что осталось сделать:

### Приоритет 1: TON Wallet Integration (8-10 часов) 💎

**Frontend:**
1. Подключить TON Connect SDK
2. Реализовать Connect/Disconnect wallet
3. Показывать TON адрес и баланс
4. UI для Deposit TON
5. UI для Withdraw TON

**Backend:**
1. Создать эндпоинт `/wallet/connect` (сохранить TON адрес)
2. Создать эндпоинт `/wallet/deposit/initiate` (генерировать deposit адрес)
3. Создать эндпоинт `/wallet/deposit/confirm` (проверить транзакцию)
4. Создать эндпоинт `/wallet/withdraw` (отправить TON)
5. Реализовать конвертацию TON ↔ PRED
6. TON blockchain integration (TON API или SDK)
7. Обработка pending транзакций

**Файлы для изменения:**
- `backend/app/api/endpoints/wallet.py` - добавить TON endpoints
- `webapp/templates/profile.html` - TON wallet UI
- `webapp/static/js/app.js` - TON Connect integration
- `webapp/api_client.py` - TON wallet methods

**TON Connect SDK:**
```html
<script src="https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.min.js"></script>
```

**Конвертация:**
- 1 TON = 1000 PRED (example rate)
- Min deposit: 1 TON
- Min withdraw: 10 TON

---

### Приоритет 2: Тестирование (2-3 часа) 🧪

**Локальное тестирование:**
1. Запустить все сервисы через Docker Compose
2. Протестировать webapp pages:
   - `/` - Markets list
   - `/market/<id>` - Market detail
   - `/profile` - User profile
   - `/missions` - Missions
   - `/leaderboard` - Leaderboard
   - `/admin` - Admin panel

**Функциональное тестирование:**
3. Создать ставки на разные рынки
4. Проверить обновление балансов
5. Claim missions rewards
6. Проверить leaderboard rankings
7. Admin panel:
   - Create new market
   - Resolve market (YES/NO/CANCELLED)
   - Promote market
   - Edit user balance
   - View user activity

**API тестирование:**
8. Проверить все backend endpoints через Swagger (`http://localhost:8000/docs`)
9. Проверить resolve market logic (выплаты, статистика)

**Команды для запуска:**
```bash
# Backend
cd backend
source venv/bin/activate
POSTGRES_HOST=localhost uvicorn app.main:app --reload --port 8000

# Webapp
cd webapp
python3 main.py

# Bot
cd bot
python3 main.py

# Docker (все вместе)
docker-compose up -d
docker-compose logs -f
```

---

### Приоритет 3: Production Deployment (4-6 часов) 🚀

**1. Server Setup:**
- VPS/Cloud server (DigitalOcean, AWS, Hetzner)
- Ubuntu 22.04 LTS
- Docker + Docker Compose installed
- Domain name configured

**2. Environment Configuration:**
```bash
# Backend .env
DATABASE_URL=postgresql://user:password@postgres:5432/thepred
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<production-secret-key>
SENTRY_DSN=<sentry-dsn>
DEBUG=false

# Bot .env
BOT_TOKEN=<telegram-bot-token>
API_URL=http://backend:8000
WEBAPP_URL=https://your-domain.com

# Webapp .env
API_URL=http://backend:8000
WEBAPP_SECRET_KEY=<webapp-secret-key>
DEV_MODE=false
```

**3. Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
    }
}
```

**4. SSL Certificates:**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

**5. Docker Production Setup:**
- Обновить `docker-compose.yml` для production
- Настроить volumes для persistence
- Настроить restart policies
- Настроить logging

**6. Monitoring & Logs:**
- Sentry для error tracking
- Логи через Docker logs
- Мониторинг через Grafana/Prometheus (опционально)

**7. Database Backup:**
```bash
# Backup script
docker exec postgres pg_dump -U user thepred > backup_$(date +%Y%m%d).sql
```

---

## 📝 Notes:

### TON Integration Resources:
- TON Connect SDK: https://github.com/ton-connect/sdk
- TON API: https://tonapi.io/
- TON Docs: https://docs.ton.org/

### Testing Checklist:
- [ ] All webapp pages load correctly
- [ ] Bets can be created successfully
- [ ] Missions can be claimed
- [ ] Leaderboard shows correct rankings
- [ ] Admin panel stats load
- [ ] Markets can be created
- [ ] Markets can be resolved (payouts work)
- [ ] User balances update correctly
- [ ] Bot sends webapp button

### Production Checklist:
- [ ] Server provisioned
- [ ] Domain configured
- [ ] SSL certificates installed
- [ ] Environment variables set
- [ ] Docker containers running
- [ ] Database backed up
- [ ] Monitoring configured
- [ ] Bot webhook configured
- [ ] Webapp accessible via domain

---

## 🎯 Next Steps:

1. **TON Wallet** - Most important feature for production
2. **Testing** - Ensure everything works correctly
3. **Deploy** - Launch to production

**Estimated Time to Production: 14-19 hours**

---

## 🔧 Quick Commands:

```bash
# Start everything locally
docker-compose up -d

# Check logs
docker-compose logs -f backend
docker-compose logs -f webapp
docker-compose logs -f bot

# Stop everything
docker-compose down

# Backend migrations
cd backend
POSTGRES_HOST=localhost alembic upgrade head

# Seed data
cd backend
POSTGRES_HOST=localhost python3 seed_data.py

# Backend API docs
open http://localhost:8000/docs

# Webapp
open http://localhost:8001
```

---

**Status**: 95% Complete
**Remaining Work**: TON Wallet → Testing → Production Deploy
