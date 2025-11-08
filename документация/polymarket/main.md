# 📖 Polymarket API Reference Documentation

## 🌐 Base URLs

```yaml
Production:
  CLOB_API: https://clob.polymarket.com
  GAMMA_API: https://gamma-api.polymarket.com  
  DATA_API: https://data-api.polymarket.com
  WEBSOCKET: wss://ws-subscriptions-clob.polymarket.com/ws
  
Network: Polygon (Chain ID: 137)
USDC_ADDRESS: 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174
```

## 🔐 Authentication

### Headers for Authenticated Requests
```http
POLY_API_KEY: your-api-key
POLY_SIGNATURE: base64-encoded-signature
POLY_TIMESTAMP: unix-timestamp
POLY_PASSPHRASE: your-passphrase
Content-Type: application/json
```

### Signature Generation
```python
# Signature = base64(hmac_sha256(secret, timestamp + method + path + body))
timestamp + "GET" + "/markets" + ""
```

---

## 📊 GAMMA API - Markets & Metadata

### GET /markets
**Get all markets**
```http
GET https://gamma-api.polymarket.com/markets
Query Parameters:
  - active: boolean (default: true)
  - closed: boolean (default: false)
  - tag: string (optional, e.g., "Crypto", "Politics")
  - limit: integer (default: 100)
  - offset: integer (default: 0)

Response:
[
  {
    "condition_id": "0xd007d71fd17b0913b9d7ff198f617caa96a9e4aab1bed7d6f9abd76bb17dd507",
    "question": "Will Bitcoin be above $100,000 on December 31, 2024?",
    "description": "This market will resolve to \"Yes\" if...",
    "tags": ["Crypto", "Bitcoin", "Price"],
    "end_date": "2024-12-31T23:59:59Z",
    "market_slug": "will-bitcoin-100k-2024",
    "icon": "https://polymarket-upload.s3.us-east-2.amazonaws.com/bitcoin.png",
    "tokens": [
      {
        "token_id": "65396714035221124737265515219989336303267439172398528294132309725835127126381",
        "outcome": "Yes"
      },
      {
        "token_id": "52050340002752890901105180731616786223343503725333424175929498217562194356499",
        "outcome": "No"
      }
    ],
    "volume": 2500000,
    "volume_24hr": 150000,
    "liquidity": 500000,
    "rewards": {
      "liquidityRewards": 1000,
      "traderRewards": 500
    },
    "enable_order_book": true,
    "active": true
  }
]
```

### GET /markets/{condition_id}
**Get specific market details**
```http
GET https://gamma-api.polymarket.com/markets/0xd007d71fd17b0913b9d7ff198f617caa96a9e4aab1bed7d6f9abd76bb17dd507

Response:
{
  "condition_id": "0xd007d71fd17b0913b9d7ff198f617caa96a9e4aab1bed7d6f9abd76bb17dd507",
  "question": "Will Bitcoin be above $100,000 on December 31, 2024?",
  "tokens": [...],
  "resolution_source": "CoinGecko API",
  "category": "Crypto",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

### GET /events
**Get grouped events**
```http
GET https://gamma-api.polymarket.com/events
Query Parameters:
  - active: boolean
  - tag: string
  - limit: integer

Response:
[
  {
    "id": "us-elections-2024",
    "title": "2024 US Presidential Election",
    "category": "Politics",
    "markets": [
      {
        "condition_id": "0x123...",
        "question": "Will Trump win?"
      }
    ]
  }
]
```

---

## 💱 CLOB API - Order Book & Trading

### GET /book
**Get order book for a token**
```http
GET https://clob.polymarket.com/book
Query Parameters:
  - token_id: string (required)
  - depth: integer (optional, default: 100)

