# crypto_price_monitor.py

import asyncio
import json
import websockets
from datetime import datetime
from typing import Dict
import os

# Binance WebSocket endpoints для разных монет
BINANCE_STREAMS = {
    'BTC': 'wss://stream.binance.com:9443/ws/btcusdt@trade',
    'ETH': 'wss://stream.binance.com:9443/ws/ethusdt@trade',
    'SOL': 'wss://stream.binance.com:9443/ws/solusdt@trade'
}

# Можно подключиться к нескольким потокам сразу
BINANCE_COMBINED = 'wss://stream.binance.com:9443/stream?streams=btcusdt@trade/ethusdt@trade/solusdt@trade'


class CryptoPriceMonitor:
    def __init__(self):
        self.prices = {
            'BTCUSDT': 0,
            'ETHUSDT': 0,
            'SOLUSDT': 0
        }
        self.last_update = {
            'BTCUSDT': None,
            'ETHUSDT': None,
            'SOLUSDT': None
        }
        self.price_change = {
            'BTCUSDT': 0,
            'ETHUSDT': 0,
            'SOLUSDT': 0
        }
        self.ws = None

    async def connect_websocket(self):
        """Подключиться к Binance WebSocket"""
        print("🔌 Подключаюсь к Binance WebSocket...")

        try:
            self.ws = await websockets.connect(BINANCE_COMBINED)
            print("✅ Подключен к Binance\n")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False

    async def listen_prices(self):
        """Слушать обновления цен"""
        if not self.ws:
            return

        while True:
            try:
                message = await self.ws.recv()
                data = json.loads(message)

                # Binance отправляет данные в формате stream
                if 'stream' in data and 'data' in data:
                    trade_data = data['data']
                    symbol = trade_data['s']  # Символ (BTCUSDT, ETHUSDT, etc)
                    price = float(trade_data['p'])  # Цена

                    # Сохраняем предыдущую цену для расчета изменения
                    old_price = self.prices.get(symbol, 0)
                    if old_price > 0:
                        self.price_change[symbol] = price - old_price

                    # Обновляем цену
                    self.prices[symbol] = price
                    self.last_update[symbol] = datetime.now()

            except websockets.ConnectionClosed:
                print("❌ Соединение закрыто, переподключаюсь...")
                await asyncio.sleep(5)
                await self.connect_websocket()
            except Exception as e:
                print(f"❌ Ошибка: {e}")

    async def display_prices(self):
        """Отображать цены каждую секунду"""

        # Ждем первых данных
        await asyncio.sleep(2)

        while True:
            # Очищаем экран (опционально - раскомментируйте если хотите)
            # os.system('clear' if os.name == 'posix' else 'cls')

            # Форматируем вывод
            timestamp = datetime.now().strftime('%H:%M:%S')

            # Определяем цвет изменения (эмодзи)
            def get_arrow(change):
                if change > 0:
                    return "🟢"
                elif change < 0:
                    return "🔴"
                else:
                    return "⚪"

            # Выводим в одну строку с обновлением
            output = f"\r⏰ {timestamp} | "

            # Bitcoin
            btc_price = self.prices.get('BTCUSDT', 0)
            btc_change = self.price_change.get('BTCUSDT', 0)
            output += f"₿ BTC: ${btc_price:,.2f} {get_arrow(btc_change)} "

            # Ethereum
            eth_price = self.prices.get('ETHUSDT', 0)
            eth_change = self.price_change.get('ETHUSDT', 0)
            output += f"| ⟠ ETH: ${eth_price:,.2f} {get_arrow(eth_change)} "

            # Solana
            sol_price = self.prices.get('SOLUSDT', 0)
            sol_change = self.price_change.get('SOLUSDT', 0)
            output += f"| ◉ SOL: ${sol_price:,.2f} {get_arrow(sol_change)}"

            print(output, end='', flush=True)

            await asyncio.sleep(1)

    async def display_detailed(self):
        """Детальная информация каждые 10 секунд"""

        # Ждем накопления данных
        await asyncio.sleep(5)

        while True:
            await asyncio.sleep(10)

            print("\n\n" + "=" * 80)
            print(f"📊 Crypto Prices Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)

            # Детальный вывод для каждой монеты
            symbols = [
                ('BTCUSDT', 'Bitcoin', '₿'),
                ('ETHUSDT', 'Ethereum', '⟠'),
                ('SOLUSDT', 'Solana', '◉')
            ]

            for symbol, name, emoji in symbols:
                price = self.prices.get(symbol, 0)
                change = self.price_change.get(symbol, 0)
                last_update = self.last_update.get(symbol)

                if price > 0:
                    print(f"\n{emoji} {name} ({symbol.replace('USDT', '/USDT')})")
                    print(f"   Цена: ${price:,.2f}")

                    if change != 0:
                        change_pct = (change / (price - change)) * 100 if (price - change) > 0 else 0
                        change_symbol = "↑" if change > 0 else "↓"
                        print(f"   Изменение: {change_symbol} ${abs(change):.2f} ({change_pct:+.3f}%)")

                    if last_update:
                        print(f"   Обновлено: {last_update.strftime('%H:%M:%S')}")

            print("\n" + "-" * 80)
            print("💡 Данные с Binance в реальном времени")
            print("🔄 Обновление каждую секунду")

    async def run(self):
        """Главная функция"""
        print("🚀 Crypto Real-time Price Monitor")
        print("=" * 80)
        print("Отслеживаемые монеты: Bitcoin (BTC), Ethereum (ETH), Solana (SOL)")
        print("=" * 80 + "\n")

        # Подключаемся к WebSocket
        connected = await self.connect_websocket()

        if not connected:
            print("Не удалось подключиться к Binance")
            return

        # Запускаем параллельные задачи
        await asyncio.gather(
            self.listen_prices(),  # Получение цен
            self.display_prices(),  # Обновление каждую секунду
            self.display_detailed()  # Детальная инфа каждые 10 секунд
        )


async def main():
    monitor = CryptoPriceMonitor()
    try:
        await monitor.run()
    except KeyboardInterrupt:
        print("\n\n👋 Остановлено пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")


if __name__ == "__main__":
    # Запускаем
    asyncio.run(main())