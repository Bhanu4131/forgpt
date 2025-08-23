from flask import Flask
from pyoauthbridge import Connect
import webbrowser
from threading import Thread 
import time
import json

app = Flask(__name__)

# --- SAS API Credentials ---
client_id = "SAS-CLIENT1"
client_secret = "Hhtg74iYYZY1nSJUvDBxKntGqfigem6yKyYw9rlb2qSXyhEEs8BZEtw27KsIE1UI"
redirect_url = "http://127.0.0.1:65015"
base_url = "https://api.stocko.in"

conn = Connect(client_id, client_secret, redirect_url, base_url)

access_token = conn.get_access_token()

print(access_token)

