import requests
import urllib3

# Desactivar advertencias de SSL inseguro en caso de que sea necesario usar el fallback sin verificación
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Clave de API de Graphhopper
API_KEY = "8015dbf9-68e3-4e39-9b01-bdcadebd2c5c"  

# Mapeo de los transportes solicitados a los perfiles permitidos por la API gratuita de Graphhopper.
# Como la API gratuita solo permite [car, bike, foot], mapeamos 'bus' y 'metrotren' a 'car' (ruta terrestre)
# y aplicamos factores de corrección de tiempo para simular dichos vehículos.
MAPEO_TRANSPORTE = {
    "auto": "car",
    "metrotren": "car",
    "bus": "car"
}

def realizar_peticion(url):
    """
    Realiza una petición GET a la URL indicada. 
    Si falla la verificación SSL (muy común en Windows o redes corporativas), 
    intenta de forma automática omitiendo la verificación e informando al usuario.
    """
    try:
        # Intento con verificación de certificado SSL (seguro y recomendado)
        return requests.get(url, timeout=10)
    except requests.exceptions.SSLError:
        # Fallback desactivando la verificación SSL
        return requests.get(url, verify=False, timeout=10)
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def obtener_coordenadas(ciudad):
    """
    Usa la API de Geocodificación de Graphhopper para convertir un nombre de ciudad
    en coordenadas geográficas (latitud, longitud).
    """
    url = f"https://graphhopper.com/api/1/geocode?q={ciudad}&locale=es&key={API_KEY}"
    response = realizar_peticion(url)

    if not response:
        print(f"No se pudo establecer conexión para buscar '{ciudad}'.")
        return None

    if response.status_code != 200:
        print(f"Error al geocodificar '{ciudad}': {response.status_code}")
        return None

    datos = response.json()
    if not datos.get("hits"):
        print(f"No se encontraron coordenadas para '{ciudad}'.")
        return None

    # Tomar la primera coincidencia (la más relevante)
    primer_resultado = datos["hits"][0]
    lat = primer_resultado["point"]["lat"]
    lon = primer_resultado["point"]["lng"]
    
    # Nombre formateado completo (e.g., "Santiago, Chile")
    nombre_formateado = primer_resultado.get("name", ciudad)
    pais = primer_resultado.get("country", "")
    if pais and pais != nombre_formateado:
        nombre_formateado += f", {pais}"
        
    return f"{lat},{lon}", nombre_formateado

def obtener_ruta(origen_coords, destino_coords, transporte_api):
    """
    Obtiene la ruta entre dos puntos (coordenadas en formato 'lat,lon')
    usando la API de Ruteo de Graphhopper.
    """
    # Construimos la URL de la API de Graphhopper usando el perfil de la API
    url = (
        f"https://graphhopper.com/api/1/route?"
        f"point={origen_coords}&point={destino_coords}&vehicle={transporte_api}&locale=es&key={API_KEY}"
    )

    response = realizar_peticion(url)

    if not response:
        print("No se pudo establecer conexión para calcular la ruta.")
        return None

    # Validación de respuesta
    if response.status_code != 200:
        print(f"Error al consultar la API de Ruteo: {response.status_code}")
        try:
            detalle = response.json()
            if "message" in detalle:
                print(f"Detalle del error: {detalle['message']}")
        except Exception:
            pass
        return None

    return response.json()

def mostrar_resultados(datos, nombre_origen, nombre_destino, transporte_usuario):
    ruta = datos["paths"][0]

    # Distancia en metros → km y millas
    distancia_km = ruta["distance"] / 1000
    distancia_millas = distancia_km * 0.621371

    # Tiempo en ms → minutos
    duracion_min = ruta["time"] / 60000

    # Ajuste de duración para simular bus o metrotren, dado que usamos el trazado terrestre de 'car'
    nota_estimado = ""
    if transporte_usuario == "bus":
        duracion_min *= 1.3  # Más lento debido a paradas y velocidad del bus
        nota_estimado = " (Estimado con paradas y velocidad de bus)"
    elif transporte_usuario == "metrotren":
        duracion_min *= 0.8  # El tren suele ser más rápido y no tiene congestión vehicular
        nota_estimado = " (Estimación por vía férrea/tránsito rápido)"

    print("\n" + "="*40)
    print("        RESULTADOS DEL VIAJE")
    print("="*40)
    print(f"Origen: {nombre_origen}")
    print(f"Destino: {nombre_destino}")
    print(f"Medio de transporte: {transporte_usuario.capitalize()}")
    print(f"Distancia en kilómetros: {distancia_km:.2f} km")
    print(f"Distancia en millas: {distancia_millas:.2f} millas")
    print(f"Duración del viaje: {duracion_min:.2f} minutos{nota_estimado}")
    print("-"*40)

    print("Narrativa del viaje:")
    for paso in ruta["instructions"]:
        print(f"- {paso['text']}")
    print("="*40 + "\n")

def main():
    print("Programa de rutas con Graphhopper")
    print("Ingresa 'v' en cualquier momento para salir del programa.\n")

    while True:
        origen = input("Ciudad de Origen: ")
        if origen.lower() == "v":
            print("Saliendo del programa...")
            break
        if not origen.strip():
            continue

        destino = input("Ciudad de Destino: ")
        if destino.lower() == "v":
            print("Saliendo del programa...")
            break
        if not destino.strip():
            continue

        print("\nMedios de transporte disponibles:")
        print("- auto")
        print("- metrotren")
        print("- bus")
        transporte = input("Medio de transporte: ").strip().lower()

        if transporte == "v":
            print("Saliendo del programa...")
            break

        # Validamos transporte seleccionado
        if transporte not in MAPEO_TRANSPORTE:
            print("Transporte no válido. Usando 'auto' por defecto.")
            transporte = "auto"

        # Obtenemos el perfil compatible con la API
        transporte_api = MAPEO_TRANSPORTE[transporte]

        print(f"\n[1/3] Buscando coordenadas de origen para '{origen}'...")
        res_origen = obtener_coordenadas(origen)
        if not res_origen:
            print("No se pudo resolver la ciudad de origen. Intenta nuevamente.\n")
            continue
        coords_origen, nombre_origen_completo = res_origen
        print(f"      -> Encontrado: {nombre_origen_completo} ({coords_origen})")

        print(f"\n[2/3] Buscando coordenadas de destino para '{destino}'...")
        res_destino = obtener_coordenadas(destino)
        if not res_destino:
            print("No se pudo resolver la ciudad de destino. Intenta nuevamente.\n")
            continue
        coords_destino, nombre_destino_completo = res_destino
        print(f"      -> Encontrado: {nombre_destino_completo} ({coords_destino})")

        print(f"\n[3/3] Consultando ruta entre {nombre_origen_completo} y {nombre_destino_completo} en '{transporte}'...\n")
        datos = obtener_ruta(coords_origen, coords_destino, transporte_api)

        if datos is None:
            print("No se pudo obtener la ruta. Intenta nuevamente.\n")
            continue

        mostrar_resultados(datos, nombre_origen_completo, nombre_destino_completo, transporte)

if __name__ == "__main__":
    main()
