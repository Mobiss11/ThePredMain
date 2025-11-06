# Leaderboard Period Management - Deploy Guide

## 📋 Обзор

Система автоматического управления периодами лидерборда с расчетом наград и Telegram уведомлениями.

### Компоненты:
1. **Backend API** - эндпоинты для управления периодами
2. **telegram_worker.py** - воркер для отправки уведомлений из очереди
3. **leaderboard_scheduler.py** - воркер для автоматического закрытия периодов
4. **Admin Panel** - UI для ручного управления

## 🗄️ 1. Применить миграции БД

```bash
cd backend

# Применить миграцию для создания таблиц
POSTGRES_HOST=localhost alembic upgrade head

# Проверить что таблицы созданы
psql -h localhost -U thepred -d thepred -c "\dt"
# Должны быть таблицы:
# - leaderboard_periods
# - telegram_notifications_queue
```

**Созданные таблицы:**
- `leaderboard_periods` - история закрытых периодов
- `telegram_notifications_queue` - очередь Telegram уведомлений

## 🚀 2. Запустить воркеры

### Вариант A: PM2 (Рекомендуется для production)

```bash
cd backend

# Установить PM2 (если еще не установлен)
npm install -g pm2

# Запустить telegram_worker
pm2 start telegram_worker.py --name telegram-worker --interpreter python3

# Запустить leaderboard_scheduler
pm2 start leaderboard_scheduler.py --name leaderboard-scheduler --interpreter python3

# Проверить статус
pm2 list

# Просмотр логов
pm2 logs telegram-worker
pm2 logs leaderboard-scheduler

# Сохранить конфигурацию для автозапуска
pm2 save
pm2 startup
```

### Вариант B: Systemd (Linux)

Создать файл `/etc/systemd/system/telegram-worker.service`:

```ini
[Unit]
Description=ThePred Telegram Notifications Worker
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ThePred/backend
Environment="PATH=/home/ubuntu/ThePred/backend/venv/bin"
Environment="POSTGRES_HOST=localhost"
Environment="BOT_TOKEN=your-bot-token"
ExecStart=/home/ubuntu/ThePred/backend/venv/bin/python3 telegram_worker.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Создать файл `/etc/systemd/system/leaderboard-scheduler.service`:

```ini
[Unit]
Description=ThePred Leaderboard Period Scheduler
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ThePred/backend
Environment="PATH=/home/ubuntu/ThePred/backend/venv/bin"
Environment="POSTGRES_HOST=localhost"
ExecStart=/home/ubuntu/ThePred/backend/venv/bin/python3 leaderboard_scheduler.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Перезагрузить systemd
sudo systemctl daemon-reload

# Запустить сервисы
sudo systemctl start telegram-worker
sudo systemctl start leaderboard-scheduler

# Включить автозапуск
sudo systemctl enable telegram-worker
sudo systemctl enable leaderboard-scheduler

# Проверить статус
sudo systemctl status telegram-worker
sudo systemctl status leaderboard-scheduler

# Просмотр логов
sudo journalctl -u telegram-worker -f
sudo journalctl -u leaderboard-scheduler -f
```

### Вариант C: Docker Compose

Добавить в `docker-compose.yml`:

```yaml
services:
  # ... existing services ...

  telegram-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: python3 telegram_worker.py
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - BOT_TOKEN=${BOT_TOKEN}
      - POSTGRES_HOST=postgres
    restart: unless-stopped
    networks:
      - thepred-network

  leaderboard-scheduler:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: python3 leaderboard_scheduler.py
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - POSTGRES_HOST=postgres
    restart: unless-stopped
    networks:
      - thepred-network
```

```bash
# Запустить
docker-compose up -d telegram-worker leaderboard-scheduler

# Проверить логи
docker-compose logs -f telegram-worker
docker-compose logs -f leaderboard-scheduler
```

### Вариант D: Локальный запуск (Development)

```bash
cd backend

# Терминал 1: Telegram Worker
POSTGRES_HOST=localhost BOT_TOKEN=your-token python3 telegram_worker.py

# Терминал 2: Leaderboard Scheduler
POSTGRES_HOST=localhost python3 leaderboard_scheduler.py
```

## ⚙️ 3. Переменные окружения

Убедитесь что установлены:

```bash
# Backend API
export DATABASE_URL=postgresql://thepred:password@localhost:5432/thepred
export POSTGRES_HOST=localhost
export REDIS_URL=redis://localhost:6379/0

# Telegram Worker
export BOT_TOKEN=your-telegram-bot-token
# или
export TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Проверка
python3 -c "import os; print('BOT_TOKEN:', os.getenv('BOT_TOKEN', 'NOT SET'))"
```

## 📊 4. Мониторинг

### Проверка работы telegram_worker:

```bash
# PM2
pm2 logs telegram-worker --lines 50

