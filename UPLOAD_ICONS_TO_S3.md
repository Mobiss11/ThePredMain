# Загрузка иконок миссий в S3

## Шаг 1: Убедитесь что S3 (MinIO) запущен

```bash
# Проверить что MinIO запущен
docker-compose ps minio

# Если не запущен, запустить
docker-compose up -d minio
```

## Шаг 2: Загрузить иконки

```bash
# Перейти в корневую директорию проекта
cd /path/to/ThePred

# Запустить скрипт загрузки
python3 upload_mission_icons_to_s3.py
```

## Шаг 3: Проверить загрузку

После загрузки иконки будут доступны по URL:
- `http://localhost:9000/thepred-events/missions/first_bet.svg`
- `http://localhost:9000/thepred-events/missions/beginner.svg`
- `http://localhost:9000/thepred-events/missions/first_win.svg`
- `http://localhost:9000/thepred-events/missions/win_streak.svg`
- `http://localhost:9000/thepred-events/missions/active_trader.svg`
- `http://localhost:9000/thepred-events/missions/crypto_lover.svg`
- `http://localhost:9000/thepred-events/missions/referral.svg`

## Production

На production сервере URL будут:
- `http://YOUR_DOMAIN:9000/thepred-events/missions/*.svg`

или если настроен публичный URL:
- `https://s3.your-domain.com/thepred-events/missions/*.svg`

## Настройка переменных окружения

Убедитесь что в `.env` файлах (backend, webapp, admin) указаны правильные значения:

```bash
S3_PUBLIC_URL=http://localhost:9000  # или https://s3.your-domain.com
S3_BUCKET=thepred-events
```
