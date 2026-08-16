import streamlit as st
import requests

# Configuración de la página
st.set_page_config(
    page_title="Recomendador de Vivienda Joven",
    page_icon="🏠",
    layout="wide"
)

# URL de tu API desplegada en Render
API_URL = "https://realstate-project-atdg.onrender.com/recomendar"

# Título de la aplicación
st.title("🏠 Buscador de Zona & Match Score")
st.markdown("Encuentra la zona ideal según tu presupuesto, transporte y estilo de vida.")

# Sidebar: Formulario de preferencias
st.sidebar.header("🎯 Tus Preferencias")

nombre = st.sidebar.text_input("Tu Nombre", value="Enrique")
presupuesto = st.sidebar.slider("Presupuesto máximo (€/mes)", min_value=200, max_value=1200, value=450, step=25)
tipo_vivienda = st.sidebar.selectbox("Tipo de vivienda", options=["habitacion", "piso"], format_func=lambda x: "Habitación" if x == "habitacion" else "Piso completo")
modalidad = st.sidebar.selectbox("Modalidad laboral", options=["hibrido", "presencial", "remoto"], format_func=lambda x: x.capitalize())
tiempo_max = st.sidebar.slider("Tiempo máx. de trayecto (minutos)", min_value=10, max_value=90, value=30, step=5)

st.sidebar.subheader("Estilo de vida & Servicios")
tags_opciones = [
    "metro_directo", "gimnasio", "ambiente_joven", 
    "zonas_verdes", "playa", "comercio_local", "ocio_nocturno"
]
tags_seleccionados = st.sidebar.multiselect(
    "¿Qué valoras en tu zona?",
    options=tags_opciones,
    default=["metro_directo", "gimnasio", "ambiente_joven"]
)

# Botón para procesar la recomendación
if st.sidebar.button("🔍 Buscar Zonas Compatibles", type="primary"):
    payload = {
        "nombre": nombre,
        "presupuesto_max": float(presupuesto),
        "tipo_vivienda": tipo_vivienda,
        "modalidad_laboral": modalidad,
        "tiempo_max_min": int(tiempo_max),
        "tags_deseados": tags_seleccionados
    }

    with st.spinner("Calculando Match Scores en vivo..."):
        try:
            response = requests.post(API_URL, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                st.success(f"¡Hola {data['usuario']}! Hemos encontrado {data['total_matches_viables']} zonas compatibles para ti.")

                # Desplegar los resultados en tarjetas
                for rec in data["recomendaciones"]:
                    score = rec["match_score"]
                    
                    with st.container():
                        st.markdown("---")
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.subheader(f"📍 {rec['zona']}")
                            st.caption(f"Renta media INE: {rec['renta_media_persona_ine']:,.0f} €/año")
                        
                        with col2:
                            st.metric("Precio Est. / mes", f"{rec['precio_estimado_mes']} €")
                            st.caption(f"⏱️ Trayecto: {rec['tiempo_trayecto_min']} min")

                        with col3:
                            st.metric("Match Score", f"{score}%")
                            st.progress(score / 100.0)

                        # Desglose desplegable
                        with st.expander("Ver desglose del Match Score"):
                            d = rec["desglose"]
                            subcol1, subcol2, subcol3, subcol4 = st.columns(4)
                            subcol1.metric("Precio", f"{d['precio']}%")
                            subcol2.metric("Transporte", f"{d['transporte']}%")
                            subcol3.metric("Estilo", f"{d['estilo']}%")
                            subcol4.metric("Servicios", f"{d['servicios']}%")

            else:
                st.error(f"Error al conectar con la API ({response.status_code})")
        except Exception as e:
            st.error(f"No se pudo conectar con el servidor: {e}")
