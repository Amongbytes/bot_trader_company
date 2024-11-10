import requests
import time
import hmac
import hashlib
import json
import pandas as pd
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configuración de log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cargar configuración desde un archivo externo
with open('config.json') as config_file:
    config = json.load(config_file)

API_KEY = config['API_KEY']
API_SECRET = config['API_SECRET']
BASE_URL = config['BASE_URL']
SYMBOL = config['SYMBOL']
BUY_THRESHOLD_RSI = config['BUY_THRESHOLD_RSI']
SELL_THRESHOLD_RSI = config['SELL_THRESHOLD_RSI']
TRADE_AMOUNT = config['TRADE_AMOUNT']
EMA_PERIOD = config['EMA_PERIOD']
RSI_PERIOD = config['RSI_PERIOD']
CHECK_INTERVAL = config['CHECK_INTERVAL']

# Sesión de requests con reintentos configurados
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

# Función para generar la firma de la solicitud
def generate_signature(params, secret):
    query_string = '&'.join([f"{key}={value}" for key, value in sorted(params.items())])
    return hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

# Función para obtener el historial de precios
def get_price_history(symbol, interval='1m', limit=100):
    try:
        url = f'{BASE_URL}/api/v1/market/klines?symbol={symbol}&interval={interval}&limit={limit}'
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        return [float(entry[4]) for entry in data['data']]
    except requests.RequestException as e:
        logging.error(f"Error al obtener el historial de precios: {e}")
        return []

# Función para calcular EMA
def calculate_ema(prices, period):
    if len(prices) < period:
        logging.warning("Datos insuficientes para calcular la EMA.")
        return None
    return pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1]

# Función para calcular RSI
def calculate_rsi(prices, period):
    if len(prices) < period:
        logging.warning("Datos insuficientes para calcular el RSI.")
        return None
    delta = pd.Series(prices).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]

# Función para realizar una orden de compra/venta
def place_order(symbol, side, quantity, price):
    try:
        url = f'{BASE_URL}/api/v1/order'
        timestamp = int(time.time() * 1000)
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'LIMIT',
            'quantity': quantity,
            'price': price,
            'timestamp': timestamp
        }
        signature = generate_signature(params, API_SECRET)
        headers = {'X-MBX-APIKEY': API_KEY}
        params['signature'] = signature
        response = session.post(url, headers=headers, data=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error al realizar la orden {side}: {e}")
        return {}

# Función para obtener el precio actual del mercado
def get_market_price(symbol):
    try:
        url = f'{BASE_URL}/api/v1/market/ticker?symbol={symbol}'
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        return float(data['data']['lastPrice'])
    except requests.RequestException as e:
        logging.error(f"Error al obtener el precio actual: {e}")
        return None

# Función para guardar los registros de las órdenes en un archivo CSV
def log_order_to_csv(order_data):
    df = pd.DataFrame([order_data])
    try:
        df.to_csv('trading_log.csv', mode='a', header=False, index=False)
    except Exception as e:
        logging.error(f"Error al guardar el registro de la orden: {e}")

# Función principal del bot
def trading_bot():
    while True:
        try:
            prices = get_price_history(SYMBOL)
            if not prices:
                time.sleep(CHECK_INTERVAL)
                continue
            
            ema = calculate_ema(prices, EMA_PERIOD)
            rsi = calculate_rsi(prices, RSI_PERIOD)
            current_price = get_market_price(SYMBOL)

            if current_price is None or ema is None or rsi is None:
                time.sleep(CHECK_INTERVAL)
                continue
            
            logging.info(f'Precio actual: {current_price} USD, EMA: {ema:.2f}, RSI: {rsi:.2f}')

            if current_price < ema and rsi < BUY_THRESHOLD_RSI:
                logging.info('El precio está bajo y el RSI indica sobreventa. Comprando...')
                order = place_order(SYMBOL, 'BUY', TRADE_AMOUNT, current_price)
                if order:
                    log_order_to_csv(order)
                logging.info(f'Orden de compra ejecutada: {order}')
            elif current_price > ema and rsi > SELL_THRESHOLD_RSI:
                logging.info('El precio está alto y el RSI indica sobrecompra. Vendiendo...')
                order = place_order(SYMBOL, 'SELL', TRADE_AMOUNT, current_price)
                if order:
                    log_order_to_csv(order)
                logging.info(f'Orden de venta ejecutada: {order}')
            else:
                logging.info('Esperando una mejor oportunidad...')

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            logging.error(f'Error inesperado: {e}')
            time.sleep(CHECK_INTERVAL)

# Ejecutar el bot
if __name__ == '__main__':
    trading_bot()
