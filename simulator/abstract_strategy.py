import uuid

from .exchange_handler import ExchangeHandler
from .orderbook import Orderbook

# (start_ts, end_ts, interval, open, high, low, close, volume, turnover)
Candle = tuple[str, str, str, float, float, float, float, float, float]
# (price, size, side, symbol, exchange, order_id, time_in_force, order_status, order_type)
Order = tuple[float, float, str, str, str, str, str, str, str]
Position = tuple[float, float, str, str]  # (size, avg_price, symbol, exchange)


class AbstractStrategy:
    def __init__(self, exchange_handlers: dict[str, ExchangeHandler], simulation: bool = True, initial_balance: float = 100):
        self.exchange_handlers = exchange_handlers
        self.simulation = simulation
        if simulation:
            self.balance: dict[str, float] = dict()  # exchange -> balance
            for exchange in self.exchange_handlers:
                self.balance[exchange] = initial_balance
            self._limit_orders: dict[str, dict[str, dict[str, Order]]] = dict()  # exchange -> symbol -> order_id -> Order

            # exchange -> symbol -> Position
            self.positions: dict[str, dict[str, Position]] = dict()

            # exchange -> symbol -> order_id -> Order
            self.orders: dict[str, dict[str, dict[str, Order]]] = dict()

    def start(self):
        for exchange_handler in self.exchange_handlers.values():
            exchange_handler.start(self)
        self._on_ready()

    # public (i.e. user-defined) callbacks

    def on_ready(self): pass

    def on_orderbook_update(self, symbol: str, exchange: ExchangeHandler,
                            orderbook: Orderbook, timestamp: int): pass

    def on_trade(self, symbol: str, exchange: ExchangeHandler,
                 side: str, price: float, size: float, timestamp: int): pass

    def on_candle_update(self, symbol: str, exchange: ExchangeHandler,
                         candle: Candle, timestamp: int): pass

    def on_liquidation(self, symbol: str, exchange: ExchangeHandler,
                       side: str, price: float, size: float, timestamp: int): pass

    def on_order_filled(self, symbol: str, exchange: ExchangeHandler,
                        order: Order, timestamp: int): pass
    
    def on_position_change(self, symbol: str, exchange: ExchangeHandler,
                            position: Position, timestamp: int): pass
    
    def on_balance_change(self, exchange: ExchangeHandler,
                            balance: float, timestamp: int): pass


    # private callbacks that call "public" (i.e. user-defined) callbacks
    def _on_ready(self):
        self.on_ready()

    def _on_orderbook_update(self, symbol: str, exchange: ExchangeHandler, orderbook: Orderbook, timestamp: int):
        # check if any limit orders has been filled
        if self.simulation:
            if exchange.name in self._limit_orders and symbol in self._limit_orders[exchange.name]:
                for order_id in self._limit_orders[exchange.name][symbol]:
                    order = self._limit_orders[exchange.name][symbol][order_id]
                    # check if order's price has been crossed
                    if order[2] == "Buy" and order[0] > orderbook.best_bid:
                        # order is filled
                        self.balance[exchange.name] -= order[1] * order[0]
                        if symbol not in self.positions[exchange.name]:
                            self.positions[exchange.name][symbol] = (
                                order[1], order[0], symbol, exchange.name)
                        else:
                            position = self.positions[exchange.name][symbol]
                            new_size = position[0] + order[1]
                            new_avg_price = (
                                (position[0] * position[1]) + (order[1] * order[0])) / new_size
                            self.positions[exchange.name][symbol] = (
                                new_size, new_avg_price, symbol, exchange.name)

                        del self._limit_orders[exchange.name][symbol][order_id]
                        self.orders[exchange.name][symbol][order_id][7] = "Filled"
                        self.on_order_filled(symbol, exchange, order, timestamp)
                    elif order[2] == "Sell" and order[0] < orderbook.best_ask:
                        # order is filled
                        self.balance[exchange.name] += order[1] * order[0]
                        if symbol not in self.positions[exchange.name]:
                            self.positions[exchange.name][symbol] = (
                                -order[1], order[0], symbol, exchange.name)
                        else:
                            position = self.positions[exchange.name][symbol]
                            new_size = position[0] - order[1]
                            new_avg_price = (
                                (position[0] * position[1]) - (order[1] * order[0])) / new_size
                            self.positions[exchange.name][symbol] = (
                                new_size, new_avg_price, symbol, exchange.name)

                        del self._limit_orders[exchange.name][symbol][order_id]
                        self.orders[exchange.name][symbol][order_id][7] = "Filled"
                        self.on_order_filled(symbol, exchange, order, timestamp)

        self.on_orderbook_update(symbol, exchange, orderbook, timestamp)

    def _on_trade(self, symbol: str, exchange: ExchangeHandler, side: str, price: float, size: float, timestamp: int):
        self.on_trade(symbol, exchange, side, price, size, timestamp)

    def _on_candle_update(self, symbol: str, exchange: ExchangeHandler, candle: Candle, timestamp: int):
        self.on_candle_update(symbol, exchange, candle, timestamp)

    def _on_liquidation(self, symbol: str, exchange: ExchangeHandler, side: str, price: float, size: float, timestamp: int):
        self.on_liquidation(symbol, exchange, side, price, size, timestamp)

    # action methods

    def market_order(self, symbol: str, exchange: str, side: str, size: float, reduce_only: bool = False, time_in_force: str = "GTC"):
        if self.simulation:
            if side == "Buy":
                if reduce_only and exchange in self.positions and symbol in self.positions[exchange] and self.positions[exchange][symbol] > 0:
                    return None
                elif reduce_only and exchange in self.positions and symbol in self.positions[exchange] and self.positions[exchange][symbol] < 0 and self.positions[exchange][symbol] > -size:
                    # ensures that the order will reduce the position to 0
                    size = -self.positions[exchange][symbol]

                if self.balance >= size:
                    self.balance[exchange] -= size
                    fill_price = self.exchange_handlers[exchange].orderbook(
                        symbol).fill_order(size=size)
                    if symbol not in self.positions[exchange]:
                        self.positions[exchange][symbol] = (
                            size, fill_price, symbol, exchange)
                    else:
                        position = self.positions[exchange][symbol]
                        new_size = position[0] + size
                        new_avg_price = (
                            (position[0] * position[1]) + (size * fill_price)) / new_size
                        self.positions[exchange][symbol] = (
                            new_size, new_avg_price, symbol, exchange)

                    order = (fill_price, size, side, symbol, exchange, str(
                        uuid.uuid4()), time_in_force, "Filled", "Market")
                    return order
                else:
                    return None  # None indicates order could not be filled
            elif side == "Sell":
                # position can be negative if shorting
                if reduce_only and exchange in self.positions and symbol in self.positions[exchange] and self.positions[exchange][symbol] < 0:
                    return None
                elif reduce_only and exchange in self.positions and symbol in self.positions[exchange] and self.positions[exchange][symbol] > 0 and self.positions[exchange][symbol] < size:
                    size = self.positions[exchange][symbol]

                if self.balance >= size:
                    self.balance[exchange] += size
                    fill_price = self.exchange_handlers[exchange].orderbook(
                        symbol).fill_order(size=-size)
                    if symbol not in self.positions[exchange]:
                        self.positions[exchange][symbol] = (
                            -size, fill_price, symbol, exchange)
                    else:
                        position = self.positions[exchange][symbol]
                        new_size = position[0] - size
                        new_avg_price = (
                            (position[0] * position[1]) + (size * fill_price)) / new_size
                        self.positions[exchange][symbol] = (
                            new_size, new_avg_price, symbol, exchange)

                    order = (fill_price, size, side, symbol, exchange, str(
                        uuid.uuid4()), time_in_force, "Filled", "Market")
                    return order
        else:
            pass

    def limit_order(self, symbol: str, exchange: str, side: str, size: float, price: float, post_only: bool = False, reduce_only: bool = False, time_in_force: str = "GTC"):
        if self.simulation:
            # see if the order can be filled immediately
            # we do a little simplification here by assuming the market order will be filled at a better (or equal) price than the limit order's
            if side == "Buy" and price >= self.exchange_handlers[exchange].orderbook(symbol).best_ask and not post_only:
                return self.market_order(symbol, exchange, side, size, reduce_only, time_in_force)
            elif side == "Sell" and price <= self.exchange_handlers[exchange].orderbook(symbol).best_bid and not post_only:
                return self.market_order(symbol, exchange, side, size, reduce_only, time_in_force)
            else:
                order = (price, size, side, symbol, exchange, str(uuid.uuid4()), time_in_force, "New", "Limit")
                self._limit_orders[exchange][symbol].append(order)
                self.orders[exchange][symbol][order[5]] = order
                return order
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
