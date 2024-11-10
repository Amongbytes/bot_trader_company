# Trading Bot 📈

Un bot de trading automatizado que ejecuta operaciones en función de indicadores técnicos como el RSI (Índice de Fuerza Relativa), EMA (Media Móvil Exponencial) y el Precio de Cierre del Día Anterior (PDL). Este bot usa una configuración basada en JSON y se conecta a una API de intercambio de criptomonedas para realizar operaciones en tiempo real.

---

## Tabla de Contenidos

- [Características](#características)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Estructura del Código](#estructura-del-código)
- [Estrategia de Trading](#estrategia-de-trading)
- [Ejemplo de Operación](#ejemplo-de-operación)
- [Precauciones y Advertencias](#precauciones-y-advertencias)
- [Licencia](#licencia)

---

## Características

- **Indicadores Técnicos:** Calcula el RSI y EMA para determinar condiciones de sobreventa/sobrecompra.
- **Configuración Personalizable:** Configura el símbolo de trading, umbrales de RSI, cantidad de operación, y período de EMA y RSI desde un archivo JSON.
- **Control de Errores:** Gestión avanzada de errores para solicitudes a la API y reintentos automáticos.
- **Registro de Operaciones:** Guarda un registro de todas las órdenes en un archivo CSV.

---

## Requisitos

- Python 3.7 o superior
- Paquetes adicionales: `requests`, `pandas`, `hmac`, `hashlib`, `json`, `logging`

Para instalar los paquetes necesarios:
```bash
pip install -r requirements.txt
```
---


## Instalación


Clona el repositorio:

```bash
git clone https://github.com/tuusuario/trading-bot.git
cd trading-bot
```

Instala los requisitos:

```bash
pip install -r requirements.txt
Crea el archivo de configuración JSON siguiendo el formato en Configuración.
```

---

## Configuración

Antes de ejecutar el bot, crea un archivo config.json en el directorio raíz del proyecto con el siguiente formato:


```bash
json

{
    "API_KEY": "tu_api_key",
    "API_SECRET": "tu_api_secret",
    "BASE_URL": "https://api.exchangename.com",
    "SYMBOL": "BTCUSDT",
    "BUY_THRESHOLD_RSI": 30,
    "SELL_THRESHOLD_RSI": 70,
    "TRADE_AMOUNT": 0.001,
    "EMA_PERIOD": 14,
    "RSI_PERIOD": 14,
    "CHECK_INTERVAL": 60
}
```

Parámetros del Archivo de Configuración
API_KEY y API_SECRET: Claves de autenticación para la API de la plataforma de intercambio.
BASE_URL: URL base de la API del intercambio.
SYMBOL: Par de trading (por ejemplo, BTCUSDT).
BUY_THRESHOLD_RSI y SELL_THRESHOLD_RSI: Umbrales para decidir cuándo comprar o vender en función del RSI.
TRADE_AMOUNT: Cantidad a operar en cada transacción.
EMA_PERIOD y RSI_PERIOD: Períodos para el cálculo de EMA y RSI, respectivamente.
CHECK_INTERVAL: Intervalo de tiempo (en segundos) para ejecutar el bucle de operaciones del bot.



--- 
## Uso


Para iniciar el bot, ejecuta el siguiente comando:

```bash

python trading_bot.py
```

El bot empezará a monitorear el mercado en función de los parámetros configurados y ejecutará órdenes de compra/venta cuando se cumplan las condiciones.

---



## Estructura del Código

```bash

Config: Clase de configuración que carga y valida parámetros desde config.json.
APIClient: Clase para manejar solicitudes GET y POST a la API, con autenticación y reintentos.
get_price_history: Función para obtener el historial de precios.
calculate_ema: Calcula la Media Móvil Exponencial (EMA).
calculate_rsi: Calcula el Índice de Fuerza Relativa (RSI).
calculate_pdl: Obtiene el Precio de Cierre del Día Anterior (PDL).
place_order: Ejecuta una orden en el intercambio.
log_order_to_csv: Guarda un registro de las órdenes en un archivo CSV.
trading_bot: Función principal que ejecuta el bot en un bucle y evalúa las condiciones de trading.
```

---

Estrategia de Trading
El bot sigue una estrategia básica basada en el análisis de los siguientes indicadores:

Media Móvil Exponencial (EMA): Se utiliza para determinar la tendencia general de precios.
Índice de Fuerza Relativa (RSI): Identifica condiciones de sobrecompra (RSI > 70) y sobreventa (RSI < 30).
Precio de Cierre del Día Anterior (PDL): Nivel de referencia para decisiones de compra cerca del PDL.
Lógica de Operación
Comprar cuando:

El precio actual está por debajo de la EMA.
El RSI está por debajo del umbral de compra (indicando sobreventa).
El precio está cerca del PDL, lo que sugiere un soporte técnico.
Vender cuando:

El precio actual está por encima de la EMA.
El RSI supera el umbral de venta (indicando sobrecompra).

---

Ejemplo de Operación
Aquí tienes un ejemplo de la salida del bot en consola:

```bash
2023-01-01 12:00:00 - INFO - Precio actual: 42000 USD, EMA: 42100.50, RSI: 28.5, PDL: 41800.00
2023-01-01 12:00:00 - INFO - El precio está bajo y el RSI indica sobreventa cerca del PDL. Comprando...
2023-01-01 12:00:01 - INFO - Orden ejecutada: {'symbol': 'BTCUSDT', 'side': 'BUY', 'price': 42000, 'quantity': 0.001}
2023-01-01 12:10:00 - INFO - Esperando una mejor oportunidad...
```

Cada orden ejecutada se registra en un archivo trading_log.csv con los detalles de la operación, que incluye el símbolo, el precio, la cantidad, y otros datos relevantes.


Recursos y Referencias
Documentación de la API de Binance
Cálculo de EMA y RSI - Investopedia
Ejemplo de Bots de Trading en Python - Medium

