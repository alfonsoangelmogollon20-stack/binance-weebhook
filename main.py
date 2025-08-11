from flask import Flask, request, jsonify
import os
from pocketoption import PocketOption

app = Flask(__name__)

# Leer credenciales de variables de entorno
PO_EMAIL = os.getenv("PO_EMAIL")
PO_PASSWORD = os.getenv("PO_PASSWORD")

MONTO = 15
EXPIRACION = 5  # minutos

# Inicializar cliente Pocket Option
client = PocketOption(email=PO_EMAIL, password=PO_PASSWORD)
client.connect()

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    symbol = data.get("symbol", "").upper()
    action = data.get("action", "").lower()  # 'call' o 'put'

    if not symbol or action not in ["call", "put"]:
        return jsonify({"error": "Datos inválidos"}), 400

    if client.is_connected():
        success = client.buy(MONTO, symbol, action, EXPIRACION)
        if success:
            return jsonify({"status": "Operación abierta"}), 200
        else:
            return jsonify({"error": "Error al abrir operación"}), 500
    else:
        return jsonify({"error": "No conectado a Pocket Option"}), 500

@app.route("/", methods=["GET"])
def index():
    return "Bot Pocket Option activo", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
