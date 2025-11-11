import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="centered")

#Explicación de la Nota Ajustada
@st.dialog("ℹ️ ¿Qué es la Nota Ajustada?", width = "medium")
def mostrar_explicacion_nota_ajustada():
    st.markdown("""
    La **Nota Ajustada** combina la media individual del jugador con la media global del equipo, 
    ponderando además por los **minutos jugados** y los **partidos jugados**.  
    Esto ofrece una medida más justa del rendimiento real: un jugador que haya jugado pocos minutos 
    no se verá tan penalizado ni premiado injustamente.

    **Fórmula:**  
    \n
    \t**(peso_minutos × nota_jugador + k × nota_global) / (peso_minutos + k)**

    **Donde:**  
    - `peso_minutos`: minutos jugados totales ÷ 90 (equivale a partidos completos jugados)  
    - `nota_jugador`: nota media del jugador  
    - `nota_global`: media global del equipo  
    - `k`: constante de suavizado (en este caso k = 25). Este es el número de partidos que se considera como peso mínimo teniendo en cuenta que un equipo juega alrededor de 60 partidos y un jugador que es titular indiscutible suele jugar alrededor de 50 partidos, equivalente a unos ~2250 minutos jugados (25×90).
    """)


# 🔹 Ajustar el ancho del contenido principal
st.markdown("""
    <style>
        .block-container {
            max-width: 1000px;
            padding-left: 2rem;
            padding-right: 2rem;
            margin: auto;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# 📂 Subir archivo CSV
# -------------------------------
st.title("📊 Análisis del Equipo y Estadísticas por Jugador según tus Notas Personales y más.")

# ------------------------------------------
# Botón para descargar la plantilla Excel
# ------------------------------------------
with st.expander("ℹ️ **IMPORTANTE** ¿Cómo usar la plantilla de Excel?"):
    st.markdown("""
    Para facilitar la carga de datos en la app, usa la plantilla de Excel predefinida.  
    Sigue estos pasos:

    1. **Descarga el archivo** usando el botón Descargar plantilla de Excel.
    2. **Crea una nueva hoja de cálculo en Google Sheets**.
    3. En la barra de navegación de Google Sheets, ve a **Archivo → Importar**.
    4. Se abrirá un pop-up. Dirígete a la pestaña **Subir** y agrega el archivo `.xlsx` descargado anteriormente.
    5. ¡Listo! Ya tienes la plantilla lista para rellenar con los datos del Equipo.
    6. Una vez que hayas completado la plantilla, descárgala como `.csv` desde Google Sheets, Archivo → Descargar → Valores separados por comas (.csv).

    💡 **Tips adicionales:**  
    - Puedes cambiar los nombres de los jugadores y las competiciones para adaptarlo a cualquier otro equipo.  
    - Guarda los cambios y luego descarga como `.csv` si quieres subirlo a la app.
    """)

with open("plantilla_estadisticas.xlsx", "rb") as f:
    excel_bytes = f.read()

st.download_button(
    label="📥 Descargar plantilla de Excel",
    data=excel_bytes,
    file_name="plantilla_estadisticas.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# -------------------------------
# Subir archivo CSV del usuario
# -------------------------------
archivo_usuario = st.file_uploader(
    "Sube tu archivo CSV con las estadísticas",
    type=["csv"]
)

archivo_ejemplo = "ejemplo.csv"
if archivo_usuario is None:
    st.info("Mostrando archivo de ejemplo.")
    df = pd.read_csv(archivo_ejemplo, dayfirst=True)
else:
    df = pd.read_csv(archivo_usuario, dayfirst=True)

# -------------------------------
# Validación de columnas
# -------------------------------
columnas_esperadas = [
    "FECHA", "COMPETICION", "NOMBRE", "GOLES", 
    "ASISTENCIAS", "NOTA", "MINS_JUGADOS", "GOLES_EN_CONTRA", "RIVAL"
]
faltantes = [col for col in columnas_esperadas if col not in df.columns]

if faltantes:
    st.error(f"Archivo CSV inválido. Faltan las columnas: {', '.join(faltantes)}")
    st.stop()

# Formato de columnas
df["FECHA"] = pd.to_datetime(df["FECHA"], dayfirst=True)
df["G/A"] = df["GOLES"] + df["ASISTENCIAS"]
df["DIFERENCIA_GOLES"] = df["GOLES"] - df["GOLES_EN_CONTRA"]

# -------------------------------
# Filtros generales
# -------------------------------
st.sidebar.header("Filtros generales")
competiciones = sorted(df["COMPETICION"].unique())
comp_filtro = st.sidebar.multiselect(
    "Selecciona las competiciones", options=competiciones, default=competiciones
)
df_filtrado = df[df["COMPETICION"].isin(comp_filtro)].copy()
if df_filtrado.empty:
    st.warning("Selecciona al menos una competición.")
    st.stop()

# -------------------------------
# Filtro especial: Primera / Segunda vuelta (solo Liga)
# -------------------------------
if "Liga" in comp_filtro:
    st.sidebar.markdown("### ⚙️ Configuración de la Liga", help="Por defecto es 38 (LaLiga). Cambia este valor si tu liga tiene otro número de jornadas.")
    total_jornadas_input = st.sidebar.number_input(
        "Número total de jornadas", min_value=1, max_value=60, value=38, step=1
    )
    vuelta = st.sidebar.radio(
        "Selecciona el tramo de la Liga", ["Toda la Liga", "Primera vuelta", "Segunda vuelta"], index=0
    )

    liga_dates = (
        df[df["COMPETICION"] == "Liga"]
        .sort_values("FECHA")["FECHA"]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    date_to_jornada = {fecha: i+1 for i, fecha in enumerate(liga_dates)}
    df_filtrado.loc[df_filtrado["COMPETICION"] == "Liga", "JORNADA"] = df_filtrado.loc[
        df_filtrado["COMPETICION"] == "Liga", "FECHA"
    ].map(date_to_jornada)

    corte_liga = total_jornadas_input // 2
    if vuelta == "Primera vuelta":
        df_filtrado = df_filtrado[~(
            (df_filtrado["COMPETICION"] == "Liga") & (df_filtrado["JORNADA"] > corte_liga)
        )]
    elif vuelta == "Segunda vuelta":
        df_filtrado = df_filtrado[~(
            (df_filtrado["COMPETICION"] == "Liga") & (df_filtrado["JORNADA"] <= corte_liga)
        )]

# -------------------------------
# SECCIÓN 1: Estadísticas por jugador o equipo (hover + resumen)
# -------------------------------
st.header("📈 Estadísticas individuales / Equipo")

opciones_jugadores = ["Equipo General"] + sorted(df["NOMBRE"].unique())
jugador_sel = st.selectbox("Selecciona el jugador o Equipo General", opciones_jugadores)
tipo_stat = st.selectbox("Selecciona la estadística a mostrar", ["NOTA", "GOLES", "ASISTENCIAS", "G/A"])

if jugador_sel == "Equipo General":
    df_equipo = (
        df_filtrado.groupby(["FECHA", "COMPETICION", "RIVAL"])
        .agg({
            "NOTA":"mean",
            "GOLES":"sum",
            "ASISTENCIAS":"sum",
            "G/A":"sum",
            "GOLES_EN_CONTRA":"max"
        })
        .reset_index()
        .sort_values("FECHA")
    )
    
    # Redondeamos nota para hover
    df_equipo["NOTA"] = df_equipo["NOTA"].round(2)
    
    hover_cols = ["COMPETICION", "RIVAL", "GOLES_EN_CONTRA", "GOLES", "ASISTENCIAS", "G/A", "NOTA"]
    fig = px.line(df_equipo, x="FECHA", y=tipo_stat, markers=True)
    fig.update_traces(
        customdata=df_equipo[hover_cols].values,
        hovertemplate=(
            "Competición: %{customdata[0]}<br>" +
            "Rival: %{customdata[1]}<br>" +
            "Goles en contra: %{customdata[2]}<br>" +
            "Goles: %{customdata[3]}<br>" +
            "Asistencias: %{customdata[4]}<br>" +
            "G/A: %{customdata[5]}<br>" +
            "Nota: %{customdata[6]}"
        )
    )
else:
    df_jugador = df_filtrado[df_filtrado["NOMBRE"]==jugador_sel].sort_values("FECHA")
    hover_cols = ["COMPETICION", "RIVAL", "GOLES_EN_CONTRA", "GOLES", "ASISTENCIAS", "G/A", "NOTA"]
    fig = px.line(df_jugador, x="FECHA", y=tipo_stat, markers=True)
    fig.update_traces(
        customdata=df_jugador[hover_cols].values,
        hovertemplate=(
            "Competición: %{customdata[0]}<br>" +
            "Rival: %{customdata[1]}<br>" +
            "Goles en contra: %{customdata[2]}<br>" +
            "Goles: %{customdata[3]}<br>" +
            "Asistencias: %{customdata[4]}<br>" +
            "G/A: %{customdata[5]}<br>" +
            "Nota: %{customdata[6]}"
        )
    )

fig.update_layout(
    xaxis_title="MESES",
    yaxis_title=tipo_stat,
    hovermode="x unified"
)
st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# Tabla resumen con estadística seleccionada (Sección 1)
# -------------------------------
def calcular_por_partido(total, partidos):
    return round(total / partidos, 2) if partidos else 0

if jugador_sel == "Equipo General":
    fila = {
        "NOMBRE": "Equipo General",
        "PARTIDOS_JUGADOS": df_filtrado["FECHA"].nunique(),
        "MINUTOS_TOTALES": df_filtrado["MINS_JUGADOS"].sum()
    }
    partidos = fila["PARTIDOS_JUGADOS"]

    if tipo_stat == "NOTA":
        nota_media = df_filtrado["NOTA"].mean()
        k = 25
        media_global = df_filtrado["NOTA"].mean()
        nota_ajustada = ((df_filtrado["MINS_JUGADOS"].sum()/90*nota_media + k*media_global) / ((df_filtrado["MINS_JUGADOS"].sum()/90)+k))
        fila.update({"NOTA_AJUSTADA": round(nota_ajustada,2), "NOTA_MEDIA": round(nota_media,2)})
        columnas = ["NOMBRE","NOTA_AJUSTADA","NOTA_MEDIA","PARTIDOS_JUGADOS","MINUTOS_TOTALES"]

    elif tipo_stat == "GOLES":
        total = df_filtrado["GOLES"].sum()
        goles_en_contra_total = df_filtrado[["FECHA","GOLES_EN_CONTRA"]].drop_duplicates()["GOLES_EN_CONTRA"].sum()
        diferencia_total = total - goles_en_contra_total
        fila.update({"GOLES": total, "GOLES_EN_CONTRA": goles_en_contra_total, "DIFERENCIA_GOLES": diferencia_total})
        fila["GOLES_POR_PARTIDO"] = calcular_por_partido(total, partidos)
        columnas = ["NOMBRE","GOLES","GOLES_POR_PARTIDO","GOLES_EN_CONTRA","DIFERENCIA_GOLES","PARTIDOS_JUGADOS","MINUTOS_TOTALES"]

    elif tipo_stat == "ASISTENCIAS":
        total = df_filtrado["ASISTENCIAS"].sum()
        fila.update({"ASISTENCIAS": total, "ASISTENCIAS_POR_PARTIDO": calcular_por_partido(total, partidos)})
        columnas = ["NOMBRE","ASISTENCIAS","ASISTENCIAS_POR_PARTIDO","PARTIDOS_JUGADOS","MINUTOS_TOTALES"]

    elif tipo_stat == "G/A":
        total = df_filtrado["G/A"].sum()
        fila.update({"G/A": total, "G/A_POR_PARTIDO": calcular_por_partido(total, partidos)})
        columnas = ["NOMBRE","G/A","G/A_POR_PARTIDO","PARTIDOS_JUGADOS","MINUTOS_TOTALES"]

    resumen = pd.DataFrame([fila])[columnas]

else:
    df_j = df_filtrado[df_filtrado["NOMBRE"]==jugador_sel]
    fila = {
        "NOMBRE": jugador_sel,
        "PARTIDOS_JUGADOS": df_j["FECHA"].nunique(),
        "MINUTOS_TOTALES": df_j["MINS_JUGADOS"].sum()
    }
    partidos = fila["PARTIDOS_JUGADOS"]

    if tipo_stat == "NOTA":
        nota_media = df_j["NOTA"].mean()
        k = 25
        media_global = df_filtrado["NOTA"].mean()
        nota_ajustada = ((df_j["MINS_JUGADOS"].sum()/90*nota_media + k*media_global) / ((df_j["MINS_JUGADOS"].sum()/90)+k))
        fila.update({"NOTA_AJUSTADA": round(nota_ajustada,2), "NOTA_MEDIA": round(nota_media,2)})
        columnas = ["NOMBRE","NOTA_AJUSTADA","NOTA_MEDIA","PARTIDOS_JUGADOS","MINUTOS_TOTALES"]

    elif tipo_stat == "GOLES":
        total = df_j["GOLES"].sum()
        fila.update({"GOLES": total, "GOLES_POR_PARTIDO": calcular_por_partido(total, partidos)})
        columnas = ["NOMBRE","GOLES","GOLES_POR_PARTIDO","PARTIDOS_JUGADOS","MINUTOS_TOTALES"]

    elif tipo_stat == "ASISTENCIAS":
        total = df_j["ASISTENCIAS"].sum()
        fila.update({"ASISTENCIAS": total, "ASISTENCIAS_POR_PARTIDO": calcular_por_partido(total, partidos)})
        columnas = ["NOMBRE","ASISTENCIAS","ASISTENCIAS_POR_PARTIDO","PARTIDOS_JUGADOS","MINUTOS_TOTALES"]

    elif tipo_stat == "G/A":
        total = df_j["G/A"].sum()
        fila.update({"G/A": total, "G/A_POR_PARTIDO": calcular_por_partido(total, partidos)})
        columnas = ["NOMBRE","G/A","G/A_POR_PARTIDO","PARTIDOS_JUGADOS","MINUTOS_TOTALES"]

    resumen = pd.DataFrame([fila])[columnas]

# Encabezado con enlace informativo
st.markdown("### 📋 Resumen de participación")
st.button("ℹ️ ¿Qué es la Nota Ajustada?", on_click=mostrar_explicacion_nota_ajustada, key="nota_ajustada_btn")
st.dataframe(resumen, use_container_width=True, hide_index=True)



# -------------------------------
# SECCIÓN 2: Comparador de jugadores (hover + resumen)
# -------------------------------
st.header("🆚 Comparador de jugadores")

jugadores = sorted(df["NOMBRE"].unique())
jugadores_comparar = st.multiselect(
    "Selecciona los jugadores a comparar",
    jugadores,
    default=[jugadores[0], jugadores[1]] if len(jugadores) > 1 else jugadores
)
tipo_comparar = st.selectbox("Selecciona la estadística a comparar", ["NOTA","GOLES","ASISTENCIAS","G/A"])

fig2 = px.line()
for j in jugadores_comparar:
    df_temp = df_filtrado[df_filtrado["NOMBRE"] == j].sort_values("FECHA")
    hover_cols = ["COMPETICION", "RIVAL", "GOLES_EN_CONTRA", "GOLES", "ASISTENCIAS", "G/A", "NOTA"]
    fig2.add_scatter(
        x=df_temp["FECHA"],
        y=df_temp[tipo_comparar],
        mode='lines+markers',
        name=j,
        hovertemplate=(
            "Competición: %{customdata[0]}<br>" +
            "Rival: %{customdata[1]}<br>" +
            "Goles en contra: %{customdata[2]}<br>" +
            "Goles: %{customdata[3]}<br>" +
            "Asistencias: %{customdata[4]}<br>" +
            "G/A: %{customdata[5]}<br>" +
            "Nota: %{customdata[6]}"
        ),
        customdata=df_temp[hover_cols].values
    )

fig2.update_layout(
    title=f"Comparativa de {tipo_comparar} entre jugadores",
    xaxis_title="MESES",
    yaxis_title=tipo_comparar,
    hovermode="x unified"
)
st.plotly_chart(fig2, use_container_width=True)

# -------------------------------
# Tabla resumen comparativa con estadística seleccionada (Sección 2)
# -------------------------------
resumen = []
for jugador in jugadores_comparar:
    df_j = df_filtrado[df_filtrado["NOMBRE"] == jugador]
    partidos = df_j["FECHA"].nunique()
    fila = {
        "NOMBRE": jugador,
        "PARTIDOS_JUGADOS": partidos,
        "MINUTOS_TOTALES": df_j["MINS_JUGADOS"].sum()
    }

    if tipo_comparar == "NOTA":
        nota_media = df_j["NOTA"].mean()
        k = 25
        media_global = df_filtrado["NOTA"].mean()
        nota_ajustada = ((df_j["MINS_JUGADOS"].sum()/90*nota_media + k*media_global) / ((df_j["MINS_JUGADOS"].sum()/90)+k))
        fila.update({"NOTA_AJUSTADA": round(nota_ajustada,2), "NOTA_MEDIA": round(nota_media,2)})
        columnas = ["NOMBRE","NOTA_AJUSTADA","NOTA_MEDIA","PARTIDOS_JUGADOS","MINUTOS_TOTALES"]

    elif tipo_comparar == "GOLES":
        total = df_j["GOLES"].sum()
        fila.update({"GOLES": total, "GOLES_POR_PARTIDO": calcular_por_partido(total, partidos)})
        columnas = ["NOMBRE","GOLES","GOLES_POR_PARTIDO","PARTIDOS_JUGADOS","MINUTOS_TOTALES"]

    elif tipo_comparar == "ASISTENCIAS":
        total = df_j["ASISTENCIAS"].sum()
        fila.update({"ASISTENCIAS": total, "ASISTENCIAS_POR_PARTIDO": calcular_por_partido(total, partidos)})
        columnas = ["NOMBRE","ASISTENCIAS","ASISTENCIAS_POR_PARTIDO","PARTIDOS_JUGADOS","MINUTOS_TOTALES"]

    elif tipo_comparar == "G/A":
        total = df_j["G/A"].sum()
        fila.update({"G/A": total, "G/A_POR_PARTIDO": calcular_por_partido(total, partidos)})
        columnas = ["NOMBRE","G/A","G/A_POR_PARTIDO","PARTIDOS_JUGADOS","MINUTOS_TOTALES"]

    resumen.append(pd.DataFrame([fila])[columnas])

st.markdown("### 📋 Resumen de participación")
st.button("ℹ️ ¿Qué es la Nota Ajustada?", on_click=mostrar_explicacion_nota_ajustada, key="nota_ajustada_btn2")
st.dataframe(pd.concat(resumen, ignore_index=True), use_container_width=True, hide_index=True)



# -------------------------------
# SECCIÓN 3: Ranking por notas medias
# -------------------------------
st.header("🏆 Ranking por notas medias")
media_global = df_filtrado["NOTA"].mean()
k = 25

ranking_notas = (
    df_filtrado.groupby("NOMBRE")
    .agg({"NOTA":"mean","FECHA":"nunique","MINS_JUGADOS":"sum"})
    .rename(columns={"FECHA":"PARTIDOS_JUGADOS","MINS_JUGADOS":"MINUTOS_TOTALES","NOTA":"NOTA_MEDIA"})
    .reset_index()
)
ranking_notas["PESO_MINUTOS"] = ranking_notas["MINUTOS_TOTALES"] / 90
ranking_notas["NOTA_AJUSTADA"] = (
    (ranking_notas["PESO_MINUTOS"]*ranking_notas["NOTA_MEDIA"] + k*media_global) /
    (ranking_notas["PESO_MINUTOS"] + k)
).round(2)
ranking_notas["NOTA_MEDIA"] = ranking_notas["NOTA_MEDIA"].round(2)

equipo_notas = pd.DataFrame({
    "NOMBRE": ["Equipo General"],
    "NOTA_MEDIA": [df_filtrado["NOTA"].mean().round(2)],
    "NOTA_AJUSTADA": [df_filtrado["NOTA"].mean().round(2)],
    "PARTIDOS_JUGADOS": [df_filtrado["FECHA"].nunique()],
    "MINUTOS_TOTALES": [df_filtrado["MINS_JUGADOS"].sum()]
})

ranking_jugadores = ranking_notas.sort_values("NOTA_AJUSTADA", ascending=False).reset_index(drop=True)
ranking_jugadores.insert(0, "POS", range(1, len(ranking_jugadores)+1))
equipo_notas.insert(0, "POS", ["-"])

ranking_jugadores = ranking_jugadores[[
    "POS", "NOMBRE", "NOTA_AJUSTADA", "NOTA_MEDIA",
    "PARTIDOS_JUGADOS", "MINUTOS_TOTALES"
]]
equipo_notas = equipo_notas[[
    "POS", "NOMBRE", "NOTA_AJUSTADA", "NOTA_MEDIA",
    "PARTIDOS_JUGADOS", "MINUTOS_TOTALES"
]]

st.markdown("### 🔴 Equipo General")
st.dataframe(equipo_notas, use_container_width=True, hide_index=True)

st.button("ℹ️ ¿Qué es la Nota Ajustada?", on_click=mostrar_explicacion_nota_ajustada, key="nota_ajustada_btn3")

st.markdown("### 🔵 Jugadores (Posición ordenada según Nota Ajustada)")
st.dataframe(
    ranking_jugadores,
    use_container_width=True,
    hide_index=True,
    height=max(400, len(ranking_jugadores)*35+40)
)

# -------------------------------
# SECCIÓN 4: Ranking ofensivo (corregido y bonito)
# -------------------------------
st.header("⚽ Ranking de rendimiento ofensivo")

# Ranking individual de jugadores
ranking_ofensivo = (
    df_filtrado.groupby("NOMBRE")
    .agg({
        "GOLES": "sum",
        "ASISTENCIAS": "sum",
        "G/A": "sum",
        "FECHA": "nunique",
        "MINS_JUGADOS": "sum"
    })
    .rename(columns={"FECHA": "PARTIDOS_JUGADOS", "MINS_JUGADOS": "MINUTOS_TOTALES"})
    .reset_index()
)
ranking_ofensivo["GOLES_POR_PARTIDO"] = (ranking_ofensivo["GOLES"] / ranking_ofensivo["PARTIDOS_JUGADOS"]).round(2)
ranking_ofensivo["ASISTENCIAS_POR_PARTIDO"] = (ranking_ofensivo["ASISTENCIAS"] / ranking_ofensivo["PARTIDOS_JUGADOS"]).round(2)
ranking_ofensivo["G/A_POR_PARTIDO"] = (ranking_ofensivo["G/A"] / ranking_ofensivo["PARTIDOS_JUGADOS"]).round(2)

# Ordenamos jugadores por G/A
ranking_jugadores_of = ranking_ofensivo.sort_values("G/A", ascending=False).reset_index(drop=True)
ranking_jugadores_of.insert(0, "POS", range(1, len(ranking_jugadores_of)+1))

# -----------------------
# Equipo General
# -----------------------
partidos = df_filtrado[["FECHA", "GOLES_EN_CONTRA"]].drop_duplicates()
goles_en_contra_total = partidos["GOLES_EN_CONTRA"].sum()
diferencia_total = df_filtrado["GOLES"].sum() - goles_en_contra_total

equipo_of = pd.DataFrame({
    "POS": ["-"],
    "NOMBRE": ["Equipo General"],
    "G/A": [df_filtrado["G/A"].sum()],
    "GOLES": [df_filtrado["GOLES"].sum()],
    "ASISTENCIAS": [df_filtrado["ASISTENCIAS"].sum()],
    "GOLES_EN_CONTRA": [goles_en_contra_total],
    "DIFERENCIA_GOLES": [diferencia_total],
    "GOLES_POR_PARTIDO": [(df_filtrado["GOLES"].sum()/df_filtrado["FECHA"].nunique()).round(2)],
    "ASISTENCIAS_POR_PARTIDO": [(df_filtrado["ASISTENCIAS"].sum()/df_filtrado["FECHA"].nunique()).round(2)],
    "G/A_POR_PARTIDO": [(df_filtrado["G/A"].sum()/df_filtrado["FECHA"].nunique()).round(2)],
    "PARTIDOS_JUGADOS": [df_filtrado["FECHA"].nunique()],
    "MINUTOS_TOTALES": [df_filtrado["MINS_JUGADOS"].sum()]
})

ranking_jugadores_of = ranking_jugadores_of[[
    "POS", "NOMBRE", "G/A", "GOLES", "ASISTENCIAS",
    "GOLES_POR_PARTIDO", "ASISTENCIAS_POR_PARTIDO", "G/A_POR_PARTIDO",
    "PARTIDOS_JUGADOS", "MINUTOS_TOTALES"
]]

# Mostrar tablas
st.markdown("### 🔴 Equipo General")
st.dataframe(equipo_of, use_container_width=True, hide_index=True)

st.markdown("### 🔵 Jugadores (Posición ordenada según el G/A)")
st.dataframe(
    ranking_jugadores_of,
    use_container_width=True,
    hide_index=True,
    height=max(400, len(ranking_jugadores_of)*35+40)
)
