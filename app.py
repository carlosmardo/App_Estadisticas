import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

st.set_page_config(layout="centered")

# 🔹 Ajustar el ancho del contenido principal
st.markdown("""
    <style>
        .block-container {
            max-width: 1000px;   /* Ancho intermedio */
            padding-left: 2rem;
            padding-right: 2rem;
            margin: auto;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# 📂 Subir archivo CSV
# -------------------------------
st.title("📊 Análisis del Equipo - Stats por Jugador")

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


with open("Plantilla.xlsx", "rb") as f:
    excel_bytes = f.read()

st.download_button(
    label="📥 Descargar plantilla de Excel",
    data=excel_bytes,
    file_name="plantilla_estadisticas.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# -------------------------------
# Archivo CSV de ejemplo dentro del proyecto
# -------------------------------
archivo_ejemplo = "ejemplo.csv"

# -------------------------------
# Subir archivo CSV del usuario
# -------------------------------
archivo_usuario = st.file_uploader(
    "Sube tu archivo CSV con las estadísticas (Ahora se esta mostrando un archivo de ejemplo)",
    type=["csv"]
)

# Si el usuario no sube archivo, usamos el CSV de ejemplo
if archivo_usuario is None:
    st.info("Mostrando archivo de ejemplo. Puedes subir tu propio CSV para reemplazarlo.")
    df = pd.read_csv(archivo_ejemplo, dayfirst=True)
else:
    df = pd.read_csv(archivo_usuario, dayfirst=True)


columnas_esperadas = ["FECHA","COMPETICION","NOMBRE","GOLES","ASISTENCIAS","NOTA","MINS_JUGADOS"]
faltantes = [col for col in columnas_esperadas if col not in df.columns]

if faltantes:
    st.error(f"Archivo CSV inválido. Faltan las columnas: {', '.join(faltantes)}")
    st.stop()


df["FECHA"] = pd.to_datetime(df["FECHA"], dayfirst=True)
df["G/A"] = df["GOLES"] + df["ASISTENCIAS"]



# -------------------------------
# Filtros generales
# -------------------------------
st.sidebar.header("Filtros generales")

competiciones = sorted(df["COMPETICION"].unique())
comp_filtro = st.sidebar.multiselect(
    "Selecciona las competiciones",
    options=competiciones,
    default=competiciones
)

df_filtrado = df[df["COMPETICION"].isin(comp_filtro)].copy()

if df_filtrado.empty:
    st.warning("⚠️ Ningún filtro seleccionado o no hay datos coincidentes.\n\n"
               "Por favor selecciona al menos **una competición** para mostrar las tablas.")
    st.stop()



# ----------------------------------
# Filtro especial: Primera / Segunda vuelta (solo Liga)
# ----------------------------------
if "Liga" in comp_filtro:
    vuelta = st.sidebar.radio(
        "Selecciona el tramo de la Liga",
        ["Toda la Liga", "Primera vuelta", "Segunda vuelta"],
        index=0
    )

    # Ordenamos las fechas únicas de los partidos de Liga
    liga_dates = (
        df[df["COMPETICION"] == "Liga"]
        .sort_values("FECHA")["FECHA"]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # 🔹 Asignamos número de jornada en orden cronológico
    date_to_jornada = {fecha: i + 1 for i, fecha in enumerate(liga_dates)}
    df_filtrado.loc[df_filtrado["COMPETICION"] == "Liga", "JORNADA"] = (
        df_filtrado.loc[df_filtrado["COMPETICION"] == "Liga", "FECHA"].map(date_to_jornada)
    )

    # 🔹 Si es Liga española, usamos corte fijo en jornada 19
    # (incluso si en el CSV solo hay 10, 20 o 38 partidos)
    corte_laliga = 19

    if vuelta == "Primera vuelta":
        df_filtrado = df_filtrado[
            ~((df_filtrado["COMPETICION"] == "Liga") & (df_filtrado["JORNADA"] > corte_laliga))
        ]
    elif vuelta == "Segunda vuelta":
        df_filtrado = df_filtrado[
            ~((df_filtrado["COMPETICION"] == "Liga") & (df_filtrado["JORNADA"] <= corte_laliga))
        ]


# -------------------------------
# SECCIÓN 1: Estadísticas por jugador o equipo
# -------------------------------
st.header("📈 Estadísticas individuales / Equipo")

opciones_jugadores = ["Equipo General"] + sorted(df["NOMBRE"].unique())
jugador_sel = st.selectbox("Selecciona el jugador o Equipo General", opciones_jugadores)

tipo_stat = st.selectbox(
    "Selecciona la estadística a mostrar",
    ["NOTA", "GOLES", "ASISTENCIAS", "G/A"]
)

if jugador_sel == "Equipo General":
    df_equipo = (
        df_filtrado.groupby(["FECHA", "COMPETICION"])
        .agg({
            "NOTA": "mean",
            "GOLES": "sum",
            "ASISTENCIAS": "sum",
            "G/A": "sum"
        })
        .reset_index()
        .sort_values("FECHA")
    )

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(df_equipo["FECHA"], df_equipo[tipo_stat],
            marker="o", markersize=6, linestyle="-", linewidth=2.5, alpha=0.8, color="royalblue")
    ax.set_title(f"Evolución de {tipo_stat} del equipo por partido", fontsize=16)
    ax.set_xlabel("MESES")
    ax.set_ylabel(tipo_stat)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.set_facecolor("white")
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45)
    st.pyplot(fig)

else:
    df_jugador = df_filtrado[df_filtrado["NOMBRE"] == jugador_sel].sort_values("FECHA")

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(
        df_jugador["FECHA"], df_jugador[tipo_stat],
        marker="o", markersize=6, linestyle="-", linewidth=2.5, alpha=0.8
    )
    ax.set_title(f"Evolución de {tipo_stat} partido a partido - {jugador_sel}", fontsize=16)
    ax.set_xlabel("MESES")
    ax.set_ylabel(tipo_stat)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.set_facecolor("white")
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45)
    st.pyplot(fig)

# Tabla resumen
if jugador_sel == "Equipo General":
    resumen = pd.DataFrame({
        "NOMBRE": ["Equipo General"],
        "PARTIDOS_JUGADOS": [df_filtrado["FECHA"].nunique()],
        "MINUTOS_TOTALES": [df_filtrado["MINS_JUGADOS"].sum()]
    })
else:
    df_jugador_filtrado = df_filtrado[df_filtrado["NOMBRE"] == jugador_sel]
    partidos_jugados = df_jugador_filtrado["FECHA"].nunique()
    minutos_totales = df_jugador_filtrado["MINS_JUGADOS"].sum()
    
    resumen = pd.DataFrame({
        "NOMBRE": [jugador_sel],
        "PARTIDOS_JUGADOS": [partidos_jugados],
        "MINUTOS_TOTALES": [minutos_totales]
    })

st.markdown("### 📋 Resumen de participación")
st.dataframe(resumen, use_container_width=True, hide_index=True)

# -------------------------------
# SECCIÓN 2: Comparador de jugadores
# -------------------------------
st.header("🆚 Comparador de jugadores")

jugadores = sorted(df["NOMBRE"].unique())

jugadores_comparar = st.multiselect(
    "Selecciona los jugadores a comparar",
    jugadores,
    default=[jugadores[0], jugadores[1]] if len(jugadores) > 1 else jugadores
)

tipo_comparar = st.selectbox(
    "Selecciona la estadística a comparar",
    ["NOTA", "GOLES", "ASISTENCIAS", "G/A"]
)

fig2, ax2 = plt.subplots(figsize=(14, 6))
for j in jugadores_comparar:
    df_temp = df_filtrado[df_filtrado["NOMBRE"] == j].sort_values("FECHA")
    ax2.plot(
        df_temp["FECHA"],
        df_temp[tipo_comparar],
        marker="o",
        linestyle="-",
        linewidth=2,
        label=j
    )

ax2.set_title(f"Comparativa de {tipo_comparar} entre jugadores", fontsize=16)
ax2.set_xlabel("MESES")
ax2.set_ylabel(tipo_comparar)
ax2.grid(True, linestyle="--", alpha=0.6)
ax2.set_facecolor("white")
ax2.legend()
ax2.xaxis.set_major_locator(mdates.MonthLocator())
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
plt.xticks(rotation=45)
st.pyplot(fig2)

# Tabla resumen
resumen = []
for jugador in jugadores_comparar:
    df_j = df_filtrado[df_filtrado["NOMBRE"] == jugador]
    partidos_jugados = df_j["FECHA"].nunique()
    minutos_totales = df_j["MINS_JUGADOS"].sum()
    
    resumen.append({
        "NOMBRE": jugador,
        "PARTIDOS_JUGADOS": partidos_jugados,
        "MINUTOS_TOTALES": minutos_totales
    })

resumen_df = pd.DataFrame(resumen)
st.markdown("### 📋 Resumen de participación")
st.dataframe(resumen_df, use_container_width=True, hide_index=True)

# -------------------------------
# SECCIÓN 3: Ranking por notas medias (ponderada por minutos)
# -------------------------------
st.header("🏆 Ranking por notas medias ponderada por minutos")

media_global = df_filtrado["NOTA"].mean()
k = 20  # constante de suavizado

# Agrupamos por jugador
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
        "NOTA": "NOTA_MEDIA"
    })
    .reset_index()
)

# Calculamos el peso por minutos jugados (equivale a "partidos completos jugados")
ranking_notas["PESO_MINUTOS"] = ranking_notas["MINUTOS_TOTALES"] / 90

# Nueva Nota Ajustada ponderada por minutos
ranking_notas["NOTA_AJUSTADA"] = (
    (ranking_notas["PESO_MINUTOS"] * ranking_notas["NOTA_MEDIA"] + k * media_global)
    / (ranking_notas["PESO_MINUTOS"] + k)
).round(2)

ranking_notas["NOTA_MEDIA"] = ranking_notas["NOTA_MEDIA"].round(2)

# Equipo General
equipo_notas = pd.DataFrame({
    "NOMBRE": ["Equipo General"],
    "NOTA_MEDIA": [df_filtrado["NOTA"].mean().round(2)],
    "NOTA_AJUSTADA": [df_filtrado["NOTA"].mean().round(2)],
    "PARTIDOS_JUGADOS": [df_filtrado["FECHA"].nunique()],
    "MINUTOS_TOTALES": [df_filtrado["MINS_JUGADOS"].sum()]
})

# Ordenamos por Nota Ajustada
ranking_jugadores = ranking_notas.sort_values("NOTA_AJUSTADA", ascending=False).reset_index(drop=True)
ranking_jugadores.insert(0, "POS", range(1, len(ranking_jugadores)+1))
equipo_notas.insert(0, "POS", ["-"])

# Reordenar columnas
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

with st.expander("ℹ️ ¿Qué es la **Nota Ajustada**?"):
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
    - `k`: constante de suavizado (en este caso k = 20). Este es el número de partidos que se considera como peso mínimo teniendo en cuenta que un equipo juega alrededor de 60 partidos y un jugador que es titular indiscutible suele jugar alrededor de 50 partidos, equivalente a unos ~1800 minutos jugados (20×90).
    """)

