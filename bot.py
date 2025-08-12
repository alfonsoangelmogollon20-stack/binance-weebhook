import os
import time
from flask import Flask, request, jsonify
from iqoptionapi.stable_api import IQ_Option

app = Flask(__name__)

# Credenciales desde variables de entorno
IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

# Conexión a IQ Option
print("🔄 Conectando a IQ Option...")
I_want_money = IQ_Option(IQ_EMAIL, IQ_PASSWORD)

# Intento de login
try:
    I_want_money.connect()
    if I_want_money.check_connect():
        print("✅ Conectado correctamente a IQ Option")
        balance_type = "PRACTICE"  # o REAL si quieres real
        balance = I_want_money.get_balance()
        print(f"💰 Balance en {balance_type}: {balance}")
    else:
        print("❌ Error de conexión a IQ Option")
except Exception as e:
    print(f"❌ Error al conectar: {e}")

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "ok", "message": "IQ Option bot online"})

@app.route('/signal', methods=['POST'])
def signal():
    data = request.get_json()
    symbol = data.get("symbol")
    direction = data.get("direction")  # 'call' o 'put'
    amount = data.get("amount", 10)
    minutes = data.get("minutes", 1)  # por defecto 1 minuto

    if not symbol or not direction:
        return jsonify({"status": "error", "msg": "symbol y direction requeridos"}), 400

    try:
        # Calcula expiración en UNIX (próximo minuto + minutos seleccionados)
        exp_time = time.time()
        exp_time = exp_time - (exp_time % 60) + (minutes * 60)

        print(f"📢 Señal recibida:")
        print(f"   Activo: {symbol}")
        print(f"   Dirección: {direction}")
        print(f"   Monto: {amount}")
        print(f"   Expira en: {minutes} min -> {int(exp_time)} (UNIX)")
        print(f"   Tipo: binary")

        # Enviar orden
        check, order_id = I_want_money.buy(amount, symbol, direction, minutes)

        if check:
            print(f"✅ Orden enviada correctamente. ID: {order_id}")
            return jsonify({"status": "success", "order_id": order_id})
        else:
            print(f"⚠️ Error al enviar la orden: {order_id}")
            return jsonify({"status": "error", "msg": order_id})

    except Exception as e:
        print(f"❌ Error en ejecución: {e}")
        return jsonify({"status": "error", "msg": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
