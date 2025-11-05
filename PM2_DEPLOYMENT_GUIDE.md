# PM2 Deployment Guide

## Архитектура

**Docker (Инфраструктура):**
- PostgreSQL - `localhost:5432`
- Redis - `localhost:6379`
- MinIO - `localhost:9000` (API), `localhost:9001` (Console)
- Nginx - `localhost:80`, `localhost:443`

**PM2 (Приложения):**
- Backend API - `localhost:8000`
- Webapp - `localhost:8001`
- Admin - `localhost:8002`
- Bot - (polling, без порта)
- Landing - `localhost:8003`

---

## Установка на сервере

### 1. Установить зависимости

```bash
# Node.js и PM2
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo npm install -g pm2

# Python 3.11+
sudo apt install -y python3 python3-pip python3-venv

# Docker (если еще не установлен)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt install -y docker-compose
```

### 2. Клонировать проект

```bash
cd /root
git clone https://github.com/Mobiss11/ThePredMain.git
cd ThePredMain
```

### 3. Установить Python зависимости

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Webapp
cd webapp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Admin
cd admin
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Bot
cd bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Landing
cd landing
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..
```

### 4. Настроить .env файл

```bash
# Скопировать и настроить .env
cp .env.example .env
nano .env

# Убедиться что все переменные правильные:
# - POSTGRES_HOST=localhost
# - REDIS_HOST=localhost
# - S3_ENDPOINT=http://localhost:9000
# - S3_PUBLIC_URL=https://thepred.store
```

### 5. Обновить ecosystem.config.js

```bash
# Отредактировать пути к venv интерпретаторам
nano ecosystem.config.js
```

Изменить `interpreter` на полные пути:
```javascript
interpreter: '/root/ThePredMain/backend/venv/bin/python3',
```

### 6. Запустить инфраструктуру (Docker)

```bash
# Запустить только инфраструктуру
docker-compose -f docker-compose.infrastructure.yml up -d

# Проверить статус
docker-compose -f docker-compose.infrastructure.yml ps

# Проверить логи
docker-compose -f docker-compose.infrastructure.yml logs -f
```

### 7. Применить миграции базы данных

```bash
cd backend
source venv/bin/activate
POSTGRES_HOST=localhost alembic upgrade head
deactivate
cd ..
```

### 8. Загрузить иконки миссий в S3

```bash
cd /root/ThePredMain
python3 upload_mission_icons_to_s3.py
```

### 9. Запустить приложения через PM2

```bash
# Запустить все приложения
pm2 start ecosystem.config.js

# Проверить статус
pm2 status

# Посмотреть логи
pm2 logs

# Мониторинг
pm2 monit

# Сохранить конфигурацию PM2 для автозапуска
pm2 save
pm2 startup
```

---

## Управление PM2

### Основные команды

```bash
# Статус всех приложений
pm2 status

# Логи всех приложений
pm2 logs

# Логи конкретного приложения
pm2 logs backend
pm2 logs webapp
pm2 logs admin
pm2 logs bot
pm2 logs landing

# Перезапуск приложений
pm2 restart all
pm2 restart backend
pm2 restart webapp

# Остановка приложений
pm2 stop all
pm2 stop backend

# Удаление приложений
pm2 delete all
pm2 delete backend

# Мониторинг ресурсов
pm2 monit

# Информация о приложении
pm2 info backend

# Список процессов
pm2 list
```

### Обновление кода

```bash
cd /root/ThePredMain

# Подтянуть изменения
git pull

# Перезапустить приложения
pm2 restart all

# Или по отдельности
pm2 restart backend
pm2 restart webapp
pm2 restart admin
pm2 restart bot
```

### Просмотр логов

```bash
# Все логи в реальном времени
pm2 logs --lines 100

# Только backend
pm2 logs backend --lines 50

# Только ошибки
pm2 logs --err

