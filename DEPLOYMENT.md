# Production Deployment Guide

Полное руководство по деплою ThePred на production сервер с доменами.

---

## 📋 Содержание

1. [Требования](#требования)
2. [Подготовка сервера](#подготовка-сервера)
3. [Настройка DNS](#настройка-dns)
4. [Установка зависимостей](#установка-зависимостей)
5. [Настройка environment](#настройка-environment)
6. [Деплой приложения](#деплой-приложения)
7. [SSL сертификаты](#ssl-сертификаты)
8. [Проверка работоспособности](#проверка-работоспособности)
9. [Мониторинг и логи](#мониторинг-и-логи)
10. [Обновление](#обновление)

---

## 🔧 Требования

### Сервер

**Минимальные требования**:
- Ubuntu 20.04+ (или Debian 11+)
- 2 CPU cores
- 4 GB RAM
- 40 GB SSD
- Статический IP адрес

**Рекомендуемые**:
- Ubuntu 22.04 LTS
- 4 CPU cores
- 8 GB RAM
- 80 GB SSD

**Провайдеры**:
- DigitalOcean (Droplet $24/month)
- Hetzner Cloud (CX31 - €9.50/month) - **Рекомендуется**
- AWS EC2 (t3.medium)
- Vultr (High Frequency $24/month)

### Домены

- `thepred.com` - Лендинг
- `thepred.tech` - WebApp (Telegram Mini App)

### Telegram Bot

- Bot token от @BotFather
- Bot username

---

## 🖥 Подготовка сервера

### Шаг 1: Создать сервер

**Hetzner Cloud (Рекомендуется)**:

```bash
# 1. Зарегистрироваться на hetzner.com
# 2. Cloud Console → New Project → "ThePred"
# 3. Add Server:
#    - Location: Helsinki (или Nuremberg)
#    - Image: Ubuntu 22.04
#    - Type: CX31 (2 vCPU, 8GB RAM)
#    - SSH Keys: Добавить свой публичный ключ
#    - Name: thepred-prod
# 4. Create & Boot
```

### Шаг 2: Подключиться к серверу

```bash
# Получить IP из панели Hetzner
ssh root@YOUR_SERVER_IP

# Первый раз спросит про fingerprint - yes
```

### Шаг 3: Обновить систему

```bash
# Обновить пакеты
apt update && apt upgrade -y

# Установить базовые утилиты
apt install -y curl wget git vim htop ufw fail2ban
```

### Шаг 4: Настроить Firewall

```bash
# Настроить UFW
ufw default deny incoming
ufw default allow outgoing

# Разрешить SSH
ufw allow 22/tcp

# Разрешить HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Разрешить админ панель
ufw allow 8002/tcp

# Включить firewall
ufw enable

# Проверить статус
ufw status
```

### Шаг 5: Настроить Fail2Ban (защита от bruteforce)

```bash
# Копировать конфиг
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Редактировать
nano /etc/fail2ban/jail.local

# Найти [sshd] секцию и установить:
# enabled = true
# maxretry = 3
# bantime = 3600

# Перезапустить
systemctl enable fail2ban
systemctl restart fail2ban
```

### Шаг 6: Создать пользователя (опционально)

```bash
# Создать non-root пользователя
adduser deploy
usermod -aG sudo deploy

# Копировать SSH ключи
mkdir -p /home/deploy/.ssh
cp ~/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys

# Переключиться на пользователя
su - deploy
```

---

## 🌐 Настройка DNS

### Шаг 1: Получить IP сервера

```bash
# На сервере
curl ifconfig.me

# Или в панели Hetzner
```

### Шаг 2: Настроить DNS записи

**В панели вашего регистратора доменов** (GoDaddy, Namecheap, etc):

**Для thepred.com**:
```
Type: A
Host: @
Value: YOUR_SERVER_IP
TTL: 300
```

```
Type: A
Host: www
Value: YOUR_SERVER_IP
TTL: 300
```

**Для thepred.tech**:
```
Type: A
Host: @
Value: YOUR_SERVER_IP
TTL: 300
```

```
Type: A
Host: www
Value: YOUR_SERVER_IP
TTL: 300
```

### Шаг 3: Проверить DNS пропагацию

```bash
# Проверить с локального компьютера (может занять до 24 часов)
dig +short thepred.com
dig +short thepred.tech

# Или онлайн
# https://dnschecker.org
```

**ВАЖНО**: Подождите пока DNS пропагируется перед получением SSL!

---

## 📦 Установка зависимостей

### Шаг 1: Установить Docker

```bash
# Удалить старые версии (если есть)
apt remove -y docker docker-engine docker.io containerd runc

# Установить зависимости
apt install -y ca-certificates curl gnupg lsb-release

# Добавить GPG ключ
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Добавить репозиторий
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установить Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Проверить
docker --version
docker compose version

# Добавить пользователя в группу docker (если используете non-root)
usermod -aG docker deploy
```

### Шаг 2: Настроить Docker

```bash
# Включить автозапуск
systemctl enable docker
systemctl start docker

# Проверить статус
systemctl status docker
```

---

## 🔑 Настройка Environment

### Шаг 1: Склонировать проект

```bash
# Перейти в домашнюю директорию
cd ~

# Склонировать (если есть git repo)
git clone https://github.com/yourusername/ThePred.git
cd ThePred

# Или загрузить через scp с локальной машины
# На локальном компьютере:
# scp -r /Users/alluc/Documents/ThePred root@YOUR_SERVER_IP:/root/
```

### Шаг 2: Создать .env файл

```bash
cd /root/ThePred

# Создать .env
nano .env
```

**Содержимое .env** (production версия):

```env
# ============ Database ============
POSTGRES_DB=thepred
POSTGRES_USER=thepred
POSTGRES_PASSWORD=SUPER_STRONG_PASSWORD_CHANGE_ME_123!@#

# ============ JWT ============
JWT_SECRET=YOUR_SUPER_SECRET_JWT_KEY_MINIMUM_32_CHARS_RANDOM
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# ============ Application ============
DEBUG=false
INITIAL_PRED_BALANCE=10000
REFERRAL_BONUS_PRED=1000

# ============ Telegram Bot ============
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
BOT_USERNAME=The_Pred_Bot

# ============ WebApp ============
WEBAPP_URL=https://thepred.tech
WEBAPP_SECRET_KEY=WEBAPP_SECRET_KEY_RANDOM_STRING_32_CHARS
DEV_MODE=false

# ============ Admin ============
ADMIN_PASSWORD=STRONG_ADMIN_PASSWORD_CHANGE_ME
ADMIN_SECRET_KEY=ADMIN_SECRET_KEY_RANDOM_32_CHARS
```

**ВАЖНО**:
- Замените все пароли и секретные ключи!
- Используйте сильные пароли (минимум 32 символа)
- Никогда не коммитьте .env в git!

### Генерация случайных ключей

```bash
# Сгенерировать случайные секретные ключи
openssl rand -base64 32

# Запустить несколько раз для разных ключей
```

### Шаг 3: Установить права на .env

```bash
chmod 600 .env
chown root:root .env  # Или deploy:deploy
```

---

## 🚀 Деплой приложения

### Шаг 1: Подготовить nginx конфиги

```bash
# Создать директорию для SSL (пока пустая)
mkdir -p nginx/ssl

# Проверить что конфиги на месте
ls -la nginx/
ls -la nginx/conf.d/

# Должны быть:
# - nginx.conf
# - conf.d/thepred.com.conf
# - conf.d/thepred.tech.conf
```

### Шаг 2: Первый запуск БЕЗ SSL (для получения сертификатов)

Временно изменим nginx конфиги для получения SSL:

```bash
cd nginx/conf.d

# Создать временные конфиги (только HTTP)
cat > thepred.com.temp.conf << 'EOF'
server {
    listen 80;
    server_name thepred.com www.thepred.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass http://landing:8003;
        proxy_set_header Host $host;
    }
}
EOF

cat > thepred.tech.temp.conf << 'EOF'
server {
    listen 80;
    server_name thepred.tech www.thepred.tech;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass http://webapp:8001;
        proxy_set_header Host $host;
    }
}
EOF

# Сделать бэкапы оригинальных
mv thepred.com.conf thepred.com.conf.backup
mv thepred.tech.conf thepred.tech.conf.backup

# Использовать временные
mv thepred.com.temp.conf thepred.com.conf
mv thepred.tech.temp.conf thepred.tech.conf

cd ../..
```

### Шаг 3: Собрать и запустить

```bash
# Собрать все образы
docker compose -f docker-compose.prod.yml build

# Запустить всё
docker compose -f docker-compose.prod.yml up -d

# Проверить что контейнеры запустились
docker compose -f docker-compose.prod.yml ps

# Все должны быть в состоянии "Up"
```

### Шаг 4: Проверить что HTTP работает

```bash
# С сервера
curl -I http://localhost:80

# С локального компьютера
curl -I http://thepred.com
curl -I http://thepred.tech

# Должны открываться (без SSL пока)
```

---

## 🔐 SSL сертификаты

См. подробную инструкцию в [SSL_SETUP.md](./SSL_SETUP.md)

### Краткая версия:

```bash
cd /root/ThePred

# Получить сертификат для thepred.com
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d thepred.com \
  -d www.thepred.com

# Получить сертификат для thepred.tech
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d thepred.tech \
  -d www.thepred.tech

# Вернуть полные конфиги с HTTPS
cd nginx/conf.d
mv thepred.com.conf thepred.com.temp.conf
mv thepred.tech.conf thepred.tech.temp.conf
mv thepred.com.conf.backup thepred.com.conf
mv thepred.tech.conf.backup thepred.tech.conf
cd ../..

# Перезапустить nginx
docker compose -f docker-compose.prod.yml restart nginx

# Проверить
curl -I https://thepred.com
curl -I https://thepred.tech
```

---

## ✅ Проверка работоспособности

### Шаг 1: Проверить все контейнеры

```bash
docker compose -f docker-compose.prod.yml ps

# Все должны быть Up:
# - postgres
# - redis
# - backend
# - bot
# - webapp
# - admin
# - landing
# - nginx
# - certbot
```

### Шаг 2: Проверить логи

```bash
# Backend
docker compose -f docker-compose.prod.yml logs backend --tail=50

# WebApp
docker compose -f docker-compose.prod.yml logs webapp --tail=50

# Nginx
docker compose -f docker-compose.prod.yml logs nginx --tail=50

# Все сервисы
docker compose -f docker-compose.prod.yml logs --tail=100
```

### Шаг 3: Проверить веб-интерфейсы

**В браузере**:

1. **Лендинг**: https://thepred.com
   - Должен открываться с зеленым замочком
   - Анимации работают
   - Кнопки "Open in Telegram" кликабельны

2. **WebApp**: https://thepred.tech
   - Откройте через Telegram бота
   - Должен быть автологин
   - Должны загружаться рынки

3. **Админ панель**: http://YOUR_SERVER_IP:8002
   - Логин с паролем из .env
   - Должна открываться админка
   - Создание рынков работает

### Шаг 4: Проверить базу данных

```bash
# Подключиться к postgres
docker compose -f docker-compose.prod.yml exec postgres psql -U thepred -d thepred

# Проверить таблицы
\dt

# Проверить пользователей
SELECT id, telegram_id, username FROM users LIMIT 5;

# Выйти
\q
```

### Шаг 5: Проверить API

```bash
# Health check
curl http://localhost:8000/health

# Список рынков
curl http://localhost:8000/api/v1/markets/
```

---

## 📊 Мониторинг и логи

### Просмотр логов

```bash
# Все логи в реальном времени
docker compose -f docker-compose.prod.yml logs -f

# Конкретный сервис
docker compose -f docker-compose.prod.yml logs -f backend

# Последние 100 строк
docker compose -f docker-compose.prod.yml logs --tail=100 webapp

# Логи nginx
docker compose -f docker-compose.prod.yml exec nginx tail -f /var/log/nginx/access.log
docker compose -f docker-compose.prod.yml exec nginx tail -f /var/log/nginx/error.log
```

### Статистика контейнеров

```bash
# Использование ресурсов
docker stats

# Информация о дисковом пространстве
docker system df

# Список volumes
docker volume ls
```

### Мониторинг сервера

```bash
# CPU, RAM, Disk
htop

# Disk usage
df -h

# Используемые порты
netstat -tulpn
```

### Автоматический мониторинг (опционально)

**Установить Grafana + Prometheus**:

```bash
# TODO: Добавить docker-compose для мониторинга
# Будет доступен в будущих версиях
```

---

## 🔄 Обновление

### Обновление кода

```bash
cd /root/ThePred

# Остановить сервисы
docker compose -f docker-compose.prod.yml down

# Обновить код (если git)
git pull

# Или загрузить новые файлы через scp

# Пересобрать образы
docker compose -f docker-compose.prod.yml build

# Запустить
docker compose -f docker-compose.prod.yml up -d

# Проверить логи
docker compose -f docker-compose.prod.yml logs -f
```

### Обновление с миграциями БД

```bash
# Остановить только backend
docker compose -f docker-compose.prod.yml stop backend bot webapp admin

# Сделать бэкап БД
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U thepred thepred > backup_$(date +%Y%m%d_%H%M%S).sql

# Обновить код
git pull

# Запустить миграции
docker compose -f docker-compose.prod.yml up -d backend
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Запустить все сервисы
docker compose -f docker-compose.prod.yml up -d
```

### Zero-downtime deployment (опционально)

```bash
# 1. Собрать новые образы
docker compose -f docker-compose.prod.yml build

# 2. Создать временные контейнеры
docker compose -f docker-compose.prod.yml up -d --no-deps --scale backend=2 backend

# 3. Подождать пока новый запустится
sleep 10

# 4. Остановить старый
docker stop thepred_backend
docker rm thepred_backend

# 5. Переименовать новый
# (требует дополнительной настройки load balancer)
```

---

## 🔒 Безопасность

### Checklist

- [ ] Все пароли сильные и уникальные
- [ ] .env файл не в git
- [ ] Firewall настроен
- [ ] Fail2Ban работает
- [ ] SSL сертификаты установлены
- [ ] DEBUG=false в production
- [ ] Бэкапы настроены
- [ ] SSH только по ключу (опционально)
- [ ] Регулярные обновления системы

### Отключить SSH по паролю (рекомендуется)

```bash
# Редактировать SSH конфиг
nano /etc/ssh/sshd_config

# Найти и изменить:
PasswordAuthentication no
PermitRootLogin prohibit-password

# Перезапустить SSH
systemctl restart sshd
```

### Настроить автообновления

```bash
# Установить unattended-upgrades
apt install -y unattended-upgrades

# Включить
dpkg-reconfigure -plow unattended-upgrades
```

---

## 💾 Бэкапы

### Автоматический бэкап БД

Создать скрипт бэкапа:

```bash
# Создать директорию
mkdir -p /root/backups

# Создать скрипт
cat > /root/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/root/backups
cd /root/ThePred

# Бэкап БД
docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U thepred thepred | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Удалить старые бэкапы (старше 7 дней)
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
EOF

chmod +x /root/backup.sh
```

Добавить в cron:

```bash
# Редактировать crontab
crontab -e

# Добавить строку (каждый день в 3 ночи)
0 3 * * * /root/backup.sh >> /var/log/backup.log 2>&1
```

### Восстановление из бэкапа

```bash
# Распаковать
gunzip /root/backups/db_backup_20251031_030000.sql.gz

# Восстановить
docker compose -f docker-compose.prod.yml exec -T postgres psql -U thepred thepred < /root/backups/db_backup_20251031_030000.sql
```

---

## 🆘 Troubleshooting

### Контейнер не запускается

```bash
# Посмотреть логи
docker compose -f docker-compose.prod.yml logs <service_name>

# Проверить статус
docker compose -f docker-compose.prod.yml ps

# Пересоздать контейнер
docker compose -f docker-compose.prod.yml up -d --force-recreate <service_name>
```

### Не работает домен

```bash
# Проверить DNS
dig +short thepred.com

# Проверить nginx конфиг
docker compose -f docker-compose.prod.yml exec nginx nginx -t

# Перезапустить nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### Ошибки SSL

```bash
# Проверить сертификаты
docker compose -f docker-compose.prod.yml exec nginx ls -la /etc/letsencrypt/live/

# Пересоздать сертификаты
docker compose -f docker-compose.prod.yml run --rm certbot renew --force-renewal

# Проверить SSL конфиг
openssl s_client -connect thepred.com:443
```

### Проблемы с БД

```bash
# Подключиться к БД
docker compose -f docker-compose.prod.yml exec postgres psql -U thepred

# Проверить подключения
SELECT * FROM pg_stat_activity;

# Перезапустить postgres
docker compose -f docker-compose.prod.yml restart postgres
```

### Очистить диск

```bash
# Удалить неиспользуемые образы
docker image prune -a

# Удалить неиспользуемые volumes
docker volume prune

# Полная очистка (ОСТОРОЖНО!)
docker system prune -a --volumes
```

---

## 📞 Поддержка

**Логи**: `/var/log/nginx/`, `docker compose logs`

**Документация**:
- [CLAUDE.md](./CLAUDE.md) - Полная документация проекта
- [SSL_SETUP.md](./SSL_SETUP.md) - Настройка SSL
- [PREDICTION_MECHANICS.md](./PREDICTION_MECHANICS.md) - Механика предсказаний

**Полезные ссылки**:
- Docker Docs: https://docs.docker.com/
- Nginx Docs: https://nginx.org/en/docs/
- Let's Encrypt: https://letsencrypt.org/docs/
