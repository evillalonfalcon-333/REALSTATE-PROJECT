import os
import re
import pandas as pd

# Nombre del archivo CSV descargado de Apify
RAW_CSV_PATH = "dataset_idealista.csv"
OUTPUT_PATH = os.path.join("data", "zonas_cv.csv")

def obtener_archivo_csv():
    """Busca el archivo CSV descargado de Apify en el directorio actual."""
    if os.path.exists(RAW_CSV_PATH):
        return RAW_CSV_PATH
    
    archivos = [f for f in os.listdir('.') if f.startswith('dataset_idealista') and f.endswith('.csv')]
    if archivos:
        print(f"🔍 Archivo detectado automáticamente: {archivos[0]}")
        return archivos[0]
    
    return None

def procesar_csv_apify(input_file=None):
    """Limpia el CSV de Idealista, descarta precios trampa y genera data/zonas_cv.csv."""
    archivo_a_procesar = obtener_archivo_csv() if not input_file else input_file
    
    if not archivo_a_procesar or not os.path.exists(archivo_a_procesar):
        print("❌ Error: No se encuentra ningún archivo CSV de Apify en esta carpeta.")
        return

    print(f"📖 Leyendo datos extraídos de Apify desde {archivo_a_procesar}...")
    df = pd.read_csv(archivo_a_procesar, low_memory=False)

    # 1. Columna de Precio (priorizando campos estandarizados de Apify)
    col_precio = None
    candidatos_precio = ['priceInfo/amount', 'priceInfo/price', 'price', 'priceInfo/price/amount', 'propertyPrice']
    for cand in candidatos_precio:
        if cand in df.columns:
            col_precio = cand
            break
            
    if not col_precio:
        col_precio = next((c for c in df.columns if 'price' in c.lower() and 'drop' not in c.lower() and 'm2' not in c.lower()), None)

    # 2. Coordenadas
    col_lat = next((c for c in df.columns if 'latitude' in c.lower() or c == 'lat'), None)
    col_lon = next((c for c in df.columns if 'longitude' in c.lower() or 'lng' in c.lower() or c == 'lon'), None)

    # 3. Zona / Ubicación (municipio o barrio)
    col_zona = None
    candidatos_zona = ['location/municipality', 'municipality', 'location/neighborhood', 'neighborhood', 'address', 'title']
    for cand in candidatos_zona:
        if cand in df.columns:
            col_zona = cand
            break
            
    if not col_zona:
        col_zona = next((c for c in df.columns if 'municipality' in c.lower() or 'neighborhood' in c.lower() or 'address' in c.lower()), df.columns[0])

    print(f"🔍 Columnas detectadas:")
    print(f" - Precio: {col_precio}")
    print(f" - Latitud: {col_lat}")
    print(f" - Longitud: {col_lon}")
    print(f" - Zona/Ubicación: {col_zona}")

    df_clean = df.dropna(subset=[col_precio, col_lat, col_lon, col_zona]).copy()
    df_clean[col_precio] = pd.to_numeric(df_clean[col_precio], errors='coerce')

    # ELIMINAR PRECIOS TRAMPA / FALSOS DE 1€ O MENORES A 150€
    df_clean = df_clean[df_clean[col_precio] >= 150].copy()

    # Función para limpiar el nombre de la zona (eliminar prefijos como "Detached house in", "Flat in", etc.)
    def limpiar_nombre_zona(texto):
        texto = str(texto)
        # Quitar tipos de propiedad en inglés/español al inicio del texto
        texto = re.sub(r'^(Flat in|Apartment in|Detached house in|House in|Studio in|Duplex in|Penthouse in|Room in|Piso en|Casa en|Habitación en)\s+', '', texto, flags=re.IGNORECASE)
        return texto.strip()

    df_clean[col_zona] = df_clean[col_zona].apply(limpiar_nombre_zona)

    if df_clean.empty:
        print("⚠️ Atención: No se encontraron registros con precios reales superiores a 150 €.")
        return

    resumen = df_clean.groupby(col_zona).agg(
        precio_habitacion=(col_precio, 'median'),
        precio_piso=(col_precio, lambda x: round(x.median() * 2.2, 1)),
        lat=(col_lat, 'mean'),
        lon=(col_lon, 'mean')
    ).reset_index()

    # Formatear al esquema de MatchMyZone
    resumen.rename(columns={col_zona: 'nombre'}, inplace=True)
    
    resumen['tiempo_trayecto'] = 15
    resumen['renta_media_ine'] = "14.800 €/año"
    resumen['tags'] = "metro_directo,ambiente_joven,comercio_local"

    resumen['precio_habitacion'] = resumen['precio_habitacion'].round(1)
    resumen['precio_piso'] = resumen['precio_piso'].round(1)
    resumen['lat'] = resumen['lat'].round(4)
    resumen['lon'] = resumen['lon'].round(4)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    resumen.to_csv(OUTPUT_PATH, index=False)
    
    print(f"✅ ¡Proceso completado con éxito! Guardado en: {OUTPUT_PATH}")
    print(f"Se han procesado {len(resumen)} zonas reales con precios corregidos.")

if __name__ == "__main__":
    procesar_csv_apify(RAW_CSV_PATH)
