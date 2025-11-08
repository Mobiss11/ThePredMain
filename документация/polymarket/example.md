# 📚 Polymarket API Integration - Полная техническая документация

## 🔧 Установка и настройка

```bash
pip install py-clob-client httpx websockets pandas asyncio
```

## ⚙️ Конфигурация

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# ВАЖНО: Никогда не храни ключи в коде!
POLYMARKET_CONFIG = {
    "api_key": os.getenv("POLYMARKET_API_KEY"),  # Твой API key
    "secret": os.getenv("POLYMARKET_SECRET"),     # Твой secret
    "passphrase": os.getenv("POLYMARKET_PASS"),   # Твой passphrase
    "private_key": os.getenv("WALLET_PRIVATE_KEY"),  # Приватный ключ кошелька (если нужен трейдинг)
}

# API Endpoints
ENDPOINTS = {
    "clob": "https://clob.polymarket.com",
    "gamma": "https://gamma-api.polymarket.com", 
    "data": "https://data-api.polymarket.com",
    "ws": "wss://ws-subscriptions-clob.polymarket.com/ws"
}

# Polygon Network
CHAIN_ID = 137
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # USDC on Polygon
```

## 1️⃣ Базовый клиент

```python
# polymarket_client.py
import hmac
import hashlib
import base64
import time
import json
from typing import Dict, List, Optional, Tuple
import httpx
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds

class PolymarketClient:
    def __init__(self, api_key: str, secret: str, passphrase: str):
        self.api_key = api_key
        self.secret = secret
        self.passphrase = passphrase
        
        # Инициализация клиентов
        self.clob_client = ClobClient(ENDPOINTS["clob"])
        self.http_client = httpx.AsyncClient()
        
        # Установка API credentials
        self.api_creds = ApiCreds(
            api_key=api_key,
            api_secret=secret,
            api_passphrase=passphrase
        )
        self.clob_client.set_api_creds(self.api_creds)
        
    def _generate_signature(self, timestamp: str, method: str, 
                           request_path: str, body: str = "") -> str:
        """Генерация подписи для запросов"""
        message = timestamp + method + request_path + body
        hmac_key = base64.b64decode(self.secret)
        signature = hmac.new(hmac_key, message.encode(), hashlib.sha256)
        return base64.b64encode(signature.digest()).decode()
    
    def _get_auth_headers(self, method: str, path: str, body: str = "") -> Dict:
        """Получение заголовков авторизации"""
        timestamp = str(time.time())
        signature = self._generate_signature(timestamp, method, path, body)
        
        return {
            "POLY_API_KEY": self.api_key,
            "POLY_SIGNATURE": signature,
            "POLY_TIMESTAMP": timestamp,
            "POLY_PASSPHRASE": self.passphrase,
            "Content-Type": "application/json"
        }
```

## 2️⃣ Получение данных о рынках

```python
# markets.py
class MarketsAPI:
    def __init__(self, client: PolymarketClient):
        self.client = client
        
    async def get_all_markets(self, active_only: bool = True) -> List[Dict]:
        """Получить все рынки"""
        url = f"{ENDPOINTS['gamma']}/markets"
        params = {"active": active_only, "closed": not active_only}
        
        response = await self.client.http_client.get(url, params=params)
        markets = response.json()
        
        # Фильтрация и обогащение данных
        enriched_markets = []
        for market in markets:
            if market.get('enable_order_book', True):
                market_data = await self.get_market_details(market['condition_id'])
                enriched_markets.append(market_data)
        
        return enriched_markets
    
    async def get_market_details(self, condition_id: str) -> Dict:
        """Детальная информация о рынке"""
        # Получаем базовую информацию
        market_url = f"{ENDPOINTS['gamma']}/markets/{condition_id}"
        market_response = await self.client.http_client.get(market_url)
        market = market_response.json()
        
        # Получаем токены рынка
        tokens = market.get('tokens', [])
        
        # Для каждого токена получаем данные
        for token in tokens:
            token_id = token['token_id']
            
            # Получаем orderbook
            orderbook = await self.get_orderbook(token_id)
            token['orderbook'] = orderbook
            
            # Получаем последнюю цену
            midpoint = await self.get_midpoint(token_id)
            token['midpoint'] = midpoint
            
            # Получаем спред
            spread = await self.get_spread(token_id)
            token['spread'] = spread
        
        return market
    
    async def get_orderbook(self, token_id: str) -> Dict:
        """Получить стакан ордеров"""
        return self.client.clob_client.get_order_book(token_id)
    
    async def get_midpoint(self, token_id: str) -> float:
        """Получить среднюю цену"""
        return self.client.clob_client.get_midpoint(token_id)
    
    async def get_spread(self, token_id: str) -> Dict:
        """Получить спред"""
        return self.client.clob_client.get_spread(token_id)
    
    async def get_markets_by_category(self, category: str) -> List[Dict]:
        """Получить рынки по категории"""
        all_markets = await self.get_all_markets()
        
        category_filter = {
            "crypto": ["Crypto", "Bitcoin", "Ethereum", "DeFi"],
            "politics": ["Politics", "Elections", "US Politics"],
            "sports": ["Sports", "NFL", "NBA", "Soccer"],
            "economics": ["Economics", "Fed", "Inflation"]
        }
        
        tags = category_filter.get(category.lower(), [])
        filtered = [
            m for m in all_markets 
            if any(tag in m.get('tags', []) for tag in tags)
        ]
        
        return filtered