Response:
{
  "market": "0xd007d71fd17b0913b9d7ff198f617caa96a9e4aab1bed7d6f9abd76bb17dd507",
  "asset_id": "65396714035221124737265515219989336303267439172398528294132309725835127126381",
  "bids": [
    {
      "price": "0.65",
      "size": "1000"
    },
    {
      "price": "0.64",
      "size": "2500"
    }
  ],
  "asks": [
    {
      "price": "0.66",
      "size": "1500"
    },
    {
      "price": "0.67",
      "size": "3000"
    }
  ],
  "timestamp": 1704067200
}
```

### GET /price
**Get best price for a side**
```http
GET https://clob.polymarket.com/price
Query Parameters:
  - token_id: string (required)
  - side: string ("BUY" or "SELL")

Response:
{
  "price": "0.65"
}
```

### GET /midpoint
**Get midpoint price**
```http
GET https://clob.polymarket.com/midpoint
Query Parameters:
  - token_id: string (required)

Response:
{
  "mid": "0.655"
}
```

### GET /spread
**Get bid-ask spread**
```http
GET https://clob.polymarket.com/spread
Query Parameters:
  - token_id: string (required)

Response:
{
  "spread": "0.01",
  "spread_percent": "1.52"
}
```

### POST /order
**Place an order** (Requires Authentication)
```http
POST https://clob.polymarket.com/order
Headers: [Authentication headers required]
Body:
{
  "order": {
    "salt": 123456789,
    "maker": "0xYourAddress",
    "signer": "0xSignerAddress",
    "taker": "0x0000000000000000000000000000000000000000",
    "tokenId": "65396714035221124737265515219989336303267439172398528294132309725835127126381",
    "makerAmount": "100000000",  // 100 USDC
    "takerAmount": "153846153",  // Amount of outcome tokens
    "side": "BUY",
    "expiration": 1704153600,
    "nonce": 1,
    "feeRateBps": "100",  // 1%
    "signatureType": 0
  },
  "signature": "0x...",
  "orderType": "GTC"  // GTC, GTD, FOK, or IOC
}

Response:
{
  "orderID": "0x123abc...",
  "status": "LIVE",
  "created_at": 1704067200
}
```

### DELETE /order
**Cancel an order** (Requires Authentication)
```http
DELETE https://clob.polymarket.com/order
Headers: [Authentication headers required]
Body:
{
  "orderID": "0x123abc..."
}

Response:
{
  "orderID": "0x123abc...",
  "status": "CANCELLED"
}
```

### GET /orders
**Get user's orders** (Requires Authentication)
```http
GET https://clob.polymarket.com/orders
Headers: [Authentication headers required]
Query Parameters:
  - state: string (optional: "LIVE", "CANCELLED", "MATCHED")
  - market: string (optional: condition_id)

Response:
[
  {
    "id": "0x123abc...",
    "market": "0xd007d71fd17b0913b9d7ff198f617caa96a9e4aab1bed7d6f9abd76bb17dd507",
    "side": "BUY",
    "price": "0.65",
    "size": "100",
    "size_matched": "50",
    "state": "LIVE",
    "created_at": 1704067200
  }
]
```

### GET /trades
**Get recent trades**
```http
GET https://clob.polymarket.com/trades
Query Parameters:
  - market: string (condition_id)
  - maker: string (address, optional)
  - limit: integer (default: 100)

Response:
[
  {
    "id": "trade_123",
    "market": "0xd007d71fd17b0913b9d7ff198f617caa96a9e4aab1bed7d6f9abd76bb17dd507",
    "token_id": "65396714035221124737265515219989336303267439172398528294132309725835127126381",
    "side": "BUY",
    "price": "0.65",
    "size": "100",
    "fee": "1",
    "timestamp": 1704067200,
    "maker": "0x123...",
    "taker": "0x456..."
  }
]
```

### GET /rewards
**Get trading rewards info**
```http
GET https://clob.polymarket.com/rewards
Query Parameters:
  - market: string (condition_id)
  - user: string (address)

