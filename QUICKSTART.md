# 🚀 Quick Start Guide

Быстрое руководство для запуска ThePred.

---

## 📦 Локальная разработка (5 минут)

### 1. Требования

- Docker & Docker Compose
- Telegram Bot Token от @BotFather

### 2. Запуск

```bash
# Клонировать проект
git clone https://github.com/yourusername/ThePred.git
cd ThePred

# Создать .env (минимальный для dev)
cat > .env << 'EOF'
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
POSTGRES_PASSWORD=devpassword
JWT_SECRET=dev_jwt_secret_key_123
ADMIN_PASSWORD=admin
EOF

# Запустить
docker-compose up -d

# Проверить
docker-compose ps
```

### 3. Доступ

- Backend API: http://localhost:8000/docs
- WebApp: http://localhost:8001
- Admin: http://localhost:8002 (admin/admin)
- Landing: http://localhost:8003

---

## 🚀 Production деплой (20 минут)

### Подготовка

**1. Сервер**
- Ubuntu 22.04
- 4GB RAM
- 40GB SSD
- Статический IP

**2. Домены**
- thepred.com → IP сервера
- thepred.tech → IP сервера

### Команды

```bash
# === НА СЕРВЕРЕ ===

# 1. Установить Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 2. Склонировать проект
cd /root
git clone https://github.com/yourusername/ThePred.git
cd ThePred

# 3. Создать .env
cp .env.production.example .env
nano .env  # Заполнить все переменные!

# 4. Запустить (БЕЗ SSL сначала)
cd nginx/conf.d
mv thepred.com.conf thepred.com.conf.backup
mv thepred.tech.conf thepred.tech.conf.backup

cat > thepred.com.conf << 'EOF'
server {
    listen 80;
    server_name thepred.com www.thepred.com;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { proxy_pass http://landing:8003; proxy_set_header Host $host; }
}
EOF

cat > thepred.tech.conf << 'EOF'
server {
    listen 80;
    server_name thepred.tech www.thepred.tech;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { proxy_pass http://webapp:8001; proxy_set_header Host $host; }
}
EOF

cd ../..

docker-compose -f docker-compose.prod.yml up -d

# 5. Получить SSL сертификаты
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  --email YOUR_EMAIL@example.com --agree-tos \
  -d thepred.com -d www.thepred.com

docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  --email YOUR_EMAIL@example.com --agree-tos \
  -d thepred.tech -d www.thepred.tech

# 6. Вернуть HTTPS конфиги
cd nginx/conf.d
mv thepred.com.conf thepred.com.temp
mv thepred.tech.conf thepred.tech.temp
mv thepred.com.conf.backup thepred.com.conf
mv thepred.tech.conf.backup thepred.tech.conf
cd ../..

# 7. Перезапустить nginx
docker-compose -f docker-compose.prod.yml restart nginx

# 8. Проверить
curl -I https://thepred.com
curl -I https://thepred.tech
```

### Готово! 🎉

- **Лендинг**: https://thepred.com
- **WebApp**: https://thepred.tech
- **Admin**: http://YOUR_IP:8002

---

## 🔧 Основные команды

### Development

```bash
# Запуск
docker-compose up -d

# Логи
docker-compose logs -f

# Остановка
docker-compose down

# Пересборка
docker-compose up -d --build
```

### Production

```bash
# Запуск
docker-compose -f docker-compose.prod.yml up -d

# Логи
docker-compose -f docker-compose.prod.yml logs -f

# Остановка
docker-compose -f docker-compose.prod.yml down

# Обновление
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```

### База данных

```bash
# Подключиться
docker-compose exec postgres psql -U thepred

# Бэкап
docker-compose exec -T postgres pg_dump -U thepred thepred > backup.sql

# Восстановление
docker-compose exec -T postgres psql -U thepred thepred < backup.sql
```

### Проверка здоровья

```bash
# Статус всех сервисов
docker-compose ps

# Использование ресурсов
docker stats

# Проверка API
curl http://localhost:8000/health

# Проверка SSL
curl -I https://thepred.com
openssl s_client -connect thepred.com:443
```

---

## 🆘 Troubleshooting

### Контейнер не запускается

```bash
# Посмотреть логи
docker-compose logs <service_name>

# Пересоздать контейнер
docker-compose up -d --force-recreate <service_name>
```

### Ошибка "port already in use"

```bash
# Найти процесс на порту
sudo lsof -i :8000

# Убить процесс
sudo kill -9 <PID>
```

### Домен не открывается

```bash
# Проверить DNS
dig +short thepred.com

# Проверить nginx
docker-compose exec nginx nginx -t
docker-compose logs nginx
```

### SSL не работает

```bash
# Проверить сертификаты
docker-compose exec nginx ls -la /etc/letsencrypt/live/

# Пересоздать сертификат
docker-compose run --rm certbot renew --force-renewal
```

---

## 📚 Полная документация

- **[README.md](./README.md)** - Обзор проекта
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Полное руководство по деплою
- **[SSL_SETUP.md](./SSL_SETUP.md)** - Настройка SSL
- **[CLAUDE.md](./CLAUDE.md)** - Техническая документация
- **[PREDICTION_MECHANICS.md](./PREDICTION_MECHANICS.md)** - Механика предсказаний

---

## ⚡ Checklist перед запуском

### Development
- [ ] Docker установлен
- [ ] BOT_TOKEN получен от @BotFather
- [ ] .env создан с минимальными переменными
- [ ] `docker-compose up -d` выполнен
- [ ] Все контейнеры в статусе "Up"

### Production
- [ ] Сервер готов (Ubuntu, 4GB RAM)
- [ ] Домены настроены и указывают на IP
- [ ] .env заполнен ВСЕМИ переменными
- [ ] Все пароли сильные и уникальные
- [ ] Firewall настроен (80, 443, 8002)
- [ ] SSL сертификаты получены
- [ ] HTTPS работает с зеленым замочком
- [ ] Бэкапы настроены

---

**Нужна помощь?** См. [DEPLOYMENT.md](./DEPLOYMENT.md) для подробностей.
