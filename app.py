import streamlit as st
import sqlite3
from datetime import date
import pandas as pd

# =========================
# CONFIGURACIÓN
# =========================

META_CASA = 40000.0
AHORRO_INICIAL = 7000.0
MONEDA = "US$"

CATEGORIAS = ["Casa", "Ómnibus", "Ocio"]

# =========================
# BASE DE DATOS
# =========================

conn = sqlite3.connect("finanzas_personales.db", check_same_thread=False)

conn.execute("""
CREATE TABLE IF NOT EXISTS movimientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    categoria TEXT NOT NULL,
    monto REAL NOT NULL,
    descripcion TEXT
)
""")

conn.commit()


# =========================
# FUNCIONES
# =========================

def obtener_movimientos():
    return pd.read_sql_query(
        "SELECT * FROM movimientos ORDER BY fecha DESC, id DESC",
        conn
    )


def agregar_movimiento(fecha, categoria, monto, descripcion):
    conn.execute(
        """
        INSERT INTO movimientos (fecha, categoria, monto, descripcion)
        VALUES (?, ?, ?, ?)
        """,
        (str(fecha), categoria, monto, descripcion)
    )
    conn.commit()


def eliminar_movimiento(id_movimiento):
    conn.execute(
        "DELETE FROM movimientos WHERE id = ?",
        (id_movimiento,)
    )
    conn.commit()


# =========================
# CONFIGURACIÓN VISUAL
# =========================

st.set_page_config(
    page_title="Mi Fondo Casa",
    page_icon="🏠",
    layout="centered"
)

st.markdown("""
<style>

.main {
    max-width: 900px;
    margin: auto;
}

.big-number {
    font-size: 42px;
    font-weight: bold;
    text-align: center;
}

.subtitle {
    text-align: center;
    color: #666;
}

</style>
""", unsafe_allow_html=True)


# =========================
# TÍTULO
# =========================

st.title("🏠 Mi Fondo Casa")
st.markdown(
    "### Tu objetivo: llegar a **US$40.000**"
)

st.write("")


# =========================
# DATOS
# =========================

df = obtener_movimientos()

if not df.empty:
    df["fecha"] = pd.to_datetime(df["fecha"])

# Ahorro registrado específicamente para la casa
if not df.empty:
    ahorro_registrado = df.loc[
        df["categoria"] == "Casa",
        "monto"
    ].sum()
else:
    ahorro_registrado = 0.0

# Total real del fondo de la casa
total_casa = AHORRO_INICIAL + ahorro_registrado

# Cuánto falta
faltante = max(META_CASA - total_casa, 0)

# Porcentaje de progreso
porcentaje = min((total_casa / META_CASA) * 100, 100)


# =========================
# OBJETIVO PRINCIPAL
# =========================

st.subheader("🎯 Progreso hacia tu casa")

st.markdown(
    f'<div class="big-number">{MONEDA} {total_casa:,.2f}</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">ahorrados</div>',
    unsafe_allow_html=True
)

st.progress(porcentaje / 100)

