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
- `https://thepred.store/thepred-events/missions/first_bet.svg`
- `https://thepred.store/thepred-events/missions/beginner.svg`
- `https://thepred.store/thepred-events/missions/first_win.svg`
- `https://thepred.store/thepred-events/missions/win_streak.svg`
- `https://thepred.store/thepred-events/missions/active_trader.svg`
- `https://thepred.store/thepred-events/missions/crypto_lover.svg`
- `https://thepred.store/thepred-events/missions/referral.svg`

## Настройка переменных окружения

Убедитесь что в `.env` файле указаны правильные значения:

```bash
# MinIO S3 Storage
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=admin
S3_SECRET_KEY=Ivanbunin110818
S3_BUCKET=thepred-events
S3_PUBLIC_URL=https://thepred.store
```

Эти переменные используются:
- Backend (app/core/config.py) - для загрузки файлов
- Webapp (main.py) - для отображения иконок
- Admin (main.py) - для отображения иконок