# Systemd
sudo journalctl -u telegram-worker -n 50

# Docker
docker-compose logs telegram-worker --tail 50
```

**Ожидаемые логи:**
```
🚀 Telegram Notifications Consumer инициализирован
🚀 Запуск Telegram Notifications Consumer
📬 Получено N сообщений для обработки
✅ Отправлено сообщение 123 для 456789
⏸️ Пауза на 5 секунд после 20 сообщений...
```

### Проверка работы leaderboard_scheduler:

```bash
# PM2
pm2 logs leaderboard-scheduler --lines 50

# Systemd
sudo journalctl -u leaderboard-scheduler -n 50

# Docker
docker-compose logs leaderboard-scheduler --tail 50
```

**Ожидаемые логи:**
```
📅 Leaderboard Scheduler инициализирован
🚀 Запуск Leaderboard Scheduler
🌍 Все операции выполняются по UTC времени
⏰ Текущее время UTC: 2025-11-06 15:30:00 UTC
```

### Проверка очереди уведомлений:

В админ-панели:
- Открыть http://localhost:8002/leaderboard
- Посмотреть секцию "📨 Очередь уведомлений"

Или через API:
```bash
curl http://localhost:8000/admin/notifications/queue-stats
```

Ответ:
```json
{
  "total": 150,
  "pending": 10,
  "processing": 2,
  "sent": 135,
  "failed": 3
}
```

### Проверка истории периодов:

В админ-панели:
- Открыть http://localhost:8002/leaderboard
- Посмотреть таблицу "📜 История закрытых периодов"

Или через API:
```bash
curl http://localhost:8000/admin/leaderboard/periods?period_type=week
```

## 🧪 5. Тестирование

### 5.1. Настроить награды (если еще не настроены):

В админ-панели `http://localhost:8002/leaderboard`:
1. Переключиться на вкладку "Неделя" или "Месяц"
2. Нажать "+ Добавить" в секции наград
3. Создать награды, например:
   - Ранг 1-1: 10000 PRED
   - Ранг 2-2: 5000 PRED
   - Ранг 3-3: 2500 PRED
   - Ранг 4-10: 1000 PRED

### 5.2. Проверить текущую статистику:

В секции "📊 Текущий период" должно показываться:
- Участники (количество пользователей со ставками)
- Потенциальные награды (сумма наград)
- Настроенные награды (количество)

### 5.3. Закрыть период вручную:

1. В секции "🏁 Закрыть период" нажать красную кнопку
2. Подтвердить в диалоге
3. Должно появиться уведомление с результатом

**Что происходит при закрытии:**
1. Рассчитывается лидерборд за период (7 или 30 дней)
2. Начисляются награды победителям (PRED на баланс)
3. Создаются уведомления в очереди
4. Сохраняется период в историю
5. telegram_worker начнет отправку уведомлений

### 5.4. Проверить уведомления:

```bash
# Мониторинг отправки
pm2 logs telegram-worker -f

# Проверить очередь в админке
# Должно увеличиться количество pending/processing/sent
```

### 5.5. Проверить автоматическое закрытие:

**Недельный период:**
- Закрывается каждое воскресенье в 23:59 UTC
- Для теста можно изменить время в `leaderboard_scheduler.py:93`

**Месячный период:**
- Закрывается в последний день месяца в 23:59 UTC
- Для теста можно изменить время в `leaderboard_scheduler.py:131`

## ⚙️ 6. Настройки Rate Limiting

В `telegram_worker.py` можно настроить:

```python
self.delay_between_messages = 0.5  # Задержка между сообщениями (секунды)
self.batch_pause_every = 20        # Пауза каждые N сообщений
self.batch_pause_duration = 5      # Длительность паузы (секунды)
```

Текущие настройки:
- 0.5 секунды между всеми сообщениями
- 5 секунд паузы каждые 20 сообщений
- Защита от Telegram flood limit

## 🔧 7. Troubleshooting

### Проблема: "BOT_TOKEN environment variable is required"

```bash
# Проверить переменную окружения
echo $BOT_TOKEN

# Установить
export BOT_TOKEN=your-token

# Или добавить в .env файл backend/.env
echo "BOT_TOKEN=your-token" >> backend/.env
```

### Проблема: "Connection refused" к БД

```bash
# Проверить PostgreSQL
sudo systemctl status postgresql

# Проверить подключение
psql -h localhost -U thepred -d thepred -c "SELECT 1"

# Установить POSTGRES_HOST
export POSTGRES_HOST=localhost
```

### Проблема: Telegram worker не отправляет сообщения

