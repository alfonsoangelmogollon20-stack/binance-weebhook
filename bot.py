import os
import json
from flask import Flask, request, jsonify
from iqoptionapi.stable_api import IQ_Option
import time

app = Flask(__name__)

# Credenciales desde variables de entorno en Render
IQ_USERNAME = os.getenv("IQ_USERNAME")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

# Conectar a IQ Option
print("🔁 Intentando conectar a IQ Option...")
I_want_money = IQ_Option(IQ_USERNAME, IQ_PASSWORD)
I_want_money.connect()

if I_want_money.check_connect():
    print("✅ Conectado a IQ Option")
else:
    print("❌ Error al conectar a IQ Option. Revisa usuario/contraseña.")
    exit()

@app.route("/")
def home():
    return "Servidor IQ Option activo 🚀"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()

        symbol = data.get("symbol")  # Ejemplo: EURUSD
        direction = data.get("direction")  # call o put
        duration = int(data.get("duration", 1))  # minutos, por defecto 1

        if not symbol or direction not in ["call", "put"]:
            return jsonify({"status": "error", "msg": "payload inválido: symbol y direction(call|put) required"}), 400

        amount = 10  # USD por operación
        print(f"📩 Señal recibida: {symbol} | {direction} | {duration}m | ${amount}")

        # Ejecutar operación
        _, order_id = I_want_money.buy(amount, symbol, direction, duration)

        if order_id:
            print(f"✅ Operación enviada: {symbol} {direction.upper()} {duration}m por ${amount}")
            return jsonify({"status": "ok", "order_id": order_id}), 200
        else:
            print("⚠️ Error al enviar la orden a IQ Option")
            return jsonify({"status": "error", "msg": "No se pudo ejecutar la orden"}), 500

    except Exception as e:
        print(f"❌ Error en webhook: {str(e)}")
        return jsonify({"status": "error", "msg": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
