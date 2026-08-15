from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import requests

# ==============================================================================
# 1. CONFIGURACIÓN Y MODELOS DE DATOS (PYDANTIC)
# ==============================================================================

app = FastAPI(
    title="API de Recomendación de Vivienda Joven",
    description="Backend en FastAPI que calcula el Match Score (%) de compatibilidad "
                "entre jóvenes y zonas/municipios según presupuesto, transporte y estilo de vida.",
    version="1.0.0"
)

# Permitir peticiones desde cualquier frontend (React, Flutter, Vue, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PerfilUsuario(BaseModel):
    nombre: str = Field(..., example="Carlos")
    presupuesto_max: float = Field(..., gt=0, description="Presupuesto máximo en euros/mes", example=450.0)
    tipo_vivienda: str = Field(default="habitacion", description="'habitacion' o 'piso'", example="habitacion")
    modalidad_laboral: str = Field(..., description="'remoto', 'hibrido' o 'presencial'", example="hibrido")
    tiempo_max_min: int = Field(..., ge=0, description="Tiempo máximo de trayecto tolerado en minutos", example=30)
    tags_deseados: List[str] = Field(
        default=[],
        description="Etiquetas de estilo de vida",
        example=["metro_directo", "gimnasio", "ambiente_joven", "zonas_verdes"]
    )

class DesgloseScore(BaseModel):
    precio: float
    transporte: float
    estilo: float
    servicios: float

class ResultadoZona(BaseModel):
    zona: str
    match_score: float
    precio_estimado_mes: float
    tiempo_trayecto_min: int
    renta_media_persona_ine: float
    desglose: DesgloseScore

class RespuestaRecomendacion(BaseModel):
    usuario: str
    total_zonas_evaluadas: int
    total_matches_viables: int
    recomendaciones: List[ResultadoZona]

# ==============================================================================
# 2. BASE DE DATOS EN MEMORIA (MVP / PROTOTIPO)
# ==============================================================================

def obtener_renta_ine(codigo_municipio: str) -> float:
    """Consulta la API pública del INE para obtener la renta media por persona."""
    url = f"https://servicios.ine.es/wsevents/enContinuo/m/JSON_URL?L=0&T=37633&C={codigo_municipio}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            data = res.json()
            return float(data['Data'][0]['Valor'])
    except Exception:
        pass
    return 13500.0  # Promedio por defecto si falla el INE

BASE_DE_DATOS_ZONAS: List[Dict[str, Any]] = [
    {
        "id": "pat-01",
        "nombre": "Paterna (Centro)",
        "codigo_ine": "46190",
        "precio_m2": 17.5,
        "t_centro_min": 25,
        "tags": ["metro_directo", "gimnasio", "zonas_verdes", "ambiente_joven"],
        "servicios_score": 82.0,
        "renta_ine": obtener_renta_ine("46190")
    },
    {
        "id": "tor-01",
        "nombre": "Torrent (Metro)",
        "codigo_ine": "46244",
        "precio_m2": 16.0,
        "t_centro_min": 22,
        "tags": ["metro_directo", "gimnasio", "ambiente_joven", "comercio_local"],
        "servicios_score": 88.0,
        "renta_ine": obtener_renta_ine("46244")
    },
    {
        "id": "sag-01",
        "nombre": "Sagunto / Puerto",
        "codigo_ine": "46220",
        "precio_m2": 14.0,
        "t_centro_min": 38,
        "tags": ["playa", "comercio_local", "zonas_verdes", "tranquilo"],
        "servicios_score": 75.0,
        "renta_ine": obtener_renta_ine("46220")
    },
    {
        "id": "ruz-01",
        "nombre": "Ruzafa (Valencia Capital)",
        "codigo_ine": "46250",
        "precio_m2": 26.0,
        "t_centro_min": 8,
        "tags": ["ocio_nocturno", "ambiente_joven", "gimnasio", "restauración"],
        "servicios_score": 98.0,
        "renta_ine": obtener_renta_ine("46250")
    }
]

# ==============================================================================
# 3. LÓGICA DEL MOTOR DE MATCH SCORE
# ==============================================================================

