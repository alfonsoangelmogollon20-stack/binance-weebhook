import os
from flask import Flask, request, jsonify
from pocketoptionapi.stable_api import PocketOption

# --- CONFIGURACIÓN ---
SSID = os.getenv("SSID")
app = Flask(__name__) # Inicia la aplicación web

# --- LÓGICA DEL WEBHOOK ---
@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Esta función se activa cuando TradingView envía una alerta a esta URL.
    """
    try:
        # 1. Recibir los datos de la alerta de TradingView
        data = request.json
        print(f"Alerta recibida: {data}")

        # 2. Extraer los datos importantes de la alerta
        #    IMPORTANTE: El formato exacto depende de cómo configures el
        #    mensaje de la alerta en TradingView.
        #    Ejemplo de mensaje en TradingView:
        #    {"asset": "EURUSD", "action": "call", "amount": 15, "expiration": 5}
        
        asset = data.get('asset')
        action = data.get('action') # "call" o "put"
        amount = int(data.get('amount'))
        expiration = int(data.get('expiration'))

        if not all([asset, action, amount, expiration]):
            return jsonify({'status': 'error', 'message': 'Faltan datos en la alerta'}), 400

        # 3. Conectar y ejecutar la operación
        api = PocketOption(ssid=SSID, demo=True)
        api.connect()

        if api.check_connect():
            print(f"Ejecutando operación: {action.upper()} de ${amount} en {asset} por {expiration} min.")
            
            # Cambia a cuenta de práctica. ¡¡COMENTA ESTA LÍNEA PARA OPERAR EN REAL!!
            api.change_balance("PRACTICE") 
            
            success = api.buy(amount=amount, asset=asset, action=action, anaysis_time=expiration)
            
            if success:
                print("Operación abierta con éxito.")
                return jsonify({'status': 'ok', 'message': 'Operación abierta'}), 200
            else:
                print("Error al abrir la operación.")
                return jsonify({'status': 'error', 'message': 'No se pudo abrir la operación'}), 500
        else:
            return jsonify({'status': 'error', 'message': 'No se pudo conectar a Pocket Option'}), 500

    except Exception as e:
        print(f"Error procesando la alerta: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Render usa Gunicorn para ejecutar Flask, por lo que esta parte
    # se usa solo si ejecutas el bot en tu propia computadora.
    # No es necesario cambiar el comando de inicio en Render.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
