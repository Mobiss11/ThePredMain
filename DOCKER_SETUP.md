# Docker Setup - Два режима работы

Документация по двум Docker Compose конфигурациям ThePred.

---

## 📦 Файловая структура

```
ThePred/
├── docker-compose.yml          # DEV - локальная разработка
├── docker-compose.prod.yml     # PROD - production с nginx
├── .env.production.example     # Пример production .env
├── nginx/
│   ├── nginx.conf              # Основной nginx конфиг
│   ├── conf.d/
│   │   ├── thepred.com.conf   # Лендинг с SSL
│   │   └── thepred.tech.conf  # WebApp с SSL
│   └── ssl/                    # SSL сертификаты (генерируются)
├── backend/
├── bot/
├── webapp/
├── admin/
└── landing/
```

---

## 🔵 Development Mode

### Назначение

Для локальной разработки БЕЗ доменов и SSL.

### Файл

`docker-compose.yml`

### Особенности

- ✅ Все порты exposed наружу
- ✅ Backend на http://localhost:8000
- ✅ WebApp на http://localhost:8001
- ✅ Admin на http://localhost:8002
- ✅ Landing на http://localhost:8003
- ✅ PostgreSQL и Redis доступны снаружи
- ✅ Hot reload для backend (--reload)
- ✅ DEV_MODE=true по умолчанию

### Запуск

```bash
# Создать .env (минимальный)
cat > .env << 'EOF'
BOT_TOKEN=your_bot_token
POSTGRES_PASSWORD=devpassword
JWT_SECRET=dev_secret_key
ADMIN_PASSWORD=admin
EOF

# Запустить
docker-compose up -d

# Проверить
docker-compose ps
docker-compose logs -f
```

### Доступ

| Сервис | URL | Описание |
|--------|-----|----------|
| Backend API | http://localhost:8000/docs | Swagger UI |
| WebApp | http://localhost:8001 | Telegram Mini App |
| Admin | http://localhost:8002 | Админ панель |
| Landing | http://localhost:8003 | Лендинг |
| PostgreSQL | localhost:5432 | DB (thepred/changeme) |
| Redis | localhost:6379 | Cache |

### Команды

```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Пересборка
docker-compose build
docker-compose up -d --build

# Логи
docker-compose logs -f
docker-compose logs -f backend

# Подключение к БД
docker-compose exec postgres psql -U thepred

# Выполнить команду в контейнере
docker-compose exec backend python manage.py

# Перезапуск сервиса
docker-compose restart webapp
```

---

## 🔴 Production Mode

### Назначение

Для production деплоя с доменами, nginx и SSL.

### Файл

`docker-compose.prod.yml`

### Особенности

