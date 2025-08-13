import csv
import os
from datetime import datetime
from scipy.stats import linregress
from services.strategy_state import StrategyState
from services.helpers import CandleAggregator
from services.order_manager import place_order, exit_trade

def run_red_candle_live(conn, symbol_token, strategy_state, stop_strategy_event):
    print(f"🚀 Starting Red Candle Live Strategy on Token: {symbol_token}")

    symbol_name = "NIFTY"  # adjust for your symbol if needed
    candles_file = f"candles_{symbol_name}.csv"

    # Load historical candles if file exists
    candles = []
    if os.path.exists(candles_file):
        with open(candles_file, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                candles.append({
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "start_time": row["start_time"],
                })
        print(f"✅ Loaded {len(candles)} candles from {candles_file}")

    # Candle aggregator for live ticks
    aggregator = CandleAggregator(symbol_token)
    
    # Subscribe to tick stream
    conn.subscribe_compact_marketdata(symbol_token)

    # If in trade, resume with saved state
    if strategy_state.in_trade:
        print(f"🔄 Resuming trade from state: Entry={strategy_state.entry}, SL={strategy_state.sl}, Target={strategy_state.target}")

    # Main tick loop
    while True:
        # 🔹 Instant stop check before reading any tick
        if stop_strategy_event.is_set():
            print("[STOP] Strategy stop signal detected — exiting immediately.")
            break

        tick = conn.read_compact_marketdata()
        if not tick:
            continue

        # 🔹 Stop check again right after receiving tick
        if stop_strategy_event.is_set():
            print("[STOP] Strategy stop signal detected after tick read — exiting.")
            break

        # Update candle aggregator
        aggregator.update(tick)

        # If new candle is formed
        if aggregator.is_new_candle():
            candle = aggregator.finalize_candle()
            if not candle:
                continue

            # Save to CSV for persistence
            candles.append(candle)
            with open(candles_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["open", "high", "low", "close", "start_time"])
                writer.writeheader()
                writer.writerows(candles)

            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] New Candle: {candle}")

            # --- Compute previous high ---
            if len(candles) >= 20:
                high_20_prev = max(c["high"] for c in candles[-20:])
            else:
                high_20_prev = None

            last = candles[-1]

            candle_near_high = (
                high_20_prev is not None and 
                high_20_prev * 0.95 <= last["high"] <= high_20_prev * 1.02
            )
            is_red = last["close"] < last["open"]

            if candle_near_high:
                hypothetical_entry = last["close"]
                hypothetical_sl = last["high"] * 1.01
                hypothetical_risk = hypothetical_sl - hypothetical_entry
                hypothetical_target = hypothetical_entry - 1.3 * hypothetical_risk
                print(f"[DEBUG] candle_near_high={candle_near_high} | "
                      f"allowed_range=({high_20_prev * 0.95 if high_20_prev else None}, "
                      f"{high_20_prev * 1.03 if high_20_prev else None}), "
                      f"last_high={last['high']} | high_20_prev={high_20_prev} | "
                      f"entry={hypothetical_entry} | sl={hypothetical_sl} | target={hypothetical_target}")

            # --- Stop check before placing order ---
            if stop_strategy_event.is_set():
                print("[STOP] Strategy stop signal detected before entry check — exiting.")
                break

            # Entry logic
            if not strategy_state.in_trade and candle_near_high and is_red:
                entry = last["close"]
                sl = last["high"] * 1.01
                risk = sl - entry
                target = entry - 1.3 * risk

                order_id = place_order(conn, symbol_token, qty=75)
                strategy_state.enter_trade(entry, sl, target, order_id)
                strategy_state.save_to_file()

                print(f"[ENTRY] Time: {candle['start_time']} | Entry: {entry} | SL: {sl:.2f} | Target: {target:.2f}")

            # Trade management
            elif strategy_state.in_trade:
                ltp = last["close"]

                # Stop-loss hit
                if ltp >= strategy_state.sl:
                    print(f"[STOP-LOSS HIT] LTP={ltp} >= SL={strategy_state.sl}")
                    exit_trade(conn, symbol_token, qty=75, reason="SL hit")
                    strategy_state.reset()
                    strategy_state.save_to_file()

                # Target hit
                elif ltp <= strategy_state.target:
                    print(f"[TARGET HIT] LTP={ltp} <= Target={strategy_state.target}")
                    exit_trade(conn, symbol_token, qty=75, reason="Target hit")
                    strategy_state.reset()
                    strategy_state.save_to_file()

    print("[STOP] Strategy loop exited cleanly.")
