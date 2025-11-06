#!/usr/bin/env python3
"""
Скрипт для создания таблиц лидерборда напрямую через SQL
Обходит проблему с ENUM типами в Alembic миграциях

Запуск: python3 create_leaderboard_tables.py
"""
import asyncio
import os
import sys
from urllib.parse import quote_plus
from sqlalchemy.ext.asyncio import create_async_engine

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
    print('  POSTGRES_PASSWORD="твой_пароль" python3 create_leaderboard_tables.py')
    sys.exit(1)

# URL-кодируем пароль чтобы обработать спецсимволы (!@# и т.д.)
POSTGRES_PASSWORD_ENCODED = quote_plus(POSTGRES_PASSWORD)

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD_ENCODED}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

async def create_tables():
    """Создать таблицы лидерборда"""
    print(f"🔌 Подключение к БД: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    try:
        async with engine.begin() as conn:
            print("✅ Подключение установлено")
            
            # Создаем ENUM типы
            print("\n📝 Создание ENUM типов...")
            await conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'periodtype') THEN
                        CREATE TYPE periodtype AS ENUM ('week', 'month');
                        RAISE NOTICE 'Created type: periodtype';
                    ELSE
                        RAISE NOTICE 'Type periodtype already exists, skipping';
                    END IF;
                END $$;
            """))
            
            await conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'periodstatus') THEN
                        CREATE TYPE periodstatus AS ENUM ('active', 'closed', 'scheduled');
                        RAISE NOTICE 'Created type: periodstatus';
                    ELSE
                        RAISE NOTICE 'Type periodstatus already exists, skipping';
                    END IF;
                END $$;
            """))
            
            await conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notificationstatus') THEN
                        CREATE TYPE notificationstatus AS ENUM ('pending', 'processing', 'sent', 'failed', 'permanent_failure');
                        RAISE NOTICE 'Created type: notificationstatus';
                    ELSE
                        RAISE NOTICE 'Type notificationstatus already exists, skipping';
                    END IF;
                END $$;
            """))
            
            await conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notificationtype') THEN
                        CREATE TYPE notificationtype AS ENUM ('leaderboard_reward', 'market_resolved', 'bet_won', 'bet_lost', 'mission_completed', 'system');
                        RAISE NOTICE 'Created type: notificationtype';
                    ELSE
                        RAISE NOTICE 'Type notificationtype already exists, skipping';
                    END IF;
                END $$;
            """))
            print("✅ ENUM типы готовы")
            
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
                    metadata TEXT,
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
        print("✅ ВСЕ ТАБЛИЦЫ УСПЕШНО СОЗДАНЫ!")
        print("="*60)
        print("\nСозданы:")
        print("  1. ENUM типы: periodtype, periodstatus, notificationstatus, notificationtype")
        print("  2. Таблица: leaderboard_periods (+ 3 индекса)")
        print("  3. Таблица: telegram_notifications_queue (+ 5 индексов)")
        print("  4. Запись в alembic_version")
        print("\nТеперь можешь запустить воркеры:")
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
    print("🚀 СОЗДАНИЕ ТАБЛИЦ ЛИДЕРБОРДА")
    print("="*60)
    
    asyncio.run(create_tables())
