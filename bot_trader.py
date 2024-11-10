import time
import hmac
import hashlib
import json

# Configuración
API_KEY = 'TU_API_KEY'
API_SECRET = 'TU_API_SECRET'
BASE_URL = 'https://api.bitflex.com'

# Parámetros de trading
SYMBOL = 'BTCUSDT'  # Par de trading
BUY_THRESHOLD = 30000  # Comprar si el precio baja por debajo de este umbral
SELL_THRESHOLD = 35000  # Vender si el precio sube por encima de este umbral
TRADE_AMOUNT = 0.001  # Cantidad de BTC a comprar/vender

# Función para generar la firma de la solicitud
def generate_signature(params, secret):
    query_string = '&'.join([f"{key}={value}" for key, value in sorted(params.items())])
    signature = hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    return signature

# Función para obtener el precio actual del mercado
def get_market_price(symbol):
    url = f'{BASE_URL}/api/v1/market/ticker?symbol={symbol}'
    response = requests.get(url)
    data = response.json()
    return float(data['data']['lastPrice'])

# Función para realizar una orden de compra
def place_order(symbol, side, quantity):
    url = f'{BASE_URL}/api/v1/order'
    timestamp = int(time.time() * 1000)
    params = {
        'symbol': symbol,
        'side': side,
        'type': 'LIMIT',
        'quantity': quantity,
        'price': get_market_price(symbol),
        'timestamp': timestamp
    }
    signature = generate_signature(params, API_SECRET)
    headers = {
        'X-MBX-APIKEY': API_KEY
    }
    params['signature'] = signature
    response = requests.post(url, headers=headers, data=params)
    return response.json()

# Función principal del bot
def trading_bot():
    while True:
        try:
            price = get_market_price(SYMBOL)
            print(f'Precio actual: {price} USD')

            if price < BUY_THRESHOLD:
                print('El precio está bajo, comprando...')
                order = place_order(SYMBOL, 'BUY', TRADE_AMOUNT)
                print('Orden de compra ejecutada:', order)
            elif price > SELL_THRESHOLD:
                print('El precio está alto, vendiendo...')
                order = place_order(SYMBOL, 'SELL', TRADE_AMOUNT)
                print('Orden de venta ejecutada:', order)
            else:
                print('Esperando una mejor oportunidad...')

            # Esperar un tiempo antes de revisar nuevamente
            time.sleep(60)

        except Exception as e:
            print('Error:', e)
            time.sleep(60)

# Ejecutar el bot
if __name__ == '__main__':
    trading_bot()