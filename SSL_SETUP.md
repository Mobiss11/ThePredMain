# SSL Certificate Setup Guide

Это руководство по настройке SSL сертификатов для production деплоя ThePred.

---

## 📋 Требования

1. **Домены**:
   - `thepred.com` (и `www.thepred.com`)
   - `thepred.tech` (и `www.thepred.tech`)

2. **DNS настройка**:
   - A-записи для доменов должны указывать на IP сервера
   - Подождать пока DNS пропагируется (может занять до 24 часов)

3. **Сервер**:
   - Docker и Docker Compose установлены
   - Порты 80 и 443 открыты

---

## 🔐 Способ 1: Автоматический (Рекомендуется)

### Шаг 1: Проверить DNS

```bash
# Проверить что домены указывают на ваш сервер
dig +short thepred.com
dig +short thepred.tech

# Или с nslookup
nslookup thepred.com
nslookup thepred.tech
```

Убедитесь что IP совпадает с вашим сервером.

### Шаг 2: Создать временные nginx конфиги (только HTTP)

Создайте временные версии конфигов без SSL для первоначального получения сертификатов.

```bash
cd /path/to/ThePred/nginx/conf.d

# Создать временный конфиг для thepred.com
cat > thepred.com.temp.conf << 'EOF'
server {
    listen 80;
    listen [::]:80;
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

# Создать временный конфиг для thepred.tech
cat > thepred.tech.temp.conf << 'EOF'
server {
    listen 80;
    listen [::]:80;
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

# Переименовать основные конфиги
mv thepred.com.conf thepred.com.conf.backup
mv thepred.tech.conf thepred.tech.conf.backup

# Использовать временные
mv thepred.com.temp.conf thepred.com.conf
mv thepred.tech.temp.conf thepred.tech.conf
```

### Шаг 3: Запустить nginx и получить сертификаты

```bash
cd /path/to/ThePred

# Запустить только nginx и certbot (без остальных сервисов)
docker-compose -f docker-compose.prod.yml up -d nginx certbot

# Подождать пока nginx запустится
sleep 5

# Получить сертификат для thepred.com
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d thepred.com \
  -d www.thepred.com

# Получить сертификат для thepred.tech
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d thepred.tech \
  -d www.thepred.tech
```

**ВАЖНО**: Замените `your-email@example.com` на ваш реальный email!

### Шаг 4: Проверить что сертификаты созданы

```bash
# Проверить сертификаты
docker-compose -f docker-compose.prod.yml exec nginx ls -la /etc/letsencrypt/live/

# Должны быть папки:
# - thepred.com
# - thepred.tech
```

### Шаг 5: Вернуть полные конфиги с HTTPS

```bash
cd nginx/conf.d

# Вернуть полные конфиги с SSL
mv thepred.com.conf thepred.com.temp.conf
mv thepred.tech.conf thepred.tech.temp.conf
mv thepred.com.conf.backup thepred.com.conf
mv thepred.tech.conf.backup thepred.tech.conf

# Перезапустить nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Шаг 6: Тест

```bash
# Проверить что HTTPS работает
curl -I https://thepred.com
curl -I https://thepred.tech

# Проверить SSL сертификат
openssl s_client -connect thepred.com:443 -servername thepred.com < /dev/null

# Проверить в браузере
# Должен быть зеленый замочек 🔒
```

---

## 🔄 Автообновление сертификатов

Сертификаты Let's Encrypt действуют 90 дней. В docker-compose.prod.yml уже настроен certbot контейнер который автоматически продлевает сертификаты каждые 12 часов.

### Проверить статус certbot

```bash
# Посмотреть логи certbot
docker-compose -f docker-compose.prod.yml logs certbot

# Ручное продление (для теста)
docker-compose -f docker-compose.prod.yml run --rm certbot renew --dry-run
```

### Настроить email уведомления (опционально)

Добавьте в crontab на сервере:

```bash
# Открыть crontab
crontab -e

# Добавить строку (проверка каждый день в 3 ночи)
0 3 * * * cd /path/to/ThePred && docker-compose -f docker-compose.prod.yml exec certbot renew --quiet && docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

---

## 🔐 Способ 2: Ручной (если не работает автомат)

### Вариант A: Использовать standalone режим

