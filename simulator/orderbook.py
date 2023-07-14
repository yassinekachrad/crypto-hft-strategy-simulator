class Orderbook:
    def __init__(self, symbol):
        self.symbol = symbol
        self.bids = dict()
        self.asks = dict()
        self.last_update_time = None
    
    def delta_update(self, bids, asks, timestamp):
        for price, size in bids:
            if size == 0 and price in self.bids:    
                del self.bids[price]
            else:
                self.bids[price] = size
        
        for price, size in asks:
            if size == 0 and price in self.asks:
                del self.asks[price]
            else:
                self.asks[price] = size
        
        self.last_update_time = timestamp
        self.best_ask = min(self.asks.keys())
        self.best_bid = max(self.bids.keys())
        self.spread = self.best_ask - self.best_bid

    def update(self, bids, asks, timestamp):
        self.bids = dict()
        self.asks = dict()
        for price, size in bids:
            if size == 0 and price in self.bids:    
                del self.bids[price]
            else:
                self.bids[price] = size
        
        for price, size in asks:
            if size == 0 and price in self.asks:
                del self.asks[price]
            else:
                self.asks[price] = size
        
        self.last_update_time = timestamp
        self.best_ask = min(self.asks.keys())
        self.best_bid = max(self.bids.keys())
        self.spread = self.best_ask - self.best_bid
    
    def imbalance(self):
        return (self.bids[self.best_bid] - self.asks[self.best_ask]) / (self.asks[self.best_ask] + self.bids[self.best_bid])
    
    def mid_price(self):
        return (self.best_ask + self.best_bid) / 2
    
    def fill_order(self, size: float) -> float: # returns average price of filled size
        raw_sum = 0
        if (size > 0):
            remaining_size = size
            while (remaining_size > 0):
                if (self.asks[self.best_ask] >= remaining_size):
                    raw_sum += self.best_ask * remaining_size
                    remaining_size = 0
                else:
                    raw_sum += self.best_ask * self.asks[self.best_ask]
                    remaining_size -= self.asks[self.best_ask]
                    del self.asks[self.best_ask]
                self.best_ask = min(self.asks.keys())
            return raw_sum / size
        elif (size < 0):
            remaining_size = -size
            while (remaining_size > 0):
                if (self.bids[self.best_bid] >= remaining_size):
                    raw_sum += self.best_bid * remaining_size
                    remaining_size = 0
                else:
                    raw_sum += self.best_bid * self.bids[self.best_bid]
                    remaining_size -= self.bids[self.best_bid]
                    del self.bids[self.best_bid]
                self.best_bid = max(self.bids.keys())
        else:
            return self.mid_price()
            

    
    def __str__(self) -> str:
        result = f"{self.symbol} (Spread: {self.spread:.2} - Imbalance: {self.imbalance():.3f})\n"
        for bidPrice, askPrice in zip(sorted(self.bids.keys(), reverse=True), sorted(self.asks.keys())):
            result += f"{bidPrice:10.2f} {self.bids[bidPrice]:10.4f} | {self.asks[askPrice]:10.4f} {askPrice:10.2f}\n"
        return result