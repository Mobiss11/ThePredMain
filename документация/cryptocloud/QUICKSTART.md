# 🚀 CryptoCloud - Quick Start Guide

Быстрая интеграция CryptoCloud платежей в ваш проект за 15 минут.

## 📦 Установка зависимостей

```bash
pip install fastapi sqlalchemy asyncpg requests pydantic python-dotenv
```

## ⚙️ Настройка .env

```bash
# Получите на https://cryptocloud.plus
CRYPTOCLOUD_API_KEY=your_api_key_here
CRYPTOCLOUD_SHOP_ID=your_shop_id_here

# URL вашего приложения
BASE_URL=https://yourdomain.com
DOMAIN=https://yourdomain.com

# База данных
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
```

## 🗄️ Создание таблиц

```sql
-- Таблица платежей
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    invoice_id VARCHAR(255) UNIQUE,
    amount FLOAT NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    payment_method VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    subscription_tier VARCHAR(20) NOT NULL,
    subscription_months INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    payment_url VARCHAR(1000),
    payment_data TEXT
);

-- Индексы для производительности
CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_invoice_id ON payments(invoice_id);
CREATE INDEX idx_payments_status ON payments(status);

-- Обновление таблицы users
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(20) DEFAULT 'free';
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_expires TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS requests_limit INTEGER DEFAULT 100;
ALTER TABLE users ADD COLUMN IF NOT EXISTS requests_used INTEGER DEFAULT 0;
```

## 📁 Минимальная структура файлов

```
your_project/
├── app/
│   ├── main.py                    # FastAPI приложение
│   ├── config.py                  # Конфигурация
│   ├── database.py                # Настройка БД
│   ├── models/
│   │   ├── payment.py             # Модель Payment
│   │   └── user.py                # Модель User
│   ├── services/
│   │   └── payment_service.py     # Логика платежей
│   └── routes/
│       └── payment.py             # API endpoints
├── .env                           # Переменные окружения
└── requirements.txt               # Зависимости
```

## 💾 Минимальный код

### 1. config.py

```python
import os
from dotenv import load_dotenv

load_dotenv()

CRYPTOCLOUD_API_KEY = os.getenv("CRYPTOCLOUD_API_KEY", "")
CRYPTOCLOUD_SHOP_ID = os.getenv("CRYPTOCLOUD_SHOP_ID", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

PRICING_TIERS = {
    "free": {"name": "Free", "requests": 100, "price": 0},
    "pro": {"name": "Pro", "requests": 100000, "price": 99},
}

class Settings:
    CRYPTOCLOUD_API_KEY = CRYPTOCLOUD_API_KEY
    CRYPTOCLOUD_SHOP_ID = CRYPTOCLOUD_SHOP_ID
    BASE_URL = BASE_URL
    PRICING_TIERS = PRICING_TIERS

settings = Settings()
```

### 2. database.py

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session
```

### 3. Скопируйте файлы из документации

Скопируйте следующие файлы из полной документации (`CRYPTOCLOUD_INTEGRATION.md`):

- `app/models/payment.py` - Модель Payment
- `app/services/payment_service.py` - CryptoCloudService и PaymentService
- `app/routes/payment.py` - API endpoints

### 4. main.py

```python
from fastapi import FastAPI
from app.routes import payment

app = FastAPI(title="Your App with CryptoCloud")

