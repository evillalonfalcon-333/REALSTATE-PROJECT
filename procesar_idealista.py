import os
import pandas as pd

# Nombre del archivo CSV que descargaste de Apify
# (Renombra tu archivo descargado a 'dataset_idealista.csv' o cambia este nombre)
RAW_CSV_PATH = "dataset_idealista.csv"
OUTPUT_PATH = os.path.join("data", "zonas_cv.csv")

def obtener_archivo_csv():
    # Si existe el nombre por defecto, usarlo
    if os.path.exists(RAW_CSV_PATH):
        return RAW_CSV_PATH
    
    # Buscar cualquier archivo CSV en el directorio que empiece por 'dataset_idealista'
    archivos = [f for f in os.listdir('.') if f.startswith('dataset_idealista') and f.endswith('.csv')]
    if archivos:
        print(f"🔍 Archivo detectado automáticamente: {archivos[0]}")
        return archivos[0]
    
    return None

def procesar_csv_apify(input_file=None):
    archivo_a_procesar = obtener_archivo_csv() if not input_file else input_file
    
    if not archivo_a_procesar or not os.path.exists(archivo_a_procesar):
        print("❌ Error: No se encuentra ningún archivo CSV de Apify (ej. 'dataset_idealista.csv') en esta carpeta.")
        return

    print(f"📖 Leyendo datos extraídos de Apify desde {archivo_a_procesar}...")
    df = pd.read_csv(archivo_a_procesar, low_memory=False)

    # Buscar dinámicamente las columnas clave del archivo de Apify
    col_precio = next((c for c in df.columns if 'price' in c.lower()), None)
    col_lat = next((c for c in df.columns if 'latitude' in c.lower() or 'lat' in c.lower()), None)
    col_lon = next((c for c in df.columns if 'longitude' in c.lower() or 'lng' in c.lower() or 'lon' in c.lower()), None)
    col_zona = next((c for c in df.columns if 'municipality' in c.lower() or 'neighborhood' in c.lower() or 'address' in c.lower()), None)

    if not all([col_precio, col_lat, col_lon, col_zona]):
        print("⚠️ Columnas detectadas:")
        print(f" - Precio: {col_precio}")
        print(f" - Latitud: {col_lat}")
        print(f" - Longitud: {col_lon}")
        print(f" - Zona/Ubicación: {col_zona}")

    # Filtrar registros válidos con datos en las columnas principales
    df_clean = df.dropna(subset=[col_precio, col_lat, col_lon, col_zona]).copy()
    df_clean[col_precio] = pd.to_numeric(df_clean[col_precio], errors='coerce')

    # Agrupar anuncios por zona y calcular los precios medios y coordenadas centrales
    resumen = df_clean.groupby(col_zona).agg(
        precio_habitacion=(col_precio, 'median'),
        precio_piso=(col_precio, lambda x: round(x.median() * 2.2, 1)),
        lat=(col_lat, 'mean'),
        lon=(col_lon, 'mean')
    ).reset_index()

    # Adaptar los nombres de columna al esquema de MatchMyZone
    resumen.rename(columns={col_zona: 'nombre'}, inplace=True)
    
    # Añadir campos auxiliares necesarios
    resumen['tiempo_trayecto'] = 15
    resumen['renta_media_ine'] = "14.800 €/año"
    resumen['tags'] = "metro_directo,ambiente_joven,comercio_local"

    # Redondear decimales
    resumen['precio_habitacion'] = resumen['precio_habitacion'].round(1)
    resumen['lat'] = resumen['lat'].round(4)
    resumen['lon'] = resumen['lon'].round(4)

    # Crear carpeta data si no existe y guardar
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    resumen.to_csv(OUTPUT_PATH, index=False)
    
    print(f"✅ ¡Proceso completado! Archivo guardado correctamente en: {OUTPUT_PATH}")
    print(f"Se han estructurado un total de {len(resumen)} zonas reales.")

if __name__ == "__main__":
    procesar_csv_apify(RAW_CSV_PATH)
