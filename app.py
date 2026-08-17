import streamlit as st
import requests
import pandas as pd

# ------------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------------------------------
st.set_page_config(
    page_title="MatchMyZone - Buscador de Vivienda",
    page_icon="🏠",
    layout="wide"
)

# URL de tu backend desplegado en Render (o localhost si estás en pruebas)
API_URL = "https://realstate-project-atdg.onrender.com/match"

# ------------------------------------------------------------------
# BARRA LATERAL: PREFERENCIAS DEL USUARIO
# ------------------------------------------------------------------
st.sidebar.header("🎯 Tus Preferencias")

nombre = st.sidebar.text_input("Tu Nombre", value="Enrique")
presupuesto_max = st.sidebar.slider("Presupuesto máximo (€/mes)", 200, 1500, 775, step=25)
tipo_vivienda = st.sidebar.selectbox("Tipo de vivienda", ["Habitación", "Piso completo"])
modalidad_laboral = st.sidebar.selectbox("Modalidad laboral", ["Híbrido", "Presencial", "Remoto"])
tiempo_max_trayecto = st.sidebar.slider("Tiempo máx. de trayecto (minutos)", 5, 60, 30, step=5)

st.sidebar.subheader("Estilo de vida & Servicios")
tags_opciones = ["metro_directo", "gimnasio", "ambiente_joven", "zonas_verdes", "comercio_local", "playa"]
tags_seleccionados = st.sidebar.multiselect(
    "¿Qué valoras en tu zona?",
    options=tags_opciones,
    default=["metro_directo", "gimnasio", "ambiente_joven"]
)

btn_buscar = st.sidebar.button("🔍 Buscar Zonas Compatibles", type="primary")

# ------------------------------------------------------------------
# CUERPO PRINCIPAL
# ------------------------------------------------------------------
st.title("🏠 Buscador de Zona & Match Score")
st.write("Encuentra la zona ideal según tu presupuesto, transporte y estilo de vida.")

# Estado inicial antes de hacer clic en buscar
if not btn_buscar and "busqueda_realizada" not in st.session_state:
    st.info("👈 Ajusta tus filtros en la barra lateral y haz clic en **Buscar Zonas Compatibles** para ver los resultados.")

elif btn_buscar or st.session_state.get("busqueda_realizada"):
    st.session_state["busqueda_realizada"] = True

    # Preparar el JSON de datos para FastAPI
    payload = {
        "nombre": nombre,
        "presupuesto_max": presupuesto_max,
        "tipo_vivienda": tipo_vivienda,
        "modalidad_laboral": modalidad_laboral,
        "tiempo_max_trayecto": tiempo_max_trayecto,
        "tags_deseados": tags_seleccionados
    }

    with st.spinner("Conectando con el servidor y calculando las mejores zonas..."):
        try:
            # Timeout ampliado a 30s para prevenir cortes si Render está 'despertando'
            response = requests.post(API_URL, json=payload, timeout=30)

            if response.status_code == 200:
                zonas = response.json()

                # ===================================================
                # MANEJO DE RESULTADOS VACÍOS (MODIFICACIÓN SUGERIDA)
                # ===================================================
                if not zonas:
                    st.warning(
                        f"⚠️ **No se encontraron zonas compatibles para {nombre}.**\n\n"
                        f"Los filtros estrictos no han devuelto ningún resultado dentro de los "
                        f"**{tiempo_max_trayecto} minutos** de trayecto o con un presupuesto máximo de "
                        f"**{presupuesto_max} €/mes**.\n\n"
                        f"💡 *Sugerencia:* Prueba a ampliar el tiempo máximo de trayecto o ajustar el presupuesto en el panel izquierdo."
                    )
                else:
                    st.success(f"¡Hola {nombre}! Hemos encontrado {len(zonas)} zonas compatibles para ti.")

                    # Preparemos lista de coordenadas para renderizar el mapa
                    mapa_data = []

                    # Mostrar resultados en tarjetas
                    for zona in zonas:
                        st.markdown("---")
                        
                        # Guardar puntos para el mapa
                        mapa_data.append({
                            "lat": zona["lat"],
                            "lon": zona["lon"],
                            "nombre": zona["nombre"]
                        })

                        col1, col2, col3 = st.columns([3, 2, 2])

                        with col1:
                            st.subheader(f"📍 {zona['nombre']}")
                            st.caption(f"Renta media INE: {zona['renta_media_ine']}")

                        with col2:
                            st.caption("Precio Est. / mes")
                            st.markdown(f"### {zona['precio_estimado']} €")
                            st.caption(f"⏱️ Trayecto: {zona['tiempo_trayecto']} min")

                        with col3:
                            st.caption("Match Score")
                            st.markdown(f"### {zona['match_score']}%")
                            st.progress(zona['match_score'] / 100.0)

                        # Desplegable interactivo con el desglose del Score
                        with st.expander("👉 Ver desglose del Match Score"):
                            desglose = zona.get("desglose_score", {})
                            d_col1, d_col2, d_col3 = st.columns(3)
                            
                            d_col1.metric("Ahorro / Precio", f"{desglose.get('precio', 0)}%")
                            d_col2.metric("Proximidad / Tiempo", f"{desglose.get('tiempo', 0)}%")
                            d_col3.metric("Servicios & Estilo de Vida", f"{desglose.get('servicios_estilo_vida', 0)}%")

                    # ===================================================
                    # MAPA INTERACTIVO CON RESULTADOS
                    # ===================================================
                    if mapa_data:
                        st.markdown("---")
                        st.subheader("🗺️ Ubicación de Zonas Recomendadas")
                        df_mapa = pd.DataFrame(mapa_data)
                        st.map(df_mapa, zoom=10)

        except requests.exceptions.Timeout:
            st.error("⏳ El servidor en Render tardó demasiado en responder (Timeout). Inténtalo de nuevo en unos segundos mientras termina de reactivarse.")
        except requests.exceptions.RequestException as e:
            st.error(f"No se pudo conectar con el servidor: {e}")