st.markdown(
    f"""
    <div style="text-align:center;">
        <strong>{porcentaje:.1f}%</strong> de la meta
        <br>
        Te faltan <strong>{MONEDA} {faltante:,.2f}</strong>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "💰 Ahorro inicial",
        f"{MONEDA} {AHORRO_INICIAL:,.2f}"
    )

with col2:
    st.metric(
        "📈 Ahorrado desde que comenzaste",
        f"{MONEDA} {ahorro_registrado:,.2f}"
    )


# =========================
# PROYECCIÓN
# =========================

st.divider()

st.subheader("📅 Proyección")

años = st.selectbox(
    "¿En cuánto tiempo querés alcanzar la meta?",
    [3, 3.5, 4],
    format_func=lambda x: f"{x} años"
)

meses = int(años * 12)

ahorro_mensual_necesario = faltante / meses


# Promedio mensual real
if not df.empty:
    df_casa = df[df["categoria"] == "Casa"].copy()

    if not df_casa.empty:
        df_casa["mes"] = df_casa["fecha"].dt.to_period("M")

        ahorro_por_mes = (
            df_casa.groupby("mes")["monto"]
            .sum()
        )

        promedio_mensual = ahorro_por_mes.mean()
    else:
        promedio_mensual = 0.0
else:
    promedio_mensual = 0.0


col1, col2 = st.columns(2)

with col1:
    st.metric(
        "🎯 Necesario por mes",
        f"{MONEDA} {ahorro_mensual_necesario:,.2f}"
    )

with col2:
    st.metric(
        "📊 Tu promedio actual",
        f"{MONEDA} {promedio_mensual:,.2f}"
    )


if promedio_mensual >= ahorro_mensual_necesario:
    st.success(
        "🔥 Vas a un ritmo suficiente para alcanzar la meta "
        "dentro del plazo seleccionado."
    )
else:
    st.info(
        "💡 Todavía estás por debajo del ritmo necesario. "
        "No pasa nada: esto es una referencia para ayudarte a planificar."
    )


# =========================
# RESUMEN MENSUAL
# =========================

st.divider()

st.subheader("📆 Resumen mensual")

if not df.empty:

    df["mes"] = df["fecha"].dt.to_period("M")

    resumen = (
        df.groupby(["mes", "categoria"])["monto"]
        .sum()
        .unstack(fill_value=0)
    )

    resumen.index = resumen.index.astype(str)

    st.dataframe(
        resumen,
        use_container_width=True
    )

else:
    st.info("Todavía no hay movimientos registrados.")


# =========================
# EVOLUCIÓN DEL AHORRO
# =========================

st.divider()

st.subheader("📈 Evolución de tu fondo")

if not df.empty:

    df_casa = df[df["categoria"] == "Casa"].copy()

    if not df_casa.empty:

        df_casa = df_casa.sort_values("fecha")

        df_casa["acumulado"] = (
            df_casa["monto"].cumsum() + AHORRO_INICIAL
        )

        grafico = df_casa[
            ["fecha", "acumulado"]
        ].set_index("fecha")

        st.line_chart(grafico)

    else:
        st.info(
            "Cuando registres tus primeros ahorros para la casa, "
            "aparecerá aquí la evolución."
        )

else:
    st.info(
        "Cuando registres tus primeros ahorros para la casa, "
        "aparecerá aquí la evolución."
    )


# =========================
# REGISTRAR MOVIMIENTO
# =========================

st.divider()

st.subheader("➕ Registrar movimiento")

with st.form("form_movimiento"):

    fecha_movimiento = st.date_input(
        "Fecha",
        value=date.today()
    )

    categoria = st.selectbox(
        "Categoría",
        CATEGORIAS
    )

    monto = st.number_input(
        "Monto",
        min_value=0.01,
        step=10.0,
        format="%.2f"
    )

    descripcion = st.text_input(
        "Descripción",
        placeholder="Ej.: ahorro del mes"
    )

    guardar = st.form_submit_button(
        "Guardar movimiento"
    )

    if guardar:

        agregar_movimiento(
            fecha_movimiento,
            categoria,
            monto,
            descripcion
        )

        st.success("Movimiento guardado correctamente.")
        st.rerun()


# =========================
# HISTORIAL
# =========================

st.divider()

st.subheader("📋 Historial")

df_historial = obtener_movimientos()

if not df_historial.empty:

    df_historial["fecha"] = pd.to_datetime(
        df_historial["fecha"]
    ).dt.strftime("%d/%m/%Y")

    st.dataframe(
        df_historial[
            [
                "id",
                "fecha",
                "categoria",
                "monto",
                "descripcion"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.write("")

    id_eliminar = st.number_input(
        "ID del movimiento que querés eliminar",
        min_value=1,
        step=1
    )

    if st.button("🗑️ Eliminar movimiento"):

        eliminar_movimiento(id_eliminar)

        st.success("Movimiento eliminado.")
        st.rerun()

else:
    st.info("Todavía no hay movimientos registrados.")


# =========================
# INFORMACIÓN DEL SALDO INICIAL
# =========================

st.divider()

st.caption(
    f"🏠 Tu fondo comenzó con {MONEDA} {AHORRO_INICIAL:,.2f} "
    "ya ahorrados. Los movimientos registrados posteriormente "
    "se suman a ese monto."
)