# Регистрируем роуты
app.include_router(payment.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 🧪 Тестирование

### Запуск приложения

```bash
uvicorn app.main:app --reload
```

### Тест создания платежа

```python
import httpx
import asyncio

async def test_payment():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/dashboard/subscription/upgrade",
            data={
                "tier": "pro",
                "months": 1,
                "payment_method": "crypto"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Redirect: {response.headers.get('location')}")

asyncio.run(test_payment())
```

### Настройка Webhook (для локальной разработки)

```bash
# Установите ngrok
brew install ngrok  # Mac
# или скачайте с https://ngrok.com/download

# Запустите ngrok
ngrok http 8000

# Используйте ngrok URL в CryptoCloud настройках
# Пример: https://abc123.ngrok.io/api/webhook/payment
```

## 📋 Основные endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/dashboard/subscription/upgrade` | POST | Создать платеж |
| `/api/webhook/payment` | POST | Webhook от CryptoCloud |
| `/dashboard/payment/success` | GET | Страница успеха |
| `/dashboard/payment/error` | GET | Страница ошибки |
| `/dashboard/payments` | GET | История платежей |

## 🔄 Типичный поток платежа

```mermaid
sequenceDiagram
    User->>App: Выбирает тариф
    App->>PaymentService: create_payment()
    PaymentService->>CryptoCloud: create_invoice()
    CryptoCloud-->>PaymentService: invoice_id + payment_url
    PaymentService->>DB: Сохраняет Payment (status=pending)
    App-->>User: Redirect на payment_url
    User->>CryptoCloud: Оплачивает криптовалютой
    CryptoCloud->>App: POST /api/webhook/payment
    App->>PaymentService: process_payment_webhook()
    PaymentService->>DB: Обновляет Payment (status=completed)
    PaymentService->>DB: Обновляет User.subscription_tier
    App-->>CryptoCloud: {"status": "success"}
    CryptoCloud-->>User: Redirect на success_url
```

## ⚠️ Важные моменты

### 1. Webhook безопасность
```python
# Всегда проверяйте статус
if data.get("status") != "success":
    return {"status": "processed"}

# Защита от дублирования
if payment.status == "completed":
    return True  # Уже обработан
```

### 2. Обработка ошибок
```python
try:
    payment = await payment_service.create_payment(...)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    # Логируем ошибку
    print(f"Payment error: {e}")
    raise HTTPException(status_code=500, detail="Internal error")
```

### 3. Возврат 200 в webhook
```python
# ВСЕГДА возвращайте 200, даже при ошибке
# Иначе CryptoCloud будет повторять запросы
return {"status": "processed", "message": "Acknowledged"}
```

## 🔍 Отладка

### Просмотр логов webhook

```python
# В payment.py добавьте логирование
@router.post("/api/webhook/payment")
async def payment_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    print("=" * 50)
    print("WEBHOOK RECEIVED")

    # Логируем raw body
    body = await request.body()
    print(f"Raw body: {body}")

    # Логируем headers
    print(f"Headers: {dict(request.headers)}")

    # ... остальная обработка
```

### Проверка статуса платежа вручную

```python
from app.services.payment_service import CryptoCloudService

crypto = CryptoCloudService()
status = crypto.check_invoice_status("invoice-uuid-here")
print(status)
```

## 📊 Мониторинг

### Основные метрики

```python
# Количество успешных платежей
SELECT COUNT(*) FROM payments WHERE status = 'completed';

# Общая выручка
SELECT SUM(amount) FROM payments WHERE status = 'completed';

# Платежи за последние 24 часа
SELECT COUNT(*) FROM payments
WHERE status = 'completed'
AND created_at > NOW() - INTERVAL '24 hours';

# Популярные тарифы
SELECT subscription_tier, COUNT(*)
FROM payments
WHERE status = 'completed'
GROUP BY subscription_tier;
```

## 🚨 Troubleshooting

| Проблема | Решение |
|----------|---------|
| Webhook не приходит | Проверьте Callback URL в CryptoCloud, используйте ngrok для локальной разработки |
| Payment not found | Проверьте формат invoice_id (с/без префикса), проверьте логи |
| Subscription не обновляется | Проверьте что webhook обработался (status=completed), проверьте права на таблицу users |
| Duplicate payments | Убедитесь в проверке `if payment.status == "completed"`, добавьте уникальный индекс на invoice_id |

## ✅ Production Checklist

- [ ] HTTPS настроен
- [ ] Переменные окружения настроены
- [ ] Webhook URL публично доступен
- [ ] Логирование включено
- [ ] Backup БД настроен
- [ ] Мониторинг платежей настроен
- [ ] Тестовые платежи прошли успешно

## 📚 Дополнительные ресурсы

- **Полная документация**: `CRYPTOCLOUD_INTEGRATION.md`
- **CryptoCloud API**: https://cryptocloud.plus/api-docs
- **Поддержка**: support@cryptocloud.plus

---

**Время интеграции**: ~15 минут
**Сложность**: Средняя
**Требуется**: Python 3.11+, PostgreSQL, FastAPI

Удачи! 🚀