def calcular_subscore_precio(p_max: float, p_zona: float) -> float:
    if p_zona <= 0.85 * p_max:
        return 100.0
    elif p_zona <= p_max:
        return 100.0 - 66.6 * ((p_zona - 0.85 * p_max) / p_max)
    else:
        return max(0.0, 90.0 - ((p_zona - p_max) / p_max) * 300.0)

def calcular_subscore_transporte(modalidad: str, t_max: int, t_zona: int) -> float:
    if modalidad == 'remoto':
        return 100.0
    if t_zona <= t_max:
        return 100.0
    minutos_extra = t_zona - t_max
    return max(0.0, 100.0 - (minutos_extra / 10.0) * 15.0)

def calcular_subscore_estilo(tags_user: List[str], tags_zona: List[str]) -> float:
    u_set, z_set = set(tags_user), set(tags_zona)
    union = len(u_set.union(z_set))
    if union == 0:
        return 50.0
    return (len(u_set.intersection(z_set)) / union) * 100.0

def calcular_factor_penalizador(p_max: float, p_zona: float) -> float:
    if p_zona <= p_max:
        return 1.0
    elif p_zona <= 1.15 * p_max:
        return 0.5
    return 0.0  # Cancelado por superar en más del 15% el presupuesto

# ==============================================================================
# 4. ENDPOINTS / RUTAS DE LA API
# ==============================================================================

@app.get("/", tags=["Estado"])
def estado_api():
    """Comprueba que el servidor está online."""
    return {"status": "ok", "mensaje": "API de Recomendación de Vivienda Joven lista"}

@app.get("/zonas", tags=["Catálogo"], response_model=List[Dict[str, Any]])
def listar_zonas():
    """Devuelve el catálogo de zonas registradas en la base de datos."""
    return BASE_DE_DATOS_ZONAS

@app.post("/recomendar", tags=["Recomendador"], response_model=RespuestaRecomendacion)
def procesar_recomendacion(
    perfil: PerfilUsuario, 
    limit: Optional[int] = Query(default=10, ge=1, le=50, description="Límite de resultados a devolver")
):
    """
    Recibe las preferencias del joven y devuelve un ranking ordenado por el **Match Score (%)**.
    """
    resultados = []
    m2_multiplicador = 25.0 if perfil.tipo_vivienda == "habitacion" else 60.0

    for zona in BASE_DE_DATOS_ZONAS:
        precio_estimado = round(zona["precio_m2"] * m2_multiplicador, 2)
        
        # Cálculo de sub-scores
        s_precio = calcular_subscore_precio(perfil.presupuesto_max, precio_estimado)
        s_transporte = calcular_subscore_transporte(perfil.modalidad_laboral, perfil.tiempo_max_min, zona["t_centro_min"])
        s_estilo = calcular_subscore_estilo(perfil.tags_deseados, zona["tags"])
        s_servicios = float(zona["servicios_score"])
        
        # Score Ponderado (40% Precio, 30% Transporte, 20% Estilo, 10% Servicios)
        score_bruto = (s_precio * 0.40) + (s_transporte * 0.30) + (s_estilo * 0.20) + (s_servicios * 0.10)
        
        # Factor Penalizador
        penalizador = calcular_factor_penalizador(perfil.presupuesto_max, precio_estimado)
        final_score = round(score_bruto * penalizador, 1)

        # Solo incluir zonas viables (Match Score > 0)
        if final_score > 0:
            resultados.append(
                ResultadoZona(
                    zona=zona["nombre"],
                    match_score=final_score,
                    precio_estimado_mes=precio_estimado,
                    tiempo_trayecto_min=zona["t_centro_min"],
                    renta_media_persona_ine=zona["renta_ine"],
                    desglose=DesgloseScore(
                        precio=round(s_precio, 1),
                        transporte=round(s_transporte, 1),
                        estilo=round(s_estilo, 1),
                        servicios=round(s_servicios, 1)
                    )
                )
            )

    # Ordenar por el Match Score más alto
    resultados.sort(key=lambda x: x.match_score, reverse=True)

    return RespuestaRecomendacion(
        usuario=perfil.nombre,
        total_zonas_evaluadas=len(BASE_DE_DATOS_ZONAS),
        total_matches_viables=len(resultados),
        recomendaciones=resultados[:limit]
    )