Response:
{
  "market": "0xd007d71fd17b0913b9d7ff198f617caa96a9e4aab1bed7d6f9abd76bb17dd507",
  "user": "0x123...",
  "trader_rewards": 150.50,
  "liquidity_rewards": 75.25,
  "epoch": 10,
  "claimable": true
}
```

---

## 📈 DATA API - Analytics & Historical Data

### GET /positions
**Get user positions**
```http
GET https://data-api.polymarket.com/positions
Query Parameters:
  - user: string (required, user address)
  - market: string (optional, condition_id)
  - outcome: string (optional, "YES" or "NO")
  - sizeThreshold: number (optional, minimum position size)
  - sortBy: string (TOKENS, CURRENT, INITIAL, CASHPNL, PERCENTPNL)
  - sortDirection: string (ASC or DESC)

Response:
[
  {
    "proxyWallet": "0x6af75d4e4aaf700450efbac3708cce1665810ff1",
    "asset": "65396714035221124737265515219989336303267439172398528294132309725835127126381",
    "conditionId": "0xd007d71fd17b0913b9d7ff198f617caa96a9e4aab1bed7d6f9abd76bb17dd507",
    "size": 1000.50,
    "avgPrice": 0.60,
    "initialValue": 600.30,
    "currentValue": 650.32,
    "cashPnl": 50.02,
    "percentPnl": 8.33,
    "totalBought": 1500.50,
    "totalSold": 500.00,
    "realizedPnl": 25.00,
    "unrealizedPnl": 25.02,
    "curPrice": 0.65,
    "outcome": "Yes",
    "title": "Will Bitcoin be above $100,000?"
  }
]
```

### GET /holders
**Get top holders for a market**
```http
GET https://data-api.polymarket.com/holders
Query Parameters:
  - market: string (condition_id)
  - outcome: string (optional, "YES" or "NO")
  - limit: integer (default: 100)

Response:
[
  {
    "user": "0x123...",
    "size": 50000,
    "avgPrice": 0.62,
    "outcome": "Yes",
    "rank": 1,
    "percentOfSupply": 2.5
  }
]
```

### GET /trades
**Get historical trades**
```http
GET https://data-api.polymarket.com/trades
Query Parameters:
  - market: string (optional)
  - user: string (optional)
  - start: integer (timestamp, optional)
  - end: integer (timestamp, optional)
  - limit: integer (default: 100)
  - sortBy: string (TIMESTAMP, SIZE, PRICE)
  - sortDirection: string (ASC or DESC)

Response:
[
  {
    "id": "0xabc123...",
    "market": "0xd007d71fd17b0913b9d7ff198f617caa96a9e4aab1bed7d6f9abd76bb17dd507",
    "user": "0x123...",
    "side": "BUY",
    "outcome": "Yes",
    "price": 0.65,
    "size": 100,
    "fee": 1,
    "timestamp": 1704067200,
    "txHash": "0xdef456..."
  }
]
```

### GET /activity
**Get on-chain activity**
```http
GET https://data-api.polymarket.com/activity
Query Parameters:
  - user: string (optional)
  - market: string (optional)
  - type: string (TRADE, SPLIT, MERGE, REDEEM, REWARD, CONVERSION)
  - start: integer (timestamp)
  - end: integer (timestamp)

Response:
[
  {
    "type": "TRADE",
    "user": "0x123...",
    "market": "0xd007d71fd17b0913b9d7ff198f617caa96a9e4aab1bed7d6f9abd76bb17dd507",
    "timestamp": 1704067200,
    "details": {
      "side": "BUY",
      "outcome": "Yes",
      "amount": 100,
      "price": 0.65
    },
    "txHash": "0xabc123..."
  }
]
```

### GET /value
**Get portfolio value over time**
```http
GET https://data-api.polymarket.com/value
Query Parameters:
  - user: string (required)
  - period: string (1D, 1W, 1M, 3M, 1Y, ALL)

