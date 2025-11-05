# Руководство по Деплою - ThePred

**Дата**: 4 ноября 2025
**Версия**: 1.1

---

## Что было исправлено и добавлено

### 1. Критические Исправления

#### Backend:
- Исправлена ошибка с фильтром "all" в статусе рынков
- Добавлены эндпоинты `/admin/markets/approved` и `/admin/markets/cancelled`
- Исправлен метод Resolve с POST на PUT
- Добавлено поле `icon` в модель Mission
- Создана система инициализации дефолтных миссий

#### Webapp:
- Исправлена загрузка фото при создании события (убран await)
- Улучшена авторизация через Telegram WebApp
- Обновлена страница профиля с реальными данными
- Полностью переработана страница миссий
- Исправлен эндпоинт claim миссий

#### Admin Panel:
- Добавлен таб "Cancelled" для отмененных событий
- "All Markets" переименован в "Approved Markets" и показывает только одобренные
- Исправлена функция Resolve события
- Добавлено отображение миссий
- Исправлена форма редактирования пользователя

### 2. Новая Функциональность

#### Система Миссий:
- 7 дефолтных миссий с иконками
- Автоматическое создание при старте приложения (без дубликатов)
- Отображение в webapp с progress bar
- Зеленая кнопка "Забрать награду" при выполнении
- Отображение в админ-панели

#### Улучшения Профиля:
- Реальный ранг из лидерборда
- Кнопка "Копировать" под реферальной ссылкой
- Реальные события, в которых участвовал пользователь

---

## Шаг 1: Подготовка к Деплою

### Локальная Проверка

Перед деплоем убедитесь, что все работает локально:

```bash
# Проверить статус git
git status

# Посмотреть измененные файлы
git diff

# Проверить, что все сервисы запущены
make ps
```

### Создать Backup БД

```bash
# На сервере создать backup перед деплоем
ssh root@your-server

cd /root/ThePred

# Backup базы данных
docker-compose exec -T postgres pg_dump -U thepred thepred > backup_$(date +%Y%m%d_%H%M%S).sql

# Убедиться, что backup создан
ls -lh backup_*.sql
```

---

## Шаг 2: Коммит и Push Изменений

### Закоммитить Backend Изменения

```bash
cd /Users/alluc/Documents/ThePred

# Добавить все изменения backend
git add backend/app/init_missions.py
git add backend/app/main.py
git add backend/app/models/mission.py
git add backend/app/api/endpoints/missions.py
git add backend/app/api/endpoints/admin.py
git add backend/alembic/versions/

# Коммит backend
git commit -m "feat: Add missions system and admin improvements

- Add default missions initialization (7 missions)
- Add icon field to Mission model
- Add /admin/markets/approved and /admin/markets/cancelled endpoints
- Fix enum filter error for market status
- Fix Resolve method (POST -> PUT)
"
```

### Закоммитить Webapp Изменения

```bash
# Добавить webapp изменения
git add webapp/main.py
git add webapp/templates/missions.html
git add webapp/templates/profile.html

# Коммит webapp
git commit -m "feat: Update webapp with missions and profile improvements

- Fix photo upload (remove await from file.read())
- Improve Telegram WebApp authentication
- Update missions page with real API integration
- Add progress bars and green claim button
- Update profile with real rank and events
- Move referral copy button below link
"
```

### Закоммитить Admin Изменения

```bash
# Добавить admin изменения
git add admin/main.py
git add admin/templates/markets.html
git add admin/templates/missions.html

# Коммит admin
git commit -m "feat: Add admin panel improvements

- Add 'Cancelled' tab for cancelled markets
- Rename 'All Markets' to 'Approved Markets'
- Fix Resolve function (PUT method)
- Add missions display page
- Fix user edit form
"
```

### Добавить DEPLOYMENT_GUIDE.md

```bash
git add DEPLOYMENT_GUIDE.md
git add MISSIONS_SUMMARY.md
git commit -m "docs: Add deployment and missions documentation"
```

### Push на GitHub

```bash
# Push всех изменений
git push origin main

# Убедиться, что push прошел успешно
git log --oneline -5
```

---

## Шаг 3: Деплой на Сервер

### Подключиться к Серверу

```bash
ssh root@your-server
cd /root/ThePred
```

### Остановить Сервисы

```bash
# Остановить все сервисы (кроме базы данных)
docker-compose stop backend webapp admin bot landing

# Проверить, что остановлены
docker-compose ps
```

### Получить Последние Изменения

```bash
# Pull изменений с GitHub
git pull origin main

# Проверить текущую версию
git log --oneline -5
```

### Применить Миграцию БД

```bash
# Применить миграцию для добавления поля icon
docker-compose exec backend alembic upgrade head

# Проверить, что миграция применена
docker-compose exec backend alembic current

# Должно показать: add_mission_icon (head)
```

