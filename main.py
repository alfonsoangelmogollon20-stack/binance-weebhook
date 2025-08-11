from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

PO_EMAIL = os.getenv("alfonso.angelmogollon20@gmail.com")
PO_PASSWORD = os.getenv("baja2016")

MONTO = 15
EXPIRACION = 5

BASE_URL = "https://pocketoption.com/api"  # Ajusta si cambia la API

def obtener_token():
    resp = requests.post(f"{BASE_URL}/login", data={
        "email": alfonso.angelmogollon20@gmail.com,
        "password": baja2016
    })
    if resp.status_code == 200:
        return resp.json().get("token")
    return None

def abrir_operacion(token, par, direccion):
    payload = {
        "symbol": par,
        "amount": MONTO,
        "direction": direccion.lower(),  # "call" o "put"
        "expiration": EXPIRACION,
        "demo": True
    }
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/trade", json=payload, headers=headers)
    return resp.json()

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    par = data.get("symbol", "").upper()
    direccion = data.get("action", "").upper()  # CALL o PUT

    if not par or not direccion:
        return jsonify({"error": "Datos incompletos"}), 400

    token = obtener_token()
    if not token:
        return jsonify({"error": "No se pudo autenticar"}), 500

    respuesta = abrir_operacion(token, par, direccion)
    if "error" not in respuesta:
        return jsonify({"status": "OK", "detalle": respuesta}), 200
    else:
        return jsonify({"status": "ERROR", "detalle": respuesta}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
