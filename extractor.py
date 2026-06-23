# Importamos las "cajas de herramientas" que necesitamos para el script
import requests         # Para conectarnos a la página web de Binance
import time             # Para manejar pausas y medir el tiempo (los 5 minutos)
import csv              # Para crear y escribir en el archivo Excel/CSV
import os               # Para revisar si el archivo ya existe en tu computadora
from datetime import datetime # Para saber la fecha y hora exacta

# --- CONFIGURACIÓN BÁSICA ---
ARCHIVO_CSV = 'precios_p2p.csv'  # El nombre del archivo donde guardaremos los datos
TIEMPO_ESPERA = 300              # 300 segundos equivalen a 5 minutos

def obtener_datos_binance(tipo_operacion):
    """
    Esta función va a la página de Binance y trae los 10 primeros anuncios.
    'tipo_operacion' puede ser "BUY" (Comprar) o "SELL" (Vender).
    """
    # Esta es la dirección secreta pública que usa la web de Binance para consultar el P2P
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    
    # Nos disfrazamos un poco para que Binance crea que somos un navegador web normal (como Chrome)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json"
    }
    
    # Aquí le decimos a Binance exactamente qué queremos buscar
    datos_busqueda = {
        "fiat": "VES",                  # Moneda local: Bolívares
        "tradeType": tipo_operacion,    # Si queremos ver a la gente que Vende o Compra
        "asset": "USDT",                # La criptomoneda: USDT (Dólar digital)
        "merchantCheck": False,         # Ver anuncios de todos, no solo de comerciantes verificados
        "page": 1,                      # Solo la primera página
        "rows": 10,                     # Queremos solo los 10 primeros resultados
        "payTypes": []                  # Todos los métodos de pago (Pago Móvil, Banesco, etc.)
    }
    
    try:
        # Hacemos la pregunta a Binance y esperamos su respuesta
        respuesta = requests.post(url, json=datos_busqueda, headers=headers)
        respuesta_json = respuesta.json() # Traducimos la respuesta a un formato manejable
        
        precios = []
        # Revisamos la lista de anuncios que nos dio Binance
        for anuncio in respuesta_json['data']:
            # Extraemos el precio del anuncio y lo convertimos en un número decimal
            precio = float(anuncio['adv']['price'])
            precios.append(precio)
            
        return precios # Entregamos la lista de los 10 precios
        
    except Exception as e:
        # Si algo falla (se cae el internet, Binance cambia algo), el programa no explota,
        # simplemente nos avisa y devuelve una lista vacía.
        print(f"Error al conectar con Binance: {e}")
        return []

def guardar_en_csv(tipo, precios):
    """
    Esta función toma los precios, saca los cálculos (promedio, máximo, mínimo)
    y los anota en el archivo.
    """
    if not precios: # Si no hay precios (por algún error), no hacemos nada
        return

    # Calculamos la matemática básica
    precio_max = max(precios)                  # El precio más alto
    precio_min = min(precios)                  # El precio más bajo
    precio_prom = sum(precios) / len(precios)  # El promedio (suma de todos dividida entre la cantidad)
    
    # Obtenemos la hora actual del sistema
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Traducimos para que el archivo se lea bonito en español
    tipo_espanol = "Compra" if tipo == "BUY" else "Venta"
    
    # Revisamos si el archivo ya existe para saber si tenemos que ponerle los títulos arriba
    archivo_existe = os.path.isfile(ARCHIVO_CSV)
    
    # Abrimos el archivo en modo 'a' (Append), lo que significa que añadimos texto al final sin borrar lo anterior
    with open(ARCHIVO_CSV, 'a', newline='', encoding='utf-8') as archivo:
        escritor = csv.writer(archivo)
        
        # Si el archivo es nuevecito, le escribimos los títulos de las columnas
        if not archivo_existe:
            escritor.writerow(["Timestamp", "Tipo", "Precio_Promedio", "Precio_Max", "Precio_Min"])
            
        # Anotamos nuestra nueva fila con los datos (redondeamos los precios a 2 decimales)
        escritor.writerow([ahora, tipo_espanol, round(precio_prom, 2), precio_max, precio_min])
        
    print(f"[{ahora}] Guardado: {tipo_espanol} -> Prom: {round(precio_prom, 2)} VES | Max: {precio_max} VES | Min: {precio_min} VES")

# --- EL MOTOR PRINCIPAL ---
# Este es el bucle infinito que mantendrá el programa vivo y trabajando
print("Iniciando el extractor de Binance P2P... (Presiona Ctrl+C para detenerlo)")

while True:
    try:
        print("\n--- Extrayendo datos nuevos ---")
        
        # 1. Obtenemos y guardamos los datos de los que están COMPRANDO (BUY)
        precios_compra = obtener_datos_binance("BUY")
        guardar_en_csv("BUY", precios_compra)
        
        # Le damos un pequeñísimo respiro de 2 segundos a la conexión para no saturar a Binance
        time.sleep(2)
        
        # 2. Obtenemos y guardamos los datos de los que están VENDIENDO (SELL)
        precios_venta = obtener_datos_binance("SELL")
        guardar_en_csv("SELL", precios_venta)
        
        # 3. Ponemos el programa a dormir por 5 minutos
        print(f"Esperando {TIEMPO_ESPERA // 60} minutos para la siguiente extracción...")
        time.sleep(TIEMPO_ESPERA)
        
    except KeyboardInterrupt:
        # Si presionas Ctrl+C, el programa sabe que debe despedirse educadamente y cerrarse
        print("\nPrograma detenido por el usuario. ¡Hasta luego!")
        break
    except Exception as e:
        # Si ocurre un error muy raro, lo ignoramos, esperamos un minuto y volvemos a intentar
        print(f"Ocurrió un error inesperado: {e}")
        time.sleep(60)