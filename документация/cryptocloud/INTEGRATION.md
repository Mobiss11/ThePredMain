# 🔐 CryptoCloud Payment Integration Guide

Полная документация по интеграции модуля оплаты CryptoCloud в любой проект на FastAPI/Python.

## 📋 Содержание

1. [Обзор системы](#обзор-системы)
2. [Требования](#требования)
3. [Архитектура](#архитектура)
4. [Пошаговая интеграция](#пошаговая-интеграция)
5. [API Reference](#api-reference)
6. [Webhook обработка](#webhook-обработка)
7. [Тестирование](#тестирование)
8. [Troubleshooting](#troubleshooting)
9. [Production Checklist](#production-checklist)

---

## 🎯 Обзор системы

**CryptoCloud** - это платежный шлюз для приема криптовалютных платежей (USDT, BTC, ETH и др.). Данный модуль обеспечивает:

- ✅ Создание платежных инвойсов
- ✅ Обработку webhook уведомлений
- ✅ Автоматическое обновление подписок пользователей
- ✅ Отслеживание истории платежей
- ✅ Защиту от дублирования платежей
- ✅ Поддержку различных тарифных планов

### Ключевые особенности:

- **Асинхронная архитектура** - все операции БД через AsyncSession
- **Webhook безопасность** - валидация и дедупликация
- **Гибкие тарифы** - поддержка различных планов подписки
- **Автоматизация** - автоматическое продление/обновление подписок

---

## 📦 Требования

### Обязательные зависимости:

```python
# requirements.txt или pyproject.toml
fastapi>=0.115.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
requests>=2.31.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

### Минимальные требования к инфраструктуре:

- **Python**: 3.11+
- **База данных**: PostgreSQL 13+ (с поддержкой async)
- **CryptoCloud аккаунт**: API ключ и Shop ID

---

## 🏗️ Архитектура

### Компоненты системы:

```
┌─────────────────┐
│  FastAPI App    │
│  (Frontend)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│ Payment Routes  │─────▶│ Payment Service  │
│ (Endpoints)     │      │ (Business Logic) │
└────────┬────────┘      └─────────┬────────┘
         │                          │
         │                          ▼
         │                ┌──────────────────┐
         │                │ CryptoCloud API  │
         │                │ (External)       │
         │                └──────────────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│ Webhook Handler │─────▶│  PostgreSQL DB   │
│ (Callbacks)     │      │  (Persistence)   │
└─────────────────┘      └──────────────────┘
```

### Поток платежа:

```
1. Пользователь выбирает тариф → POST /dashboard/subscription/upgrade
2. Backend создает инвойс → CryptoCloudService.create_invoice()
3. Создается запись Payment (status=pending) в БД
4. Пользователь перенаправляется на payment_url CryptoCloud
5. Пользователь оплачивает криптовалютой
6. CryptoCloud отправляет webhook → POST /api/webhook/payment
7. Backend обрабатывает webhook → PaymentService.process_payment_webhook()
8. Payment обновляется (status=completed)
9. Подписка пользователя обновляется автоматически
10. Пользователь перенаправляется на success_url
```

---

## 🚀 Пошаговая интеграция

### Шаг 1: Настройка окружения

Создайте `.env` файл с необходимыми переменными:

```bash
# CryptoCloud API Credentials
CRYPTOCLOUD_API_KEY=your_api_key_here
CRYPTOCLOUD_SHOP_ID=your_shop_id_here

# Application URLs
BASE_URL=https://yourdomain.com
DOMAIN=https://yourdomain.com

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# Optional: Payment settings
DOWNLOAD_FILE_EXPIRY_HOURS=24
```

**Получение ключей CryptoCloud:**
1. Зарегистрируйтесь на https://cryptocloud.plus
2. Создайте магазин в панели управления
3. Получите API ключ и Shop ID в настройках

### Шаг 2: Создание моделей базы данных

#### 2.1 Модель Payment

Создайте файл `app/models/payment.py`:

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class Payment(Base):
    """
    Модель для хранения платежных транзакций

    Attributes:
        id: Уникальный ID платежа
        user_id: ID пользователя (FK)
        invoice_id: Уникальный ID инвойса от CryptoCloud
        amount: Сумма платежа
        currency: Валюта (USD, EUR, etc.)
        payment_method: Способ оплаты (cryptocloud, stripe, etc.)
        status: pending, completed, failed, refunded
        subscription_tier: Тариф подписки (starter, pro, etc.)
        subscription_months: Количество месяцев подписки
        payment_url: URL для оплаты
        payment_data: JSON данные от провайдера
        created_at: Время создания
        updated_at: Время последнего обновления
    """
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invoice_id = Column(String(255), unique=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    payment_method = Column(String(50))
    status = Column(String(20), default="pending")
    subscription_tier = Column(String(20), nullable=False)
    subscription_months = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    payment_url = Column(String(1000))
    payment_data = Column(Text)

    # Relationships
    user = relationship("User", back_populates="payments")

    def __repr__(self):
        return f"<Payment {self.id}: {self.status} - {self.amount} {self.currency}>"
```

#### 2.2 Обновление модели User

Добавьте в модель `User` поля для подписки:

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)

    # Subscription fields
    subscription_tier = Column(String(20), default="free")
    subscription_expires = Column(DateTime, nullable=True)
    requests_limit = Column(Integer, default=100)
    requests_used = Column(Integer, default=0)

    # Relationships
    payments = relationship("Payment", back_populates="user")
```

#### 2.3 Создание миграции

Если используете Alembic:

```bash
# Создать миграцию
alembic revision --autogenerate -m "add_payment_tables"

# Применить миграцию
alembic upgrade head
```

Или вручную создайте таблицы:

```python
from app.database import engine
from app.models.base import Base

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

### Шаг 3: Настройка конфигурации

Создайте `app/config.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# CryptoCloud settings
CRYPTOCLOUD_API_KEY = os.getenv("CRYPTOCLOUD_API_KEY", "")
CRYPTOCLOUD_SHOP_ID = os.getenv("CRYPTOCLOUD_SHOP_ID", "")

# Application settings
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
DOMAIN = os.getenv("DOMAIN", "http://localhost:8000")

# Pricing tiers - настройте под свои нужды
PRICING_TIERS = {
    "free": {"name": "Free", "requests": 100, "price": 0},
    "starter": {"name": "Starter", "requests": 50000, "price": 129},
    "basic": {"name": "Basic", "requests": 100000, "price": 199},
    "pro": {"name": "Pro", "requests": 300000, "price": 299},
    "business": {"name": "Business", "requests": 500000, "price": 399},
    "enterprise": {"name": "Enterprise", "requests": 1000000, "price": 599}
}

class Settings:
    CRYPTOCLOUD_API_KEY = CRYPTOCLOUD_API_KEY
    CRYPTOCLOUD_SHOP_ID = CRYPTOCLOUD_SHOP_ID
    BASE_URL = BASE_URL
    DOMAIN = DOMAIN
    PRICING_TIERS = PRICING_TIERS

settings = Settings()
```

### Шаг 4: Создание сервиса CryptoCloud

Создайте `app/services/payment_service.py`:

```python
import json
import uuid
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.payment import Payment
from app.models.user import User
from app.config import settings


class CryptoCloudService:
    """Сервис для работы с CryptoCloud API"""

    BASE_URL = "https://api.cryptocloud.plus/v2"

    def __init__(self):
        self.api_key = settings.CRYPTOCLOUD_API_KEY
        self.shop_id = settings.CRYPTOCLOUD_SHOP_ID

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Выполнить HTTP запрос к CryptoCloud API

        Args:
            method: HTTP метод (get/post)
            endpoint: API endpoint (например, /invoice/create)
            data: Данные для отправки

        Returns:
            Dict с ответом от API

        Raises:
            requests.HTTPError: При ошибке HTTP запроса
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }

        if method.lower() == "get":
            response = requests.get(url, headers=headers, params=data)
        elif method.lower() == "post":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()

    def create_invoice(self,
                      amount: float,
                      user_id: int,
                      subscription_tier: str,
                      subscription_months: int = 1,
                      email: str = "",
                      currency: str = "USD") -> Dict[str, Any]:
        """
        Создать платежный инвойс в CryptoCloud

        Args:
            amount: Сумма платежа
            user_id: ID пользователя
            subscription_tier: Тариф подписки
            subscription_months: Количество месяцев
            email: Email пользователя
            currency: Валюта платежа

        Returns:
            Dict с данными инвойса:
            {
                "status": "success",
                "result": {
                    "uuid": "xxx-xxx-xxx",
                    "link": "https://cryptocloud.plus/pay/xxx"
                }
            }
        """
        order_id = str(uuid.uuid4())
        data = {
            "shop_id": self.shop_id,
            "amount": amount,
            "order_id": order_id,
            "currency": currency,
            "email": email,
            "description": f"Subscription to {subscription_tier.capitalize()} plan for {subscription_months} month(s)",
            "success_url": f"{settings.BASE_URL}/dashboard/payment/success?order_id={order_id}",
            "fail_url": f"{settings.BASE_URL}/dashboard/payment/error?order_id={order_id}",
            "callback_url": f"{settings.BASE_URL}/api/webhook/payment",
            "metadata": {
                "user_id": user_id,
                "subscription_tier": subscription_tier,
                "subscription_months": subscription_months
            }
        }

        response = self._make_request("post", "/invoice/create", data)
        return response

    def check_invoice_status(self, invoice_id: str) -> Dict[str, Any]:
        """
        Проверить статус инвойса

        Args:
            invoice_id: UUID инвойса

        Returns:
            Dict со статусом инвойса
        """
        data = {
            "shop_id": self.shop_id,
            "uuid": invoice_id
        }

        response = self._make_request("get", "/invoice/info", data)
        return response


class PaymentService:
    """Сервис для управления платежами и подписками"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.crypto_cloud = CryptoCloudService()

        # Импортируем тарифы из config
        from app.config import PRICING_TIERS
        self.pricing = {tier: data["price"] for tier, data in PRICING_TIERS.items()}

    def get_price_for_tier(self, tier: str, months: int = 1) -> float:
        """
        Получить цену для тарифного плана

        Args:
            tier: Название тарифа
            months: Количество месяцев

        Returns:
            Итоговая цена с учетом скидок
        """
        if tier not in self.pricing:
            raise ValueError(f"Invalid subscription tier: {tier}")

        # Free tier всегда бесплатный
        if tier == "free":
            return 0

        # Применяем скидки для длительных подписок
        price = self.pricing[tier]
        if months == 12:
            # 10% скидка за 12 месяцев
            price = price * 12 * 0.9
        else:
            # Обычная цена за N месяцев
            price = price * months

        return price

    async def create_payment(self, user_id: int, subscription_tier: str, subscription_months: int = 1) -> Payment:
        """
        Создать платеж для подписки

        Args:
            user_id: ID пользователя
            subscription_tier: Тариф подписки
            subscription_months: Количество месяцев

        Returns:
            Payment объект с payment_url для оплаты

        Raises:
            ValueError: Если пользователь не найден или невалидный тариф
        """
        # Получаем пользователя
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalars().first()

        if not user:
            raise ValueError(f"User with id {user_id} not found")

        # Рассчитываем сумму
        amount = self.get_price_for_tier(subscription_tier, subscription_months)

        # Для бесплатного тарифа пропускаем процесс оплаты
        if subscription_tier == "free":
            payment = Payment(
                user_id=user_id,
                invoice_id=str(uuid.uuid4()),
                amount=0,
                currency="USD",
                payment_method="system",
                status="completed",
                subscription_tier=subscription_tier,
                subscription_months=subscription_months
            )

            self.db.add(payment)
            await self.db.commit()
            await self.db.refresh(payment)

            # Обновляем подписку пользователя
            await self._update_user_subscription(user, subscription_tier, subscription_months)

            return payment

        # Создаем инвойс в CryptoCloud
        response = self.crypto_cloud.create_invoice(
            amount=amount,
            user_id=user_id,
            subscription_tier=subscription_tier,
            subscription_months=subscription_months,
            email=user.email
        )

        # Извлекаем данные из ответа
        if response.get("status") != "success" or "result" not in response:
            raise ValueError("Failed to create payment invoice")

        invoice_data = response["result"]

        # Создаем запись о платеже
        payment = Payment(
            user_id=user_id,
            invoice_id=invoice_data["uuid"],
            amount=amount,
            currency="USD",
            payment_method="cryptocloud",
            status="pending",
            subscription_tier=subscription_tier,
            subscription_months=subscription_months,
            payment_url=invoice_data["link"],
            payment_data=json.dumps(response)
        )

        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)

        return payment

    async def process_payment_webhook(self, data: Dict[str, Any]) -> bool:
        """
        Обработать webhook уведомление от CryptoCloud

        Webhook data format:
        {
            "status": "success",
            "invoice_id": "XXXXXXXX",
            "amount_crypto": 100,
            "currency": "USDT_TRC20",
            "order_id": "order_id",
            "token": "token",
            "invoice_info": { ... }
        }

        Args:
            data: Данные webhook от CryptoCloud

        Returns:
            True если платеж успешно обработан, False иначе
        """
        print(f"Processing webhook data: {data}")

        # Получаем invoice ID из webhook
        webhook_invoice_id = data.get("invoice_id")

        if not webhook_invoice_id:
            print("No invoice_id found in webhook data")
            return False

        # CryptoCloud может отправлять invoice_id без префикса "INV-"
        # Пробуем найти платеж в обоих форматах
        full_invoice_id = f"INV-{webhook_invoice_id}"

        print(f"Looking for payment with invoice_id: {webhook_invoice_id} or {full_invoice_id}")

        # Ищем платеж по полному invoice_id (с префиксом)
        query = select(Payment).where(Payment.invoice_id == full_invoice_id)
        result = await self.db.execute(query)
        payment = result.scalars().first()

        # Если не найден, пробуем без префикса
        if not payment:
            query = select(Payment).where(Payment.invoice_id == webhook_invoice_id)
            result = await self.db.execute(query)
            payment = result.scalars().first()

        # Пробуем извлечь UUID из invoice_info
        if not payment:
            invoice_info = data.get("invoice_info")
            if invoice_info and isinstance(invoice_info, dict):
                uuid_from_info = invoice_info.get("uuid")
                if uuid_from_info:
                    print(f"Trying UUID from invoice_info: {uuid_from_info}")
                    query = select(Payment).where(Payment.invoice_id == uuid_from_info)
                    result = await self.db.execute(query)
                    payment = result.scalars().first()

        if not payment:
            print(f"No payment found with invoice_id: {webhook_invoice_id}")
            return False

        # Защита от дублирования - если платеж уже completed
        if payment.status == "completed":
            print(f"Payment {payment.invoice_id} already completed, skipping")
            return True

        # Обновляем статус платежа на completed
        payment.status = "completed"
        payment.payment_data = json.dumps(data)
        payment.updated_at = datetime.utcnow()

        await self.db.commit()
        print(f"Payment {payment.invoice_id} updated to completed")

        # Обновляем подписку пользователя
        query = select(User).where(User.id == payment.user_id)
        result = await self.db.execute(query)
        user = result.scalars().first()

        if user:
            await self._update_user_subscription(
                user,
                payment.subscription_tier,
                payment.subscription_months
            )
            print(f"User {user.id} subscription updated to {payment.subscription_tier}")

        return True

    async def _update_user_subscription(self, user: User, tier: str, months: int) -> None:
        """
        Обновить подписку пользователя

        Args:
            user: Объект пользователя
            tier: Новый тариф
            months: Количество месяцев
        """
        from app.config import PRICING_TIERS

        user.subscription_tier = tier

        # Обновляем лимиты на основе тарифа
        tier_data = PRICING_TIERS.get(tier, PRICING_TIERS["free"])
        user.requests_limit = tier_data["requests"]

        # Сбрасываем использованные запросы при апгрейде
        user.requests_used = 0

        # Рассчитываем новую дату окончания подписки
        if user.subscription_expires and user.subscription_expires > datetime.utcnow():
            # Продлеваем текущую подписку
            user.subscription_expires = user.subscription_expires + timedelta(days=30 * months)
        else:
            # Новая подписка
            user.subscription_expires = datetime.utcnow() + timedelta(days=30 * months)

        await self.db.commit()

    async def get_user_payments(self, user_id: int, limit: int = 10) -> List[Payment]:
        """
        Получить историю платежей пользователя

        Args:
            user_id: ID пользователя
            limit: Максимальное количество записей

        Returns:
            Список объектов Payment
        """
        query = select(Payment).where(
            Payment.user_id == user_id
        ).order_by(Payment.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_all_payments(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """
        Получить все платежи (для админ панели)

        Args:
            page: Номер страницы
            limit: Количество записей на странице

        Returns:
            Dict с платежами и пагинацией
        """
        from sqlalchemy import func

        offset = (page - 1) * limit

        # Получаем общее количество
        count_query = select(func.count(Payment.id))
        count_result = await self.db.execute(count_query)
        total_payments = count_result.scalar()

        # Получаем платежи с данными пользователя
        query = select(Payment).options(
            selectinload(Payment.user)
        ).order_by(Payment.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        payments = result.scalars().all()

        return {
            "payments": payments,
            "total": total_payments,
            "total_pages": (total_payments + limit - 1) // limit,
            "current_page": page
        }
```

### Шаг 5: Создание API эндпоинтов

Создайте `app/routes/payment.py`:

```python
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Form, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.services.payment_service import PaymentService
from app.api.auth import get_current_user  # Ваша функция аутентификации
from app.models.user import User
from app.models.payment import Payment
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard/payments")
async def payments_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Страница истории платежей пользователя"""
    payment_service = PaymentService(db)
    payments = await payment_service.get_user_payments(current_user.id)

    return templates.TemplateResponse(
        "dashboard/payments.html",
        {
            "request": request,
            "user": current_user,
            "payments": payments,
        }
    )


@router.post("/dashboard/subscription/upgrade")
async def upgrade_subscription(
    request: Request,
    tier: str = Form(...),
    months: int = Form(1),
    payment_method: str = Form("crypto"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создание платежа для апгрейда подписки

    Args:
        tier: Тариф (free, starter, pro, etc.)
        months: Количество месяцев (1 или 12)
        payment_method: Метод оплаты (crypto или card)
    """
    # Валидация тарифа
    if tier not in settings.PRICING_TIERS:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")

    # Валидация длительности
    if months not in [1, 12]:
        raise HTTPException(status_code=400, detail="Invalid subscription duration")

    # Если уже на этом тарифе
    if tier == current_user.subscription_tier:
        return RedirectResponse(url="/dashboard/subscription", status_code=303)

    # Создаем платеж
    payment_service = PaymentService(db)
    payment = await payment_service.create_payment(
        user_id=current_user.id,
        subscription_tier=tier,
        subscription_months=months
    )

    # Для free тарифа сразу redirect на success
    if tier == "free":
        return RedirectResponse(url="/dashboard/payment/success", status_code=303)

    # Для платных тарифов - redirect на страницу оплаты
    payment_url = f'{payment.payment_url}?lang=en'
    return RedirectResponse(url=payment_url, status_code=303)


@router.get("/dashboard/payment/success")
async def payment_success(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Страница успешной оплаты"""
    return templates.TemplateResponse(
        "dashboard/payment_success.html",
        {
            "request": request,
            "user": current_user,
        }
    )


@router.get("/dashboard/payment/error")
async def payment_error(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Страница ошибки оплаты"""
    return templates.TemplateResponse(
        "dashboard/payment_error.html",
        {
            "request": request,
            "user": current_user,
        }
    )


@router.post("/api/webhook/payment")
async def payment_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook endpoint для обработки уведомлений от CryptoCloud

    CryptoCloud отправляет POST запрос с данными:
    {
        "status": "success",
        "invoice_id": "XXXXXXXX",
        "amount_crypto": 100,
        "currency": "USDT_TRC20",
        "order_id": "order_id",
        "token": "token",
        "invoice_info": { ... }
    }
    """
    try:
        print("Received payment webhook")

        # Пробуем получить данные как form
        try:
            form_data = await request.form()
            data = {key: form_data.get(key) for key in form_data}
            print(f"Received form data: {data}")
        except Exception as form_error:
            print(f"Failed to parse form data: {str(form_error)}")

            # Если form не работает, пробуем JSON
            try:
                data = await request.json()
                print(f"Received JSON data: {data}")
            except Exception as json_error:
                print(f"Failed to parse JSON data: {str(json_error)}")
                body = await request.body()
                print(f"Raw request body: {body}")
                return Response(
                    status_code=400,
                    content=f"Could not parse request data"
                )

        # Проверяем статус
        if data.get("status") != "success":
            print(f"Invalid status: {data.get('status')}")
            return {"status": "processed", "message": "Invalid status but acknowledged"}

        # Проверяем наличие invoice_id
        invoice_id = data.get("invoice_id")
        if not invoice_id:
            print("Missing invoice_id in webhook data")
            return {"status": "processed", "message": "Missing invoice_id"}

        # Обрабатываем webhook
        payment_service = PaymentService(db)
        success = await payment_service.process_payment_webhook(data)

        if success:
            return {"status": "success", "message": "Payment processed successfully"}
        else:
            # Возвращаем 200 даже при ошибке, чтобы избежать повторных попыток
            return {"status": "processed", "message": "Payment processing failed"}

    except Exception as e:
        print(f"Webhook processing error: {str(e)}")
        # Возвращаем 200 даже при ошибке
        return {"status": "error", "message": f"Error: {str(e)}"}
```

### Шаг 6: Регистрация роутов

В главном файле приложения `app/main.py`:

```python
from fastapi import FastAPI
from app.routes import payment

app = FastAPI()

# Регистрируем роуты
app.include_router(payment.router)
```

### Шаг 7: Создание HTML шаблонов (опционально)

#### Страница подписки

`app/templates/dashboard/subscription.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Управление подпиской</title>
</head>
<body>
    <h1>Выберите тариф</h1>

    <form method="post" action="/dashboard/subscription/upgrade">
        <select name="tier" required>
            <option value="free">Free - $0/месяц</option>
            <option value="starter">Starter - $129/месяц</option>
            <option value="basic">Basic - $199/месяц</option>
            <option value="pro">Pro - $299/месяц</option>
        </select>

        <select name="months" required>
            <option value="1">1 месяц</option>
            <option value="12">12 месяцев (-10%)</option>
        </select>

        <select name="payment_method" required>
            <option value="crypto">Криптовалюта</option>
            <option value="card">Банковская карта</option>
        </select>

        <button type="submit">Оплатить</button>
    </form>
</body>
</html>
```

#### Страница успеха

`app/templates/dashboard/payment_success.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Оплата успешна</title>
</head>
<body>
    <h1>✅ Платеж успешно обработан!</h1>
    <p>Ваша подписка активирована.</p>
    <a href="/dashboard">Вернуться в панель управления</a>
</body>
</html>
```

### Шаг 8: Тестирование

#### 8.1 Тестовый платеж

```python
# test_payment.py
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.payment_service import PaymentService

async def test_create_payment():
    async for db in get_db():
        payment_service = PaymentService(db)

        # Создаем тестовый платеж
        payment = await payment_service.create_payment(
            user_id=1,  # Замените на реальный ID
            subscription_tier="starter",
            subscription_months=1
        )

        print(f"Payment created:")
        print(f"ID: {payment.id}")
        print(f"Invoice ID: {payment.invoice_id}")
        print(f"Amount: ${payment.amount}")
        print(f"Payment URL: {payment.payment_url}")

        break

asyncio.run(test_create_payment())
```

#### 8.2 Тестирование webhook локально

Используйте ngrok для тестирования webhook:

```bash
# Установите ngrok
brew install ngrok  # Mac
# или скачайте с https://ngrok.com/download

# Запустите приложение
uvicorn app.main:app --reload --port 8000

# В другом терминале запустите ngrok
ngrok http 8000

# Используйте ngrok URL в настройках CryptoCloud
# Например: https://abc123.ngrok.io/api/webhook/payment
```

---

## 📚 API Reference

### CryptoCloudService

#### `__init__()`
Инициализирует сервис с API ключами из settings.

#### `create_invoice(amount, user_id, subscription_tier, subscription_months, email, currency)`
Создает платежный инвойс в CryptoCloud.

**Параметры:**
- `amount` (float): Сумма платежа
- `user_id` (int): ID пользователя
- `subscription_tier` (str): Тариф подписки
- `subscription_months` (int): Количество месяцев (по умолчанию 1)
- `email` (str): Email пользователя
- `currency` (str): Валюта (по умолчанию "USD")

**Возвращает:**
```python
{
    "status": "success",
    "result": {
        "uuid": "xxx-xxx-xxx-xxx",
        "link": "https://cryptocloud.plus/pay/xxx"
    }
}
```

#### `check_invoice_status(invoice_id)`
Проверяет статус инвойса.

**Параметры:**
- `invoice_id` (str): UUID инвойса

**Возвращает:**
```python
{
    "status": "success",
    "result": {
        "status": "paid",  # или "pending", "expired", "canceled"
        "amount": 129.0,
        "currency": "USD"
    }
}
```

### PaymentService

#### `__init__(db: AsyncSession)`
Инициализирует сервис с сессией БД.

#### `get_price_for_tier(tier, months)`
Рассчитывает цену с учетом скидок.

**Параметры:**
- `tier` (str): Название тарифа
- `months` (int): Количество месяцев

**Возвращает:** `float` - итоговая цена

#### `create_payment(user_id, subscription_tier, subscription_months)`
Создает платеж и запись в БД.

**Параметры:**
- `user_id` (int): ID пользователя
- `subscription_tier` (str): Тариф
- `subscription_months` (int): Количество месяцев

**Возвращает:** `Payment` объект

#### `process_payment_webhook(data)`
Обрабатывает webhook от CryptoCloud.

**Параметры:**
- `data` (Dict): Данные webhook

**Возвращает:** `bool` - успешность обработки

#### `get_user_payments(user_id, limit)`
Получает историю платежей пользователя.

**Параметры:**
- `user_id` (int): ID пользователя
- `limit` (int): Максимум записей (по умолчанию 10)

**Возвращает:** `List[Payment]`

---

## 🔔 Webhook обработка

### Формат webhook от CryptoCloud

CryptoCloud отправляет POST запрос на `callback_url` при успешной оплате:

```json
{
    "status": "success",
    "invoice_id": "12345678",
    "amount_crypto": 100.5,
    "currency": "USDT_TRC20",
    "order_id": "xxx-xxx-xxx-xxx",
    "token": "verification_token",
    "invoice_info": {
        "uuid": "xxx-xxx-xxx-xxx",
        "status": "paid",
        "amount": 129.0
    }
}
```

### Безопасность webhook

**Рекомендации:**

1. **Проверка статуса**: Обрабатывайте только `status: "success"`
2. **Дедупликация**: Проверяйте, не обработан ли платеж (`status == "completed"`)
3. **Идемпотентность**: Возвращайте 200 даже при повторных запросах
4. **Логирование**: Логируйте все входящие webhook для отладки
5. **Timeout**: Обрабатывайте webhook быстро (<30 сек)

### Настройка в CryptoCloud

1. Войдите в панель управления CryptoCloud
2. Перейдите в настройки магазина
3. Укажите Callback URL: `https://yourdomain.com/api/webhook/payment`
4. Сохраните изменения

---

## 🧪 Тестирование

### Unit тесты

Создайте `tests/test_payment_service.py`:

```python
import pytest
from unittest.mock import Mock, patch
from app.services.payment_service import CryptoCloudService, PaymentService

@pytest.mark.asyncio
async def test_create_payment(db_session, test_user):
    """Тест создания платежа"""
    payment_service = PaymentService(db_session)

    with patch.object(CryptoCloudService, 'create_invoice') as mock_create:
        mock_create.return_value = {
            "status": "success",
            "result": {
                "uuid": "test-uuid",
                "link": "https://cryptocloud.plus/pay/test"
            }
        }

        payment = await payment_service.create_payment(
            user_id=test_user.id,
            subscription_tier="starter",
            subscription_months=1
        )

        assert payment.status == "pending"
        assert payment.amount == 129.0
        assert payment.payment_url is not None

@pytest.mark.asyncio
async def test_process_webhook(db_session, test_payment):
    """Тест обработки webhook"""
    payment_service = PaymentService(db_session)

    webhook_data = {
        "status": "success",
        "invoice_id": test_payment.invoice_id,
        "amount_crypto": 100,
        "currency": "USDT_TRC20"
    }

    success = await payment_service.process_payment_webhook(webhook_data)

    assert success is True
    assert test_payment.status == "completed"
```

### Integration тесты

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_upgrade_subscription_flow(async_client: AsyncClient, authenticated_user):
    """Тест полного потока апгрейда подписки"""

    # Создаем платеж
    response = await async_client.post(
        "/dashboard/subscription/upgrade",
        data={
            "tier": "starter",
            "months": 1,
            "payment_method": "crypto"
        }
    )

    assert response.status_code == 303  # Redirect
    assert "cryptocloud.plus" in response.headers["location"]

@pytest.mark.asyncio
async def test_webhook_endpoint(async_client: AsyncClient, test_payment):
    """Тест webhook endpoint"""

    webhook_data = {
        "status": "success",
        "invoice_id": test_payment.invoice_id,
        "amount_crypto": 129,
        "currency": "USDT_TRC20"
    }

    response = await async_client.post(
        "/api/webhook/payment",
        json=webhook_data
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

---

## 🐛 Troubleshooting

### Проблема: Webhook не приходит

**Решение:**
1. Проверьте настройки Callback URL в CryptoCloud
2. Убедитесь что URL доступен публично (используйте ngrok для локальной разработки)
3. Проверьте логи сервера на наличие ошибок
4. Проверьте firewall настройки

### Проблема: Платеж не находится в БД

**Решение:**
1. Проверьте логи: `print(f"Looking for payment with invoice_id: {invoice_id}")`
2. Проверьте формат invoice_id (с/без префикса "INV-")
3. Убедитесь что создание платежа прошло успешно
4. Проверьте транзакции БД (commit был вызван?)

### Проблема: Подписка не обновляется

**Решение:**
1. Проверьте что webhook обработался успешно
2. Проверьте логи обновления подписки
3. Убедитесь что `_update_user_subscription` вызывается
4. Проверьте права доступа к таблице users

### Проблема: Duplicate payments

**Решение:**
1. Убедитесь что проверка `if payment.status == "completed"` работает
2. Добавьте уникальный индекс на `invoice_id` в БД
3. Используйте transaction isolation level для критичных операций

---

## ✅ Production Checklist

Перед запуском в production:

### Безопасность
- [ ] HTTPS настроен на всех endpoints
- [ ] Webhook URL защищен от DDoS
- [ ] API ключи хранятся в переменных окружения (не в коде!)
- [ ] Webhook signature verification реализована
- [ ] Rate limiting настроен для webhook endpoint
- [ ] SQL injection protection (используйте ORM)

### Мониторинг
- [ ] Логирование всех платежей и webhook
- [ ] Алерты на failed платежи
- [ ] Метрики: количество успешных/failed платежей
- [ ] Мониторинг доступности CryptoCloud API
- [ ] Backup базы данных настроен

### Тестирование
- [ ] Unit тесты покрывают основную логику
- [ ] Integration тесты для webhook
- [ ] Тестовые платежи на staging среде
- [ ] Load testing для высокой нагрузки

### Документация
- [ ] API документация обновлена
- [ ] Runbook для операционной команды
- [ ] Контакты поддержки CryptoCloud
- [ ] Процедуры для рефандов

### Конфигурация
- [ ] Все переменные окружения документированы
- [ ] Production и staging конфиги разделены
- [ ] Database indexes оптимизированы
- [ ] Connection pooling настроен

---

## 📞 Поддержка

### CryptoCloud Support
- **Документация**: https://cryptocloud.plus/docs
- **Email**: support@cryptocloud.plus
- **Telegram**: @cryptocloud_support

### Полезные ссылки
- CryptoCloud API Docs: https://cryptocloud.plus/api-docs
- Status Page: https://status.cryptocloud.plus
- Supported Currencies: https://cryptocloud.plus/currencies

---

## 📝 Changelog

### Version 1.0.0 (2025-01-XX)
- Начальная версия модуля
- Поддержка создания инвойсов
- Webhook обработка
- Автоматическое обновление подписок
- История платежей
- Защита от дублирования

---

## 📄 License

MIT License - свободно используйте в своих проектах.

---

**Автор**: Instagram API Team
**Последнее обновление**: Январь 2025
