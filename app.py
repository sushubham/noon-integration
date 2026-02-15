import os
import time
import uuid
import jwt
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# -------------------------------
# ENV VARIABLES (Render)
# -------------------------------
NOON_KEY_ID = os.getenv("NOON_KEY_ID")
NOON_PRIVATE_KEY = os.getenv("NOON_PRIVATE_KEY")
NOON_PROJECT_CODE = os.getenv("NOON_PROJECT_CODE")

if not NOON_KEY_ID or not NOON_PRIVATE_KEY or not NOON_PROJECT_CODE:
    raise Exception("Missing required environment variables.")

# Fix multiline private key
PRIVATE_KEY = NOON_PRIVATE_KEY.replace("\\n", "\n")

# -------------------------------
# SESSION CACHE
# -------------------------------
SESSION = None
SESSION_CREATED_AT = 0
SESSION_TTL = 50 * 60  # 50 minutes


# -------------------------------
# JWT CREATION
# -------------------------------
def create_jwt():
    payload = {
        "sub": NOON_KEY_ID,
        "iat": int(time.time()),
        "jti": str(uuid.uuid4())
    }

    token = jwt.encode(
        payload,
        PRIVATE_KEY,
        algorithm="RS256"
    )

    return token


# -------------------------------
# SMART SESSION LOGIN
# -------------------------------
def get_session():
    global SESSION, SESSION_CREATED_AT
    if SESSION and (time.time() - SESSION_CREATED_AT) < SESSION_TTL:
        return SESSION

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Zoho-Noon-Integration/1.0",
        "Content-Type": "application/json"
    })

    login_payload = {
        "token": create_jwt(),
        "default_project_code": NOON_PROJECT_CODE
    }

    resp = session.post(
        "https://noon-api-gateway.noon.partners/identity/public/v1/api/login",
        json=login_payload
    )

    if resp.status_code != 200:
        raise Exception(f"Login failed: {resp.text}")

    SESSION = session
    SESSION_CREATED_AT = time.time()

    return SESSION


# -------------------------------
# HEALTH CHECK
# -------------------------------
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "Noon JWT Service Running"})


# -------------------------------
# LOGIN TEST
# -------------------------------
@app.route("/login", methods=["GET"])
def login_test():
    session = get_session()

    whoami = session.get(
        "https://noon-api-gateway.noon.partners/identity/v1/whoami"
    )

    return jsonify(whoami.json()), whoami.status_code


# -------------------------------
# STOCK LIST
# -------------------------------
@app.route("/stock-list", methods=["POST"])
def stock_list():
    payload = request.json
    session = get_session()

    response = session.post(
        "https://noon-api-gateway.noon.partners/stock/v1/stock-list",
        json=payload
    )

    return jsonify(response.json()), response.status_code


# -------------------------------
# STOCK UPDATE
# -------------------------------
@app.route("/stock-update", methods=["POST"])
def stock_update():
    payload = request.json
    session = get_session()

    response = session.post(
        "https://noon-api-gateway.noon.partners/stock/v1/stock-update",
        json=payload
    )

    return jsonify(response.json()), response.status_code


# -------------------------------
# FBPI ORDER FETCH
# -------------------------------
@app.route("/fbpi-order/<fbpi_order_nr>", methods=["GET"])
def get_fbpi_order(fbpi_order_nr):
    session = get_session()

    url = f"https://noon-api-gateway.noon.partners/fbpi/v1/fbpi-order/{fbpi_order_nr}/get"

    response = session.get(url)

    return jsonify(response.json()), response.status_code


# -------------------------------
# RUN (Render uses Gunicorn)
# -------------------------------
if __name__ == "__main__":
    app.run()
