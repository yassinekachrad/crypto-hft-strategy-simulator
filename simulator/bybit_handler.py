from pybit.unified_trading import WebSocket
from .abstract_strategy import AbstractStrategy

from .exchange_handler import ExchangeHandler


class BybitHandler(ExchangeHandler):
    def __init__(self, api_key, api_secret, symbols: set[str], orderbook_depth: int = 50, kline_intervals: dict[str, str] = {"BTCUSDT": "1"}):
        super().__init__(name="Bybit", symbols=symbols)
        self.api_key = api_key
        self.api_secret = api_secret
        self.websocket = WebSocket(testnet=False, channel_type="linear")
        self.orderbook_depth = orderbook_depth
        self.kline_intervals = kline_intervals

    def start(self, strategy: AbstractStrategy):
        super().start(strategy)
        for symbol in self.symbols:
            self.websocket.orderbook_stream(depth=self.orderbook_depth,
                                            symbol=symbol,
                                            callback=self.update_orderbook)
            self.websocket.trade_stream(symbol, self.update_trade)
            self.websocket.liquidation_stream(symbol, self.update_liquidation)
            for symbol in self.kline_intervals:
                for interval in self.kline_intervals[symbol]:
                    self.websocket.kline_stream(interval=interval,
                                                symbol=symbol,
                                                callback=self.update_candle)

    def update_orderbook(self, data):
        bids = map(lambda x: (float(x[0]), float(x[1])), data["data"]["b"])
        asks = map(lambda x: (float(x[0]), float(x[1])), data["data"]["a"])
        symbol = data["data"]["s"]
        ts = data["data"]["u"]/1000
        if data["type"] == "snapshot":
            self.orderbook(symbol=symbol).update(
                bids=bids, asks=asks, timestamp=ts)
        elif data["type"] == "delta":
            self.orderbook(symbol=symbol).delta_update(
                bids=bids, asks=asks, timestamp=ts)

        self.strategy.on_orderbook_update(
            symbol=symbol, exchange=self, orderbook=self.orderbook(symbol), timestamp=ts)

    def update_trade(self, data):
        for trade in data["data"]:
            symbol = trade["s"]
            ts = trade["T"]/1000
            price = float(trade["p"])
            size = float(trade["v"])
            side = trade["S"]
            self.strategy.on_trade(
                symbol=symbol, exchange=self, side=side, price=price, size=size, timestamp=ts)

    def update_candle(self, data):
        symbol = data["topic"].split(".")[2]
        for candle_data in data["data"]:
            start = candle_data["start"]/1000
            end = candle_data["end"]/1000
            interval = candle_data["interval"]
            open = float(candle_data["open"])
            close = float(candle_data["close"])
            high = float(candle_data["high"])
            low = float(candle_data["low"])
            volume = float(candle_data["volume"])
            turnover = float(candle_data["turnover"])
            ts = candle_data["timestamp"]/1000
            confirmed = candle_data["confirm"]

            candle = (start, end, interval, open, close,
                      high, low, volume, turnover)
            self.strategy.on_candle_update(
                symbol=symbol, exchange=self, candle=candle, timestamp=ts, confirmed=confirmed)

    def update_liquidation(self, data):
        with open("liquidation.txt", "a") as f:
            f.write(str(data) + "\n")
        for liquidation in data["data"]:
            symbol = liquidation["symbol"]
            ts = liquidation["updatedTime"]/1000
            price = float(liquidation["price"])
            size = float(liquidation["size"])
            side = liquidation["side"]

            self.strategy.on_liquidation(
                symbol=symbol, exchange=self, side=side, price=price, size=size, timestamp=ts)