### Перезапустить Backend

```bash
# Перезапустить backend
docker-compose up -d backend

# Подождать 5-10 секунд для старта
sleep 10

# Проверить логи
docker-compose logs backend | tail -50

# Ищем в логах:
# "Initializing default missions..."
# "✓ Created 7 default missions" (если первый запуск)
# или
# "✓ Missions already exist (7 missions found)" (если миссии уже были)
```

### Перезапустить Webapp

```bash
# Перезапустить webapp
docker-compose up -d webapp

# Подождать 5 секунд
sleep 5

# Проверить логи
docker-compose logs webapp | tail -30
```

### Перезапустить Admin Panel

```bash
# Перезапустить admin
docker-compose up -d admin

# Проверить логи
docker-compose logs admin | tail -30
```

### Перезапустить Bot

```bash
# Перезапустить bot
docker-compose up -d bot

# Проверить логи
docker-compose logs bot | tail -30
```

### Проверить Все Сервисы

```bash
# Проверить статус всех контейнеров
docker-compose ps

# Должны быть все "Up":
# - postgres (Up)
# - redis (Up)
# - backend (Up)
# - webapp (Up)
# - admin (Up)
# - bot (Up)
# - landing (Up)
```

---

## Шаг 4: Проверка Работоспособности

### 1. Проверить Backend API

```bash
# На сервере
curl http://localhost:8000/health

# Должен вернуть: {"status":"ok"}

# Проверить missions endpoint
curl http://localhost:8000/admin/missions | jq '.[] | {id, title, icon}'

# Должен показать 7 миссий с иконками
```

### 2. Проверить Webapp

```bash
# В браузере открыть
https://your-domain.com

# Проверить:
# - Главная страница загружается
# - События отображаются
# - Можно создать событие с фото
# - Страница миссий работает (/missions)
# - Страница профиля показывает реальный ранг (/profile)
```

### 3. Проверить Admin Panel

```bash
# В браузере открыть
https://your-domain.com/admin

# Проверить:
# - 3 таба: Pending, Approved Markets, Cancelled
# - Approve/Reject работает
# - После апрува кнопки исчезают
# - Resolve работает (PUT)
# - Страница Missions показывает 7 миссий
# - Редактирование пользователя работает
```

### 4. Проверить Telegram Bot

```bash
# В Telegram открыть @The_Pred_Bot
# Отправить /start

# Проверить:
# - Бот отвечает
# - Кнопка "Открыть ThePred" работает
# - WebApp открывается
# - Баланс отображается корректно (не "...")
# - Можно делать ставки
```

### 5. Проверить Миссии

```bash
# В WebApp:
# - Открыть /missions
# - Проверить, что показываются 7 миссий
# - Progress bar отображается
# - Если миссия выполнена, кнопка зеленая

# В Admin:
# - Открыть /admin/missions
# - Должны быть все 7 миссий в таблице
```

---

## Шаг 5: Мониторинг После Деплоя

### Проверить Логи

```bash
# Backend логи
docker-compose logs -f backend

# Webapp логи
docker-compose logs -f webapp

# Admin логи
docker-compose logs -f admin

# Bot логи
docker-compose logs -f bot

# Все логи вместе
docker-compose logs -f
```

### Проверить Ошибки

```bash
# Ошибки backend
docker-compose logs backend | grep ERROR

# Ошибки webapp
docker-compose logs webapp | grep ERROR

# Ошибки admin
docker-compose logs admin | grep ERROR
```

### Проверить База Данных

```bash
# Подключиться к БД
docker-compose exec postgres psql -U thepred -d thepred

# Проверить миссии
SELECT id, title, icon, reward_amount FROM missions;

# Должно показать 7 строк

# Проверить поле icon существует
\d missions

# В колонках должна быть строка:
# icon | character varying(10)

# Выйти
\q
```

---

## Rollback (Откат Изменений)

Если что-то пошло не так, можно откатить изменения:

### 1. Откатить Код

```bash
# Посмотреть последние коммиты
git log --oneline -10

# Откатиться на предыдущий коммит
git reset --hard <commit-hash-before-changes>

# Перезапустить сервисы
docker-compose restart backend webapp admin bot
```

### 2. Откатить Миграцию

```bash
# Откатить последнюю миграцию
docker-compose exec backend alembic downgrade -1

# Проверить текущую версию
docker-compose exec backend alembic current
```

### 3. Восстановить из Backup

```bash
# Остановить backend
docker-compose stop backend

# Восстановить БД из backup
docker-compose exec -T postgres psql -U thepred -d thepred < backup_20251104_120000.sql

# Запустить backend
docker-compose up -d backend
```

---

## Troubleshooting

### Проблема: Миссии не создались

**Симптомы**: В логах нет "Created 7 default missions"