- ✅ Nginx reverse proxy
- ✅ Два домена: thepred.com и thepred.tech
- ✅ Автоматическое получение SSL (Let's Encrypt)
- ✅ Backend в internal network (безопасность)
- ✅ Admin только на порту :8002
- ✅ HTTP → HTTPS redirect
- ✅ Auto-renewal SSL сертификатов
- ✅ Rate limiting
- ✅ Gzip compression
- ✅ Security headers

### Сети

**frontend** (bridge):
- nginx
- webapp
- admin
- landing

**backend** (internal):
- postgres
- redis
- backend

Backend недоступен извне напрямую - только через internal network.

### Запуск

См. подробно в [DEPLOYMENT.md](./DEPLOYMENT.md)

**Краткая версия**:

```bash
# 1. Настроить DNS (A-записи)
# thepred.com → YOUR_IP
# thepred.tech → YOUR_IP

# 2. Создать .env
cp .env.production.example .env
nano .env  # Заполнить ВСЕ переменные

# 3. Первый запуск БЕЗ SSL (для certbot)
# См. DEPLOYMENT.md шаг "Временные конфиги"

# 4. Запустить
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 5. Получить SSL
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  --email your@email.com --agree-tos \
  -d thepred.com -d www.thepred.com

docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  --email your@email.com --agree-tos \
  -d thepred.tech -d www.thepred.tech

# 6. Вернуть HTTPS конфиги и перезапустить nginx
# См. DEPLOYMENT.md
```

### Доступ

| Сервис | URL | Описание |
|--------|-----|----------|
| Landing | https://thepred.com | Лендинг с SSL |
| WebApp | https://thepred.tech | Mini App с SSL |
| Admin | http://YOUR_IP:8002 | Админка без домена |
| Backend | Internal network | Недоступен снаружи |

### Команды

```bash
# Запуск
docker-compose -f docker-compose.prod.yml up -d

# Остановка
docker-compose -f docker-compose.prod.yml down

# Пересборка
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d --build

# Логи
docker-compose -f docker-compose.prod.yml logs -f
docker-compose -f docker-compose.prod.yml logs -f nginx

# Проверка nginx конфига
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Перезапуск nginx
docker-compose -f docker-compose.prod.yml restart nginx

# SSL renewal
docker-compose -f docker-compose.prod.yml run --rm certbot renew

# Бэкап БД
docker-compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U thepred thepred | gzip > backup_$(date +%Y%m%d).sql.gz
```

---

## 🔄 Переменные окружения

### Development (.env)

```env
# Минимальные для dev
BOT_TOKEN=your_token
POSTGRES_PASSWORD=devpassword
JWT_SECRET=dev_secret
ADMIN_PASSWORD=admin
DEV_MODE=true
```

### Production (.env)

См. [.env.production.example](./.env.production.example)

**ВАЖНО**:
- Все пароли СИЛЬНЫЕ (32+ символов)
- Уникальные секретные ключи для каждого сервиса
- DEV_MODE=false
- Реальный BOT_TOKEN от @BotFather
- WEBAPP_URL=https://thepred.tech

---

## 🌐 Nginx конфигурация

### thepred.com (лендинг)

```nginx
# HTTP → HTTPS redirect
server {
    listen 80;
    server_name thepred.com www.thepred.com;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://thepred.com$request_uri; }
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name thepred.com www.thepred.com;

    ssl_certificate /etc/letsencrypt/live/thepred.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/thepred.com/privkey.pem;

    location / {
        proxy_pass http://landing:8003;
        # headers...
    }
}
```

### thepred.tech (webapp)

```nginx
# HTTP → HTTPS redirect
server {
    listen 80;
    server_name thepred.tech www.thepred.tech;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://thepred.tech$request_uri; }
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name thepred.tech www.thepred.tech;

    ssl_certificate /etc/letsencrypt/live/thepred.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/thepred.tech/privkey.pem;

    # Telegram WebApp CSP
    add_header Content-Security-Policy "frame-ancestors 'self' https://web.telegram.org https://telegram.org";

    location / {
        proxy_pass http://webapp:8001;
        # headers...
    }
}
```

### Основной nginx.conf

- Worker processes: auto
- Gzip: включен
- Security headers
- Rate limiting zones
- SSL protocols: TLSv1.2, TLSv1.3

---

## 🔒 Безопасность

### Development

- ⚠️ Простые пароли OK
- ⚠️ Порты exposed OK
- ⚠️ DEBUG=true OK
- ⚠️ Без SSL OK

### Production

- ✅ Сильные пароли обязательны
- ✅ Backend в internal network
- ✅ SSL сертификаты
- ✅ DEBUG=false
- ✅ Rate limiting
- ✅ Security headers
- ✅ Firewall (UFW)
- ✅ Fail2Ban

---

## 📊 Мониторинг

### Проверка статуса

```bash
# Dev
docker-compose ps
docker stats

# Prod
docker-compose -f docker-compose.prod.yml ps
docker stats
```

### Логи

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f backend

# Последние 100 строк
docker-compose logs --tail=100

# Nginx логи
docker-compose exec nginx tail -f /var/log/nginx/access.log
docker-compose exec nginx tail -f /var/log/nginx/error.log
```

### Health checks

```bash
# API health
curl http://localhost:8000/health

# Domains (prod)
curl -I https://thepred.com
curl -I https://thepred.tech

# SSL test
openssl s_client -connect thepred.com:443 -servername thepred.com
```

---

## 🔄 Обновление

### Development

```bash
# Остановить
docker-compose down

# Обновить код
git pull

# Пересобрать и запустить
docker-compose up -d --build

# Проверить логи
docker-compose logs -f
```

### Production

```bash
# Остановить
docker-compose -f docker-compose.prod.yml down

# Бэкап БД
docker-compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U thepred thepred > backup_before_update.sql

# Обновить код
git pull

# Пересобрать
docker-compose -f docker-compose.prod.yml build

# Запустить
docker-compose -f docker-compose.prod.yml up -d

# Проверить
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 🆘 Troubleshooting

### Port already in use

```bash
# Найти процесс
sudo lsof -i :8000

# Убить
sudo kill -9 <PID>

# Или остановить все Docker
docker stop $(docker ps -aq)
```

### Container fails to start

```bash
# Посмотреть логи
docker-compose logs <service>

# Пересоздать контейнер
docker-compose up -d --force-recreate <service>

# Полная переустановка
docker-compose down -v  # ВНИМАНИЕ: удалит volumes!
docker-compose up -d
```

### Nginx error

```bash
# Проверить конфиг
docker-compose exec nginx nginx -t

# Перезапустить
docker-compose restart nginx

# Посмотреть логи
docker-compose logs nginx
docker-compose exec nginx cat /var/log/nginx/error.log
```

### SSL issues

```bash
# Проверить сертификаты
docker-compose exec nginx ls -la /etc/letsencrypt/live/

# Пересоздать
docker-compose run --rm certbot renew --force-renewal

# Проверить SSL
curl -vI https://thepred.com
```

### Database issues

```bash
# Подключиться
docker-compose exec postgres psql -U thepred

# Проверить подключения
SELECT * FROM pg_stat_activity;

# Перезапустить
docker-compose restart postgres
```

---

## 📚 См. также

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Полный гайд по production деплою
- [SSL_SETUP.md](./SSL_SETUP.md) - Подробно про SSL
- [QUICKSTART.md](./QUICKSTART.md) - Быстрый старт
- [README.md](./README.md) - Обзор проекта
- [CLAUDE.md](./CLAUDE.md) - Техническая документация

---

## ✅ Checklist

### Development
- [ ] Docker установлен
- [ ] .env создан
- [ ] `docker-compose up -d`
- [ ] Все сервисы Up
- [ ] http://localhost:8000/docs открывается

### Production
- [ ] DNS настроен
- [ ] .env.production заполнен
- [ ] `docker-compose.prod.yml up -d`
- [ ] SSL сертификаты получены
- [ ] https://thepred.com работает
- [ ] https://thepred.tech работает
- [ ] Бэкапы настроены
- [ ] Мониторинг работает
