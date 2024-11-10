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