**Решение**:
```bash
# Проверить логи
docker-compose logs backend | grep missions

# Если ошибки с БД, проверить подключение
docker-compose exec backend python -c "from app.core.database import engine; print('DB OK')"

# Создать миссии вручную
docker-compose exec backend python -c "from app.init_missions import init_default_missions; import asyncio; asyncio.run(init_default_missions())"
```

### Проблема: Миграция не применилась

**Симптомы**: Ошибка "column missions.icon does not exist"

**Решение**:
```bash
# Проверить текущую версию
docker-compose exec backend alembic current

# Если не на head, применить вручную
docker-compose exec backend alembic upgrade head

# Если ошибка, откатить и применить заново
docker-compose exec backend alembic downgrade -1
docker-compose exec backend alembic upgrade head
```

### Проблема: Баланс "..." в Telegram

**Симптомы**: При открытии через Telegram показывается "..." вместо баланса

**Решение**:
```bash
# Проверить DEV_MODE в webapp
docker-compose exec webapp env | grep DEV_MODE

# Должно быть DEV_MODE=false в продакшене

# Если нужно изменить:
# Отредактировать .env
nano .env
# Найти DEV_MODE=true
# Изменить на DEV_MODE=false

# Перезапустить webapp
docker-compose restart webapp
```

### Проблема: Resolve не работает

**Симптомы**: При нажатии Resolve ничего не происходит

**Решение**:
```bash
# Проверить логи admin
docker-compose logs admin | grep resolve

# Проверить логи backend
docker-compose logs backend | grep resolve

# Убедиться, что используется PUT метод
docker-compose exec admin grep -A5 "resolve" /app/main.py | grep -i put
```

### Проблема: Фото не загружается

**Симптомы**: Ошибка при создании события с фото

**Решение**:
```bash
# Проверить S3/MinIO работает
docker-compose ps | grep minio

# Проверить логи webapp
docker-compose logs webapp | grep photo

# Проверить права на /app/uploads
docker-compose exec webapp ls -la /app/uploads
```

---

## Итоговый Чеклист

После успешного деплоя отметьте выполненные пункты:

- [ ] Создан backup БД
- [ ] Код закоммичен и запушен на GitHub
- [ ] Изменения получены на сервере (git pull)
- [ ] Миграция применена (alembic upgrade head)
- [ ] Backend перезапущен
- [ ] Webapp перезапущен
- [ ] Admin перезапущен
- [ ] Bot перезапущен
- [ ] Все контейнеры в статусе "Up"
- [ ] Backend API отвечает (/health)
- [ ] 7 миссий созданы в БД
- [ ] Webapp главная страница загружается
- [ ] Можно создать событие с фото
- [ ] Страница миссий работает
- [ ] Страница профиля показывает реальный ранг
- [ ] Admin панель: 3 таба работают
- [ ] Admin: Approve/Reject работает
- [ ] Admin: Resolve работает
- [ ] Admin: Миссии отображаются
- [ ] Admin: Редактирование пользователя работает
- [ ] Telegram бот отвечает
- [ ] WebApp открывается из бота
- [ ] Баланс отображается корректно в Telegram
- [ ] Можно делать ставки
- [ ] Логи без критических ошибок

---

## Дополнительная Информация

### Файлы, Которые Были Изменены

**Backend**:
- `backend/app/init_missions.py` (новый файл)
- `backend/app/main.py`
- `backend/app/models/mission.py`
- `backend/app/api/endpoints/missions.py`
- `backend/app/api/endpoints/admin.py`
- `backend/alembic/versions/add_mission_icon.py` (миграция)

**Webapp**:
- `webapp/main.py`
- `webapp/templates/missions.html`
- `webapp/templates/profile.html`

**Admin**:
- `admin/main.py`
- `admin/templates/markets.html`
- `admin/templates/missions.html`

### Новые Эндпоинты

**Backend API**:
- `GET /admin/markets/approved` - Только одобренные рынки
- `GET /admin/markets/cancelled` - Только отмененные рынки
- `PUT /admin/markets/{id}/resolve` - Расчет события (изменен с POST на PUT)

**Admin Proxy**:
- `GET /admin/markets/approved` - Прокси к backend
- `GET /admin/markets/cancelled` - Прокси к backend

### Новые Таблицы/Колонки

- Добавлена колонка `icon VARCHAR(10)` в таблицу `missions`

### Константы

**7 Дефолтных Миссий**:
1. Первая Ставка (500 PRED) - 1 ставка
2. Новичок (1000 PRED) - 5 ставок
3. Первая Победа (750 PRED) - 1 выигрыш
4. Серия Побед (2000 PRED) - 3 победы подряд
5. Активный Трейдер (2500 PRED) - 10 ставок
6. Любитель Крипты (1500 PRED) - 3 ставки на Crypto
7. Пригласи Друга (2000 PRED) - 1 реферал

---

**Успешного Деплоя!** 🚀
