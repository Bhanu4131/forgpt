from flask import Flask, request, redirect
from requests_oauthlib import OAuth2Session
import webbrowser
import os, json


CLIENT_ID = 'SAS-CLIENT1'
CLIENT_SECRET = 'Hhtg74iYYZY1nSJUvDBxKntGqfigem6yKyYw9rlb2qSXyhEEs8BZEtw27KsIE1UI'
REDIRECT_URI = 'http://127.0.0.1:65015/'
BASE_URL = 'https://api.stocko.in'

AUTH_URL = f'{BASE_URL}/oauth2/auth'
TOKEN_URL = f'{BASE_URL}/oauth2/token'

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
app = Flask(__name__)

@app.route('/getcode')
def getcode():
    oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope='orders holdings')
    auth_url, _ = oauth.authorization_url(AUTH_URL)
    print(f"Visit: {auth_url}")
    return redirect(auth_url)

@app.route('/')
def callback():
    oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope='orders holdings')
    token = oauth.fetch_token(TOKEN_URL, authorization_response=request.url, client_secret=CLIENT_SECRET)
    with open("token.json", "w") as f:
        json.dump(token, f)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if shutdown: shutdown()
    return "Token saved to token.json"

if __name__ == "__main__":
    url = "http://127.0.0.1:65015/getcode"
    print("Open this URL in your browser to start OAuth flow:")
    print(url + "\n")
    webbrowser.open(url)
    app.run(port=65015)

