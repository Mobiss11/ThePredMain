"""
Примеры тестирования CryptoCloud интеграции

Этот файл содержит unit и integration тесты для модуля платежей.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient

# Импорты из вашего приложения
from app.services.payment_service import CryptoCloudService, PaymentService
from app.models.payment import Payment
from app.models.user import User


# ============================================================================
# Fixtures для тестов
# ============================================================================

@pytest.fixture
async def db_session():
    """Фикстура для создания тестовой сессии БД"""
    # Используем in-memory SQLite для тестов
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=True
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Фикстура для создания тестового пользователя"""
    user = User(
        email="test@example.com",
        subscription_tier="free",
        requests_limit=100,
        requests_used=0
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_payment(db_session: AsyncSession, test_user: User):
    """Фикстура для создания тестового платежа"""
    payment = Payment(
        user_id=test_user.id,
        invoice_id="TEST-INV-123",
        amount=129.0,
        currency="USD",
        payment_method="cryptocloud",
        status="pending",
        subscription_tier="starter",
        subscription_months=1,
        payment_url="https://cryptocloud.plus/pay/test"
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)
    return payment


# ============================================================================
# Unit тесты для CryptoCloudService
# ============================================================================

class TestCryptoCloudService:
    """Тесты для CryptoCloudService"""

    @patch('requests.post')
    def test_create_invoice_success(self, mock_post):
        """Тест успешного создания инвойса"""
        # Настраиваем mock ответ
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "success",
            "result": {
                "uuid": "test-uuid-123",
                "link": "https://cryptocloud.plus/pay/test"
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Создаем сервис
        service = CryptoCloudService()

        # Вызываем метод
        result = service.create_invoice(
            amount=129.0,
            user_id=1,
            subscription_tier="starter",
            subscription_months=1,
            email="test@example.com"
        )

        # Проверяем результат
        assert result["status"] == "success"
        assert result["result"]["uuid"] == "test-uuid-123"
        assert "cryptocloud.plus" in result["result"]["link"]

        # Проверяем что был вызван POST запрос
        mock_post.assert_called_once()

    @patch('requests.get')
    def test_check_invoice_status(self, mock_get):
        """Тест проверки статуса инвойса"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "success",
            "result": {
                "status": "paid",
                "amount": 129.0
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        service = CryptoCloudService()
        result = service.check_invoice_status("test-invoice-id")

        assert result["status"] == "success"
        assert result["result"]["status"] == "paid"


# ============================================================================
# Unit тесты для PaymentService
# ============================================================================

class TestPaymentService:
    """Тесты для PaymentService"""

    def test_get_price_for_tier(self):
        """Тест расчета цены для тарифа"""
        # Создаем mock сессии БД
        db_mock = AsyncMock()
        service = PaymentService(db_mock)

        # Тест обычной цены
        price_1_month = service.get_price_for_tier("starter", 1)
        assert price_1_month == 129.0

        # Тест цены с годовой скидкой (10%)
        price_12_months = service.get_price_for_tier("starter", 12)
        expected = 129.0 * 12 * 0.9  # 1396.8
        assert price_12_months == expected

        # Тест бесплатного тарифа
        price_free = service.get_price_for_tier("free", 1)
        assert price_free == 0

    def test_invalid_tier_raises_error(self):
        """Тест что невалидный тариф вызывает ошибку"""
        db_mock = AsyncMock()
        service = PaymentService(db_mock)

        with pytest.raises(ValueError, match="Invalid subscription tier"):
            service.get_price_for_tier("invalid_tier", 1)

    @pytest.mark.asyncio
    async def test_create_payment_success(self, db_session, test_user):
        """Тест успешного создания платежа"""
        service = PaymentService(db_session)

        # Мокаем CryptoCloud API
        with patch.object(CryptoCloudService, 'create_invoice') as mock_create:
            mock_create.return_value = {
                "status": "success",
                "result": {
                    "uuid": "test-uuid",
                    "link": "https://cryptocloud.plus/pay/test"
                }
            }

            payment = await service.create_payment(
                user_id=test_user.id,
                subscription_tier="starter",
                subscription_months=1
            )

            assert payment is not None
            assert payment.status == "pending"
            assert payment.amount == 129.0
            assert payment.payment_url is not None
            assert "cryptocloud.plus" in payment.payment_url

    @pytest.mark.asyncio
    async def test_create_free_payment_completes_immediately(
        self, db_session, test_user
    ):
        """Тест что бесплатный тариф завершается сразу"""
        service = PaymentService(db_session)

        payment = await service.create_payment(
            user_id=test_user.id,
            subscription_tier="free",
            subscription_months=1
        )

        # Проверяем что платеж сразу completed
        assert payment.status == "completed"
        assert payment.amount == 0

        # Проверяем что подписка пользователя обновилась
        await db_session.refresh(test_user)
        assert test_user.subscription_tier == "free"

    @pytest.mark.asyncio
    async def test_process_webhook_success(self, db_session, test_payment):
        """Тест успешной обработки webhook"""
        service = PaymentService(db_session)

        webhook_data = {
            "status": "success",
            "invoice_id": test_payment.invoice_id,
            "amount_crypto": 100,
            "currency": "USDT_TRC20"
        }

        success = await service.process_payment_webhook(webhook_data)

        assert success is True

        # Проверяем что статус обновился
        await db_session.refresh(test_payment)
        assert test_payment.status == "completed"

    @pytest.mark.asyncio
    async def test_process_webhook_duplicate_ignored(
        self, db_session, test_payment
    ):
        """Тест что повторный webhook игнорируется"""
        # Устанавливаем платеж как completed
        test_payment.status = "completed"
        await db_session.commit()

        service = PaymentService(db_session)

        webhook_data = {
            "status": "success",
            "invoice_id": test_payment.invoice_id,
            "amount_crypto": 100,
            "currency": "USDT_TRC20"
        }

        # Обрабатываем webhook второй раз
        success = await service.process_payment_webhook(webhook_data)

        # Должно вернуть True (уже обработан)
        assert success is True

    @pytest.mark.asyncio
    async def test_webhook_updates_user_subscription(
        self, db_session, test_payment, test_user
    ):
        """Тест что webhook обновляет подписку пользователя"""
        service = PaymentService(db_session)

        webhook_data = {
            "status": "success",
            "invoice_id": test_payment.invoice_id,
            "amount_crypto": 129,
            "currency": "USDT_TRC20"
        }

        await service.process_payment_webhook(webhook_data)

        # Проверяем что подписка обновилась
        await db_session.refresh(test_user)
        assert test_user.subscription_tier == "starter"
        assert test_user.requests_limit == 50000
        assert test_user.requests_used == 0
        assert test_user.subscription_expires is not None

    @pytest.mark.asyncio
    async def test_get_user_payments(self, db_session, test_user, test_payment):
        """Тест получения истории платежей пользователя"""
        service = PaymentService(db_session)

        payments = await service.get_user_payments(test_user.id)

        assert len(payments) == 1
        assert payments[0].id == test_payment.id


# ============================================================================
# Integration тесты для API endpoints
# ============================================================================

class TestPaymentEndpoints:
    """Integration тесты для API endpoints"""

    @pytest.mark.asyncio
    async def test_create_payment_endpoint(self, async_client: AsyncClient):
        """Тест endpoint создания платежа"""
        response = await async_client.post(
            "/dashboard/subscription/upgrade",
            data={
                "tier": "starter",
                "months": 1,
                "payment_method": "crypto"
            }
        )

        # Должен быть redirect
        assert response.status_code == 303
        assert "location" in response.headers

        # URL должен вести на CryptoCloud
        location = response.headers["location"]
        assert "cryptocloud.plus" in location or "payment" in location

    @pytest.mark.asyncio
    async def test_webhook_endpoint(
        self, async_client: AsyncClient, test_payment
    ):
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
        data = response.json()
        assert data["status"] in ["success", "processed"]

    @pytest.mark.asyncio
    async def test_payment_success_page(self, async_client: AsyncClient):
        """Тест страницы успешной оплаты"""
        response = await async_client.get("/dashboard/payment/success")

        assert response.status_code == 200
        assert "success" in response.text.lower() or "успешн" in response.text.lower()

    @pytest.mark.asyncio
    async def test_payment_error_page(self, async_client: AsyncClient):
        """Тест страницы ошибки оплаты"""
        response = await async_client.get("/dashboard/payment/error")

        assert response.status_code == 200
        assert "error" in response.text.lower() or "ошибк" in response.text.lower()


# ============================================================================
# Performance тесты
# ============================================================================

class TestPaymentPerformance:
    """Тесты производительности"""

    @pytest.mark.asyncio
    async def test_concurrent_payments(self, db_session):
        """Тест создания множественных платежей одновременно"""
        service = PaymentService(db_session)

        # Создаем 10 пользователей
        users = []
        for i in range(10):
            user = User(
                email=f"user{i}@example.com",
                subscription_tier="free",
                requests_limit=100,
                requests_used=0
            )
            db_session.add(user)
            users.append(user)
        await db_session.commit()

        # Мокаем API
        with patch.object(CryptoCloudService, 'create_invoice') as mock_create:
            mock_create.return_value = {
                "status": "success",
                "result": {
                    "uuid": "test-uuid",
                    "link": "https://cryptocloud.plus/pay/test"
                }
            }

            # Создаем платежи параллельно
            tasks = [
                service.create_payment(user.id, "starter", 1)
                for user in users
            ]

            payments = await asyncio.gather(*tasks)

            # Проверяем что все создались
            assert len(payments) == 10
            assert all(p.status == "pending" for p in payments)


# ============================================================================
# Edge cases тесты
# ============================================================================

class TestEdgeCases:
    """Тесты граничных случаев"""

    @pytest.mark.asyncio
    async def test_webhook_with_invalid_invoice_id(self, db_session):
        """Тест webhook с несуществующим invoice_id"""
        service = PaymentService(db_session)

        webhook_data = {
            "status": "success",
            "invoice_id": "non-existent-id",
            "amount_crypto": 100,
            "currency": "USDT_TRC20"
        }

        success = await service.process_payment_webhook(webhook_data)

        # Должно вернуть False
        assert success is False

    @pytest.mark.asyncio
    async def test_webhook_with_invalid_status(self, db_session, test_payment):
        """Тест webhook с невалидным статусом"""
        service = PaymentService(db_session)

        webhook_data = {
            "status": "failed",
            "invoice_id": test_payment.invoice_id,
        }

        # Не должно обрабатываться
        success = await service.process_payment_webhook(webhook_data)
        assert success is False

    @pytest.mark.asyncio
    async def test_create_payment_for_nonexistent_user(self, db_session):
        """Тест создания платежа для несуществующего пользователя"""
        service = PaymentService(db_session)

        with pytest.raises(ValueError, match="not found"):
            await service.create_payment(
                user_id=99999,  # Несуществующий ID
                subscription_tier="starter",
                subscription_months=1
            )


# ============================================================================
# Запуск тестов
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
