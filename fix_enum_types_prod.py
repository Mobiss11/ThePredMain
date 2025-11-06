#!/usr/bin/env python3
"""
Скрипт для исправления ENUM типов на UPPERCASE в продакшн БД
Пересоздает таблицы leaderboard_periods и telegram_notifications_queue
с правильными ENUM значениями

Запуск на сервере:
POSTGRES_PASSWORD='...' python3 fix_enum_types_prod.py
"""
import asyncio
import os
import sys
from urllib.parse import quote_plus
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Получаем параметры подключения из env
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'thepred')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'thepred')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

if not POSTGRES_PASSWORD:
    print("❌ ОШИБКА: Переменная окружения POSTGRES_PASSWORD не установлена!")
    print("\nУстанови переменную:")
    print('  export POSTGRES_PASSWORD="твой_пароль"')
    print("\nИли передай через командную строку:")
    print('  POSTGRES_PASSWORD="твой_пароль" python3 fix_enum_types_prod.py')
    sys.exit(1)

# URL-кодируем пароль чтобы обработать спецсимволы
POSTGRES_PASSWORD_ENCODED = quote_plus(POSTGRES_PASSWORD)

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD_ENCODED}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

async def fix_enums():
    """Исправить ENUM типы на UPPERCASE"""
    print(f"🔌 Подключение к БД: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")

    engine = create_async_engine(DATABASE_URL, echo=False)

    try:
        async with engine.begin() as conn:
            print("✅ Подключение установлено")

            # Удаляем существующие таблицы если есть
            print("\n⚠️  ВНИМАНИЕ: Удаление таблиц leaderboard_periods и telegram_notifications_queue...")
            print("Это удалит все данные в этих таблицах!")
            await conn.execute(text("DROP TABLE IF EXISTS telegram_notifications_queue CASCADE;"))
            await conn.execute(text("DROP TABLE IF EXISTS leaderboard_periods CASCADE;"))
            print("✅ Таблицы удалены")

            # Удаляем и создаем ENUM типы с UPPERCASE значениями
            print("\n📝 Пересоздание ENUM типов с UPPERCASE значениями...")

            # periodtype
            await conn.execute(text("DROP TYPE IF EXISTS periodtype CASCADE;"))
            await conn.execute(text("CREATE TYPE periodtype AS ENUM ('WEEK', 'MONTH');"))
            print("✅ Создан periodtype: WEEK, MONTH")

            # periodstatus
            await conn.execute(text("DROP TYPE IF EXISTS periodstatus CASCADE;"))
            await conn.execute(text("CREATE TYPE periodstatus AS ENUM ('ACTIVE', 'CLOSED', 'SCHEDULED');"))
            print("✅ Создан periodstatus: ACTIVE, CLOSED, SCHEDULED")

            # notificationstatus - ИСПРАВЛЕНО: UPPERCASE значения
            await conn.execute(text("DROP TYPE IF EXISTS notificationstatus CASCADE;"))
            await conn.execute(text("CREATE TYPE notificationstatus AS ENUM ('PENDING', 'PROCESSING', 'SENT', 'FAILED', 'PERMANENT_FAILURE');"))
            print("✅ Создан notificationstatus: PENDING, PROCESSING, SENT, FAILED, PERMANENT_FAILURE")

            # notificationtype
            await conn.execute(text("DROP TYPE IF EXISTS notificationtype CASCADE;"))
            await conn.execute(text("CREATE TYPE notificationtype AS ENUM ('LEADERBOARD_REWARD', 'MARKET_RESOLVED', 'BET_WON', 'BET_LOST', 'MISSION_COMPLETED', 'SYSTEM');"))
            print("✅ Создан notificationtype: LEADERBOARD_REWARD, MARKET_RESOLVED, BET_WON, BET_LOST, MISSION_COMPLETED, SYSTEM")

            # Создаем таблицу leaderboard_periods
            print("\n📝 Создание таблицы leaderboard_periods...")
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS leaderboard_periods (
                    id SERIAL PRIMARY KEY,
                    period_type periodtype NOT NULL,
                    start_date TIMESTAMPTZ NOT NULL,
                    end_date TIMESTAMPTZ NOT NULL,
                    status periodstatus NOT NULL,
                    total_rewards_distributed INTEGER DEFAULT 0,
                    participants_count INTEGER DEFAULT 0,
                    winners_count INTEGER DEFAULT 0,
                    closed_at TIMESTAMPTZ,
                    closed_by_admin_id INTEGER,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))
            print("✅ Таблица leaderboard_periods создана")

            # Создаем индексы для leaderboard_periods
            print("📝 Создание индексов для leaderboard_periods...")
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_leaderboard_periods_id ON leaderboard_periods(id);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_leaderboard_periods_status ON leaderboard_periods(status);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_leaderboard_periods_period_type ON leaderboard_periods(period_type);"))
            print("✅ Индексы для leaderboard_periods созданы")

            # Создаем таблицу telegram_notifications_queue
            print("\n📝 Создание таблицы telegram_notifications_queue...")
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS telegram_notifications_queue (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT NOT NULL,
                    user_id INTEGER,
                    message_text TEXT NOT NULL,
                    parse_mode VARCHAR(10) DEFAULT 'HTML',
                    notification_type notificationtype NOT NULL,
                    status notificationstatus NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    max_attempts INTEGER DEFAULT 5,
                    scheduled_at TIMESTAMPTZ,
                    processing_at TIMESTAMPTZ,
                    sent_at TIMESTAMPTZ,
                    error_message TEXT,
                    last_error_at TIMESTAMPTZ,
                    notification_metadata TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))
            print("✅ Таблица telegram_notifications_queue создана")

            # Создаем индексы для telegram_notifications_queue
            print("📝 Создание индексов для telegram_notifications_queue...")
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_telegram_notifications_queue_id ON telegram_notifications_queue(id);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_telegram_notifications_queue_telegram_id ON telegram_notifications_queue(telegram_id);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_telegram_notifications_queue_user_id ON telegram_notifications_queue(user_id);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_telegram_notifications_queue_status ON telegram_notifications_queue(status);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_telegram_notifications_queue_created_at ON telegram_notifications_queue(created_at);"))
            print("✅ Индексы для telegram_notifications_queue созданы")

            # Отмечаем миграцию как примененную
            print("\n📝 Отметка миграции как примененной...")
            await conn.execute(text("""
                INSERT INTO alembic_version (version_num)
                VALUES ('c8d9e5f6g7h8')
                ON CONFLICT (version_num) DO NOTHING;
            """))
            print("✅ Миграция отмечена как примененная (c8d9e5f6g7h8)")

        print("\n" + "="*60)
        print("✅ ВСЕ ИСПРАВЛЕНО! ENUM ТИПЫ ТЕПЕРЬ UPPERCASE!")
        print("="*60)
        print("\nИсправлено:")
        print("  1. ENUM типы пересозданы с UPPERCASE значениями")
        print("  2. Таблица: leaderboard_periods (+ 3 индекса)")
        print("  3. Таблица: telegram_notifications_queue (+ 5 индексов)")
        print("  4. Запись в alembic_version")
        print("\nТеперь перезапусти воркеры:")
        print("  pm2 reload ecosystem.config.js")
        print("  pm2 logs telegram-worker")
        print("  pm2 logs leaderboard-scheduler")

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    # Импортируем text здесь чтобы избежать проблем
    from sqlalchemy import text

    print("="*60)
    print("🚀 ИСПРАВЛЕНИЕ ENUM ТИПОВ НА UPPERCASE")
    print("="*60)
    print("\n⚠️  ВНИМАНИЕ: Этот скрипт удалит таблицы:")
    print("  - leaderboard_periods")
    print("  - telegram_notifications_queue")
    print("\nПродолжить? (yes/no): ", end="")

    response = input().strip().lower()
    if response != 'yes':
        print("❌ Отменено")
        sys.exit(0)

    print("\n")
    asyncio.run(fix_enums())
