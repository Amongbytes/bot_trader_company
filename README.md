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

---
## Instalación


Clona el repositorio:

```bash
git clone https://github.com/tuusuario/trading-bot.git
cd trading-bot
Instala los requisitos:

```bash
Copiar código
pip install -r requirements.txt
Crea el archivo de configuración JSON siguiendo el formato en Configuración.

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
Parámetros del Archivo de Configuración
API_KEY y API_SECRET: Claves de autenticación para la API de la plataforma de intercambio.
BASE_URL: URL base de la API del intercambio.
SYMBOL: Par de trading (por ejemplo, BTCUSDT).
BUY_THRESHOLD_RSI y SELL_THRESHOLD_RSI: Umbrales para decidir cuándo comprar o vender en función del RSI.
TRADE_AMOUNT: Cantidad a operar en cada transacción.
EMA_PERIOD y RSI_PERIOD: Períodos para el cálculo de EMA y RSI, respectivamente.
CHECK_INTERVAL: Intervalo de tiempo (en segundos) para ejecutar el bucle de operaciones del bot.