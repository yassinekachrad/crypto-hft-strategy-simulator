import uuid

from .exchange_handler import ExchangeHandler
from .orderbook import Orderbook

Order = tuple[float, float, str, str, str, str, str, str, str] # (price, size, side, symbol, exchange, order_id, time_in_force, order_status, order_type) 
Position = tuple[float, float, str, str] # (size, avg_price, symbol, exchange)

class AbstractStrategy:
    def __init__(self, exchange_handlers: dict[str, ExchangeHandler], simulation: bool = True, initial_balance: float = 100):
        self.exchange_handlers = exchange_handlers
        self.simulation = simulation
        if simulation:
            self.balance: dict[str, float] = dict() # exchange -> balance 
            for exchange in self.exchange_handlers:
                self.balance[exchange] = initial_balance
            
            # exchange -> symbol -> Position
            self.positions: dict[str, dict[str, Position]] = dict()

            # exchange -> symbol -> order_id -> Order
            self.orders: dict[str, dict[str, dict[str, Order]]] = dict()

    def start(self):
        for exchange_handler in self.exchange_handlers.values():
            exchange_handler.start(self)
        self.on_ready()

    def on_ready(self):
        pass

    def on_orderbook_update(self, symbol: str, exchange: ExchangeHandler, orderbook: Orderbook, timestamp: int):
        pass

    def on_trade(self, symbol: str, exchange: ExchangeHandler, side: str, price: float, size: float, timestamp: int):
        pass

    def on_candle_update(self, symbol: str, exchange: ExchangeHandler, candle: tuple[str, str, str, float, float, float, float, float, float], timestamp: int):
        pass

    def on_liquidation(self, symbol: str, exchange: ExchangeHandler, side: str, price: float, size: float, timestamp: int):
        pass

    # still need to add "private" callbacks (e.g. on_order_update, on_position_update, etc.)

    # action methods

    def market_order(self, symbol: str, exchange: str, side: str, size: float, reduce_only: bool = False, time_in_force: str = "GTC"):
        if self.simulation:
            if side == "Buy":
                if reduce_only and exchange in self.positions and symbol in self.positions[exchange] and self.positions[exchange][symbol] > 0:
                    return None
                elif reduce_only and exchange in self.positions and symbol in self.positions[exchange] and self.positions[exchange][symbol] < 0 and self.positions[exchange][symbol] > -size:
                    size = -self.positions[exchange][symbol] # ensures that the order will reduce the position to 0
                    
                if self.balance >= size:
                    self.balance[exchange] -= size
                    fill_price = self.exchange_handlers[exchange].orderbook(symbol).fill_order(size=size)
                    if symbol not in self.positions[exchange]:
                        self.positions[exchange][symbol] = (size, fill_price, symbol, exchange)
                    else:
                        position = self.positions[exchange][symbol]
                        new_size = position[0] + size
                        new_avg_price = ((position[0] * position[1]) + (size * fill_price)) / new_size
                        self.positions[exchange][symbol] = (new_size, new_avg_price, symbol, exchange)
                    
                    order = (fill_price, size, side, symbol, exchange, str(uuid.uuid4()), time_in_force, "Filled", "Market")
                    return order
                else:
                    return None # None indicates order could not be filled 
            elif side == "Sell":
                # position can be negative if shorting
                if reduce_only and exchange in self.positions and symbol in self.positions[exchange] and self.positions[exchange][symbol] < 0:
                    return None
                elif reduce_only and exchange in self.positions and symbol in self.positions[exchange] and self.positions[exchange][symbol] > 0 and self.positions[exchange][symbol] < size:
                    size = self.positions[exchange][symbol]
                
                if self.balance >= size:
                    self.balance[exchange] += size
                    fill_price = self.exchange_handlers[exchange].orderbook(symbol).fill_order(size=-size)
                    if symbol not in self.positions[exchange]:
                        self.positions[exchange][symbol] = (-size, fill_price, symbol, exchange)
                    else:
                        position = self.positions[exchange][symbol]
                        new_size = position[0] - size
                        new_avg_price = ((position[0] * position[1]) + (size * fill_price)) / new_size
                        self.positions[exchange][symbol] = (new_size, new_avg_price, symbol, exchange)
                    
                    order = (fill_price, size, side, symbol, exchange, str(uuid.uuid4()), time_in_force, "Filled", "Market")
                    return order
        else:
            pass

    def limit_order(self, symbol: str, exchange: str, side: str, size: float, price: float, post_only: bool = False, reduce_only: bool = False, time_in_force: str = "GTC"):
        if self.simulation:
            # for this to work, we will need a callback system to detect when the order would have been filled
            pass
        else:
            pass

    def cancel_order(self, symbol: str, exchange: str, order_id: str):
        if self.simulation:
            pass
        else:
            pass

    def cancel_all_orders(self, symbol: str, exchange: str):
        if self.simulation:
            pass
        else:
            pass

    def get_order(self, symbol: str, exchange: str, order_id: str):
        if self.simulation:
            return self.orders[exchange][symbol][order_id]
        else:
            pass

    def get_orders(self, symbol: str, exchange: str) -> list[tuple[str, str, str, str, float, float]]:
        if self.simulation:
            return list(self.orders[exchange][symbol].values())
        else:
            pass

    def get_position(self, symbol: str, exchange: str):
        if self.simulation:
            return self.positions[exchange][symbol]
        else:
            pass

    def get_positions(self, exchange: str):
        if self.simulation:
            return list(self.positions[exchange].values())
        else:
            pass

    def get_equity(self, exchange: str):
        if self.simulation:
            return self.balance[exchange] + sum([position[0] * position[1] for position in self.positions[exchange].values()])
        else:
            pass
    
    def get_balance(self, exchange: str):
        if self.simulation:
            return self.balance[exchange]
        else:
            pass