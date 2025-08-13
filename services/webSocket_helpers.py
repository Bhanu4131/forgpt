# services/webSocket_helpers.py
import time
import traceback
from threading import Thread
from config import (
    conn,
    symbol_token,
    strategy_state,
    state_lock,
    socket_lock,
    strategy_lock,
    strategy_thread,
    stop_strategy_event,
    SOCKET_RETRY_BASE,
    SOCKET_RETRY_MAX,
)
from pyoauthbridge.wsclient import get_ws_connection_status
from strategies.red_candle_live import run_red_candle_live


def start_socket_once():
    """Ensure WebSocket is running (thread-safe)."""
    with socket_lock:
        try:
            if get_ws_connection_status():
                return True
        except Exception:
            pass

        backoff = SOCKET_RETRY_BASE
        attempt = 0
        while True:
            attempt += 1
            try:
                print(f"[Socket] Attempting conn.run_socket() (attempt {attempt})...")
                ok = conn.run_socket()
                if ok:
                    print("[Socket] conn.run_socket() returned True — socket should be up.")
                    return True
                else:
                    print(f"[Socket] conn.run_socket() returned False. Backing off {backoff}s.")
            except Exception as e:
                print(f"[Socket] run_socket raised: {e}")
                traceback.print_exc()

            time.sleep(backoff)
            backoff = min(backoff * 2, SOCKET_RETRY_MAX)

            try:
                if get_ws_connection_status():
                    return True
            except Exception:
                pass


def _strategy_wrapper():
    try:
        print("[Strategy] Starting run_red_candle_live()")
        run_red_candle_live(conn, symbol_token, strategy_state, stop_strategy_event)
    except Exception:
        print("[Strategy] Strategy thread exited with exception:")
        traceback.print_exc()
    finally:
        print("[Strategy] Strategy thread finished/returned.")


def ensure_strategy_running():
    """Start strategy thread if not alive and socket is up."""
    global strategy_thread
    with strategy_lock:
        if strategy_thread is not None and strategy_thread.is_alive():
            print("[Strategy] Already running.")
            return True

        try:
            if not get_ws_connection_status():
                return False
        except Exception:
            return False

        stop_strategy_event.clear()
        strategy_thread = Thread(
            target=_strategy_wrapper,
            daemon=True
        )
        strategy_thread.start()
        print("[Monitor] Strategy thread started.")
        return True


def stop_strategy():
    """Stop strategy safely."""
    global strategy_thread
    print("[STOP] Stop request received — signalling strategy to exit.")
    stop_strategy_event.set()

    # Save current state for safety
    with state_lock:
        print(f"[STOP] Saving state before exit. In trade: {strategy_state.in_trade}")
        strategy_state.save_to_file()

    if strategy_thread is not None:
        strategy_thread.join(timeout=5)
        if strategy_thread.is_alive():
            print("[STOP] Strategy thread did not exit within timeout.")
        else:
            print("[STOP] Strategy stopped successfully.")
    else:
        print("[STOP] No active strategy thread.")


def monitor_websocket():
    """Keep socket alive and resubscribe as needed."""
    while True:
        try:
            if not get_ws_connection_status():
                print("[Monitor] WebSocket not up — attempting restart...")
                if conn.run_socket():
                    print("[Monitor] WebSocket restarted successfully.")
                    try:
                        conn.subscribe_compact_marketdata(symbol_token)
                        print("[Monitor] Resubscribed to symbol feed.")
                    except Exception as e:
                        print(f"[Monitor] Resubscribe error: {e}")
                else:
                    print("[Monitor] WebSocket restart failed.")
        except Exception as e:
            print(f"[Monitor] Status check error: {e}")
        time.sleep(5)


def register_routes(app, socketio):
    """Optional: WebSocket debug or control routes can be registered here if needed."""
    pass
