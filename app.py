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
# FBPI ORDER GET
# -------------------------------
@app.route("/fbpi-order/get/<fbpi_order_nr>", methods=["GET"])
def fetch_fbpi_order(fbpi_order_nr):
    session = get_session()

    url = f"https://noon-api-gateway.noon.partners/fbpi/v1/fbpi-order/{fbpi_order_nr}/get"

    response = session.get(url)

    return jsonify(response.json()), response.status_code

# -------------------------------
# FBPI ORDER UPDATE
# -------------------------------
@app.route("/fbpi-order/update", methods=["POST"])
def update_fbpi_order():
    payload = request.json
    session = get_session()

    response = session.post(
        "https://noon-api-gateway.noon.partners/fbpi/v1/fbpi-order/update",
        json=payload
    )

    return jsonify(response.json()), response.status_code

# -------------------------------
# CREATE SHIPMENT
# -------------------------------
@app.route("/shipment/create", methods=["POST"])
def create_shipment():
    payload = request.json
    session = get_session()

    response = session.post(
        "https://noon-api-gateway.noon.partners/fbpi/v1/shipment/create",
        json=payload
    )

    return jsonify(response.json()), response.status_code


# -------------------------------
# CANCEL SHIPMENT
# -------------------------------
@app.route("/shipment/cancel", methods=["POST"])
def cancel_shipment():
    payload = request.json
    session = get_session()

    response = session.post(
        "https://noon-api-gateway.noon.partners/fbpi/v1/shipment/cancel",
        json=payload
    )

    return jsonify(response.json()), response.status_code

# -------------------------------
# GET SHIPMENT
# -------------------------------
@app.route("/shipment/get", methods=["POST"])
def get_shipment():
    payload = request.json
    session = get_session()

    response = session.post(
        "https://noon-api-gateway.noon.partners/fbpi/v1/shipment/get",
        json=payload
    )

    return jsonify(response.json()), response.status_code

# -------------------------------
# GET NOON LOGISTICS AWBs
# -------------------------------
@app.route("/shipment/noon-logistics-awbs", methods=["POST"])
def get_noon_logistics_awbs():
    payload = request.json
    session = get_session()

    response = session.post(
        "https://noon-api-gateway.noon.partners/fbpi/v1/shipment/noon-logistics-awbs/get",
        json=payload
    )

    return jsonify(response.json()), response.status_code
# -------------------------------
# FBPI ORDERS LIST
# -------------------------------
@app.route("/fbpi-orders/list", methods=["POST"])
def list_fbpi_orders():
    payload = request.json
    session = get_session()

    response = session.post(
        "https://noon-api-gateway.noon.partners/fbpi/v1/fbpi-orders/list",
        json=payload
    )

    return jsonify(response.json()), response.status_code
# -------------------------------
# FBPI ORDER CUSTOMER DETAILS
# -------------------------------
@app.route("/fbpi-order/<fbpi_order_nr>/customer-details", methods=["GET"])
def get_customer_details(fbpi_order_nr):
    session = get_session()

    url = f"https://noon-api-gateway.noon.partners/fbpi/v1/fbpi-order/{fbpi_order_nr}/customer-details/get"

    response = session.get(url)

    return jsonify(response.json()), response.status_code
# -------------------------------
# FBPI ORDER UPDATE (ITEM LEVEL)
# -------------------------------
@app.route("/fbpi-order/update-items", methods=["POST"])
def update_fbpi_order_items():
    payload = request.json
    session = get_session()

    response = session.post(
        "https://noon-api-gateway.noon.partners/fbpi/v1/fbpi-order/update",
        json=payload
    )

    return jsonify(response.json()), response.status_code
# -------------------------------
# FBPO PURCHASE ORDER GET
# -------------------------------
@app.route("/fbpo/<po_nr>", methods=["GET"])
def get_purchase_order(po_nr):
    session = get_session()

    url = f"https://noon-api-gateway.noon.partners/fbpo/v1/po/{po_nr}/get"

    response = session.get(url)

    return jsonify(response.json()), response.status_code
# -------------------------------
# RUN (Render uses Gunicorn)
# -------------------------------
if __name__ == "__main__":
    app.run()
