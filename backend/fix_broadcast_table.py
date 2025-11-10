#!/usr/bin/env python3
"""
Скрипт для создания таблицы scheduled_broadcasts
Запуск: python3 fix_broadcast_table.py
"""
import asyncio
import asyncpg
import os
import sys

# Database credentials
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'database': os.getenv('POSTGRES_DB', 'thepred'),
    'user': os.getenv('POSTGRES_USER', 'thepred'),
    'password': os.getenv('POSTGRES_PASSWORD', 'SUPER_STRONG_PASSWORD_CHANGE_ME_123!@#')
}


async def fix_broadcast_table():
    """Создать таблицу scheduled_broadcasts если её нет"""
    print("🔌 Подключение к базе данных...")

    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        print("✅ Подключено к PostgreSQL")

        # 1. Создать enum если нет
        print("\n📋 Создание enum broadcaststatus...")
        await conn.execute("""
            DO $$ BEGIN
                CREATE TYPE broadcaststatus AS ENUM (
                    'PENDING', 'PROCESSING', 'COMPLETED', 'CANCELLED'
                );
                RAISE NOTICE 'Enum broadcaststatus создан';
            EXCEPTION
                WHEN duplicate_object THEN
                    RAISE NOTICE 'Enum broadcaststatus уже существует';
            END $$;
        """)
        print("✅ Enum готов")

        # 2. Проверить существует ли таблица
        print("\n🔍 Проверка таблицы scheduled_broadcasts...")
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'scheduled_broadcasts'
            );
        """)

        if table_exists:
            print("⚠️  Таблица scheduled_broadcasts уже существует")

            # Проверить структуру
            columns = await conn.fetch("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'scheduled_broadcasts'
                ORDER BY ordinal_position;
            """)

            print("\n📊 Текущие колонки:")
            for col in columns:
                print(f"   - {col['column_name']}: {col['data_type']}")

        else:
            print("📝 Создание таблицы scheduled_broadcasts...")

            # 3. Создать таблицу
            await conn.execute("""
                CREATE TABLE scheduled_broadcasts (
                    id SERIAL PRIMARY KEY,
                    message_text TEXT NOT NULL,
                    parse_mode VARCHAR(10) DEFAULT 'HTML',
                    photo_url VARCHAR(500),
                    target VARCHAR(20) DEFAULT 'all',
                    target_telegram_id INTEGER,
                    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    status broadcaststatus NOT NULL DEFAULT 'PENDING',
                    total_recipients INTEGER DEFAULT 0,
                    sent_count INTEGER DEFAULT 0,
                    created_by INTEGER,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    processed_at TIMESTAMP WITH TIME ZONE
                );
            """)
            print("✅ Таблица создана")

            # 4. Создать индексы
            print("\n🔗 Создание индексов...")
            await conn.execute("""
                CREATE INDEX ix_scheduled_broadcasts_id
                ON scheduled_broadcasts (id);
            """)
            await conn.execute("""
                CREATE INDEX ix_scheduled_broadcasts_scheduled_at
                ON scheduled_broadcasts (scheduled_at);
            """)
            await conn.execute("""
                CREATE INDEX ix_scheduled_broadcasts_status
                ON scheduled_broadcasts (status);
            """)
            print("✅ Индексы созданы")

        # 5. Обновить alembic_version если нужно
        print("\n📌 Обновление alembic_version...")
        current_version = await conn.fetchval("""
            SELECT version_num FROM alembic_version LIMIT 1;
        """)
        print(f"   Текущая версия: {current_version}")

        target_version = '42cdd14f53a4'
        if current_version != target_version:
            await conn.execute("""
                UPDATE alembic_version SET version_num = $1;
            """, target_version)
            print(f"✅ Версия обновлена до {target_version}")
        else:
            print("✅ Версия уже актуальна")

        await conn.close()
        print("\n🎉 Все готово! Таблица scheduled_broadcasts настроена.")
        print("\n📝 Теперь запусти:")
        print("   pm2 restart backend")
        print("   pm2 start ecosystem.config.js --only broadcast-scheduler")

        return True

    except Exception as e:
        print(f"\n❌ Ошибка: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(fix_broadcast_table())
    sys.exit(0 if success else 1)
