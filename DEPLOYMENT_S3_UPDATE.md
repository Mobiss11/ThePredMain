# Деплой обновления с S3 хранилищем

## Шаг 1: Настройка DNS (в панели управления доменом)

Зайди в панель управления доменом `thepred.store` и настрой **A-запись**:

```
Тип: A
Имя: @ (или оставь пустым для корневого домена)
Значение: IP твоего сервера (тот же IP что у thepred.tech)
TTL: Auto или 3600
```

После добавления подожди 5-10 минут, чтобы DNS обновился.

Проверить можно командой:
```bash
ping thepred.store
```

Должен отвечать IP твоего сервера.

---

## Шаг 2: Подключись к серверу

```bash
ssh root@твой_сервер_ip
cd /root/ThePred  # или где у тебя проект
```

---

## Шаг 3: Подтяни новый код

```bash
git pull origin main
```

---

## Шаг 4: Обнови .env файл

Открой файл `.env`:
```bash
nano .env
```

Добавь в конец файла новые переменные для MinIO:

```env
# MinIO S3 Storage
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=твой_сложный_пароль_минимум_8_символов
```

**ВАЖНО**: Замени `твой_сложный_пароль_минимум_8_символов` на реальный сложный пароль!

Сохрани файл: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## Шаг 5: Останови контейнеры

```bash
docker-compose -f docker-compose.prod.yml down
```

---

## Шаг 6: Пересобери и запусти контейнеры

```bash
docker-compose -f docker-compose.prod.yml build backend
docker-compose -f docker-compose.prod.yml up -d
```

Подожди пару минут, пока всё запустится.

---

## Шаг 7: Проверь что контейнеры запущены

```bash
docker-compose -f docker-compose.prod.yml ps
```

Все сервисы должны быть в статусе `Up`.

---

## Шаг 8: Запусти миграции базы данных

```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

Должно вывести:
```
INFO  [alembic.runtime.migration] Running upgrade faa5267d165a -> 79fa342a014c, add_market_photo_and_moderation
```

---

## Шаг 9: Получи SSL сертификат для thepred.store

```bash
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  -d thepred.store \
  --email твой@email.com \
  --agree-tos \
  --no-eff-email
```

**ВАЖНО**: Замени `твой@email.com` на свой реальный email.

---

## Шаг 10: Перезапусти nginx

```bash
docker-compose -f docker-compose.prod.yml restart nginx
```

---

## Шаг 11: Проверь что всё работает

### Проверка основного сайта:
```bash
curl -I https://thepred.tech
```

Должен вернуть `HTTP/2 200`

### Проверка S3 домена:
```bash
curl -I https://thepred.store
```

Должен вернуть либо `HTTP/2 200`, либо `HTTP/2 403` (это нормально для MinIO)

### Проверка что MinIO работает внутри:
```bash
docker-compose -f docker-compose.prod.yml exec minio mc alias set local http://localhost:9000 admin твой_пароль_из_env
```

---

## Шаг 12: Проверь логи сервисов

### Логи backend:
```bash
docker-compose -f docker-compose.prod.yml logs backend | tail -50
```

Должно быть:
```
INFO:     Initializing S3 bucket...
INFO:     Bucket thepred-events already exists
INFO:     S3 bucket initialized
```

### Логи MinIO:
```bash
docker-compose -f docker-compose.prod.yml logs minio | tail -20
```

### Логи nginx:
```bash
docker-compose -f docker-compose.prod.yml logs nginx | tail -20
```

---

## Шаг 13: Тестирование создания события

1. Открой Telegram бота
2. Запусти `/start` и открой Web App
3. Перейди на страницу "Рынки"
4. Нажми кнопку **"Создать Событие"**
5. Загрузи фото, заполни форму, отправь
6. Должно появиться уведомление "Событие отправлено на модерацию!"

---

## Проверка работоспособности S3

Попробуй создать тестовое событие с фотографией. Если фото загрузилось, проверь что оно доступно по URL:

```bash
# В логах backend должен быть URL загруженной фотки
docker-compose -f docker-compose.prod.yml logs backend | grep "Uploaded file to"
```

URL будет вида: `https://thepred.store/thepred-events/[uuid].jpg`

Попробуй открыть этот URL в браузере - должна открыться картинка.

---

## Что делать если что-то не работает

### DNS не резолвится (thepred.store не пингуется)
- Подожди ещё 10-15 минут
- Проверь правильность A-записи в DNS панели
- Убедись что указал правильный IP сервера

### Ошибка при получении SSL сертификата
```bash
# Проверь что nginx слушает 80 порт и отдаёт challenge
curl http://thepred.store/.well-known/acme-challenge/test
```

Если 404 - это нормально. Если connection refused - проблема с nginx.

### MinIO не запускается
```bash
# Проверь что пароль в .env достаточно длинный (минимум 8 символов)
docker-compose -f docker-compose.prod.yml logs minio
```

### Ошибка миграции "relation markets does not exist"
Это значит что база пустая. Нужно запустить ВСЕ миграции:
```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Backend не может подключиться к MinIO
```bash
# Проверь что MinIO запущен
docker-compose -f docker-compose.prod.yml ps minio

# Проверь логи backend на ошибки S3
docker-compose -f docker-compose.prod.yml logs backend | grep -i "s3\|minio"
```

---

## Полезные команды

### Перезапустить все сервисы:
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Пересобрать и перезапустить backend:
```bash
docker-compose -f docker-compose.prod.yml up -d --build backend
```

### Посмотреть статус всех контейнеров:
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Очистить логи:
```bash
docker-compose -f docker-compose.prod.yml logs --tail=0 -f
```

### Зайти внутрь контейнера backend:
```bash
docker-compose -f docker-compose.prod.yml exec backend bash
```

---

## Финальная проверка

После всех шагов должно работать:

✅ `https://thepred.tech` - основной сайт
✅ `https://api.thepred.tech` - API
✅ `https://thepred.store` - MinIO S3 хранилище
✅ Создание событий с загрузкой фото
✅ Отображение фото в карточках событий
✅ Модерация событий (статус PENDING для новых)