# Очистить логи
pm2 flush
```

---

## Nginx конфигурация

Nginx должен проксировать на localhost порты:

```nginx
# /etc/nginx/sites-available/thepred

upstream backend_api {
    server localhost:8000;
}

upstream webapp {
    server localhost:8001;
}

upstream admin_panel {
    server localhost:8002;
}

upstream landing_page {
    server localhost:8003;
}

upstream minio_s3 {
    server localhost:9000;
}

server {
    listen 80;
    listen 443 ssl http2;
    server_name thepred.tech www.thepred.tech;

    # SSL certificates
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # Webapp (Mini App)
    location / {
        proxy_pass http://webapp;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend_api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Landing Page
    location /landing/ {
        proxy_pass http://landing_page/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    listen 443 ssl http2;
    server_name admin.thepred.tech;

    # SSL certificates
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # Admin Panel
    location / {
        proxy_pass http://admin_panel;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    listen 443 ssl http2;
    server_name thepred.store;

    # SSL certificates
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # MinIO S3
    location / {
        proxy_pass http://minio_s3;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS для S3
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods 'GET, POST, PUT, DELETE, OPTIONS';
    }
}
```

Применить конфигурацию:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## Troubleshooting

### Проблема: Приложение не запускается

```bash
# Проверить логи PM2
pm2 logs backend --lines 50 --err

# Проверить что venv существует
ls -la backend/venv/bin/python3

# Переустановить зависимости
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Перезапустить
pm2 restart backend
```

### Проблема: Не подключается к PostgreSQL

```bash
# Проверить что PostgreSQL запущен
docker ps | grep postgres

# Проверить подключение
psql -h localhost -U thepred -d thepred

# Проверить порт
netstat -tulpn | grep 5432

# Перезапустить Docker
docker-compose -f docker-compose.infrastructure.yml restart postgres
```

### Проблема: S3 иконки не загружаются

```bash
# Проверить что MinIO запущен
docker ps | grep minio

# Проверить доступность
curl http://localhost:9000/minio/health/live

# Загрузить иконки заново
python3 upload_mission_icons_to_s3.py

# Проверить что файлы загружены
curl https://thepred.store/thepred-events/missions/first_bet.svg
```

### Проблема: PM2 логи переполняются

```bash
# Установить PM2 log rotate
pm2 install pm2-logrotate

# Настроить лимит размера логов (10MB)
pm2 set pm2-logrotate:max_size 10M

# Настроить количество файлов (10)
pm2 set pm2-logrotate:retain 10

# Очистить старые логи
pm2 flush
```

---

## Мониторинг

### PM2 Plus (опционально)

Регистрация на https://pm2.io для продвинутого мониторинга:

```bash
pm2 link <secret_key> <public_key>
```

### Базовый мониторинг

```bash
# Системные ресурсы
pm2 monit

# Статистика
pm2 list

# Информация о процессе
pm2 info backend
```

---

## Преимущества PM2 vs Docker

✅ **Быстрые обновления** - `git pull && pm2 restart all` (секунды)
✅ **Удобные логи** - `pm2 logs` в реальном времени
✅ **Автоперезапуск** - при падении или перезагрузке сервера
✅ **Мониторинг** - встроенный `pm2 monit`
✅ **Нет пересборки** - изменения кода сразу применяются
✅ **Меньше ресурсов** - нет overhead от Docker контейнеров

---

## Backup & Recovery

### Backup базы данных

```bash
# Создать backup
docker exec thepred_postgres pg_dump -U thepred thepred > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановить из backup
docker exec -i thepred_postgres psql -U thepred thepred < backup.sql
```

### Backup S3 данных

```bash
# Создать backup MinIO
docker run --rm -v minio_data:/data -v $(pwd):/backup alpine tar czf /backup/minio_backup_$(date +%Y%m%d).tar.gz /data
```

---

**Готово!** Теперь у вас гибкая настройка с инфраструктурой в Docker и приложениями в PM2 🚀