```

## 3️⃣ WebSocket для real-time данных

```python
# websocket_client.py
import asyncio
import json
import websockets
from typing import Callable, Optional

class PolymarketWebSocket:
    def __init__(self, api_key: str, secret: str, passphrase: str):
        self.api_key = api_key
        self.secret = secret
        self.passphrase = passphrase
        self.ws = None
        self.subscriptions = {}
        
    async def connect(self):
        """Подключение к WebSocket"""
        self.ws = await websockets.connect(ENDPOINTS["ws"])
        
        # Авторизация
        auth_message = {
            "type": "auth",
            "apiKey": self.api_key,
            "secret": self.secret,
            "passphrase": self.passphrase
        }
        await self.ws.send(json.dumps(auth_message))
        
        # Ждем подтверждения
        response = await self.ws.recv()
        auth_result = json.loads(response)
        
        if auth_result.get("type") != "authenticated":
            raise Exception("WebSocket authentication failed")
            
        # Запускаем обработчик сообщений
        asyncio.create_task(self._message_handler())
    
    async def _message_handler(self):
        """Обработчик входящих сообщений"""
        async for message in self.ws:
            data = json.loads(message)
            
            # Роутинг по типам сообщений
            if data.get("type") == "market_update":
                await self._handle_market_update(data)
            elif data.get("type") == "trade":
                await self._handle_trade(data)
            elif data.get("type") == "book_update":
                await self._handle_book_update(data)
    
    async def subscribe_to_market(self, token_id: str, 
                                 callback: Optional[Callable] = None):
        """Подписка на обновления рынка"""
        subscribe_msg = {
            "type": "subscribe",
            "channel": "market",
            "token_id": token_id
        }
        await self.ws.send(json.dumps(subscribe_msg))
        
        if callback:
            self.subscriptions[f"market_{token_id}"] = callback
    
    async def subscribe_to_trades(self, token_id: str,
                                 callback: Optional[Callable] = None):
        """Подписка на сделки"""
        subscribe_msg = {
            "type": "subscribe", 
            "channel": "trades",
            "token_id": token_id
        }
        await self.ws.send(json.dumps(subscribe_msg))
        
        if callback:
            self.subscriptions[f"trades_{token_id}"] = callback
    
    async def subscribe_to_user_updates(self, user_address: str,
                                       callback: Optional[Callable] = None):
        """Подписка на обновления пользователя"""
        subscribe_msg = {
            "type": "subscribe",
            "channel": "user",
            "user": user_address
        }
        await self.ws.send(json.dumps(subscribe_msg))
        
        if callback:
            self.subscriptions[f"user_{user_address}"] = callback
    
    async def _handle_market_update(self, data: Dict):
        """Обработка обновлений рынка"""
        token_id = data.get("token_id")
        callback = self.subscriptions.get(f"market_{token_id}")
        
        if callback:
            await callback(data)
    
    async def _handle_trade(self, data: Dict):
        """Обработка новых сделок"""
        token_id = data.get("token_id")
        callback = self.subscriptions.get(f"trades_{token_id}")
        
        if callback:
            await callback(data)
    
    async def _handle_book_update(self, data: Dict):
        """Обработка изменений в стакане"""
        # Обновление orderbook в реальном времени
        token_id = data.get("token_id")
        update_type = data.get("update_type")  # "bid" или "ask"
        
        print(f"Book update for {token_id}: {update_type}")
        print(f"New price: {data.get('price')}, Size: {data.get('size')}")
