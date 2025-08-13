import time
import datetime
import json
import csv
import os


class CandleAggregator:
    def __init__(self, symbol: str, interval: int = 60):
        self.symbol = symbol
        self.interval = interval  # seconds
        self.current_candle = None
        self.last_candle_time = None
        self.finalized = None
        self.candles = self.load_candles_from_csv(symbol="NIFTY", limit=30)

    def update(self, tick):
        ltp = (tick.get("last_traded_price") or tick.get("ltp") or 0) / 100
        if ltp is None or ltp == 0:
            return

        now = datetime.datetime.now().replace(second=0, microsecond=0)

        # Start a new candle if none exists
        if self.current_candle is None:
            self.current_candle = {
                "open": ltp,
                "high": ltp,
                "low": ltp,
                "close": ltp,
                "start_time": now.isoformat()
            }
        else:
            self.current_candle["high"] = max(self.current_candle["high"], ltp)
            self.current_candle["low"] = min(self.current_candle["low"], ltp)
            self.current_candle["close"] = ltp

        self.finalized = False

    def is_new_candle(self):
        now = datetime.datetime.now().replace(second=0, microsecond=0)
        if self.current_candle is None:
            return False
        current_start = datetime.datetime.fromisoformat(self.current_candle["start_time"])
        if current_start != now:
            self.finalized = True
            return True
        return False

    def finalize_candle(self):
        if not self.current_candle:
            return None

        if self.current_candle["high"] == 0:
            print("⚠️ Skipping empty candle.")
            return None

        candle = self.current_candle
        self.candles.append(candle)

        # Keep only the last 1 day's candles (e.g., 400 candles max for safety)
        self.candles = self.candles[-60:]

        # Save updated candle list to file
        self.save_candles_to_csv("NIFTY", candle)

        self.current_candle = None
        return candle   


    def save_candles_to_csv(self, symbol, candle):
        """
        Append a single candle to CSV. Writes header if file doesn't exist.
        """
        filename = f"candles_{symbol}.csv"
        fieldnames = ["start_time", "open", "high", "low", "close"]

        # Append mode — no rewrites
        file_exists = os.path.isfile(filename) and os.path.getsize(filename) > 0

        try:
            with open(filename, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(candle)
        except PermissionError:
            print(f"⚠ Cannot write {filename} — is it open in Excel?")
        except Exception as e:
            print(f"❌ Error writing candle to {filename}: {e}")

    def load_candles_from_csv(self, symbol, limit=None):
        """
        Loads last `limit` candles from CSV safely:
        - Skips corrupted rows
        - Skips duplicate headers
        """
        filename = f"candles_{symbol}.csv"
        candles = []

        if not os.path.exists(filename):
            print(f"⚠ No CSV found for {symbol}")
            return candles

        try:
            with open(filename, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Skip any accidental header rows
                    if row["start_time"] == "start_time":
                        continue
                    try:
                        candles.append({
                            "start_time": row["start_time"],
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                        })
                    except (ValueError, KeyError) as e:
                        print(f"⚠ Skipping bad row in {filename}: {row} ({e})")
                        continue

            # Keep only last N if limit is set
            if limit:
                candles = candles[-limit:]

            print(f"✅ Loaded {len(candles)} candles from {filename}")
        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")

        return candles



    """def save_candles_to_file(self):
        filename = f"candles_{self.symbol}.json"
        with open(filename, "w") as f:
            json.dump(self.candles, f, indent=2)

    def load_candles_from_file(self):
        filename = f"candles_{self.symbol}.json"
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return json.load(f)
        return []"""
