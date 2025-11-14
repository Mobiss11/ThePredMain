# 💰 CryptoCloud Payment Module

Готовый к использованию модуль для интеграции криптовалютных платежей через CryptoCloud API.

## 📚 Документация

### Основные документы:

1. **[INTEGRATION.md](./INTEGRATION.md)** - Полная документация по интеграции
   - Подробная архитектура
   - Пошаговая установка
   - API Reference
   - Webhook обработка
   - Тестирование
   - Production checklist

2. **[QUICKSTART.md](./QUICKSTART.md)** - Быстрый старт за 15 минут
   - Минимальный код
   - Быстрая настройка
   - Тестирование
   - Troubleshooting

## 🎯 Что умеет модуль?

✅ **Создание платежей** - Генерация инвойсов для криптовалютных платежей
✅ **Webhook обработка** - Автоматическая обработка уведомлений от CryptoCloud
✅ **Управление подписками** - Автоматическое обновление тарифов пользователей
✅ **История платежей** - Отслеживание всех транзакций
✅ **Защита от дублирования** - Идемпотентная обработка платежей
✅ **Гибкие тарифы** - Поддержка различных планов и скидок

## 🚀 Быстрый старт

### 1. Установка

```bash
pip install fastapi sqlalchemy asyncpg requests pydantic python-dotenv
```

### 2. Настройка

```bash
# .env файл
CRYPTOCLOUD_API_KEY=your_api_key
CRYPTOCLOUD_SHOP_ID=your_shop_id
BASE_URL=https://yourdomain.com
```

### 3. Копирование файлов

Скопируйте следующие файлы в ваш проект:

```
app/
├── models/payment.py           # Модель БД
├── services/payment_service.py # Бизнес-логика
└── routes/payment.py           # API endpoints
```

### 4. Запуск

```bash
# Создайте таблицы БД
alembic upgrade head

# Запустите приложение
uvicorn app.main:app --reload
```

## 📁 Структура модуля

```
cryptocloud/
├── README.md                    # Этот файл
├── INTEGRATION.md               # Полная документация
├── QUICKSTART.md                # Быстрый старт
├── examples/                    # Примеры использования
│   ├── basic_integration.py     # Базовая интеграция
│   ├── custom_pricing.py        # Кастомные тарифы
│   └── webhook_testing.py       # Тестирование webhook
└── sql/
    ├── create_tables.sql        # SQL для создания таблиц
    └── indexes.sql              # Индексы для производительности
```

## 🔧 Основные компоненты

### 1. CryptoCloudService
Взаимодействие с CryptoCloud API:
- `create_invoice()` - создание инвойса
- `check_invoice_status()` - проверка статуса
- `_make_request()` - HTTP клиент

### 2. PaymentService
Бизнес-логика платежей:
- `create_payment()` - создание платежа в БД
- `process_payment_webhook()` - обработка webhook
- `get_user_payments()` - история платежей
- `_update_user_subscription()` - обновление подписки

### 3. Payment Routes
API endpoints:
- `POST /dashboard/subscription/upgrade` - создать платеж
- `POST /api/webhook/payment` - webhook endpoint
- `GET /dashboard/payment/success` - страница успеха
- `GET /dashboard/payment/error` - страница ошибки

## 💡 Примеры использования

### Создание платежа

```python
from app.services.payment_service import PaymentService

async def upgrade_user_subscription(user_id: int, tier: str):
    payment_service = PaymentService(db)
    payment = await payment_service.create_payment(
        user_id=user_id,
        subscription_tier=tier,
        subscription_months=1
    )
    return payment.payment_url  # Redirect пользователя сюда
```

### Обработка webhook

```python
@router.post("/api/webhook/payment")
async def payment_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    payment_service = PaymentService(db)
    success = await payment_service.process_payment_webhook(data)
    return {"status": "success" if success else "error"}
```

### Получение истории платежей

```python
async def get_payment_history(user_id: int):
    payment_service = PaymentService(db)
    payments = await payment_service.get_user_payments(user_id, limit=10)
    return payments
```

## 🔄 Поток платежа

```
1. Пользователь → Выбирает тариф
2. Backend → Создает инвойс в CryptoCloud
3. Backend → Сохраняет Payment (status=pending)
4. Пользователь → Переходит на payment_url
5. Пользователь → Оплачивает криптовалютой
6. CryptoCloud → Отправляет webhook на /api/webhook/payment
7. Backend → Обрабатывает webhook
8. Backend → Обновляет Payment (status=completed)
9. Backend → Обновляет subscription_tier пользователя
10. Пользователь → Перенаправляется на success_url
```

## 🛡️ Безопасность

### Реализованные защиты:

