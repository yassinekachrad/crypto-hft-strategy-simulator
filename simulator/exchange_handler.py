from .orderbook import Orderbook

class ExchangeHandler:
    def __init__(self, name: str, symbols: set[str]):
        self.name: str = name
        self.symbols: set[str] = symbols.copy()
        self.orderbooks: dict[str, Orderbook] = dict()
        self.strategy = None

    def start(self, strategy):
        self.strategy = strategy

    def orderbook(self, symbol: str):
        if symbol not in self.orderbooks:
            self.orderbooks[symbol] = Orderbook(symbol)
        return self.orderbooks[symbol]