```

## 4️⃣ Получение цен криптовалют

```python
# crypto_prices.py
class CryptoPriceService:
    def __init__(self, client: PolymarketClient):
        self.client = client
        self.price_cache = {}
        
    async def get_crypto_markets(self) -> List[Dict]:
        """Получить все крипто-рынки с ценовыми предсказаниями"""
        markets = await self.client.get_markets_by_category("crypto")
        
        crypto_predictions = []
        for market in markets:
            # Парсим вопрос для извлечения цены и актива
            question = market.get('question', '')
            
            # Примеры: "Will Bitcoin be above $100,000?"
            if 'Bitcoin' in question or 'BTC' in question:
                asset = 'BTC'
                target_price = self._extract_price(question)
            elif 'Ethereum' in question or 'ETH' in question:
                asset = 'ETH'
                target_price = self._extract_price(question)
            elif 'Solana' in question or 'SOL' in question:
                asset = 'SOL'
                target_price = self._extract_price(question)
            else:
                continue
            
            if target_price:
                # Получаем вероятность достижения цены
                tokens = market.get('tokens', [])
                if tokens:
                    yes_token = tokens[0]
                    midpoint = await self.client.get_midpoint(yes_token['token_id'])
                    
                    crypto_predictions.append({
                        'asset': asset,
                        'target_price': target_price,
                        'probability': midpoint,  # 0.65 = 65% шанс
                        'market_id': market['condition_id'],
                        'question': question,
                        'end_date': market.get('end_date'),
                        'volume': market.get('volume24hr', 0)
                    })
        
        return crypto_predictions
    
    def _extract_price(self, question: str) -> Optional[float]:
        """Извлечь целевую цену из вопроса"""
        import re
        
        # Ищем паттерны типа "$100,000" или "100k"
        price_match = re.search(r'\$?([\d,]+)(?:k|K)?', question)
        if price_match:
            price_str = price_match.group(1).replace(',', '')
            price = float(price_str)
            
            # Если было "k", умножаем на 1000
            if 'k' in question.lower() or 'K' in question:
                price *= 1000
                
            return price
        return None
    
    async def get_price_predictions_timeline(self, asset: str) -> List[Dict]:
        """Получить предсказания цен на разные даты"""
        all_predictions = await self.get_crypto_markets()
        
        asset_predictions = [
            p for p in all_predictions 
            if p['asset'] == asset
        ]
        
        # Сортируем по дате окончания
        asset_predictions.sort(key=lambda x: x.get('end_date', ''))
        
        return asset_predictions
```

## 5️⃣ Аналитика и данные пользователей

```python
# analytics.py
class AnalyticsAPI:
    def __init__(self, client: PolymarketClient):
        self.client = client
        self.data_api = f"{ENDPOINTS['data']}"
        
    async def get_user_positions(self, user_address: str) -> List[Dict]:
        """Получить позиции пользователя"""
        url = f"{self.data_api}/positions"
        params = {"user": user_address}
        
        response = await self.client.http_client.get(url, params=params)
        positions = response.json()
        
        # Обогащаем данными о прибыли/убытке
        for position in positions:
            position['pnl'] = position.get('currentValue', 0) - position.get('initialValue', 0)
            position['pnl_percent'] = position.get('percentPnl', 0)
            
        return positions
    
    async def get_top_traders(self, market_id: Optional[str] = None) -> List[Dict]:
        """Получить топ трейдеров (китов)"""
        url = f"{self.data_api}/holders"
        params = {}
        if market_id:
            params["market"] = market_id
            
        response = await self.client.http_client.get(url, params=params)
        holders = response.json()
        
        # Анализируем китов
        whales = []
        for holder in holders:
            if holder.get('size', 0) > 10000:  # >$10k позиция
                whales.append({
                    'address': holder['user'],
                    'position_size': holder['size'],
                    'avg_price': holder.get('avgPrice', 0),
                    'pnl': holder.get('cashPnl', 0),
                    'outcome': holder.get('outcome')  # YES или NO
                })
        
        return whales
    
    async def get_market_trades(self, market_id: str, 
                               limit: int = 100) -> List[Dict]:
        """Получить последние сделки по рынку"""
        url = f"{self.data_api}/trades"
        params = {
            "market": market_id,
            "limit": limit
        }
        
        response = await self.client.http_client.get(url, params=params)
        trades = response.json()
        
        # Анализ потока ордеров
        buy_volume = sum(t['size'] for t in trades if t['side'] == 'BUY')
        sell_volume = sum(t['size'] for t in trades if t['side'] == 'SELL')
        
        return {
            'trades': trades,
            'buy_pressure': buy_volume / (buy_volume + sell_volume) if (buy_volume + sell_volume) > 0 else 0.5,
            'total_volume': buy_volume + sell_volume,
            'avg_trade_size': (buy_volume + sell_volume) / len(trades) if trades else 0
        }
    
    async def get_market_activity(self, market_id: str) -> Dict:
        """Полная активность по рынку"""
        url = f"{self.data_api}/activity"
        params = {"market": market_id}
        
        response = await self.client.http_client.get(url, params=params)
        activities = response.json()
        
        # Группируем по типам
        activity_summary = {
            'trades': [],
            'splits': [],
            'merges': [],
            'redemptions': []
        }
        
        for activity in activities:
            activity_type = activity.get('type', '').lower()
            if activity_type in activity_summary:
                activity_summary[activity_type].append(activity)
        
        return activity_summary