✅ **Валидация webhook** - Проверка статуса и данных
✅ **Дедупликация** - Защита от повторной обработки
✅ **Идемпотентность** - Безопасные повторные запросы
✅ **SQL injection protection** - Использование SQLAlchemy ORM
✅ **Async безопасность** - Корректная работа с AsyncSession

### Рекомендации:

- Используйте HTTPS для всех endpoints
- Храните API ключи в переменных окружения
- Настройте rate limiting для webhook
- Логируйте все платежные операции
- Настройте мониторинг и алерты

## 📊 Метрики и мониторинг

### Ключевые метрики:

- **Успешные платежи**: `SELECT COUNT(*) FROM payments WHERE status='completed'`
- **Общая выручка**: `SELECT SUM(amount) FROM payments WHERE status='completed'`
- **Conversion rate**: completed / (completed + failed)
- **Среднее время обработки**: webhook receive → status update

### Рекомендуемые алерты:

- Failed payments > 5% за последний час
- Webhook processing time > 30 секунд
- CryptoCloud API недоступен
- Duplicate payment attempts

## 🧪 Тестирование

### Unit тесты

```bash
pytest tests/test_payment_service.py -v
```

### Integration тесты

```bash
pytest tests/test_payment_routes.py -v
```

### Локальное тестирование webhook

```bash
# Запустите ngrok
ngrok http 8000

# Используйте ngrok URL в CryptoCloud
# Например: https://abc123.ngrok.io/api/webhook/payment
```

## 🚨 Troubleshooting

### Частые проблемы:

| Проблема | Решение |
|----------|---------|
| Webhook не приходит | Проверьте Callback URL в CryptoCloud панели |
| Payment not found | Проверьте формат invoice_id (могут быть разные префиксы) |
| Subscription не обновляется | Проверьте логи webhook обработки |
| Duplicate payments | Убедитесь в проверке `status == "completed"` |

### Логирование для отладки:

```python
# Включите подробное логирование
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# В webhook handler
logger.debug(f"Received webhook: {data}")
logger.debug(f"Found payment: {payment.id if payment else None}")
```

## 📞 Поддержка

### CryptoCloud

- **Документация**: https://cryptocloud.plus/docs
- **API Docs**: https://cryptocloud.plus/api-docs
- **Email**: support@cryptocloud.plus
- **Telegram**: @cryptocloud_support

### Этот модуль

- **GitHub Issues**: [Создать issue](https://github.com/yourrepo/issues)
- **Email**: your-support@email.com
- **Документация**: См. INTEGRATION.md

## 📝 Changelog

### Version 1.0.0 (2025-01-14)
- ✨ Начальная версия модуля
- ✨ Создание инвойсов через CryptoCloud API
- ✨ Webhook обработка с защитой от дублирования
- ✨ Автоматическое обновление подписок
- ✨ История платежей
- ✨ Поддержка различных тарифных планов
- ✨ Полная async архитектура

## 🎓 Обучающие материалы

### Видео туториалы
- [Интеграция CryptoCloud за 15 минут](#) (coming soon)
- [Настройка webhook локально](#) (coming soon)
- [Production deployment](#) (coming soon)

### Статьи
- [Как работают крипто платежи](#)
- [Безопасная обработка webhook](#)
- [Оптимизация производительности](#)

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие модуля!

### Как помочь:

1. Fork репозитория
2. Создайте feature branch: `git checkout -b feature/amazing-feature`
3. Commit изменения: `git commit -m 'Add amazing feature'`
4. Push в branch: `git push origin feature/amazing-feature`
5. Создайте Pull Request

### Areas for contribution:

- 📝 Улучшение документации
- 🧪 Дополнительные тесты
- 🔧 Новые функции
- 🐛 Исправление багов
- 🌍 Переводы

## 📄 Лицензия

MIT License - свободно используйте в коммерческих и некоммерческих проектах.

```
Copyright (c) 2025 Your Company

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## 🌟 Благодарности

- **CryptoCloud** за отличный API
- **FastAPI** за современный фреймворк
- **SQLAlchemy** за мощный ORM
- Всем контрибьюторам проекта

---

**Создано с ❤️ командой Instagram API**

**Версия**: 1.0.0
**Последнее обновление**: Январь 2025

---

## 🔗 Быстрые ссылки

- 📖 [Полная документация](./INTEGRATION.md)
- 🚀 [Быстрый старт](./QUICKSTART.md)
- 💻 [Примеры кода](./examples/)
- 🗄️ [SQL скрипты](./sql/)
- 🐛 [Сообщить о проблеме](https://github.com/yourrepo/issues)
- 💬 [Обсуждения](https://github.com/yourrepo/discussions)

---

**Ready to accept crypto payments in 15 minutes! 🚀**
