# Deployment Guide: Missions System

## Что было сделано

### 1. Backend ✅
- Добавлен тип миссии `subscription` для подписки на канал
- Создан `MissionService` для автоматического обновления прогресса миссий
- Добавлены поля: `channel_id`, `channel_username`, `channel_url`, `custom_icon_url` в модель Mission
- Обновлены API endpoints:
  - `GET /missions/{user_id}` - получить миссии с автообновлением прогресса
  - `POST /missions/claim/{user_id}/{mission_id}` - получить награду
  - `POST /missions/check-subscription/{user_id}/{mission_id}` - проверить подписку
- Добавлены админ API:
  - `GET /admin/missions` - список всех миссий
  - `POST /admin/missions` - создать миссию
  - `PUT /admin/missions/{id}` - обновить миссию
  - `DELETE /admin/missions/{id}` - удалить миссию
  - `GET /admin/missions/stats` - статистика миссий

### 2. Frontend Webapp ✅
- Полностью обновлен UI миссий с динамической загрузкой
- Добавлены табы: Daily, Weekly, Achievements
- Прогресс-бары для каждой миссии
- Кнопки для claim наград
- Поддержка subscription миссий (открытие канала + проверка)
- Авто-обновление каждые 30 секунд

### 3. Миссии ✅
Создано 20 типовых миссий:
- **Daily** (3): Ежедневная ставка, Победа дня, Ежедневный вход
- **Weekly** (3): Недельный марафон, Мастер недели, Огненная серия
- **Achievements** (14): От "Первая ставка" до "Неудержимый"

### 4. Иконки ✅
- Создан `mission_icons.json` с 30+ эмодзи иконками
- Поддержка custom_icon_url для загрузки своих иконок

## Deployment Steps

### 1. Применить миграции

```bash
# На production сервере
cd /Users/alluc/Documents/ThePred/backend

# Применить SQL скрипт вручную
psql -U postgres -d your_database < apply_missions_migrations.sql

# Или через Docker
cat apply_missions_migrations.sql | docker exec -i your_postgres_container psql -U postgres -d your_database
```

### 2. Инициализировать миссии

```bash
cd /Users/alluc/Documents/ThePred/backend

# Запустить скрипт инициализации миссий
python3 app/init_missions.py
```

### 3. Перезапустить сервисы

```bash
pm2 restart backend
pm2 restart webapp
pm2 restart admin
```

### 4. Проверить работу

1. **Откройте миссии (User)**: http://localhost:8001/missions
2. **Проверьте API**: http://localhost:8000/docs#/missions
3. **Админка миссий**: http://localhost:8002/missions

## Что осталось сделать

### 1. Админка для миссий ✅ ГОТОВО
Админ панель для управления миссиями полностью реализована!

**Реализовано:**
- ✅ Страница `/missions` со списком миссий
- ✅ Форма создания миссии (все поля + requirements)
- ✅ Форма редактирования миссий
- ✅ Удаление миссий с подтверждением
- ✅ Поддержка всех типов (daily/weekly/achievement/subscription)
- ✅ Выбор emoji иконок (16 вариантов)
- ✅ Поддержка custom_icon_url
- ✅ Поля для subscription миссий (channel_id, channel_username, channel_url)
- ✅ Визуальный редактор requirements (без ручного JSON)
- ✅ Toast уведомления
- ✅ Proxy routes в admin/main.py (GET, POST, PUT, DELETE)

**Как использовать:**
1. Открыть http://localhost:8002/missions
2. Нажать "Create Mission"
3. Заполнить форму:
   - Выбрать emoji иконку или ввести custom URL
   - Для subscription типа: заполнить Channel ID, Username, URL
   - Выбрать тип требования и указать значение
4. Сохранить миссию

### 2. Профиль - секция достижений ⚠️
Добавить на страницу профиля секцию "Достижения":
- Показать все achievements с типом `achievement`
- Галочка если completed
- Прогресс если не completed
- Иконка + название

