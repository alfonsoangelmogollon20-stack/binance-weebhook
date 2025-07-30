# main.py - Versión final para GitHub/Render
import time
import os
import sqlite3
from flask import Flask, request, jsonify, render_template
from binance.client import Client

# --- CONFIGURACIÓN ---
# Recuerda poner esto en las "Environment Variables" de Render
API_KEY = os.environ.get('BINANCE_API_KEY')
API_SECRET = os.environ.get('BINANCE_API_SECRET')
WEBHOOK_PASSPHRASE = os.environ.get('WEBHOOK_PASSPHRASE')

client = Client(API_KEY, API_SECRET, testnet=True) # True para pruebas
app = Flask(__name__)

# --- LÓGICA DE BASE DE DATOS AUTOMÁTICA ---
def init_db():
    """Crea la base de datos y la tabla si no existen."""
    conn = sqlite3.connect('trades.db')
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      symbol TEXT NOT NULL,
      side TEXT NOT NULL,
      quantity REAL NOT NULL,
      entry_price REAL NOT NULL,
      entry_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      status TEXT NOT NULL,
      pnl REAL
    );
    """)
    conn.commit()
    conn.close()
    print("Base de datos lista.")

def get_db_connection():
    """Se conecta a la base de datos."""
    conn = sqlite3.connect('trades.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- LÓGICA DE TRADING (con TP/SL por ATR) ---
def open_trade(symbol, side, quantity, atr_value):
    try:
            # 1. Abrir posición
    order = client.futures_create_order(symbol=symbol, side=side, type='MARKET', quantity=quantity)

time.sleep(2) 
    
        # Hacemos una consulta para obtener los datos de la orden ya ejecutada
    order_details = client.futures_get_order(symbol=symbol, orderId=order['orderId'])
    
    # Usamos directamente el 'avgPrice', que en esta consulta ya debería estar correcto.
    entry_price = float(order_details.get('avgPrice', 0.0))



        # 2. Guardar en la BD
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO trades (symbol, side, quantity, entry_price, status) VALUES (?, ?, ?, ?, ?)',
            (symbol, 'LONG' if side == 'BUY' else 'SHORT', quantity, entry_price, 'OPEN')
        )
        conn.commit()
        conn.close()

        # 3. Calcular y colocar TP/SL con ATR
        atr_value = float(atr_value)
        sl_multiplier = 1.5
        tp_rr_ratio = 2.0
        sl_distance = atr_value * sl_multiplier
        tp_distance = sl_distance * tp_rr_ratio

        if side == 'BUY':
            sl_price = round(entry_price - sl_distance, 2)
            tp_price = round(entry_price + tp_distance, 2)
            close_side = 'SELL'
        else:
            sl_price = round(entry_price + sl_distance, 2)
            tp_price = round(entry_price - tp_distance, 2)
            close_side = 'BUY'
            
        client.futures_create_order(symbol=symbol, side=close_side, type='TAKE_PROFIT_MARKET', stopPrice=tp_price, closePosition=True, quantity=quantity)
        client.futures_create_order(symbol=symbol, side=close_side, type='STOP_MARKET', stopPrice=sl_price, closePosition=True, quantity=quantity)
        
        return {"status": "success", "message": f"Trade {side} en {entry_price}, TP: {tp_price}, SL: {sl_price}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- ENDPOINTS (RUTAS WEB) ---
@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/api/positions')
def get_positions():
    # Esta función es la misma que te di antes, no cambia.
    # ... (busca las operaciones abiertas, calcula el PnL y las devuelve como JSON)
    conn = get_db_connection()
    open_trades = conn.execute('SELECT * FROM trades WHERE status = "OPEN"').fetchall()
    conn.close()
    
    positions_with_pnl = []
    for trade in open_trades:
        try:
                                    current_price = float(client.futures_ticker(symbol=trade['symbol'])['lastPrice'])

            if trade['side'] == 'LONG':
                pnl = (current_price - trade['entry_price']) * trade['quantity']
            else:
                pnl = (trade['entry_price'] - current_price) * trade['quantity']
            
            position_dict = dict(trade)
            position_dict['current_price'] = current_price
            position_dict['unrealized_pnl'] = pnl
            positions_with_pnl.append(position_dict)
        except Exception as e:
            print(f"Error calculando PnL para {trade['symbol']}: {e}")

    return jsonify(positions_with_pnl)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data.get('passphrase') != WEBHOOK_PASSPHRASE:
        return {"status": "error", "message": "No autorizado"}, 401
    
    result = open_trade(
        symbol=data['symbol'],
        side=data['side'],
        quantity=float(data['quantity']),
        atr_value=data['atr']
    )
    return jsonify(result)

# --- INICIO DE LA APLICACIÓN ---
if __name__ == "__main__":
    init_db() # Crea la base de datos al iniciar
    # El puerto lo gestiona Render, no es necesario especificarlo para producción
    app.run()
else:
    # Esto se ejecuta cuando Render usa Gunicorn
    init_db()