Response:
{
  "user": "0x123...",
  "currentValue": 10000.50,
  "initialValue": 8000.00,
  "pnl": 2000.50,
  "pnlPercent": 25.01,
  "history": [
    {
      "timestamp": 1704067200,
      "value": 8500.00
    },
    {
      "timestamp": 1704153600,
      "value": 9200.00
    }
  ]
}
```

---

## 🔄 WebSocket API

### Connection
```javascript
ws://ws-subscriptions-clob.polymarket.com/ws
```

### Authentication Message
```json
{
  "type": "auth",
  "apiKey": "your-api-key",
  "secret": "your-secret",
  "passphrase": "your-passphrase"
}
```

### Subscribe to Market Updates
```json
{
  "type": "subscribe",
  "channel": "market",
  "token_id": "65396714035221124737265515219989336303267439172398528294132309725835127126381"
}

Response Stream:
{
  "type": "market_update",
  "token_id": "65396714035221124737265515219989336303267439172398528294132309725835127126381",
  "bid": 0.65,
  "ask": 0.66,
  "last": 0.65,
  "volume_24h": 150000,
  "timestamp": 1704067200
}
```

### Subscribe to Order Book Updates
```json
{
  "type": "subscribe",
  "channel": "book",
  "token_id": "65396714035221124737265515219989336303267439172398528294132309725835127126381",
  "depth": 10
}

Response Stream:
{
  "type": "book_update",
  "token_id": "65396714035221124737265515219989336303267439172398528294132309725835127126381",
  "side": "bid",
  "price": 0.65,
  "size": 1000,
  "action": "add"  // add, remove, or update
}
```

### Subscribe to Trades
```json
{
  "type": "subscribe",
  "channel": "trades",
  "token_id": "65396714035221124737265515219989336303267439172398528294132309725835127126381"
}

Response Stream:
{
  "type": "trade",
  "token_id": "65396714035221124737265515219989336303267439172398528294132309725835127126381",
  "id": "trade_123",
  "price": 0.65,
  "size": 100,
  "side": "BUY",
  "timestamp": 1704067200
}
```

### Subscribe to User Updates
```json
{
  "type": "subscribe",
  "channel": "user",
  "user": "0x123..."
}

Response Stream:
{
  "type": "user_update",
  "user": "0x123...",
  "event": "order_filled",
  "details": {
    "order_id": "0xabc...",
    "filled_amount": 50,
    "remaining": 50,
    "price": 0.65
  }
}
```

### Subscribe to Multiple Channels
```json
{
  "type": "subscribe_multi",
  "subscriptions": [
    {
      "channel": "market",
      "token_id": "token_1"
    },
    {
      "channel": "trades",
      "token_id": "token_2"
    }
  ]
}
```

### Unsubscribe
```json
{
  "type": "unsubscribe",
  "channel": "market",
  "token_id": "65396714035221124737265515219989336303267439172398528294132309725835127126381"
}
```

### Ping/Pong (Keep Alive)
```json
// Client sends
{
  "type": "ping"
}

// Server responds
{
  "type": "pong",
  "timestamp": 1704067200
}
```

### Error Messages
```json
{
  "type": "error",
  "code": "INVALID_TOKEN",
  "message": "Token ID not found",
  "details": {
    "token_id": "invalid_token_123"
  }
}
```

---

## 📊 Special Endpoints

### GET /markets/trending
**Get trending markets**
```http
GET https://gamma-api.polymarket.com/markets/trending
Query Parameters:
  - period: string (1H, 24H, 7D)
  - limit: integer (default: 10)

Response:
[
  {
    "condition_id": "0xd007...",
    "question": "Will Bitcoin reach $100k?",
    "volume_change": 250.5,  // percentage
    "price_change": 0.15,
    "trade_count": 1500
  }
]
```

### GET /leaderboard
**Get top traders**
```http
GET https://data-api.polymarket.com/leaderboard
Query Parameters:
  - period: string (DAILY, WEEKLY, MONTHLY, ALL_TIME)
  - metric: string (PNL, VOLUME, WIN_RATE)
  - limit: integer (default: 100)

Response:
[
  {
    "rank": 1,
    "user": "0x123...",
    "pnl": 50000,
    "volume": 500000,
    "trades": 150,
    "win_rate": 0.65,
    "best_trade": {
      "market": "0xd007...",
      "pnl": 10000
    }
  }
]
```

### GET /stats/global
**Get global platform statistics**
```http
GET https://gamma-api.polymarket.com/stats/global

