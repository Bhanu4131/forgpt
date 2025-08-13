import json
import os

class StrategyState:
    FILE_PATH = "strategy_state.json"

    def __init__(self):
        self.in_trade = False
        self.entry = None
        self.sl = None
        self.target = None
        self.order_id = None
        self.sl_trailed = False

    def enter_trade(self, entry, sl, target, order_id):
        self.in_trade = True
        self.entry = entry
        self.sl = sl
        self.target = target
        self.order_id = order_id
        self.sl_trailed = False

    def reset(self):
        self.in_trade = False
        self.entry = None
        self.sl = None
        self.target = None
        self.order_id = None
        self.sl_trailed = False

    def save_to_file(self):
        data = {
            "in_trade": self.in_trade,
            "entry": self.entry,
            "sl": self.sl,
            "target": self.target,
            "order_id": self.order_id,
            "sl_trailed": self.sl_trailed
        }
        with open(self.FILE_PATH, "w") as f:
            json.dump(data, f)

    def load_from_file(self):
        if not os.path.exists(self.FILE_PATH):
            return
        with open(self.FILE_PATH, "r") as f:
            data = json.load(f)
        self.in_trade = data.get("in_trade", False)
        self.entry = data.get("entry")
        self.sl = data.get("sl")
        self.target = data.get("target")
        self.order_id = data.get("order_id")
        self.sl_trailed = data.get("sl_trailed", False)
    
    @classmethod
    def load(cls, filepath="strategy_state.json"):
        instance = cls()
        instance.FILE_PATH = filepath
        instance.load_from_file()
        return instance