```

## 6️⃣ Трейдинг (размещение ордеров)

```python
# trading.py
from py_clob_client.clob_types import OrderArgs, MarketOrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY, SELL

class TradingAPI:
    def __init__(self, client: PolymarketClient, private_key: str, wallet_address: str):
        self.client = client
        
        # Инициализируем трейдинг клиент
        self.trading_client = ClobClient(
            ENDPOINTS["clob"],
            key=private_key,
            chain_id=CHAIN_ID,
            signature_type=0,  # EOA wallet
            funder=wallet_address
        )
        
        # Устанавливаем API credentials
        self.trading_client.set_api_creds(client.api_creds)
    
    async def place_limit_order(self, token_id: str, side: str, 
                               price: float, size: float) -> Dict:
        """Разместить лимитный ордер"""
        order = OrderArgs(
            token_id=token_id,
            price=price,
            size=size,
            side=BUY if side.upper() == "BUY" else SELL
        )
        
        signed_order = self.trading_client.create_order(order)
        response = self.trading_client.post_order(signed_order, OrderType.GTC)
        
        return response
    
    async def place_market_order(self, token_id: str, side: str,
                                amount: float) -> Dict:
        """Разместить рыночный ордер"""
        market_order = MarketOrderArgs(
            token_id=token_id,
            amount=amount,
            side=BUY if side.upper() == "BUY" else SELL,
            order_type=OrderType.FOK  # Fill or Kill
        )
        
        signed_order = self.trading_client.create_market_order(market_order)
        response = self.trading_client.post_order(signed_order, OrderType.FOK)
        
        return response
    
    async def cancel_order(self, order_id: str) -> Dict:
        """Отменить ордер"""
        return self.trading_client.cancel_order(order_id)
    
    async def cancel_all_orders(self) -> Dict:
        """Отменить все ордера"""
        return self.trading_client.cancel_all_orders()
    
    async def get_open_orders(self) -> List[Dict]:
        """Получить открытые ордера"""
        return self.trading_client.get_orders()
```

## 7️⃣ Главный класс для интеграции

```python
# main_integration.py
import asyncio
from typing import Dict, List, Optional

class PolymarketIntegration:
    def __init__(self, api_key: str, secret: str, passphrase: str,
                 private_key: Optional[str] = None, wallet_address: Optional[str] = None):
        
        # Основной клиент
        self.client = PolymarketClient(api_key, secret, passphrase)
        
        # API модули
        self.markets = MarketsAPI(self.client)
        self.analytics = AnalyticsAPI(self.client)
        self.crypto = CryptoPriceService(self.client)
        
        # WebSocket
        self.ws = PolymarketWebSocket(api_key, secret, passphrase)
        
        # Трейдинг (опционально)
        if private_key and wallet_address:
            self.trading = TradingAPI(self.client, private_key, wallet_address)
        else:
            self.trading = None
    
    async def initialize(self):
        """Инициализация подключений"""
        await self.ws.connect()
        print("✅ Connected to Polymarket")
    
    async def get_aggregated_market_data(self, question_keywords: str) -> Dict:
        """Получить агрегированные данные по рынку"""
        # Ищем подходящие рынки
        all_markets = await self.markets.get_all_markets()
        
        matching_markets = [
            m for m in all_markets
            if any(kw.lower() in m.get('question', '').lower() 
                  for kw in question_keywords.split())
        ]
        
        if not matching_markets:
            return {"error": "No matching markets found"}
        
        # Берем первый подходящий
        market = matching_markets[0]
        market_id = market['condition_id']
        
        # Собираем полные данные
        result = {
            'market': market,
            'trades': await self.analytics.get_market_trades(market_id),
            'whales': await self.analytics.get_top_traders(market_id),
            'activity': await self.analytics.get_market_activity(market_id),
            'orderbooks': {}
        }
        
        # Orderbooks для каждого токена
        for token in market.get('tokens', []):
            token_id = token['token_id']
            result['orderbooks'][token['outcome']] = await self.markets.get_orderbook(token_id)
        
        return result
    
    async def monitor_market_realtime(self, token_id: str):
        """Мониторинг рынка в реальном времени"""
        
        async def on_market_update(data):
            print(f"📊 Market Update: {data}")
        
        async def on_trade(data):
            print(f"💰 New Trade: {data['side']} {data['size']} @ {data['price']}")
        
        # Подписываемся на обновления
        await self.ws.subscribe_to_market(token_id, on_market_update)
        await self.ws.subscribe_to_trades(token_id, on_trade)
        
        print(f"👀 Monitoring token {token_id}")
    
    async def get_price_predictions_summary(self) -> Dict:
        """Сводка по ценовым предсказаниям крипты"""
        predictions = {
            'BTC': await self.crypto.get_price_predictions_timeline('BTC'),
            'ETH': await self.crypto.get_price_predictions_timeline('ETH'),
            'SOL': await self.crypto.get_price_predictions_timeline('SOL')
        }
        
        return predictions
