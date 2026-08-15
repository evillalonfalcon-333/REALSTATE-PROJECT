# 🏠 API de Recomendación de Vivienda Joven

Backend en **FastAPI** que calcula un **Match Score (%)** de compatibilidad entre jóvenes y zonas/municipios según presupuesto, transporte y estilo de vida.

## 📋 Características

- **Match Score inteligente**: Algoritmo que pondera 4 factores:
  - 40% Precio (compatibilidad con presupuesto)
  - 30% Transporte (distancia al centro/trabajo)
  - 20% Estilo de vida (tags/amenidades)
  - 10% Servicios (equipamientos disponibles)

- **Integración con INE**: Consulta datos reales de renta media por municipios
- **CORS habilitado**: Compatible con cualquier frontend (React, Vue, Flutter, etc.)
- **Validación robusta**: Modelos Pydantic con ejemplos y descripciones
- **Documentación interactiva**: Swagger UI incluida

## 🚀 Quick Start

### 1. Clonar repositorio e instalar dependencias
```bash
git clone https://github.com/evillalonfalcon-333/REALSTATE-PROJECT.git
cd REALSTATE-PROJECT
pip install -r requirements.txt
```

### 2. Ejecutar el servidor
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Acceder a la API
- **API base**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 Endpoints

### `GET /` - Estado del servidor
```bash
curl http://localhost:8000/
```
**Respuesta:**
```json
{
  "status": "ok",
  "mensaje": "API de Recomendación de Vivienda Joven lista"
}
```

### `GET /zonas` - Listar todas las zonas
```bash
curl http://localhost:8000/zonas
```

### `POST /recomendar` - Obtener recomendaciones personalizadas
```bash
curl -X POST http://localhost:8000/recomendar \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Carlos",
    "presupuesto_max": 450,
    "tipo_vivienda": "habitacion",
    "modalidad_laboral": "hibrido",
    "tiempo_max_min": 30,
    "tags_deseados": ["metro_directo", "gimnasio", "ambiente_joven", "zonas_verdes"]
  }'
```

**Respuesta ejemplo:**
```json
{
  "usuario": "Carlos",
  "total_zonas_evaluadas": 4,
  "total_matches_viables": 3,
  "recomendaciones": [
    {
      "zona": "Torrent (Metro)",
      "match_score": 89.5,
      "precio_estimado_mes": 400.0,
      "tiempo_trayecto_min": 22,
      "renta_media_persona_ine": 15200.5,
      "desglose": {
        "precio": 100.0,
        "transporte": 95.5,
        "estilo": 75.0,
        "servicios": 88.0
      }
    }
  ]
}
```

## 📊 Parámetros de entrada

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `nombre` | string | Nombre del usuario | "Carlos" |
| `presupuesto_max` | float | Presupuesto máximo mensual (€) | 450.0 |
| `tipo_vivienda` | string | "habitacion" o "piso" | "habitacion" |
| `modalidad_laboral` | string | "remoto", "hibrido" o "presencial" | "hibrido" |
| `tiempo_max_min` | int | Tiempo máximo de trayecto (min) | 30 |
| `tags_deseados` | array | Preferencias de estilo de vida | ["metro_directo", "gimnasio"] |
| `limit` | int (query) | Máximo de resultados (1-50) | 10 |

## 🏙️ Zonas registradas

- **Paterna (Centro)** - Centro económico, bien conectado
- **Torrent (Metro)** - Excelente transporte, ambiente joven
- **Sagunto / Puerto** - Playa, tranquilo, más económico
- **Ruzafa (Valencia Capital)** - Zona premium, ocio nocturno

## 🎯 Lógica de cálculo

### Match Score = (Precio × 0.40 + Transporte × 0.30 + Estilo × 0.20 + Servicios × 0.10) × Factor Penalizador

**Factor Penalizador:**
- `1.0` si el precio está dentro del presupuesto
- `0.5` si excede el presupuesto hasta un 15%
- `0.0` si excede más del 15% (cancelado)

## 📝 Estructura del proyecto

```
main.py                 Aplicación principal FastAPI
requirements.txt        Dependencias Python
README.md              Este archivo
```

## 🔧 Requisitos

- Python 3.8+
- FastAPI 0.104+
- Uvicorn 0.24+
- Requests 2.31+

## 📌 Próximas mejoras

- [ ] Integración con base de datos (PostgreSQL)
- [ ] Autenticación JWT
- [ ] Sistema de favoritos
- [ ] Caché de datos del INE
- [ ] Testing automatizado
- [ ] Docker

## 📄 Licencia

MIT License - Libre para usar y modificar