```bash
# Проверить логи
pm2 logs telegram-worker

# Проверить очередь
curl http://localhost:8000/admin/notifications/queue-stats

# Проверить права бота
# Убедитесь что пользователи не заблокировали бота (/start)
```

### Проблема: Scheduler не закрывает периоды

```bash
# Проверить логи
pm2 logs leaderboard-scheduler

# Проверить текущее время UTC
date -u

# Проверить настроенные награды
curl http://localhost:8000/admin/leaderboard/rewards?period=week
```

### Проблема: Дублирование уведомлений

Система защищена от дублирования через:
- `FOR UPDATE SKIP LOCKED` в запросах
- Атомарные транзакции
- Статусы: PENDING → PROCESSING → SENT/FAILED

Если дублирование все же происходит:
```bash
# Проверить что запущен только 1 экземпляр telegram_worker
pm2 list | grep telegram-worker

# Остановить лишние
pm2 stop telegram-worker
pm2 start telegram-worker --name telegram-worker -i 1
```

## 📈 8. Production Checklist

- [ ] Миграции БД применены
- [ ] Воркеры запущены через PM2/systemd
- [ ] Автозапуск воркеров настроен
- [ ] BOT_TOKEN установлен
- [ ] Награды настроены для week и month
- [ ] Тестовое закрытие периода выполнено
- [ ] Уведомления отправляются корректно
- [ ] Мониторинг работает (логи, админка)
- [ ] Rate limiting не вызывает бан от Telegram

## 📚 9. API Documentation

### POST /admin/leaderboard/close-period

Закрыть период вручную.

**Request:**
```json
{
  "period_type": "week",  // "week" или "month"
  "admin_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "period_id": 123,
  "period_type": "week",
  "start_date": "2025-10-30T00:00:00Z",
  "end_date": "2025-11-06T15:30:00Z",
  "participants_count": 150,
  "winners_count": 25,
  "total_rewards": 50000,
  "notifications_queued": 25
}
```

### GET /admin/leaderboard/periods

История закрытых периодов.

**Query params:**
- `period_type` (optional): "week" или "month"
- `limit` (optional): количество записей (default: 50)

**Response:**
```json
[
  {
    "id": 123,
    "period_type": "week",
    "start_date": "2025-10-30T00:00:00Z",
    "end_date": "2025-11-06T15:30:00Z",
    "status": "closed",
    "total_rewards_distributed": 50000,
    "participants_count": 150,
    "winners_count": 25,
    "closed_at": "2025-11-06T15:30:00Z",
    "closed_by_admin_id": 1
  }
]
```

### GET /admin/leaderboard/current-stats

Статистика текущего периода.

**Query params:**
- `period_type`: "week" или "month"

**Response:**
```json
{
  "period_type": "week",
  "start_date": "2025-10-30T00:00:00Z",
  "end_date": "2025-11-06T15:30:00Z",
  "participants_count": 150,
  "potential_rewards": 50000,
  "rewards_configured": 4
}
```

### GET /admin/notifications/queue-stats

Статистика очереди уведомлений.

**Response:**
```json
{
  "total": 150,
  "pending": 10,
  "processing": 2,
  "sent": 135,
  "failed": 3
}
```

## 🌍 10. Timezone (UTC)

Все операции выполняются в UTC:
- Закрытие периодов: Воскресенье 23:59 UTC (неделя), последний день месяца 23:59 UTC (месяц)
- Даты в БД: timezone-aware datetime
- Логи: UTC timestamps

**Конвертация в локальное время:**
```python
from datetime import datetime, timezone
import pytz

# UTC -> Moscow (UTC+3)
utc_time = datetime.now(timezone.utc)
moscow_tz = pytz.timezone('Europe/Moscow')
moscow_time = utc_time.astimezone(moscow_tz)

print(f"UTC: {utc_time}")
print(f"Moscow: {moscow_time}")
```

## 📞 11. Support

При проблемах:
1. Проверить логи воркеров
2. Проверить очередь уведомлений в админке
3. Проверить историю периодов
4. Проверить переменные окружения
5. Проверить BOT_TOKEN

Полезные команды:
```bash
# Статус всех сервисов
pm2 list

# Перезапуск воркеров
pm2 restart telegram-worker
pm2 restart leaderboard-scheduler

# Очистка логов
pm2 flush

# Очистка старых уведомлений (выполняется автоматически)
# можно запустить вручную через psql:
psql -h localhost -U thepred -d thepred -c "
  DELETE FROM telegram_notifications_queue
  WHERE status IN ('sent', 'permanent_failure')
  AND created_at < NOW() - INTERVAL '7 days'
"
```

---

**Версия**: 1.0
**Дата**: 2025-11-06
**Автор**: ThePred Team
