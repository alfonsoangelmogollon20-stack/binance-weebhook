import os
import asyncio
from flask import Flask, request, jsonify
from pocketoptionapi.stable_api import PocketOption
import logging
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(message)s')

app = Flask(__name__)

# Configuração da sessão
ssid="""42["auth",{"session":"gqep422ie95ar8uabq0q9nsdsf","isDemo":1,"uid":107695044,"platform":2,"isFastHistory":true,"isOptimized":true}]"""
demo=True
api = PocketOption(ssid,demo)

# Conecta à API
connect=api.connect()
print(connect)

async def execute_trade_logic(data):
    print(f"DEBUG: Intentando conectar con el SSID completo: '{ssid}'")

    # Cambiar 'asset' por 'symbol'
    symbol = data.get('asset')  # 'asset' debe ser 'symbol'
    action = data.get('action')
    amount = int(data.get('amount'))
    expiration = int(data.get('expiration'))

    if not symbol or not action or not isinstance(amount, int) or not isinstance(expiration, int):
        raise ValueError("Faltan datos o son inválidos.")

    if api.check_connect():
        print(f"Ejecutando operación: {action.upper()} de ${amount} en {symbol} por {expiration} min.")
        
        # Se cambia 'asset' a 'symbol'
        success, _ = await api.buy(amount=amount, symbol=symbol, action=action, analysis_time=expiration)
        
        if success:
            print("Operación abierta con éxito.")
            return {'status': 'ok', 'message': 'Operación abierta'}
        else:
            raise ConnectionError("La API no pudo abrir la operación.")
    else:
        raise ConnectionError("No se pudo conectar a Pocket Option.")



@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print(f"Alerta recibida: {data}")
        result = asyncio.run(execute_trade_logic(data))
        return jsonify(result), 200
    except Exception as e:
        print(f"Error procesando la alerta: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
