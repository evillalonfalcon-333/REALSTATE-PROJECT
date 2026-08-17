from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import ast
import os

app = FastAPI(
    title="MatchMyZone API",
    description="Backend de recomendación de zonas de residencia en la Comunitat Valenciana",
    version="1.0.0"
)

# ------------------------------------------------------------------
# 1. MODELOS DE DATOS
# ------------------------------------------------------------------
class UserPreferences(BaseModel):
    nombre: Optional[str] = "Usuario"
    presupuesto_max: float
    tipo_vivienda: str
    modalidad_laboral: str
    tiempo_max_trayecto: int
    tags_deseados: List[str]

class ZoneResult(BaseModel):
    nombre: str
    precio_estimado: float
    tiempo_trayecto: int
    renta_media_ine: str
    match_score: float
    desglose_score: dict
    lat: float
    lon: float

# ------------------------------------------------------------------
# 2. CARGA DE DATOS DESDE CSV
# ------------------------------------------------------------------
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "zonas_cv.csv")

def cargar_datos():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        # Convertir la cadena del CSV a lista en la columna tags
        df['tags'] = df['tags'].apply(lambda x: [t.strip() for t in x.split(',')] if isinstance(x, str) else x)
        return df
    else:
        # Fallback si no encuentra el CSV
        return pd.DataFrame()

# ------------------------------------------------------------------
# 3. ENDPOINTS Y LÓGICA DEL ALGORITMO
# ------------------------------------------------------------------
@app.get("/")
def read_root():
    return {"status": "ok", "message": "MatchMyZone CV API Activa"}

@app.post("/match", response_model=List[ZoneResult])
def calculate_matches(prefs: UserPreferences):
    df = cargar_datos()
    if df.empty:
        return []

    # Determinar el precio según tipo de vivienda
    if prefs.tipo_vivienda == "Habitación":
        df["precio_evaluado"] = df["precio_habitacion"]
    else:
        df["precio_evaluado"] = df["precio_piso"]

    # ===============================================================
    # FILTROS DUROS (HARD FILTERS)
    # ===============================================================
    df = df[df["precio_evaluado"] <= prefs.presupuesto_max]

    if prefs.modalidad_laboral != "Remoto":
        df = df[df["tiempo_trayecto"] <= prefs.tiempo_max_trayecto]

    if df.empty:
        return []

    # ===============================================================
    # FILTROS BLANDOS (PONDERACIÓN MATCH SCORE)
    # ===============================================================
    resultados = []

    for _, row in df.iterrows():
        # A) Puntuación por Precio (30%)
        ahorro_ratio = (prefs.presupuesto_max - row["precio_evaluado"]) / prefs.presupuesto_max
        score_precio = min(1.0, 0.7 + (ahorro_ratio * 0.3))

        # B) Puntuación por Tiempo de Trayecto (30%)
        if prefs.tiempo_max_trayecto > 0:
            ratio_tiempo = 1.0 - (row["tiempo_trayecto"] / prefs.tiempo_max_trayecto)
            score_tiempo = max(0.5, ratio_tiempo)
        else:
            score_tiempo = 1.0

        # C) Puntuación por Tags / Estilo de Vida (40%)
        tags_zona = set(row["tags"])
        tags_usuario = set(prefs.tags_deseados)

        if len(tags_usuario) > 0:
            coincidencias = len(tags_zona.intersection(tags_usuario))
            score_tags = coincidencias / len(tags_usuario)
        else:
            score_tags = 1.0

        # SCORE FINAL
        match_score = (score_precio * 0.30) + (score_tiempo * 0.30) + (score_tags * 0.40)
        match_score_pct = round(match_score * 100, 1)

        resultados.append({
            "nombre": row["nombre"],
            "precio_estimado": float(row["precio_evaluado"]),
            "tiempo_trayecto": int(row["tiempo_trayecto"]),
            "renta_media_ine": str(row["renta_media_ine"]),
            "match_score": match_score_pct,
            "desglose_score": {
                "precio": round(score_precio * 100, 1),
                "tiempo": round(score_tiempo * 100, 1),
                "servicios_estilo_vida": round(score_tags * 100, 1)
            },
            "lat": float(row["lat"]),
            "lon": float(row["lon"])
        })

    return sorted(resultados, key=lambda x: x["match_score"], reverse=True)