```

## 8️⃣ Примеры использования

```python
# examples.py

async def main():
    # Инициализация
    poly = PolymarketIntegration(
        api_key="YOUR_API_KEY",
        secret="YOUR_SECRET",
        passphrase="YOUR_PASSPHRASE"
    )
    
    await poly.initialize()
    
    # Пример 1: Получить все крипто-рынки
    crypto_markets = await poly.markets.get_markets_by_category("crypto")
    print(f"Found {len(crypto_markets)} crypto markets")
    
    # Пример 2: Получить предсказания цен
    btc_predictions = await poly.crypto.get_price_predictions_timeline('BTC')
    for pred in btc_predictions:
        print(f"BTC > ${pred['target_price']}: {pred['probability']*100:.1f}% chance by {pred['end_date']}")
    
    # Пример 3: Найти китов на конкретном рынке
    market_data = await poly.get_aggregated_market_data("Bitcoin 100k")
    whales = market_data['whales']
    print(f"Top whales: {whales[:5]}")
    
    # Пример 4: Мониторинг в реальном времени
    if crypto_markets:
        token_id = crypto_markets[0]['tokens'][0]['token_id']
        await poly.monitor_market_realtime(token_id)
        
        # Держим подключение
        await asyncio.sleep(60)  # Мониторим 1 минуту

if __name__ == "__main__":
    asyncio.run(main())
```

## 📊 Структура ответов API

```python
# Response structures

# Market structure
market_response = {
    "condition_id": "0x...",
    "question": "Will Bitcoin reach $100,000 by Dec 31?",
    "tokens": [
        {
            "token_id": "1234...",
            "outcome": "Yes",
            "price": 0.65,  # 65% вероятность
        },
        {
            "token_id": "5678...",
            "outcome": "No",
            "price": 0.35
        }
    ],
    "volume24hr": 1500000,
    "liquidity": 500000,
    "end_date": "2024-12-31T00:00:00Z"
}

# Trade structure
trade_response = {
    "id": "trade_123",
    "token_id": "1234...",
    "side": "BUY",
    "price": 0.65,
    "size": 100,
    "timestamp": "2024-01-01T12:00:00Z",
    "user": "0x..."
}

# Position structure
position_response = {
    "user": "0x...",
    "token_id": "1234...",
    "size": 1000,
    "avgPrice": 0.60,
    "currentPrice": 0.65,
    "pnl": 50,  # $50 profit
    "percentPnl": 8.33
}
```

## ⚠️ Rate Limits и Best Practices

```python
# Rate limits
RATE_LIMITS = {
    "clob_api": {
        "requests_per_second": 10,
        "requests_per_minute": 100
    },
    "data_api": {
        "requests_per_second": 5,
        "requests_per_minute": 100
    },
    "websocket": {
        "subscriptions": 100,  # Макс подписок
        "messages_per_second": 20
    }
}

# Best practices
BEST_PRACTICES = """
1. Используй WebSocket для real-time данных вместо polling
2. Кешируй статичные данные (market metadata)
3. Batch запросы где возможно
4. Обрабатывай ошибки и реконнекты
5. Логируй все транзакции
6. Никогда не храни приватные ключи в коде
7. Используй rate limiting на своей стороне
"""
```

## ✅ Готовая структура проекта

```
polymarket_integration/
├── config.py              # Конфигурация и ключи
├── client.py             # Базовый клиент
├── markets.py            # API рынков
├── websocket.py          # WebSocket клиент
├── analytics.py          # Аналитика
├── crypto.py            # Крипто-предсказания
├── trading.py           # Трейдинг (опционально)
├── main.py              # Главный класс интеграции
└── examples.py          # Примеры использования
```

Это полная документация для интеграции Polymarket в ThePred. Все готово к реализации!