st.markdown("### 🔵 Jugadores (ordenados por Nota Ajustada ponderada por minutos)")
altura_notas = max(400, len(ranking_jugadores) * 35 + 40)
st.dataframe(ranking_jugadores, use_container_width=True, hide_index=True, height=altura_notas)

# -------------------------------
# SECCIÓN 4: Ranking ofensivo
# -------------------------------
st.header("⚽ Ranking de rendimiento ofensivo")

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

# Ranking solo jugadores
ranking_jugadores_of = ranking_ofensivo.sort_values("G/A", ascending=False).reset_index(drop=True)
ranking_jugadores_of.insert(0, "POS", range(1, len(ranking_jugadores_of)+1))

# Equipo General
equipo_of = pd.DataFrame({
    "POS": ["-"],
    "NOMBRE": ["Equipo General"],
    "G/A": [df_filtrado["G/A"].sum()],
    "GOLES": [df_filtrado["GOLES"].sum()],
    "ASISTENCIAS": [df_filtrado["ASISTENCIAS"].sum()],
    "GOLES_POR_PARTIDO": [(df_filtrado["GOLES"].sum()/df_filtrado["FECHA"].nunique()).round(2)],
    "ASISTENCIAS_POR_PARTIDO": [(df_filtrado["ASISTENCIAS"].sum()/df_filtrado["FECHA"].nunique()).round(2)],
    "G/A_POR_PARTIDO": [(df_filtrado["G/A"].sum()/df_filtrado["FECHA"].nunique()).round(2)],
    "PARTIDOS_JUGADOS": [df_filtrado["FECHA"].nunique()],
    "MINUTOS_TOTALES": [df_filtrado["MINS_JUGADOS"].sum()]
})

# Reordenar columnas
ranking_jugadores_of = ranking_jugadores_of[[
    "POS", "NOMBRE", "G/A", "GOLES", "ASISTENCIAS",
    "GOLES_POR_PARTIDO", "ASISTENCIAS_POR_PARTIDO", "G/A_POR_PARTIDO",
    "PARTIDOS_JUGADOS", "MINUTOS_TOTALES"
]]

st.markdown("### 🔴 Equipo General")
st.dataframe(equipo_of, use_container_width=True, hide_index=True)

st.markdown("### 🔵 Jugadores (Posición ordenada según el G/A)")
altura_ofensivo = max(400, len(ranking_jugadores_of) * 35 + 40)
st.dataframe(ranking_jugadores_of, use_container_width=True, hide_index=True, height=altura_ofensivo)