---

## Дополнительные проверки

### Проверка Админ-панели

Админ-панель доступна на порту `8002`:

```bash
# На сервере проверь что контейнер админки запущен
docker-compose -f docker-compose.prod.yml ps admin
```

Админка доступна по адресу: `http://IP_СЕРВЕРА:8002`

**Первый вход:**
- URL: `http://IP_СЕРВЕРА:8002/login`
- Пароль: значение из `ADMIN_PASSWORD` в `.env`

**Функционал админки:**
- **Dashboard** - статистика платформы в реальном времени
- **Users** - управление пользователями (просмотр, изменение баланса/ранга)
- **Markets** - модерация событий (Approve/Reject), управление статусами, resolve
- **Missions** - создание/редактирование/удаление миссий
- **Leaderboard** - топ-100 пользователей
- **Broadcast** - рассылка сообщений всем пользователям или конкретному

**Важно:** Админка НЕ защищена SSL, только по HTTP. Используй VPN или SSH tunnel для доступа.

### Создание SSH туннеля для админки (опционально)

Для безопасного доступа к админке с локального компьютера:

```bash
ssh -L 8002:localhost:8002 root@твой_сервер_ip
```

Теперь админка доступна локально: `http://localhost:8002`

### Проверка BOT_TOKEN для рассылки

Broadcast функция использует `BOT_TOKEN` из `.env`. Проверь что он установлен:

```bash
# На сервере
cat .env | grep BOT_TOKEN
```

Если не установлен - добавь в `.env`:
```env
BOT_TOKEN=твой_токен_бота
```

И перезапусти backend:
```bash
docker-compose -f docker-compose.prod.yml restart backend
```

### Тест рассылки

1. Зайди в админку: `Broadcast`
2. Выбери "Specific User"
3. Введи свой Telegram ID
4. Напиши тестовое сообщение
5. Отправь

Должно прийти сообщение в Telegram.

---

## Что ещё нужно для полного развёртывания

### 1. Настройка домена thepred.store

Если у тебя уже есть домен `thepred.store`, настрой его в DNS панели как описано в Шаге 1.

Если домена ещё нет - зарегистрируй его или используй другой свободный домен для S3.

### 2. Пароли в .env

Убедись что все пароли установлены в `.env`:

```env
# Обязательные
POSTGRES_PASSWORD=твой_сложный_пароль_postgres
JWT_SECRET=твой_секретный_jwt_ключ
ADMIN_PASSWORD=твой_пароль_админки
ADMIN_SECRET_KEY=твой_секретный_ключ_админки
WEBAPP_SECRET_KEY=твой_секретный_ключ_вебапп
MINIO_ROOT_PASSWORD=твой_пароль_minio
BOT_TOKEN=твой_токен_бота
```

### 3. Переменные для бота

Проверь что все переменные установлены в `.env`:

```env
BOT_USERNAME=твой_юзернейм_бота_без_@
```

### 4. Первый запуск - порядок действий

**Правильная последовательность:**

1. Настроить DNS (thepred.store → IP сервера)
2. Обновить `.env` со всеми паролями
3. Выполнить `git pull` на сервере
4. Остановить контейнеры: `docker-compose -f docker-compose.prod.yml down`
5. Пересобрать: `docker-compose -f docker-compose.prod.yml build`
6. Запустить: `docker-compose -f docker-compose.prod.yml up -d`
7. Дождаться запуска всех сервисов (2-3 минуты)
8. Выполнить миграции: `docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head`
9. Получить SSL для thepred.store
10. Перезапустить nginx
11. Проверить все сервисы

### 5. Проверка портов

Убедись что открыты порты на сервере:

```bash
# Firewall должен разрешать:
# 80 (HTTP)
# 443 (HTTPS)
# 8002 (Admin Panel) - только если нужен внешний доступ
```

Если используешь `ufw`:
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8002/tcp  # Опционально для админки
```

### 6. Логирование

Для отладки смотри логи сервисов:

```bash
# Все логи
docker-compose -f docker-compose.prod.yml logs --tail=100 -f

# Конкретный сервис
docker-compose -f docker-compose.prod.yml logs backend --tail=100 -f
docker-compose -f docker-compose.prod.yml logs minio --tail=50 -f
docker-compose -f docker-compose.prod.yml logs admin --tail=50 -f
```

### 7. Бэкапы

**Важно!** Настрой автоматические бэкапы:

```bash
# Бэкап базы данных
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U thepred thepred > backup_$(date +%Y%m%d).sql

# Бэкап MinIO данных
docker run --rm -v thepred_minio_data:/data -v $(pwd):/backup alpine tar czf /backup/minio_backup_$(date +%Y%m%d).tar.gz /data
```

Настрой cron для автоматических бэкапов:
```bash
crontab -e

# Добавь строку (бэкап каждую ночь в 3:00):
0 3 * * * cd /root/ThePred && docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U thepred thepred > /root/backups/db_$(date +\%Y\%m\%d).sql
```

---

## Коммит изменений в .env

**НЕ ЗАБУДЬ** добавить `.env` в `.gitignore`, если его там нет:

```bash
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Add .env to gitignore"
```

---

Всё готово! 🚀