Response:
{
  "total_volume": 1000000000,
  "total_markets": 5000,
  "active_markets": 500,
  "total_users": 100000,
  "volume_24h": 5000000,
  "trades_24h": 50000
}
```

---

## 🔴 Error Codes

```json
{
  "400": "Bad Request - Invalid parameters",
  "401": "Unauthorized - Invalid API credentials",
  "403": "Forbidden - Insufficient permissions",
  "404": "Not Found - Resource does not exist",
  "429": "Too Many Requests - Rate limit exceeded",
  "500": "Internal Server Error",
  "503": "Service Unavailable"
}

Error Response Format:
{
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "Insufficient USDC balance",
    "details": {
      "required": 100,
      "available": 50
    }
  }
}
```

---

## 📈 Rate Limits

```yaml
CLOB API:
  Per Second: 10 requests
  Per Minute: 100 requests
  Per Hour: 3000 requests

GAMMA API:
  Per Second: 10 requests
  Per Minute: 200 requests
  Per Hour: 5000 requests

DATA API:
  Per Second: 5 requests
  Per Minute: 100 requests
  Per Hour: 2000 requests

WebSocket:
  Connections per IP: 5
  Subscriptions per connection: 100
  Messages per second: 20

Rate Limit Headers:
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 95
  X-RateLimit-Reset: 1704067200
```

---

## 🔧 Order Types

```yaml
GTC (Good Till Cancel): Order remains active until filled or cancelled
GTD (Good Till Date): Order expires at specified time
FOK (Fill or Kill): Must be filled immediately in full or cancelled
IOC (Immediate or Cancel): Fill what you can immediately, cancel the rest
```

---

## 💰 Fee Structure

```yaml
Taker Fee: 0.10% (10 basis points)
Maker Fee: 0.00% (0 basis points)
Minimum Fee: $0.01
Maximum Fee: $100

Rewards:
  Liquidity Provider: 0.05% rebate
  Volume Trader: Tiered discounts based on 30-day volume
```

---

## 🔍 Useful Query Examples

### Find Bitcoin markets above $100k
```http
GET https://gamma-api.polymarket.com/markets?tag=Bitcoin&active=true
Filter results where question contains "100" or "100k" or "100,000"
```

### Get whale positions
```http
GET https://data-api.polymarket.com/positions?sizeThreshold=10000&sortBy=CURRENT&sortDirection=DESC
```

### Monitor specific trader
```http
GET https://data-api.polymarket.com/activity?user=0x123...&type=TRADE
```

### Get arbitrage opportunities
```http
# Compare same market across different times
GET https://clob.polymarket.com/midpoint?token_id=YES_TOKEN
GET https://clob.polymarket.com/midpoint?token_id=NO_TOKEN
# If YES + NO != 1.00, arbitrage exists
```

---

## 📝 Notes

1. All timestamps are Unix timestamps (seconds since epoch)
2. All prices are decimals between 0 and 1 (0.65 = 65 cents = 65% probability)
3. All amounts are in smallest units (USDC = 6 decimals, so 1 USDC = 1000000)
4. Token IDs are unique identifiers for each outcome token
5. Condition IDs identify the market/question
6. Always check `enable_order_book` before trying to trade
7. Markets can be resolved early if outcome becomes certain
8. Use WebSocket for real-time data instead of polling

---

## 🚀 Quick Start Examples

### Get market price
```bash
curl "https://clob.polymarket.com/midpoint?token_id=YOUR_TOKEN_ID"
```

### Subscribe to updates (WebSocket)
```javascript
const ws = new WebSocket('wss://ws-subscriptions-clob.polymarket.com/ws');
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'market',
  token_id: 'YOUR_TOKEN_ID'
}));
```

### Get user positions
```bash
curl "https://data-api.polymarket.com/positions?user=0xYOUR_ADDRESS"
```

---

**Документация готова к использованию! Все эндпоинты, форматы и примеры в одном месте.**