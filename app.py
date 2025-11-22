import streamlit as st
import pandas as pd
import plotly.express as px


st.set_page_config(layout="centered")

#Explicación de la Nota Ajustada
@st.dialog("ℹ️ ¿Qué es la Nota Ajustada?", width="medium")
def mostrar_explicacion_nota_ajustada():
    st.markdown("""
    La **Nota Ajustada** busca reflejar de manera más justa el rendimiento real de cada jugador a lo largo de la temporada.  
    Tiene en cuenta tanto su **nota media individual** como el **volumen de minutos jugados**, premiando la regularidad y constancia.

    ---

    ### ⚙️ Cómo se calcula

    La nota ajustada se compone de dos partes: una **base ponderada** y un **bonus por minutos**.

    **1️⃣ Base ponderada:**
    \n
    \tBASE = (PESO_MINUTOS × NOTA_MEDIA + k × NOTA_GLOBAL) / (PESO_MINUTOS + k)

    **2️⃣ Bonus por minutos jugados:**
    \n
    \tBONUS = γ × (MINUTOS_TOTALES / MINUTOS_MÁXIMO) ^ β

    **3️⃣ Nota final:**
    \n
    \tNOTA_AJUSTADA = BASE + BONUS

    ---

    ### 📘 Significado de los parámetros

    - **NOTA_MEDIA** → Promedio de las notas del jugador en todos los partidos que ha disputado.  
    - **NOTA_GLOBAL** → Media general de todos los jugadores del equipo (sirve como referencia).  
    - **MINUTOS_TOTALES** → Total de minutos jugados por el jugador durante la temporada.  
      Cuantos más minutos acumula, más peso tiene su rendimiento.
    - **MINUTOS_MÁXIMO** → Es el número de minutos del jugador que más ha jugado en el equipo.  
      Se usa para normalizar el bonus: el que más juega recibe el bonus completo `γ`, y el resto una fracción proporcional.  
    - **PESO_MINUTOS = (MINUTOS_TOTALES / 90) ^ `α`**  
      Representa los **“partidos equivalentes”** jugados por el jugador (minutos ÷ 90),  
      elevados a una potencia `α` para **dar más importancia a quienes acumulan más minutos**.  
      En este caso **`α = 2`**, por lo que el peso crece de forma **exponencial**, beneficiando a los más constantes.  
    - **`k = 60`** → Controla cuánto se suaviza el resultado hacia la media global del equipo.  
      Cuanto mayor sea, **menos se aleja la nota ajustada de la nota global**.  
    - **`γ (gamma) = 0.25`** → Define la intensidad del bonus adicional por minutos jugados.  
    - **`β (beta) = 2`** → Ajusta la curvatura del bonus, haciendo que el efecto crezca más rápido con muchos minutos.

    ---

    ### 🎯 Interpretación

    - Un jugador con una nota media ligeramente inferior, pero muchos más minutos,  
      puede superar a otro con más media pero que haya jugado menos partidos.  
    - Un jugador con pocos minutos **no queda penalizado de forma extrema**,  
      pero su impacto en la temporada será menor.  
    - En resumen: **la fórmula recompensa la constancia y el rendimiento sostenido**.

    ---

    ### 🧮 Ejemplo simplificado
    Si dos defensas tienen notas medias similares (7.6 y 7.5), pero uno ha jugado 1.000 minutos más,  
    la fórmula elevará su nota ajustada final, reflejando mejor su **impacto global en la temporada**.
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
        "MINUTOS_TOTALES": df_filtrado["MINS_JUGADOS"].sum(),
    }
    partidos = fila["PARTIDOS_JUGADOS"]

    if tipo_stat == "NOTA":
        nota_media = df_filtrado["NOTA"].mean()
        
        media_global = df_filtrado["NOTA"].mean()
        
        fila.update({"NOTA_MEDIA": round(nota_media,2)})
        columnas = ["NOMBRE", "NOTA_MEDIA","PARTIDOS_JUGADOS","MINUTOS_TOTALES"]

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
        "MINUTOS_TOTALES": df_j["MINS_JUGADOS"].sum(),
        "PARTIDOS_REALES": (df_j["MINS_JUGADOS"].sum() / 90).round(2)
    }
    partidos = fila["PARTIDOS_JUGADOS"]

    if tipo_stat == "NOTA":
        nota_media = df_j["NOTA"].mean()
        
        media_global = df_filtrado["NOTA"].mean()
        
        fila.update({"NOTA_MEDIA": round(nota_media,2)})
        columnas = ["NOMBRE", "NOTA_MEDIA","PARTIDOS_JUGADOS","MINUTOS_TOTALES", "PARTIDOS_REALES"]

    elif tipo_stat == "GOLES":
        total = df_j["GOLES"].sum()
        fila.update({"GOLES": total, "GOLES_POR_PARTIDO": calcular_por_partido(total, partidos)})
        columnas = ["NOMBRE","GOLES","GOLES_POR_PARTIDO","PARTIDOS_JUGADOS","MINUTOS_TOTALES", "PARTIDOS_REALES"]

    elif tipo_stat == "ASISTENCIAS":
        total = df_j["ASISTENCIAS"].sum()
        fila.update({"ASISTENCIAS": total, "ASISTENCIAS_POR_PARTIDO": calcular_por_partido(total, partidos)})
        columnas = ["NOMBRE","ASISTENCIAS","ASISTENCIAS_POR_PARTIDO","PARTIDOS_JUGADOS","MINUTOS_TOTALES", "PARTIDOS_REALES"]

    elif tipo_stat == "G/A":
        total = df_j["G/A"].sum()
        fila.update({"G/A": total, "G/A_POR_PARTIDO": calcular_por_partido(total, partidos)})
        columnas = ["NOMBRE","G/A","G/A_POR_PARTIDO","PARTIDOS_JUGADOS","MINUTOS_TOTALES", "PARTIDOS_REALES"]

    resumen = pd.DataFrame([fila])[columnas]

# Encabezado con enlace informativo
st.markdown("### 📋 Resumen de participación")

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
    hovermode="x",
    #height=600
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
        "MINUTOS_TOTALES": df_j["MINS_JUGADOS"].sum(),
        "PARTIDOS_REALES": (df_j["MINS_JUGADOS"].sum() / 90).round(2)
    }

    if tipo_comparar == "NOTA":
        nota_media = df_j["NOTA"].mean()
        
        media_global = df_filtrado["NOTA"].mean()
        
        fila.update({"NOTA_MEDIA": round(nota_media,2)})
        columnas = ["NOMBRE", "NOTA_MEDIA","PARTIDOS_JUGADOS","MINUTOS_TOTALES", "PARTIDOS_REALES"]

    elif tipo_comparar == "GOLES":
        total = df_j["GOLES"].sum()
        fila.update({"GOLES": total, "GOLES_POR_PARTIDO": calcular_por_partido(total, partidos)})
        columnas = ["NOMBRE","GOLES","GOLES_POR_PARTIDO","PARTIDOS_JUGADOS","MINUTOS_TOTALES", "PARTIDOS_REALES"]

    elif tipo_comparar == "ASISTENCIAS":
        total = df_j["ASISTENCIAS"].sum()
        fila.update({"ASISTENCIAS": total, "ASISTENCIAS_POR_PARTIDO": calcular_por_partido(total, partidos)})
        columnas = ["NOMBRE","ASISTENCIAS","ASISTENCIAS_POR_PARTIDO","PARTIDOS_JUGADOS","MINUTOS_TOTALES", "PARTIDOS_REALES"]

    elif tipo_comparar == "G/A":
        total = df_j["G/A"].sum()
        fila.update({"G/A": total, "G/A_POR_PARTIDO": calcular_por_partido(total, partidos)})
        columnas = ["NOMBRE","G/A","G/A_POR_PARTIDO","PARTIDOS_JUGADOS","MINUTOS_TOTALES", "PARTIDOS_REALES"]

    resumen.append(pd.DataFrame([fila])[columnas])

st.markdown("### 📋 Resumen de participación")

st.dataframe(pd.concat(resumen, ignore_index=True), use_container_width=True, hide_index=True)



# -------------------------------
# SECCIÓN 3: Ranking por notas de rendimiento (versión mejorada)
# -------------------------------
st.header("🏆 Ranking por notas de rendimiento")

# Parámetros de la fórmula ajustable
alpha = 2    # Potencia para peso de minutos
k = 60       # Suavizado hacia la nota global
gamma = 0.25 # Intensidad del bonus por minutos
beta = 2     # Curvatura del bonus
media_global = df_filtrado["NOTA"].mean()

# Agrupamos datos base por jugador
ranking_notas = (
    df_filtrado.groupby("NOMBRE")
    .agg({
        "NOTA": "mean",
        "FECHA": "nunique",
        "MINS_JUGADOS": "sum"
    })
    .rename(columns={
        "FECHA": "PARTIDOS_JUGADOS",
        "MINS_JUGADOS": "MINUTOS_TOTALES",
        "NOTA": "NOTA_MEDIA",
    })
    .reset_index()
)

# Calculamos máximo de minutos para normalizar el bonus
minutos_max = ranking_notas["MINUTOS_TOTALES"].replace(0, 1).max()

# Paso 1: peso no lineal por minutos (partidos equivalentes ^ alpha)
ranking_notas["PESO_MINUTOS"] = (ranking_notas["MINUTOS_TOTALES"] / 90.0) ** alpha

# Paso 2: base ponderada entre nota del jugador y media global
ranking_notas["BASE"] = (
    (ranking_notas["PESO_MINUTOS"] * ranking_notas["NOTA_MEDIA"] + k * media_global)
    / (ranking_notas["PESO_MINUTOS"] + k)
)

# Paso 3: bonus por minutos jugados (normalizado respecto al máximo/2)
ranking_notas["BONUS"] = gamma * (ranking_notas["MINUTOS_TOTALES"] / minutos_max) ** beta

# Paso 4: nota ajustada final
ranking_notas["NOTA_AJUSTADA"] = (ranking_notas["BASE"] + ranking_notas["BONUS"]).round(2)
ranking_notas["NOTA_MEDIA"] = ranking_notas["NOTA_MEDIA"].round(2)

# Añadimos columna de partidos reales
ranking_notas["PARTIDOS_REALES"] = (ranking_notas["MINUTOS_TOTALES"] / 90).round(2)

# -------------------------------
# Equipo general
# -------------------------------
nota_ajustada_equipo = ranking_notas["NOTA_AJUSTADA"].mean().round(2)
nota_media_equipo = ranking_notas["NOTA_MEDIA"].mean().round(2)

equipo_notas = pd.DataFrame({
    "POS": ["-"],
    "NOMBRE": ["Equipo General"],
    "NOTA_AJUSTADA": [nota_ajustada_equipo],
    "NOTA_MEDIA": [nota_media_equipo],
    "PARTIDOS_JUGADOS": [df_filtrado["FECHA"].nunique()],
    "MINUTOS_TOTALES": [df_filtrado["MINS_JUGADOS"].sum()],
})

# -------------------------------
# Ranking final de jugadores
# -------------------------------
ranking_jugadores = ranking_notas.sort_values("NOTA_AJUSTADA", ascending=False).reset_index(drop=True)
ranking_jugadores.insert(0, "POS", range(1, len(ranking_jugadores) + 1))

# Columnas a mostrar
columnas_equipo = [
    "POS", "NOMBRE", "NOTA_AJUSTADA", "NOTA_MEDIA",
    "PARTIDOS_JUGADOS", "MINUTOS_TOTALES"
]

columnas_jugadores = columnas_equipo + ["PARTIDOS_REALES"]

ranking_jugadores = ranking_jugadores[columnas_jugadores]
equipo_notas = equipo_notas[columnas_equipo]

# -------------------------------
# Mostrar resultados
# -------------------------------
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
ranking_ofensivo["PARTIDOS_REALES"] = (ranking_ofensivo["MINUTOS_TOTALES"] / 90).round(2)

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
    #"G/A": [df_filtrado["G/A"].sum()],
    "GOLES": [df_filtrado["GOLES"].sum()],
    #"ASISTENCIAS": [df_filtrado["ASISTENCIAS"].sum()],
    "GOLES_EN_CONTRA": [goles_en_contra_total],
    "DIFERENCIA_GOLES": [diferencia_total],
    "GOLES_POR_PARTIDO": [(df_filtrado["GOLES"].sum()/df_filtrado["FECHA"].nunique()).round(2)],
    #"ASISTENCIAS_POR_PARTIDO": [(df_filtrado["ASISTENCIAS"].sum()/df_filtrado["FECHA"].nunique()).round(2)],
    #"G/A_POR_PARTIDO": [(df_filtrado["G/A"].sum()/df_filtrado["FECHA"].nunique()).round(2)],
    "PARTIDOS_JUGADOS": [df_filtrado["FECHA"].nunique()],
    #"MINUTOS_TOTALES": [df_filtrado["MINS_JUGADOS"].sum()],
})

ranking_jugadores_of = ranking_jugadores_of[[
    "POS", "NOMBRE", "G/A", "GOLES", "ASISTENCIAS",
    "GOLES_POR_PARTIDO", "ASISTENCIAS_POR_PARTIDO", "G/A_POR_PARTIDO",
    "PARTIDOS_JUGADOS", "MINUTOS_TOTALES", "PARTIDOS_REALES"
]]

# Mostrar tablas
st.markdown("### 🔴 Equipo General")
st.dataframe(equipo_of, use_container_width=True, hide_index=True)

st.markdown("### 🔵 Jugadores (Posición ordenada según G/A)")
st.dataframe(
    ranking_jugadores_of,
    use_container_width=True,
    hide_index=True,
    height=max(400, len(ranking_jugadores_of)*35+40)
)

