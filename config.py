# config.py
from threading import Lock, Event
from pyoauthbridge import Connect
from utils.strategy_state import StrategyState

# === SAS API Credentials ===
CLIENT_ID = "SAS-CLIENT1"
CLIENT_SECRET = "Hhtg74iYYZY1nSJUvDBxKntGqfigem6yKyYw9rlb2qSXyhEEs8BZEtw27KsIE1UI"
REDIRECT_URL = "http://127.0.0.1:65015"
BASE_URL = "https://api.stocko.in"
ACCESS_TOKEN = "IU-u3gLeh4fh4dQbsQ9nzZxI-X6u9gPGMczoSeiblZA.yDdTfo-9GXYQnBcjr--ucyAiT_6S69pwIaUXCzHJiJs"  # <-- put your live token here

# === Connect ===
conn = Connect(CLIENT_ID, CLIENT_SECRET, REDIRECT_URL, BASE_URL)
conn.set_access_token(ACCESS_TOKEN)

# === Symbol to trade ===
symbol_token = {'exchangeCode': 2, 'instrumentToken': 47100}  # Example: NIFTY

# === Strategy state ===
strategy_state = StrategyState.load("strategy_state.json")

# === Locks & Flags (shared across modules) ===
socket_lock = Lock()
strategy_lock = Lock()
state_lock = Lock()
stop_strategy_event = Event()

# === Strategy thread reference ===
strategy_thread = None

# === Monitor config ===
SOCKET_RETRY_BASE = 1.0
SOCKET_RETRY_MAX = 30.0
CHECK_INTERVAL = 5.0

