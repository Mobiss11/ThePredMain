# 🔧 Деплой исправлений: Админ-панель + Telegram Auth

**Дата**: 2025-11-04
**Версия**: 1.3

---

## ✅ Что исправлено:

### 1. ✅ Telegram Auth (баланс "..." fix)
**Проблема**: При доступе через Telegram баланс показывал "..." вместо цифр

**Решение**:
- Добавлена проверка источника запроса (Telegram WebApp)
- Теперь даже при `DEV_MODE=true` Telegram пользователи видят страницу авторизации
- Добавлено подробное логирование

**Файлы**: `webapp/main.py` (строки 100-128, 131-200)

### 2. ✅ Backend enum error ("all" status)
**Проблема**: При клике "All Markets" падала ошибка `invalid input value for enum marketstatus: "all"`

**Решение**: Добавлена проверка `if status and status != "all"`

**Файлы**: `backend/app/api/endpoints/admin.py` (строки 204-206)

### 3. ✅ Добавлен таб "Cancelled"
**Новый функционал**: Отдельный таб для просмотра отменённых событий

**Что сделано**:
- Добавлен таб "Cancelled" с счётчиком
- Backend эндпоинт `/admin/markets/cancelled`
- Admin proxy route для cancelled
- Автообновление счётчика каждые 30 секунд

**Файлы**:
- `admin/templates/markets.html` (HTML, JavaScript)
- `backend/app/api/endpoints/admin.py` (эндпоинт)
- `admin/main.py` (proxy route)

### 4. ✅ "All Markets" → "Approved Markets"
**Изменение**: Теперь показывает только approved события

**Что сделано**:
- Переименован таб "All Markets" → "Approved Markets"
- Backend эндпоинт `/admin/markets/approved`
- Admin proxy route для approved
- Фильтрация по `moderation_status == 'APPROVED'`

**Файлы**:
- `admin/templates/markets.html` (изменён URL запроса)
- `backend/app/api/endpoints/admin.py` (новый эндпоинт)
- `admin/main.py` (proxy route)

### 5. ✅ Исправлен Resolve (расчёт события)
**Проблема**: Кнопка "Resolve" не работала

**Решение**: Изменён метод с POST на PUT в admin proxy

**Файлы**: `admin/main.py` (строки 145, 152)

### 6. ✅ Кнопки Approve/Reject скрываются после апрува (уже работало)
**Примечание**: Это уже работало правильно! После апрува `moderation_status` становится `APPROVED`, и кнопки автоматически скрываются. Остаются только Close, Resolve и Cancel.

---

## 📦 Измененные файлы:

```
webapp/main.py                          ✅ Telegram auth detection + logging
backend/app/api/endpoints/admin.py      ✅ Enum fix + новые эндпоинты (approved, cancelled)
admin/templates/markets.html            ✅ Новый таб Cancelled + обновление логики
admin/main.py                           ✅ Proxy routes + Resolve fix (PUT)
```

---

## 🚀 Инструкция по деплою:

### 1. На локальной машине - Закоммитить изменения

```bash
cd /Users/alluc/Documents/ThePred

# Добавить все изменённые файлы
git add webapp/main.py backend/app/api/endpoints/admin.py admin/templates/markets.html admin/main.py DEPLOY_ADMIN_FIXES.md

# Создать коммит
git commit -m "feat: Admin panel improvements and fixes

- Add Telegram WebApp auth detection (fix balance '...')
- Fix backend enum error for 'all' status filter
- Add 'Cancelled' tab for cancelled events
- Rename 'All Markets' to 'Approved Markets' with filtering
- Fix Resolve endpoint (change POST to PUT)
- Add backend endpoints: /admin/markets/approved, /admin/markets/cancelled
- Add detailed logging for Telegram auth

Closes issues:
- Balance showing '...' from Telegram
- Admin 'All Markets' crash
- No cancelled events tab
- Resolve not working"

# Запушить
git push origin main
```

### 2. На сервере - Обновить код

```bash
ssh root@твой_ip
cd /root/ThePred

# Подтянуть изменения
git pull origin main

# Проверить что BOT_TOKEN настроен
grep BOT_TOKEN .env
```

**Если BOT_TOKEN нет**:
```bash
echo "BOT_TOKEN=8067436515:AAGHg6_ojgsnBmREI1U9Sr_iibgXYGInml0" >> .env
```

### 3. Перезапустить контейнеры

