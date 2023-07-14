from datetime import datetime
from time import sleep
from simulator.abstract_strategy import AbstractStrategy
from simulator.bybit_handler import BybitHandler
from simulator.exchange_handler import ExchangeHandler
from simulator.orderbook import Orderbook

class MyBybitStrategy(AbstractStrategy):
    def __init__(self, api_key=None, api_secret=None):
        kline_intervals = {"BTCUSDT": ["1"]}
        handlers = {
            "Bybit": BybitHandler(api_key, api_secret, symbols={"BTCUSDT"}, orderbook_depth=50, kline_intervals=kline_intervals)
        }
        super().__init__(exchange_handlers=handlers)

    def on_ready(self):
        print("Startegy successfully started.")

    def on_orderbook_update(self, symbol: str, exchange: ExchangeHandler, orderbook: Orderbook, timestamp: int):
        # Handle how you want your strategy to react to orderbook updates here

        # Example: print the best bid, ask and the spread
        # print(f"Best bid: {orderbook.best_bid}, Best ask: {orderbook.best_ask}, Spread: {orderbook.spread:.2f}")

        # Example 2: print the orderbook
        # print(self.exchange_handlers["bybit"].orderbook("BTCUSDT"))
        pass

    def on_trade(self, symbol: str, exchange: ExchangeHandler, side: str, price: float, size: float, timestamp: int):
        # Handle how you want your strategy to react to trades here 
        
        # Example: print the trade
        # time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S.%f")[:-3]
        # print(f"{time_str} > TRADE {exchange.name:8} {side:4} {size:6.3f} {symbol} at {price:6.2f} (${price*size:.2f})")
        pass

    def on_candle_update(self, symbol: str, exchange: ExchangeHandler, candle: tuple[str, str, str, float, float, float, float, float, float], timestamp: int, confirmed: bool):
        # Handle how you want your strategy to react to candle updates here (confirmed=True means the candle is closed)
        # start_ts, end_ts, interval, open, high, low, close, volume, turnover = candle

        # Example: print the candle
        # time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S.%f")[:-3]
        # print(f"{time_str} > CANDLE {exchange.name:8} {symbol} {interval} {start_ts} {end_ts} {open:6.2f} {high:6.2f} {low:6.2f} {close:6.2f} {volume:6.2f} {turnover:6.2f} {confirmed}")
        pass

    def on_liquidation(self, symbol: str, exchange: ExchangeHandler, side: str, price: float, size: float, timestamp: int):
        # Handle how you want your strategy to react to liquidations here

        # Example: print the liquidation
        # time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S.%f")[:-3]
        # print(f"{time_str} > LIQUIDATION {exchange.name:8} {side:4} {size:6.3f} {symbol} at {price:6.2f} (${price*size:.2f})")
        pass

if __name__ == "__main__":
    api_key = ""
    api_secret = ""
    strategy = MyBybitStrategy()
    strategy.start()

    while True:
        sleep(1)