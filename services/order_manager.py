import time

def place_order(client, symbol_token, qty,):
    order_payload = {
        "exchange": "NFO",  # or "NSE" for stocks
        "instrument_token": symbol_token["instrumentToken"],
        "client_id": "BS193",  # assuming your client object has this
        "order_type": "MARKET",       # "MARKET" or "LIMIT"
        "amo": "false",
        "price": 0,
        "quantity": qty,
        "disclosed_quantity": 0,
        "validity": "DAY",
        "product": "NRML",
        "order_side": "SELL",  # "BUY" or "SELL"
        "device": "api",
        "user_order_id": int(str(int(time.time()))[-5:]),
        "trigger_price": 0,
        "execution_type": "REGULAR"
    }

    try:
        response = client.place_order(order_payload)
        print(f"✅ Order Placed: {response}")
        return response.get("order_id", "UNKNOWN")
    except Exception as e:
        print(f"❌ Order Error: {e}")
        return None


def exit_trade(client, symbol_token, qty, reason="EXIT"):
    print(f"⚠️ Exiting trade due to: {reason}")

    order_payload = {
        "exchange": "NFO",
        "instrument_token": symbol_token["instrumentToken"],
        "client_id": "BS193",
        "order_type": "MARKET",
        "amo": "false",
        "price": 0,
        "quantity": qty,
        "disclosed_quantity": 0,
        "validity": "DAY",
        "product": "NRML",
        "order_side": "BUY",  # Assuming you're exiting a SELL trade. Flip if opposite.
        "device": "api",
        "user_order_id": int(str(int(time.time()))[-5:]),
        "trigger_price": 0,
        "execution_type": "REGULAR"
    }

    try:
        response = client.place_order(order_payload)
        print(f"✅ Exit Order Placed: {response}")
        return response.get("order_id", "UNKNOWN")
    except Exception as e:
        print(f"❌ Exit Order Error: {e}")
        return None
