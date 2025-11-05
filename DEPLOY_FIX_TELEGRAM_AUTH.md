# 🔧 Деплой исправлений: Telegram Auth + Backend Enum Fix

**Дата**: 2025-11-04
**Версия**: 1.2

---

## ✅ Что исправлено:

### 1. ✅ Аутентификация через Telegram (баланс "..." fix)
**Проблема**: При доступе через Telegram Mini App баланс показывал "..." вместо цифр

**Решение**:
- Добавлена проверка источника запроса (Telegram WebApp) в `webapp/main.py`
- Теперь даже при `DEV_MODE=true` пользователи из Telegram видят страницу авторизации
- Добавлено подробное логирование для отслеживания процесса авторизации

**Измененные файлы**:
- `webapp/main.py` (строки 100-128, 131-200)

### 2. ✅ Backend enum error в админке
**Проблема**: При клике на "All Markets" в админ панели падала ошибка:
```
ERROR: invalid input value for enum marketstatus: "all"
```

**Решение**:
- Добавлена проверка `if status and status != "all"` перед фильтрацией
- Теперь "all" обрабатывается как "показать все рынки без фильтра"

**Измененные файлы**:
- `backend/app/api/endpoints/admin.py` (строки 204-206)

---

## 📦 Измененные файлы (для git commit):

```
webapp/main.py                          ✅ Telegram auth detection + logging
backend/app/api/endpoints/admin.py      ✅ Fixed enum "all" filter
```

---

## 🚀 Инструкция по деплою:

### 1. Подключись к серверу

```bash
ssh root@твой_ip
cd /root/ThePred
```

### 2. Создай коммит и запуш изменения (с локальной машины)

```bash
# На локальной машине
cd /Users/alluc/Documents/ThePred

# Добавь изменения
git add webapp/main.py backend/app/api/endpoints/admin.py

# Создай коммит
git commit -m "fix: Telegram auth detection and backend enum filter

- Fix Telegram WebApp auth not working with DEV_MODE=true
- Add detailed logging to /auth/telegram endpoint
- Fix backend enum error when filtering markets with status='all'
- Closes issues: balance showing '...' from Telegram, admin 'All Markets' crash"

# Запуш
git push origin main
```

### 3. Обнови код на сервере

```bash
# На сервере
git pull origin main
```

### 4. Проверь что BOT_TOKEN настроен

```bash
grep BOT_TOKEN .env
```

**Должно быть**:
```
BOT_TOKEN=8067436515:AAGHg6_ojgsnBmREI1U9Sr_iibgXYGInml0
```

Если нет - добавь его:
```bash
echo "BOT_TOKEN=8067436515:AAGHg6_ojgsnBmREI1U9Sr_iibgXYGInml0" >> .env
```

### 5. Перезапусти контейнеры

```bash
# Пересобрать и перезапустить webapp и backend
docker-compose down
docker-compose up -d --build

# Проверить что запущены
docker-compose ps
```

### 6. Проверь логи

```bash
# Логи webapp (для Telegram auth)
docker-compose logs -f webapp

# Должно показать при старте:
# ==================================================
# WEBAPP CONFIGURATION:
# DEV_MODE: True (from env: true)
# API_URL: http://backend:8000
# BOT_USERNAME: The_Pred_Bot
# ==================================================

# Логи backend
docker-compose logs -f backend
```

---

## 🧪 Тестирование:

### Тест 1: Telegram Auth (баланс "..." fix)

1. Открой бота в Telegram: @The_Pred_Bot
2. Нажми "Открыть приложение" (WebApp button)
3. **Ожидается**: Увидишь страницу с логотипом ThePred и прогресс-баром
4. **Ожидается**: Через 3 секунды перенаправит на /markets
5. **Ожидается**: Баланс показывает число (например "10.0K"), НЕ "..."

**Если баланс всё равно "..."**:

Открой логи webapp:
```bash
docker-compose logs -f webapp | grep "auth"
```

Смотри что происходит:
```
[/auth/telegram] ===== TELEGRAM AUTH REQUEST =====
[/auth/telegram] initData received: True, length: XXX
[/auth/telegram] BOT_TOKEN configured: True, length: 46
[/auth/telegram] Validating Telegram initData...
[/auth/telegram] Telegram data validated! User ID: XXX
[/auth/telegram] Backend returned user: id=XX
[/auth/telegram] Session created: user_id=XX
[/auth/telegram] ===== AUTH SUCCESS =====
```