```bash
# Остановить
docker-compose down

# Пересобрать и запустить
docker-compose up -d --build

# Проверить что всё запущено
docker-compose ps
```

**Ожидается**:
```
NAME                   STATUS
thepred-backend-1      Up
thepred-webapp-1       Up
thepred-admin-1        Up
thepred-bot-1          Up
thepred-postgres-1     Up
thepred-redis-1        Up
thepred-minio-1        Up
```

### 4. Проверить логи

```bash
# Логи webapp (для Telegram auth)
docker-compose logs -f webapp | head -30

# Должно показать:
# ==================================================
# WEBAPP CONFIGURATION:
# DEV_MODE: True (from env: true)
# API_URL: http://backend:8000
# BOT_USERNAME: The_Pred_Bot
# ==================================================

# Логи backend
docker-compose logs backend | tail -50

# Логи admin
docker-compose logs admin | tail -30
```

---

## 🧪 Тестирование:

### Тест 1: Telegram Auth (баланс "...")

1. Открой бота в Telegram: @The_Pred_Bot
2. Нажми "Открыть приложение"
3. **Ожидается**: Страница с логотипом ThePred, прогресс-бар
4. **Ожидается**: Через 3 секунды → редирект на /markets
5. **Ожидается**: Баланс показывает число (например "10.0K"), НЕ "..." ✅

**Если баланс всё равно "..."**:
```bash
docker-compose logs -f webapp | grep "auth"
```

Должно быть:
```
[/] Request from Telegram WebApp, showing auth.html
[/auth/telegram] ===== TELEGRAM AUTH REQUEST =====
[/auth/telegram] Telegram data validated! User ID: XXX
[/auth/telegram] ===== AUTH SUCCESS =====
```

### Тест 2: Админ панель - Новые табы

1. Открой: https://admin.thepred.tech/markets
2. **Ожидается**: 3 таба:
   - "Approved Markets" (активен по умолчанию)
   - "Pending Moderation" (с красным счётчиком)
   - "Cancelled" (с серым счётчиком)

3. Кликни на **"Approved Markets"**
   - **Ожидается**: Список всех approved событий ✅
   - **Было**: Ошибка enum "all" ❌

4. Кликни на **"Cancelled"**
   - **Ожидается**: Список отменённых событий ✅
   - **Было**: Таба не было ❌

### Тест 3: Кнопки после апрува

1. Открой таб "Pending Moderation"
2. Найди событие со статусом "PENDING"
3. **Ожидается**: Кнопки "Approve", "Reject", "Cancel" ✅

4. Нажми "Approve"
5. **Ожидается**: Событие исчезает из "Pending"
6. Открой таб "Approved Markets"
7. **Ожидается**: Событие теперь здесь, со статусом "APPROVED"
8. **Ожидается**: Кнопки "Approve" и "Reject" БОЛЬШЕ НЕ ПОКАЗЫВАЮТСЯ ✅
9. **Ожидается**: Видны только кнопки "Close", "Resolve", "Cancel" ✅

### Тест 4: Resolve (расчёт события)

1. В табе "Approved Markets" найди событие со статусом "OPEN"
2. **Ожидается**: Кнопки "Close", "Resolve", "Cancel"

3. Нажми **"Resolve"**
4. **Ожидается**: Модальное окно (prompt) с текстом "Enter outcome (YES, NO, or CANCELLED):"
5. Введи "YES" (или "NO")
6. Нажми OK
7. **Ожидается**: Toast notification "Market resolved successfully" ✅
8. **Ожидается**: Событие обновилось, статус теперь "RESOLVED" ✅
9. **Было**: Ошибка, ничего не работало ❌

**Если Resolve не работает**:
```bash
# Смотри логи admin
docker-compose logs admin | grep "resolve"

# Смотри логи backend
docker-compose logs backend | grep "resolve"
```

### Тест 5: Dev Mode через браузер

1. Открой в браузере: http://thepred.tech
2. **Ожидается**: Редирект на `/dev/login` ✅
3. **Ожидается**: Форма с полями user_id, username, telegram_id
4. Введи данные и нажми "Login"
5. **Ожидается**: Редирект на `/markets`, баланс показывается ✅

---

## 📊 Структура табов в админке:

### 1. **Approved Markets** (по умолчанию)
- Показывает только события с `moderation_status == 'APPROVED'`
- Эндпоинт: `/admin/markets/approved`
- Кнопки (если статус OPEN): Close, Resolve, Cancel
- Кнопки Approve/Reject НЕ показываются (уже approved!)