### 3. Автоматический reset миссий (Cron) ⚠️
Настроить автоматический reset daily/weekly миссий:

```python
# Добавить в scheduler или cron
from app.services.mission_service import MissionService

# Daily reset (каждый день в 00:00 UTC)
@schedule.daily(hour=0, minute=0)
async def reset_daily_missions():
    async with AsyncSessionLocal() as db:
        await MissionService.reset_daily_missions(db)

# Weekly reset (каждый понедельник в 00:00 UTC)
@schedule.weekly(day=0, hour=0, minute=0)
async def reset_weekly_missions():
    async with AsyncSessionLocal() as db:
        await MissionService.reset_weekly_missions(db)
```

### 4. Хуки для автообновления прогресса
Добавить вызов `MissionService.check_and_update_all_missions()` после:
- Создания ставки
- Завершения ставки (выигрыш/проигрыш)
- Регистрации реферала

## API Endpoints

### User Missions
- `GET /missions/{user_id}` - Получить миссии с прогрессом
- `POST /missions/claim/{user_id}/{mission_id}` - Получить награду
- `POST /missions/check-subscription/{user_id}/{mission_id}` - Проверить подписку

### Admin Missions
- `GET /admin/missions` - Список миссий (filter: type)
- `POST /admin/missions` - Создать миссию
- `PUT /admin/missions/{id}` - Обновить миссию
- `DELETE /admin/missions/{id}` - Удалить миссию
- `GET /admin/missions/stats` - Статистика

## Requirements JSON Examples

```json
// Сделать N ставок
{"bets_count": 5}

// Выиграть N раз
{"wins_count": 10}

// Win streak
{"win_streak": 3}

// Ставки на категорию
{"category_bets": {"category": "Crypto", "count": 3}}

// Рефералы
{"referrals_count": 1}

// Ежедневные ставки
{"daily_bets": 3}

// Недельные ставки
{"weekly_bets": 20}

// Подписка на канал
{"subscription": true}
```

## Icon Names

См. `mission_icons.json` для полного списка:
- Daily: 🎯 📅 🏆 🔥 💰
- Weekly: 📊 🌟 ⚡ 💎 👑
- Achievements: 🎯 🌱 🥇 🔥 📈 🎖️ 🏅 ₿ ⚽ 🗳️ 👥 🎁 🚀
- Subscription: 📢 👨‍👩‍👧‍👦 📰 🤝

## Troubleshooting

### Миграции не применились
```sql
-- Проверить текущую схему
\d missions

-- Применить вручную
ALTER TABLE missions ADD COLUMN IF NOT EXISTS channel_id VARCHAR(255);
```

### Прогресс не обновляется
- Проверить: `MissionService.check_and_update_all_missions()` вызывается при загрузке миссий
- Проверить логи backend: должны быть записи о проверке миссий

### Subscription не работает
- Проверить BOT_TOKEN в .env
- Проверить что бот админ в канале
- Проверить channel_id (должен быть с @)

## Files Modified/Created

### Backend
- `app/models/mission.py` - добавлены поля
- `app/services/mission_service.py` - новый сервис
- `app/api/endpoints/missions.py` - обновлены endpoints
- `app/api/endpoints/admin.py` - добавлены admin endpoints
- `app/init_missions.py` - обновлен список миссий
- `alembic/versions/4abc70c234d7_add_subscription_mission_fields.py` - миграция

### Frontend
- `webapp/templates/missions.html` - полностью переписан
- `webapp/main.py` - добавлены proxy routes

### Other
- `mission_icons.json` - библиотека иконок
- `apply_missions_migrations.sql` - SQL для применения миграций

## Support

При проблемах проверить:
1. Применены ли все миграции
2. Перезапущены ли сервисы
3. Инициализированы ли миссии
4. BOT_TOKEN в .env для subscription миссий