```bash
# Остановить nginx
docker-compose -f docker-compose.prod.yml stop nginx

# Получить сертификаты в standalone режиме
docker run -it --rm \
  -p 80:80 \
  -v certbot_conf:/etc/letsencrypt \
  certbot/certbot certonly \
  --standalone \
  --email your-email@example.com \
  --agree-tos \
  -d thepred.com \
  -d www.thepred.com

docker run -it --rm \
  -p 80:80 \
  -v certbot_conf:/etc/letsencrypt \
  certbot/certbot certonly \
  --standalone \
  --email your-email@example.com \
  --agree-tos \
  -d thepred.tech \
  -d www.thepred.tech

# Запустить nginx обратно
docker-compose -f docker-compose.prod.yml up -d nginx
```

### Вариант B: Использовать DNS challenge (для wildcard)

```bash
# Для получения wildcard сертификата (*.thepred.com)
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --manual \
  --preferred-challenges=dns \
  --email your-email@example.com \
  --agree-tos \
  -d "*.thepred.com" \
  -d thepred.com

# Certbot попросит добавить TXT запись в DNS
# Добавьте запись и подождите 5 минут перед продолжением
```

---

## 🛠 Troubleshooting

### Ошибка: "Connection refused"

```bash
# Проверить что порт 80 открыт
sudo netstat -tulpn | grep :80

# Проверить firewall
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### Ошибка: "Domain not pointing to server"

```bash
# Проверить DNS
dig +short thepred.com

# Если не совпадает - нужно подождать пока DNS пропагируется
# Или изменить A-запись в панели управления доменом
```

### Ошибка: "Too many certificates already issued"

Let's Encrypt имеет лимит: **50 сертификатов в неделю** для одного домена.

Решение:
- Используйте `--dry-run` для тестирования
- Подождите неделю
- Или используйте staging окружение для тестов

```bash
# Тестовый запуск (не учитывается в лимите)
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  --dry-run \
  -d thepred.com
```

### Проверить логи

```bash
# Nginx логи
docker-compose -f docker-compose.prod.yml logs nginx

# Certbot логи
docker-compose -f docker-compose.prod.yml logs certbot

# Ошибки сертификатов
docker-compose -f docker-compose.prod.yml exec nginx cat /var/log/nginx/error.log
```

---

## 📚 Дополнительная информация

### Структура сертификатов

```
certbot_conf/
└── live/
    ├── thepred.com/
    │   ├── fullchain.pem  # Сертификат + цепочка
    │   ├── privkey.pem    # Приватный ключ
    │   ├── cert.pem       # Только сертификат
    │   └── chain.pem      # Только цепочка
    └── thepred.tech/
        ├── fullchain.pem
        ├── privkey.pem
        ├── cert.pem
        └── chain.pem
```

### SSL Test

После настройки проверьте качество SSL:

**SSL Labs Test**: https://www.ssllabs.com/ssltest/analyze.html?d=thepred.com

Должен быть рейтинг **A** или **A+**.

### Ручное продление

```bash
# Продлить все сертификаты
docker-compose -f docker-compose.prod.yml run --rm certbot renew

# Продлить конкретный домен
docker-compose -f docker-compose.prod.yml run --rm certbot renew --cert-name thepred.com

# Перезагрузить nginx после продления
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### Отозвать сертификат

```bash
# Отозвать сертификат
docker-compose -f docker-compose.prod.yml run --rm certbot revoke \
  --cert-path /etc/letsencrypt/live/thepred.com/cert.pem

# Удалить сертификат
docker-compose -f docker-compose.prod.yml run --rm certbot delete \
  --cert-name thepred.com
```

---

## ✅ Checklist финальной проверки

После настройки SSL проверьте:

- [ ] `https://thepred.com` открывается с зеленым замочком
- [ ] `http://thepred.com` редиректит на HTTPS
- [ ] `https://www.thepred.com` работает
- [ ] `https://thepred.tech` открывается с зеленым замочком
- [ ] `http://thepred.tech` редиректит на HTTPS
- [ ] `https://www.thepred.tech` работает
- [ ] SSL Labs test показывает A/A+
- [ ] Certbot автообновление работает (проверить через неделю)

---

## 🆘 Помощь

**Документация Let's Encrypt**: https://letsencrypt.org/docs/
**Certbot документация**: https://eff-certbot.readthedocs.io/

**Основные команды**:

```bash
# Список всех сертификатов
docker-compose -f docker-compose.prod.yml run --rm certbot certificates

# Статус сертификата
docker-compose -f docker-compose.prod.yml run --rm certbot certificates --cert-name thepred.com

# Проверить что осталось до истечения
openssl x509 -in /etc/letsencrypt/live/thepred.com/cert.pem -noout -dates
```
