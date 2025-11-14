"""
Базовый пример интеграции CryptoCloud в FastAPI приложение

Этот файл демонстрирует минимальную рабочую интеграцию с CryptoCloud
для приема криптовалютных платежей.

Требования:
    - FastAPI
    - SQLAlchemy с AsyncPG
    - PostgreSQL база данных
    - CryptoCloud аккаунт (API key и Shop ID)
"""

from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Импортируем наши модели и сервисы
# (Предполагается что вы скопировали эти файлы из документации)
from app.models.payment import Payment
from app.models.user import User
from app.services.payment_service import PaymentService

# ============================================================================
# Настройка базы данных
# ============================================================================

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """Dependency для получения сессии БД"""
    async with async_session() as session:
        yield session


# ============================================================================
# Создание FastAPI приложения
# ============================================================================

app = FastAPI(
    title="CryptoCloud Payment Demo",
    description="Базовая интеграция с CryptoCloud для приема крипто платежей",
    version="1.0.0"
)


# ============================================================================
# Простая аутентификация (для примера - замените на свою)
# ============================================================================

async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    """
    Простая функция получения текущего пользователя
    В production используйте JWT или session-based auth
    """
    # Для примера берем первого пользователя из БД
    query = select(User).limit(1)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Главная страница с простой формой выбора тарифа"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CryptoCloud Payment Demo</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
            }
            .tier-card {
                border: 2px solid #ddd;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }
            button {
                background: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background: #45a049;
            }
        </style>
    </head>
    <body>
        <h1>🚀 CryptoCloud Payment Demo</h1>
        <p>Выберите тариф и оплатите криптовалютой</p>

        <form method="post" action="/create-payment">
            <div class="tier-card">
                <h2>Free Tier</h2>
                <p>100 запросов в месяц</p>
                <p><strong>$0/месяц</strong></p>
                <input type="radio" name="tier" value="free" required> Выбрать
            </div>

            <div class="tier-card">
                <h2>Starter Tier</h2>
                <p>50,000 запросов в месяц</p>
                <p><strong>$129/месяц</strong></p>
                <input type="radio" name="tier" value="starter" required> Выбрать
            </div>

            <div class="tier-card">
                <h2>Pro Tier</h2>
                <p>300,000 запросов в месяц</p>
                <p><strong>$299/месяц</strong></p>
                <input type="radio" name="tier" value="pro" required> Выбрать
            </div>

            <h3>Длительность подписки:</h3>
            <select name="months" required>
                <option value="1">1 месяц</option>
                <option value="12">12 месяцев (скидка 10%)</option>
            </select>

            <br><br>
            <button type="submit">Перейти к оплате 💰</button>
        </form>
    </body>
    </html>
    """


@app.post("/create-payment")
async def create_payment(
    tier: str = Form(...),
    months: int = Form(1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создание платежа и перенаправление на страницу оплаты CryptoCloud

    Args:
        tier: Выбранный тариф (free, starter, pro)
        months: Количество месяцев (1 или 12)
    """
    try:
        # Валидация тарифа
        valid_tiers = ["free", "starter", "basic", "pro", "business", "enterprise"]
        if tier not in valid_tiers:
            raise HTTPException(status_code=400, detail="Invalid tier")

        # Валидация длительности
        if months not in [1, 12]:
            raise HTTPException(status_code=400, detail="Invalid duration")

        # Создаем платеж через сервис
        payment_service = PaymentService(db)
        payment = await payment_service.create_payment(
            user_id=current_user.id,
            subscription_tier=tier,
            subscription_months=months
        )

        # Для бесплатного тарифа сразу показываем success
        if tier == "free":
            return RedirectResponse(url="/payment/success", status_code=303)

        # Для платных тарифов - redirect на CryptoCloud
        # Добавляем lang=en для английского интерфейса
        payment_url = f"{payment.payment_url}?lang=en"

        return RedirectResponse(url=payment_url, status_code=303)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error creating payment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/webhook/payment")
async def payment_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook endpoint для обработки уведомлений от CryptoCloud

    CryptoCloud отправляет POST запрос когда платеж успешно завершен
    """
    try:
        print("=" * 50)
        print("📨 Received webhook from CryptoCloud")

        # Пробуем получить данные как form data
        try:
            form_data = await request.form()
            data = {key: form_data.get(key) for key in form_data}
            print(f"📝 Form data: {data}")
        except Exception:
            # Если не получилось, пробуем JSON
            data = await request.json()
            print(f"📝 JSON data: {data}")

        # Проверяем статус
        if data.get("status") != "success":
            print(f"⚠️ Non-success status: {data.get('status')}")
            return {"status": "processed", "message": "Non-success status"}

        # Проверяем наличие invoice_id
        if not data.get("invoice_id"):
            print("❌ Missing invoice_id")
            return {"status": "processed", "message": "Missing invoice_id"}

        # Обрабатываем платеж
        payment_service = PaymentService(db)
        success = await payment_service.process_payment_webhook(data)

        if success:
            print("✅ Payment processed successfully")
            return {"status": "success", "message": "Payment processed"}
        else:
            print("⚠️ Payment processing failed")
            return {"status": "processed", "message": "Processing failed"}

    except Exception as e:
        print(f"❌ Webhook error: {e}")
        # Возвращаем 200 даже при ошибке, чтобы CryptoCloud не повторял запросы
        return {"status": "error", "message": str(e)}


@app.get("/payment/success", response_class=HTMLResponse)
async def payment_success(current_user: User = Depends(get_current_user)):
    """Страница успешной оплаты"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Оплата успешна</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                text-align: center;
                padding: 20px;
            }}
            .success {{
                color: #4CAF50;
                font-size: 48px;
            }}
            button {{
                background: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="success">✅</div>
        <h1>Платеж успешно обработан!</h1>
        <p>Ваша подписка <strong>{current_user.subscription_tier}</strong> активирована.</p>
        <p>Лимит запросов: {current_user.requests_limit}</p>
        <a href="/"><button>Вернуться на главную</button></a>
    </body>
    </html>
    """


@app.get("/payment/error", response_class=HTMLResponse)
async def payment_error():
    """Страница ошибки оплаты"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ошибка оплаты</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                text-align: center;
                padding: 20px;
            }
            .error {
                color: #f44336;
                font-size: 48px;
            }
            button {
                background: #2196F3;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="error">❌</div>
        <h1>Ошибка при обработке платежа</h1>
        <p>К сожалению, платеж не был завершен.</p>
        <p>Попробуйте еще раз или свяжитесь с поддержкой.</p>
        <a href="/"><button>Попробовать снова</button></a>
    </body>
    </html>
    """


@app.get("/payments")
async def get_payments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить историю платежей текущего пользователя

    Returns:
        JSON список платежей
    """
    payment_service = PaymentService(db)
    payments = await payment_service.get_user_payments(current_user.id, limit=10)

    return {
        "user_id": current_user.id,
        "subscription_tier": current_user.subscription_tier,
        "payments": [
            {
                "id": p.id,
                "invoice_id": p.invoice_id,
                "amount": p.amount,
                "currency": p.currency,
                "status": p.status,
                "subscription_tier": p.subscription_tier,
                "subscription_months": p.subscription_months,
                "created_at": p.created_at.isoformat(),
                "payment_method": p.payment_method
            }
            for p in payments
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CryptoCloud Payment Integration",
        "version": "1.0.0"
    }


# ============================================================================
# Запуск приложения
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("🚀 Starting CryptoCloud Payment Demo")
    print("=" * 60)
    print(f"📍 Local: http://localhost:8000")
    print(f"📖 Docs: http://localhost:8000/docs")
    print(f"💰 Home: http://localhost:8000/")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