### 2. **Pending Moderation**
- Показывает события с `moderation_status == 'PENDING'`
- Эндпоинт: `/admin/markets/pending`
- Кнопки: Approve, Reject, Cancel
- Счётчик обновляется каждые 30 секунд

### 3. **Cancelled**
- Показывает события с `status == 'CANCELLED'`
- Эндпоинт: `/admin/markets/cancelled`
- Кнопки: только Cancel (уже отменено, больше ничего не нужно)
- Счётчик обновляется каждые 30 секунд

---

## 🐛 Troubleshooting:

### Проблема: Баланс всё равно "..." через Telegram

**Решение**:
1. Проверь логи webapp:
```bash
docker-compose logs -f webapp | grep -A 10 "auth/telegram"
```

2. Если видишь `ERROR: BOT_TOKEN not configured`:
```bash
echo "BOT_TOKEN=8067436515:AAGHg6_ojgsnBmREI1U9Sr_iibgXYGInml0" >> .env
docker-compose restart webapp
```

3. Если видишь `ERROR: Invalid Telegram data`:
   - BOT_TOKEN неправильный, проверь в .env

4. Если видишь `ERROR: Backend error`:
   - Backend API недоступен, проверь `docker-compose ps`

### Проблема: Таб "Approved Markets" пустой

**Решение**: В базе нет approved событий!
1. Создай событие через webapp
2. Зайди в админку, открой "Pending Moderation"
3. Нажми "Approve" на событии
4. Теперь открой "Approved Markets" - событие должно быть там

### Проблема: "Resolve" не работает

**Решение**:
1. Проверь логи admin:
```bash
docker-compose logs admin | grep "resolve"
```

2. Проверь логи backend:
```bash
docker-compose logs backend | grep "resolve"
```

3. Убедись что метод PUT используется:
```bash
grep -A 5 "markets.*resolve" admin/main.py
```

Должно быть:
```python
@app.route('/admin/markets/<int:market_id>/resolve', methods=['PUT'])
...
    async with session_http.put(
```

Если видишь POST - код не обновился:
```bash
git pull origin main
docker-compose up -d --build admin
```

### Проблема: Backend enum error всё равно падает

**Решение**:
```bash
grep -A 3 "Only filter by status" backend/app/api/endpoints/admin.py
```

Должно быть:
```python
# Only filter by status if it's not "all"
if status and status != "all":
    query = query.where(Market.status == status)
```

Если нет:
```bash
git pull origin main
docker-compose up -d --build backend
```

---

## ✅ Чеклист перед тестированием:

- [ ] Закоммичены и запушены все изменения на GitHub
- [ ] На сервере выполнен `git pull origin main`
- [ ] BOT_TOKEN добавлен в .env (`grep BOT_TOKEN .env`)
- [ ] Контейнеры перезапущены: `docker-compose down && docker-compose up -d --build`
- [ ] Все контейнеры в статусе "Up": `docker-compose ps`
- [ ] Логи webapp показывают конфигурацию
- [ ] Логи backend без ошибок
- [ ] Логи admin без ошибок

---

## 📝 После успешного деплоя:

Скинь скриншоты:
1. ✅ Баланс через Telegram (должно быть число, не "...")
2. ✅ Админка с 3 табами (Approved, Pending, Cancelled)
3. ✅ Событие в "Approved Markets" БЕЗ кнопок Approve/Reject (только Close, Resolve, Cancel)
4. ✅ Resolve модальное окно и успешное завершение
5. Логи webapp при auth: `docker-compose logs webapp | grep "AUTH SUCCESS"`
6. Логи backend (последние 50 строк): `docker-compose logs --tail=50 backend`

---

## 🎯 Краткая сводка изменений:

| Проблема | Статус | Решение |
|----------|--------|---------|
| Баланс "..." через Telegram | ✅ Исправлено | Telegram auth detection в webapp |
| Backend enum error "all" | ✅ Исправлено | Проверка `status != "all"` |
| Нет таба Cancelled | ✅ Добавлено | Новый таб + эндпоинт |
| "All Markets" показывает всё | ✅ Изменено | Теперь "Approved Markets" + фильтрация |
| Resolve не работает | ✅ Исправлено | Изменён POST на PUT |
| Кнопки после апрува | ✅ Работает | Автоматически скрываются |

---

**Удачного деплоя!** 🚀

**P.S.**: Не забудь проверить логи после деплоя, чтобы убедиться что всё работает правильно!
