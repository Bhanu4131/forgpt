from flask import render_template, request, jsonify
from config import state_lock, strategy_state
import services.webSocket_helpers as ws_helpers  # so we can start/stop strategies


def register_routes(app, socketio):
    @app.route("/")
    def dashboard():
        with state_lock:
            return render_template("dashboard.html", state=strategy_state)

    @app.route("/state")
    def api_state():
        from pyoauthbridge.wsclient import get_ws_connection_status
        try:
            socket_up = bool(get_ws_connection_status())
        except Exception:
            socket_up = False

        with state_lock:
            s = {
                "in_trade": strategy_state.in_trade,
                "entry": strategy_state.entry,
                "sl": strategy_state.sl,
                "target": strategy_state.target,
                "order_id": strategy_state.order_id,
                "sl_trailed": strategy_state.sl_trailed,
                "socket_up": socket_up,
            }
        return jsonify(s)

    @app.route("/update", methods=["POST"])
    def api_update():
        data = request.get_json(force=True, silent=True) or {}
        msgs = []

        with state_lock:
            if "trail_to_entry" in data and data["trail_to_entry"]:
                if strategy_state.entry is not None:
                    strategy_state.sl = strategy_state.entry
                    strategy_state.sl_trailed = True
                    msgs.append(f"SL trailed to entry ({strategy_state.entry}).")
                else:
                    msgs.append("No entry price to trail to.")

            if "sl" in data and data["sl"] is not None:
                try:
                    strategy_state.sl = float(data["sl"])
                    strategy_state.sl_trailed = True
                    msgs.append(f"SL set to {strategy_state.sl}.")
                except ValueError:
                    return jsonify({"error": "Invalid SL"}), 400

            if "target" in data and data["target"] is not None:
                try:
                    strategy_state.target = float(data["target"])
                    msgs.append(f"Target set to {strategy_state.target}.")
                except ValueError:
                    return jsonify({"error": "Invalid target"}), 400

            strategy_state.save_to_file()

        return jsonify({"message": " ".join(msgs) if msgs else "No changes."})

    @app.route("/exit", methods=["POST"])
    def api_exit():
        from services.order_manager import exit_trade
        with state_lock:
            if not strategy_state.in_trade:
                return jsonify({"message": "Not in a trade."})
            try:
                exit_trade(ws_helpers.conn, ws_helpers.symbol_token, qty=75, reason="Manual exit from dashboard")
                strategy_state.reset()
                strategy_state.save_to_file()
                return jsonify({"message": "Trade exited & state reset."})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

    # 🔹 Start Strategy Route
    @app.route("/start_strategy", methods=["POST"])
    def start_strategy_route():
        try:
            ws_helpers.ensure_strategy_running()
            return jsonify({"message": "Strategy started."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # 🔹 Stop Strategy Route
    @app.route("/stop_strategy", methods=["POST"])
    def stop_strategy_route():
        try:
            ws_helpers.stop_strategy_event.set()
            return jsonify({"message": "Strategy stopped."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