Если видишь ошибку:
- `ERROR: No initData provided` - Telegram не отправил initData (проблема с ботом)
- `ERROR: BOT_TOKEN not configured` - Проверь .env файл
- `ERROR: Invalid Telegram data` - BOT_TOKEN неправильный
- `ERROR: Backend error` - Backend API недоступен

### Тест 2: Admin "All Markets" tab

1. Открой админ панель: https://admin.thepred.tech/markets
2. Кликни на таб "All Markets"
3. **Ожидается**: Список всех рынков загружается ✅
4. **Было**: Ошибка `invalid input value for enum marketstatus: "all"` ❌

Если всё равно ошибка:
```bash
docker-compose logs backend | grep "enum"
```

### Тест 3: Dev Mode через браузер (должно работать как раньше)

1. Открой в браузере: http://thepred.tech
2. **Ожидается**: Редирект на `/dev/login`
3. **Ожидается**: Форма с user_id, username, telegram_id
4. Нажми "Login"
5. **Ожидается**: Редирект на `/markets`, баланс показывается ✅

---

## 📊 Логирование:

После деплоя логи webapp будут очень подробными. Смотри логи для диагностики:

### При заходе через Telegram:
```
[/] Request from Telegram WebApp, showing auth.html
[/auth/telegram] ===== TELEGRAM AUTH REQUEST =====
[/auth/telegram] initData received: True
[/auth/telegram] BOT_TOKEN configured: True
[/auth/telegram] Validating Telegram initData...
[/auth/telegram] Telegram data validated! User ID: 123456
[/auth/telegram] Calling backend to register/login user
[/auth/telegram] Backend returned user: id=1
[/auth/telegram] Session created: user_id=1
[/auth/telegram] ===== AUTH SUCCESS =====
```

### При заходе через браузер (DEV_MODE):
```
[/] DEV_MODE is ON, redirecting to dev_login
[/dev/login] DEV_MODE: True, method: GET
[/dev/login] Showing dev_login.html
```

### При загрузке профиля:
```
[/api/profile] Session user_id: 1, All session: {'user_id': '1', 'telegram_id': 123456}
[/api/profile] Fetching profile for user_id: 1
[/api/profile] Profile loaded: 1
```

---

## 🐛 Troubleshooting:

### Проблема: "initData received: False" в логах

**Решение**: Telegram не отправляет initData. Проверь:
1. Бот настроен с WebApp button? (`web_app=WebAppInfo(url="https://thepred.tech")`)
2. URL бота правильный? Должен быть `https://thepred.tech`
3. SSL сертификат на сервере действителен?

### Проблема: "BOT_TOKEN configured: False"

**Решение**: Добавь BOT_TOKEN в .env:
```bash
echo "BOT_TOKEN=8067436515:AAGHg6_ojgsnBmREI1U9Sr_iibgXYGInml0" >> .env
docker-compose down
docker-compose up -d
```

### Проблема: "Invalid Telegram data (validation failed)"

**Решение**: BOT_TOKEN неправильный. Проверь:
```bash
# Получить актуальный токен от @BotFather
# Обновить в .env
nano .env
# Найти BOT_TOKEN=... и заменить на правильный
# Перезапустить
docker-compose restart webapp
```

### Проблема: Backend всё равно падает на "all" status

**Решение**: Убедись что код обновился:
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

- [ ] Закоммичен и запушен код на GitHub
- [ ] На сервере выполнен `git pull origin main`
- [ ] BOT_TOKEN добавлен в .env (проверить: `grep BOT_TOKEN .env`)
- [ ] Контейнеры перезапущены: `docker-compose down && docker-compose up -d --build`
- [ ] Все контейнеры в статусе "Up": `docker-compose ps`
- [ ] Логи webapp показывают конфигурацию: `docker-compose logs webapp | head -20`
- [ ] Логи backend без ошибок: `docker-compose logs backend | tail -50`

---

## 📝 После успешного деплоя:

Скинь скриншоты:
1. Баланс через Telegram (должен показывать число, не "...")
2. Admin panel "All Markets" tab (должен загружаться без ошибок)
3. Логи webapp при авторизации через Telegram
4. Логи backend (последние 50 строк): `docker-compose logs --tail=50 backend`

---

**Примечание**: Если баланс всё равно показывает "...", это значит что:
1. Telegram не отправляет initData (проверь WebApp button в боте)
2. BOT_TOKEN неправильный (проверь в .env)
3. Backend API недоступен (проверь `docker-compose ps`)
4. Пользователь не зарегистрирован в backend (проверь `curl http://localhost:8000/admin/users`)

Логи покажут точную причину.

---

**Удачного деплоя!** 🚀
