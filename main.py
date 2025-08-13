# main.py
import eventlet
eventlet.monkey_patch()  # MUST be first before any other imports

from flask import Flask
from flask_socketio import SocketIO
from threading import Thread

from services import dashboard_routes, webSocket_helpers
from config import symbol_token, conn
from services.webSocket_helpers import start_socket_once, ensure_strategy_running, monitor_websocket

# === Flask ===
app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"

# Attach SocketIO to app
socketio = SocketIO(app, async_mode="eventlet")

# Register dashboard routes
dashboard_routes.register_routes(app, socketio)
webSocket_helpers.register_routes(app, socketio)  # currently pass, but can be extended

# ---------- Bootstrapping ----------
def start_everything():
    print("✅ Ensuring socket up…")
    start_socket_once()
    print("✅ Ensuring strategy running…")
    ensure_strategy_running()
    # Start a separate WS monitor (reconnect + resubscribe)
    Thread(target=monitor_websocket, daemon=True).start()

if __name__ == "__main__":
    start_everything()
    socketio.run(app, host="0.0.0.0", port=5000)
