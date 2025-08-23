import time
from datetime import datetime

from services.helpers import CandleAggregator
from services.order_manager import place_order, exit_trade
from services.strategy_state import StrategyState

def run_red_candle_live(client, symbol_token, strategy_state, stop_strategy_event):
    print(f"🚀 Starting Red Candle Live Strategy on Token: {symbol_token}")
    
    aggregator = CandleAggregator(symbol="NIFTY", interval=60)
    state = strategy_state
    candles = aggregator.candles

    print(f"✅ Loaded {len(candles)} historical candles")

    def on_tick(tick):
        aggregator.update(tick)
        
        if aggregator.is_new_candle():
            candle = aggregator.finalize_candle()
            if not candle:
                return

            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] New Candle: {candle}")

            candles.append(candle)  # ✅ Append first

            # --- Compute previous high before adding the latest candle ---
            if len(candles) >= 20:
                high_20_prev = max(c["high"] for c in candles[-20:])
                print(high_20_prev)
            else:
                high_20_prev = None

            if len(candles) < 20:
                return

            last = candles[-1]

            # --- Trend detection ---
            """trend_window = [c["close"] for c in candles[-5:]]
            slope = linregress(range(5), trend_window).slope
            is_uptrend = slope > 0.1"""

            # --- Candle conditions ---
            candle_near_high = (
                high_20_prev is not None and 
                high_20_prev * 0.97 <= last["high"] <= high_20_prev * 1.02 and
                last["close"] >= high_20_prev * 0.97  # Close also within 3% of high_20_prev
            )
            is_red = last["close"] < last["open"]

            # --- Debug: print what strategy is "looking at" ---
            if candle_near_high:
                hypothetical_entry = last["close"]
                hypothetical_sl = high_20_prev * 1.01
                hypothetical_risk = hypothetical_sl - hypothetical_entry
                hypothetical_target = hypothetical_entry - 1.5 * hypothetical_risk
                print(f"[DEBUG] candle_near_high={candle_near_high} | "
                    f"allowed_range=({high_20_prev * 0.97 if high_20_prev else None}, "
                    f"{high_20_prev * 1.03 if high_20_prev else None}), "
                    f"last_high={last['high']} | high_20_prev={high_20_prev} | "
                    f"entry={hypothetical_entry} | sl={hypothetical_sl} | target={hypothetical_target}")

            # --- Entry condition ---
            if not state.in_trade and candle_near_high and is_red:
                entry = last["close"]
                sl = high_20_prev * 1.01  # SL just above high
                risk = sl - entry
                target = entry - 1.5 * risk  # Short position target

                order_id = place_order(client, symbol_token, qty=75)
                state.enter_trade(entry, sl, target, order_id)
                state.save_to_file()

                print(f"[ENTRY] Time: {candle['start_time']} | Entry: {entry} | SL: {sl:.2f} | Target: {target:.2f}")

        # --- Exit logic ---
        if state.in_trade:
            ltp = tick.get("last_traded_price") / 100  # Convert from integer paise to rupees

            # SL trail for shorts
            if not state.sl_trailed and ltp <= state.entry * 0.95:
                state.sl = state.entry
                state.sl_trailed = True
                state.save_to_file()
                print(f"[TRAIL] SL moved to entry at LTP: {ltp:.2f}")

            # Stop Loss hit (short trade => SL is ABOVE entry)
            if ltp >= state.sl:
                exit_trade(client, symbol_token, qty=75, reason="SL")
                print(f"[EXIT] SL Hit at LTP: {ltp:.2f}")
                state.reset()
                state.save_to_file()

            # Target hit
            elif ltp <= state.target:
                exit_trade(client, symbol_token, qty=75, reason="Target")
                print(f"[EXIT] Target Hit at LTP: {ltp:.2f}")
                state.reset()
                state.save_to_file()

    # --- Subscribe to tick stream ---
    client.subscribe_compact_marketdata(symbol_token)

    while not stop_strategy_event.is_set():
        tick = client.read_compact_marketdata()
        if tick:
            on_tick(tick)
        time.sleep(1)

    print("🛑 Strategy stopped.")
