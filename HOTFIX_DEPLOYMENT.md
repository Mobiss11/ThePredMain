# 🚨 HOTFIX: Исправление миграций Alembic

## Проблема
- **Multiple head revisions** в Alembic
- Backend не запускается из-за конфликта миграций
- Ошибка: `Multiple head revisions are present for given argument 'head'`

## Решение
Объединены ветки миграций - теперь `leaderboard_rewards` миграция идет после `update_mission_icon_size`.

---

## Шаги для деплоя (на production сервере)

### 1. Остановить сервисы
```bash
cd ~/ThePredMain  # или путь к вашему проекту
pm2 stop all
# или через docker:
# docker-compose down
```

### 2. Pull изменений
```bash
git pull origin main
```

**Изменения:**
- Commit `823474c` - Fix: Объединены ветки миграций Alembic

### 3. Применить миграцию
```bash
cd backend

# Проверить текущее состояние
POSTGRES_HOST=localhost alembic heads
# Должен показать только одну head: b8c9d4e5f6a7

# Применить миграцию
POSTGRES_HOST=localhost alembic upgrade head
```

**Что создаст миграция:**
- Таблица `leaderboard_rewards` (если еще не существует)
- Дефолтные награды для недели и месяца

### 4. Перезапустить сервисы
```bash
pm2 restart all
# или через docker:
# docker-compose up -d
```

### 5. Проверить логи
```bash
pm2 logs backend --lines 50
# или docker:
# docker logs backend -f
```

**Должны увидеть:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade update_mission_icon_size -> b8c9d4e5f6a7, add leaderboard rewards
```

### 6. Проверить работоспособность

```bash
# Проверить API
curl https://thepred.tech/api/leaderboard?period=week
curl https://thepred.tech/api/leaderboard/rewards/week

# Проверить admin leaderboard
curl https://thepred.tech/admin/leaderboard?period=week
curl https://thepred.tech/admin/leaderboard/rewards
```

**Ожидаемый результат:**
- ✅ Backend запустился без ошибок
- ✅ `/api/leaderboard?period=week` возвращает лидерборд
- ✅ `/api/leaderboard/rewards/week` возвращает награды
- ✅ Webapp показывает лидерборд с наградами
- ✅ Admin panel показывает лидерборд и CRUD для наград

---

## Если что-то пошло не так

### Ошибка: "Target database is not up to date"
```bash
# Показать историю миграций
POSTGRES_HOST=localhost alembic history

# Показать текущую версию БД
POSTGRES_HOST=localhost alembic current

# Применить конкретную миграцию
POSTGRES_HOST=localhost alembic upgrade b8c9d4e5f6a7
```

### Ошибка: "Table already exists"
Если таблица `leaderboard_rewards` уже существует:
```bash
# Войти в PostgreSQL
docker exec -it thepred-postgres psql -U thepred -d thepred

# Пометить миграцию как выполненную
# (замените '79fa342a014c' на текущую версию из alembic current)
INSERT INTO alembic_version VALUES ('b8c9d4e5f6a7');

# Проверить
SELECT * FROM alembic_version;
\q
```

### Backend все еще не запускается
```bash
# Откатить миграцию
POSTGRES_HOST=localhost alembic downgrade -1

# Применить заново
POSTGRES_HOST=localhost alembic upgrade head

# Проверить логи
pm2 logs backend --lines 100
```

---

## Резервный план (Rollback)

Если нужно откатить изменения:

```bash
# 1. Откатить код
git reset --hard f9e5105

# 2. Откатить миграцию БД
cd backend
POSTGRES_HOST=localhost alembic downgrade update_mission_icon_size

# 3. Перезапустить
pm2 restart all
```

---

## Дата: 6 ноября 2025
## Автор: Claude Code
## Срочность: 🚨 CRITICAL - Backend не запускается
