SESSION = None
SESSION_CREATED_AT = 0
SESSION_TTL = 50 * 60  # 50 minutes

import json
import time
import uuid
import jwt
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Load credentials
import os

credentials = {
    "key_id": os.getenv("NOON_KEY_ID"),
    "private_key": os.getenv("NOON_PRIVATE_KEY"),
    "project_code": os.getenv("NOON_PROJECT_CODE")
}

# ---------- JWT ----------
def create_jwt():
    payload = {
        "sub": credentials["key_id"],
        "iat": int(time.time()),
        "jti": str(uuid.uuid4())
    }

    return jwt.encode(
        payload,
        credentials["private_key"],
        algorithm="RS256"
    )

# ---------- SESSION (SMART LOGIN) ----------
def get_session():
    global SESSION, SESSION_CREATED_AT

    # Reuse session if still valid
    if SESSION and (time.time() - SESSION_CREATED_AT) < SESSION_TTL:
        return SESSION

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Zoho-Noon-Integration/1.0",
        "Content-Type": "application/json"
    })

    login_payload = {
        "token": create_jwt(),
        "default_project_code": credentials["project_code"]
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

# ---------- TEST LOGIN ----------
@app.route("/login", methods=["GET"])
def login_test():
    session = get_session()

    whoami = session.get(
        "https://noon-api-gateway.noon.partners/identity/v1/whoami"
    )

    return jsonify({
        "status": "success",
        "user": whoami.json()
    })

# ---------- STOCK LIST ----------
@app.route("/stock-list", methods=["POST"])
def stock_list():
    payload = request.json

    session = get_session()

    stock_res = session.post(
        "https://noon-api-gateway.noon.partners/stock/v1/stock-list",
        json=payload
    )
    return jsonify(stock_res.json()), stock_res.status_code

@app.route("/stock-update", methods=["POST"])
def stock_update():
    payload = request.json

    session = get_session()

    stock_update_res = session.post(
        "https://noon-api-gateway.noon.partners/stock/v1/stock-update",
        json=payload
    )

    return jsonify(stock_update_res.json()), stock_update_res.status_code
@app.route("/ping", methods=["GET"])
def ping():
    return {"status": "ok"}
# ---------- RUN ----------
if __name__ == "__main__":
    app.run(port=5000, debug=True)
