import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import datetime
import uuid
from groq import Groq

st.set_page_config(
    page_title="GestiónDocente Premium",
    page_icon="🎓",
    layout="wide"
)

# ==========================================
# ESTILOS PERSONALIZADOS
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --primary: #1e293b;
    --primary-dark: #0f172a;
    --accent: #ca8a04;
    --info: #2563eb;
    --success: #16a34a;
    --warning: #d97706;
    --danger: #dc2626;
    --card-bg: #ffffff;
    --text-main: #1e293b;
    --text-muted: #64748b;
    --border: #e2e8f0;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: linear-gradient(180deg, #f8fafc 0%, #fefce8 100%); }

.app-header {
    background: linear-gradient(120deg, var(--primary) 0%, var(--primary-dark) 100%);
    padding: 1.75rem 2rem;
    border-radius: 16px;
    margin-bottom: 1rem;
    box-shadow: 0 10px 30px -12px rgba(15, 23, 42, 0.45);
    border-bottom: 3px solid var(--accent);
}
.app-header h1 { color: #ffffff !important; font-weight: 800; font-size: 1.9rem; margin: 0; }
.app-header p { color: rgba(255,255,255,0.88) !important; font-size: 1rem; margin: 0.25rem 0 0 0; }

[data-testid="stForm"] {
    background: var(--card-bg);
    padding: 1.5rem 1.75rem;
    border-radius: 18px;
    border: 1px solid var(--border);
    box-shadow: 0 15px 35px -20px rgba(15, 23, 42, 0.25);
}

.kpi-card {
    background: var(--card-bg);
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    border: 1px solid var(--border);
    border-left: 5px solid var(--kpi-color, var(--primary));
    box-shadow: 0 4px 14px -8px rgba(30,41,59,0.15);
}
.kpi-card .kpi-label { color: var(--text-muted); font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
.kpi-card .kpi-value { color: var(--text-main); font-size: 2rem; font-weight: 800; line-height: 1.2; }

[data-testid="stMetric"] {
    background: var(--card-bg);
    border-radius: 14px;
    padding: 1rem 1.2rem;
    border: 1px solid var(--border);
    border-left: 5px solid var(--accent);
    box-shadow: 0 4px 14px -8px rgba(30,41,59,0.15);
}

.stTabs [data-baseweb="tab-list"] { gap: 4px; background: #ffffff; padding: 6px; border-radius: 12px; border: 1px solid var(--border); }
.stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 10px 18px; font-weight: 600; color: var(--text-muted); }
.stTabs [aria-selected="true"] { background: var(--primary) !important; color: #ffffff !important; }

.stButton > button, .stDownloadButton > button {
    border-radius: 10px;
    font-weight: 600;
    border: 1px solid var(--border);
    transition: all 0.15s ease;
}
.stButton > button[kind^="primary"], .stFormSubmitButton > button[kind^="primary"] {
    background: linear-gradient(120deg, var(--primary), var(--primary-dark)) !important;
    border: none !important;
    color: #ffffff !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 18px -8px rgba(15,23,42,0.5);
}

[data-testid="stAlert"] { border-radius: 12px; }
[data-testid="stExpander"] { border-radius: 10px; border: 1px solid var(--border); }
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid var(--border); }

h2, h3 { color: var(--text-main); font-weight: 700; }
hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SECRETS Y CONFIGURACIÓN
# ==========================================
GAS_URL = st.secrets.get("GAS_URL", "https://script.google.com/macros/s/AKfycbwYHuOc0WBnSV1luPpMlF2tGackRWBu9FT_5SjIigI_EAcCh0KB_mxwlIfy8YQVwD0H/exec")
# NOTA: las URLs publicadas estaban rotadas una posición (cada constante apuntaba a la hoja
# siguiente): URL_ALUMNOS servía la hoja Cualitativo, URL_ASISTENCIA servía Alumnos, URL_NOTAS
# servía Asistencia y URL_CUALITATIVO servía Notas. Esto hacía que los datos recién guardados
# nunca aparecieran (se guardaban bien, pero se leían de la hoja equivocada). Corregido.
URL_ALUMNOS = st.secrets.get("URL_ALUMNOS", "https://docs.google.com/spreadsheets/d/e/2PACX-1vSFbojcRukwXL1qE-n6WYxR1sOoYcXtVkteUTc_oqs7pFeoO0N31ffGIiGQeKP0GP7VgFwVPtl0uMaO/pub?output=csv")
URL_ASISTENCIA = st.secrets.get("URL_ASISTENCIA", "https://docs.google.com/spreadsheets/d/e/2PACX-1vS9MHCz6vQtCDUvxBnG21dJ26BW5JtdidUY3I8kRtb_veqMXWb_v8h-XjcdNOsHSr_FWsbW7XKLpd1z/pub?output=csv")
URL_NOTAS = st.secrets.get("URL_NOTAS", "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmv2UX24YXYHhMuj6R0YXUlsmv1Tk25jS6ZdPGFoXqM2S5J7EqBX4y90jH9GpnY1pIkJUqt-9JzMRd/pub?output=csv")
URL_CUALITATIVO = st.secrets.get("URL_CUALITATIVO", "https://docs.google.com/spreadsheets/d/e/2PACX-1vSzRRBBX9BKgCdTuFI-tiITl5jXfQQSolJe36S1xaJaA4GYTJ0lIU9LBQcJwXpxQ7XrhcUZdzS0BrNd/pub?output=csv")
DEMO_USER = st.secrets.get("DEMO_USER", "docente")
DEMO_PASS = st.secrets.get("DEMO_PASS", "gestion2026")
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")

try:
    client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
except Exception:
    client = None

# ==========================================
# LOGIN
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style='text-align:center; margin-bottom: 1.5rem;'>
                <div style='font-size:3rem; line-height:1;'>🎓</div>
                <h1 style='color:#0f172a; font-weight:800; margin:0.3rem 0 0 0;'>GestiónDocente</h1>
                <p style='color:#64748b; font-size:1rem; margin-top:0.3rem;'>Sistema Premium de Gestión Educativa</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        with st.form("login_form"):
            usuario = st.text_input("Usuario:", placeholder="docente")
            clave = st.text_input("Contraseña:", type="password", placeholder="••••••••")
            st.caption("ℹ️ Demo: usuario `docente` / contraseña `gestion2026`")
            if st.form_submit_button("Ingresar", type="primary", use_container_width=True):
                if usuario == DEMO_USER and clave == DEMO_PASS:
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos.")
    st.stop()

# ==========================================
# CARGA DE DATOS
# ==========================================
@st.cache_data(ttl=30)
def cargar_alumnos():
    try:
        df = pd.read_csv(URL_ALUMNOS)
        return df.dropna(how='all')
    except:
        return pd.DataFrame(columns=["ID","Nombre","Apellido","Grado","Seccion","DNI","Fecha_Nacimiento","Contacto"])

@st.cache_data(ttl=30)
def cargar_asistencia():
    try:
        df = pd.read_csv(URL_ASISTENCIA)
        return df.dropna(how='all')
    except:
        return pd.DataFrame(columns=["ID_Alumno","Nombre","Fecha","Estado","Observacion"])

@st.cache_data(ttl=30)
def cargar_notas():
    try:
        df = pd.read_csv(URL_NOTAS)
        return df.dropna(how='all')
    except:
        return pd.DataFrame(columns=["ID_Alumno","Nombre","Materia","Periodo","Nota","Observacion"])

@st.cache_data(ttl=30)
def cargar_cualitativo():
    try:
        df = pd.read_csv(URL_CUALITATIVO)
        return df.dropna(how='all')
    except:
        return pd.DataFrame(columns=["ID_Alumno","Nombre","Fecha","Conducta","Compañerismo","Destaca_En","Observacion","Tipo"])

def enviar_gas(datos):
    try:
        res = requests.post(GAS_URL, json=datos, timeout=10)
        return res.json().get("success", False)
    except Exception:
        return False

# ==========================================
# HEADER
# ==========================================
col_titulo, col_logout = st.columns([5, 1])
with col_titulo:
    st.markdown(
        """
        <div class="app-header">
            <h1>🎓 GestiónDocente Premium</h1>
            <p>Sistema Integral de Gestión Educativa con IA</p>
        </div>
        """,
        unsafe_allow_html=True
    )
with col_logout:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# ==========================================
# PESTAÑAS
# ==========================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Dashboard",
    "👥 Alumnos",
    "📅 Asistencia",
    "📝 Calificaciones",
    "🧠 Registro Cualitativo",
    "🤖 Reportes IA"
])

# ==========================================
# TAB 1: DASHBOARD
# ==========================================
with tab1:
    st.subheader("Vista General del Grado")

    df_alumnos = cargar_alumnos()
    df_asistencia = cargar_asistencia()
    df_notas = cargar_notas()
    df_cualitativo = cargar_cualitativo()

    def kpi_card(col, label, value, color):
        col.markdown(
            f"""
            <div class="kpi-card" style="--kpi-color:{color};">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    k1, k2, k3, k4 = st.columns(4)
    kpi_card(k1, "👥 Total Alumnos", len(df_alumnos), "#1e293b")
    kpi_card(k2, "📅 Registros Asistencia", len(df_asistencia), "#2563eb")
    kpi_card(k3, "📝 Calificaciones", len(df_notas), "#ca8a04")
    kpi_card(k4, "🧠 Registros Cualitativos", len(df_cualitativo), "#16a34a")

    st.markdown("---")

    if not df_asistencia.empty and "Estado" in df_asistencia.columns:
        st.subheader("🚨 Alertas Automáticas")

        # Alertas de asistencia baja
        ausentes = df_asistencia[df_asistencia["Estado"].str.lower() == "ausente"]
        if not ausentes.empty:
            conteo_ausencias = ausentes.groupby("Nombre").size().reset_index(name="Ausencias")
            alertas = conteo_ausencias[conteo_ausencias["Ausencias"] >= 3]
            for _, row in alertas.iterrows():
                st.warning(f"⚠️ **{row['Nombre']}** tiene {row['Ausencias']} ausencias registradas.")

        # Alertas conducta grave
        if not df_cualitativo.empty and "Conducta" in df_cualitativo.columns:
            graves = df_cualitativo[df_cualitativo["Conducta"].str.lower() == "grave"]
            for _, row in graves.iterrows():
                st.error(f"🚨 **{row['Nombre']}** tiene registro de conducta **Grave** el {row.get('Fecha', 'fecha no especificada')}.")

    if not df_asistencia.empty and "Estado" in df_asistencia.columns:
        st.markdown("---")
        st.subheader("📊 Distribución de Asistencia")
        estado_counts = df_asistencia["Estado"].value_counts().reset_index()
        estado_counts.columns = ["Estado", "Cantidad"]
        fig = px.pie(estado_counts, names="Estado", values="Cantidad", hole=0.4,
                     color_discrete_sequence=["#1e293b", "#2563eb", "#ca8a04", "#16a34a", "#dc2626"])
        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="#1e293b")
        )
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TAB 2: ALUMNOS
# ==========================================
with tab2:
    st.subheader("👥 Directorio de Alumnos")

    with st.expander("➕ Agregar nuevo alumno"):
        with st.form("form_alumno", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nombre = st.text_input("Nombre *")
                apellido = st.text_input("Apellido *")
                grado = st.selectbox("Grado:", ["1°","2°","3°","4°","5°","6°"])
                seccion = st.selectbox("Sección:", ["A","B","C","D"])
            with c2:
                dni = st.text_input("DNI")
                fecha_nac = st.date_input("Fecha de Nacimiento", datetime.date(2015, 1, 1))
                contacto = st.text_input("Contacto (teléfono o email)")

            if st.form_submit_button("✅ Guardar Alumno", type="primary"):
                if nombre and apellido:
                    datos = {
                        "action": "agregar_alumno",
                        "id": str(uuid.uuid4())[:8].upper(),
                        "nombre": nombre,
                        "apellido": apellido,
                        "grado": grado,
                        "seccion": seccion,
                        "dni": dni,
                        "fecha_nacimiento": str(fecha_nac),
                        "contacto": contacto
                    }
                    if enviar_gas(datos):
                        st.success("✅ Alumno guardado.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Error al guardar.")
                else:
                    st.warning("Nombre y apellido son obligatorios.")

    df_alumnos = cargar_alumnos()
    if not df_alumnos.empty:
        st.dataframe(df_alumnos, use_container_width=True, hide_index=True)
    else:
        st.info("No hay alumnos cargados todavía.")

# ==========================================
# TAB 3: ASISTENCIA
# ==========================================
with tab3:
    st.subheader("📅 Registro de Asistencia")

    df_alumnos = cargar_alumnos()

    if df_alumnos.empty:
        st.warning("Primero cargá alumnos en la pestaña Alumnos.")
    else:
        opciones = [f"{row['Nombre']} {row['Apellido']}" for _, row in df_alumnos.iterrows()]
        ids = [row['ID'] for _, row in df_alumnos.iterrows()]

        with st.form("form_asistencia", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                alumno_sel = st.selectbox("Alumno *", opciones)
                fecha = st.date_input("Fecha *", datetime.date.today())
            with c2:
                estado = st.selectbox("Estado *", ["Presente", "Ausente", "Tardanza", "Ausente con aviso"])
                observacion = st.text_input("Observación (opcional)")

            if st.form_submit_button("✅ Registrar Asistencia", type="primary"):
                idx = opciones.index(alumno_sel)
                datos = {
                    "action": "registrar_asistencia",
                    "id_alumno": ids[idx],
                    "nombre": alumno_sel,
                    "fecha": str(fecha),
                    "estado": estado,
                    "observacion": observacion
                }
                if enviar_gas(datos):
                    st.success("✅ Asistencia registrada.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Error al guardar.")

        st.markdown("---")
        df_asistencia = cargar_asistencia()
        if not df_asistencia.empty:
            st.subheader("Historial de Asistencia")
            st.dataframe(df_asistencia, use_container_width=True, hide_index=True)

# ==========================================
# TAB 4: CALIFICACIONES
# ==========================================
with tab4:
    st.subheader("📝 Registro de Calificaciones")

    df_alumnos = cargar_alumnos()

    if df_alumnos.empty:
        st.warning("Primero cargá alumnos en la pestaña Alumnos.")
    else:
        opciones = [f"{row['Nombre']} {row['Apellido']}" for _, row in df_alumnos.iterrows()]
        ids = [row['ID'] for _, row in df_alumnos.iterrows()]

        with st.form("form_notas", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                alumno_sel = st.selectbox("Alumno *", opciones)
                materia = st.selectbox("Materia *", [
                    "Prácticas del Lenguaje", "Matemática", "Ciencias Naturales",
                    "Ciencias Sociales", "Educación Física", "Música", "Plástica", "Inglés", "Otra"
                ])
            with c2:
                periodo = st.selectbox("Período *", ["1° Trimestre", "2° Trimestre", "3° Trimestre"])
                nota = st.slider("Nota *", 1, 10, 7)
                observacion = st.text_input("Observación (opcional)")

            if st.form_submit_button("✅ Guardar Nota", type="primary"):
                idx = opciones.index(alumno_sel)
                datos = {
                    "action": "cargar_nota",
                    "id_alumno": ids[idx],
                    "nombre": alumno_sel,
                    "materia": materia,
                    "periodo": periodo,
                    "nota": nota,
                    "observacion": observacion
                }
                if enviar_gas(datos):
                    st.success("✅ Nota guardada.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Error al guardar.")

        st.markdown("---")
        df_notas = cargar_notas()
        if not df_notas.empty:
            st.subheader("Historial de Calificaciones")
            st.dataframe(df_notas, use_container_width=True, hide_index=True)

# ==========================================
# TAB 5: REGISTRO CUALITATIVO
# ==========================================
with tab5:
    st.subheader("🧠 Bitácora Cualitativa del Alumno")

    df_alumnos = cargar_alumnos()

    if df_alumnos.empty:
        st.warning("Primero cargá alumnos en la pestaña Alumnos.")
    else:
        opciones = [f"{row['Nombre']} {row['Apellido']}" for _, row in df_alumnos.iterrows()]
        ids = [row['ID'] for _, row in df_alumnos.iterrows()]

        with st.form("form_cualitativo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                alumno_sel = st.selectbox("Alumno *", opciones)
                fecha = st.date_input("Fecha *", datetime.date.today())
                conducta = st.selectbox("Conducta *", ["Excelente", "Muy Buena", "Buena", "Regular", "Grave"])
                compañerismo = st.selectbox("Compañerismo *", ["Excelente", "Muy Bueno", "Bueno", "Regular", "Deficiente"])
            with c2:
                destaca_en = st.text_input("Destaca en:", placeholder="Ej: Matemática, Arte, Liderazgo")
                tipo = st.selectbox("Tipo de registro:", ["Observación general", "Logro", "Alerta", "Comunicación con familia"])
                observacion = st.text_area("Observación detallada:", height=100)

            if st.form_submit_button("✅ Guardar Registro", type="primary"):
                idx = opciones.index(alumno_sel)
                datos = {
                    "action": "registro_cualitativo",
                    "id_alumno": ids[idx],
                    "nombre": alumno_sel,
                    "fecha": str(fecha),
                    "conducta": conducta,
                    "compañerismo": compañerismo,
                    "destaca_en": destaca_en,
                    "observacion": observacion,
                    "tipo": tipo
                }
                if enviar_gas(datos):
                    st.success("✅ Registro guardado.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Error al guardar.")

        st.markdown("---")
        df_cual = cargar_cualitativo()
        if not df_cual.empty:
            st.subheader("Historial de Registros Cualitativos")
            st.dataframe(df_cual, use_container_width=True, hide_index=True)

# ==========================================
# TAB 6: REPORTES IA
# ==========================================
with tab6:
    st.subheader("🤖 Generador de Informes con IA")
    st.caption("Seleccioná un alumno y la IA genera un informe formal con todos sus datos.")

    df_alumnos = cargar_alumnos()

    if df_alumnos.empty:
        st.warning("Primero cargá alumnos para poder generar informes.")
    elif client is None:
        st.error("❌ Clave de Groq no configurada en Secrets.")
    else:
        opciones = [f"{row['Nombre']} {row['Apellido']}" for _, row in df_alumnos.iterrows()]
        ids = [row['ID'] for _, row in df_alumnos.iterrows()]

        alumno_sel = st.selectbox("Seleccioná el alumno:", opciones)
        periodo_inf = st.selectbox("Período del informe:", ["1° Trimestre", "2° Trimestre", "3° Trimestre", "Anual"])
        nombre_docente = st.text_input("Nombre del/la docente:", placeholder="Maestra Laura García")
        nombre_escuela = st.text_input("Nombre de la escuela:", placeholder="Escuela N°5 San Pedro")

        if st.button("✨ Generar Informe Formal", type="primary"):
            idx = opciones.index(alumno_sel)
            id_alumno = ids[idx]

            df_asistencia = cargar_asistencia()
            df_notas = cargar_notas()
            df_cual = cargar_cualitativo()

            asist_alumno = df_asistencia[df_asistencia["ID_Alumno"].astype(str) == str(id_alumno)] if not df_asistencia.empty else pd.DataFrame()
            notas_alumno = df_notas[df_notas["ID_Alumno"].astype(str) == str(id_alumno)] if not df_notas.empty else pd.DataFrame()
            cual_alumno = df_cual[df_cual["ID_Alumno"].astype(str) == str(id_alumno)] if not df_cual.empty else pd.DataFrame()

            total_dias = len(asist_alumno)
            presentes = len(asist_alumno[asist_alumno["Estado"] == "Presente"]) if not asist_alumno.empty else 0
            porcentaje_asist = f"{int(presentes/total_dias*100)}%" if total_dias > 0 else "Sin datos"

            notas_txt = ""
            if not notas_alumno.empty:
                for _, r in notas_alumno.iterrows():
                    notas_txt += f"- {r['Materia']}: {r['Nota']}/10 ({r['Periodo']})\n"
            else:
                notas_txt = "Sin calificaciones registradas."

            cual_txt = ""
            if not cual_alumno.empty:
                for _, r in cual_alumno.iterrows():
                    cual_txt += f"- {r['Fecha']}: Conducta {r['Conducta']}, Compañerismo {r['Compañerismo']}. {r['Observacion']}\n"
            else:
                cual_txt = "Sin registros cualitativos."

            with st.spinner("Generando informe..."):
                prompt = f"""Sos una docente experta de nivel primario de la Provincia de Buenos Aires.
Generá un informe pedagógico formal y completo del siguiente alumno para el {periodo_inf}.

ALUMNO: {alumno_sel}
DOCENTE: {nombre_docente if nombre_docente else 'No especificado'}
ESCUELA: {nombre_escuela if nombre_escuela else 'No especificada'}
FECHA: {datetime.date.today().strftime('%d/%m/%Y')}

ASISTENCIA:
- Total de registros: {total_dias}
- Presencias: {presentes}
- Porcentaje: {porcentaje_asist}

CALIFICACIONES:
{notas_txt}

REGISTROS CUALITATIVOS:
{cual_txt}

El informe debe:
1. Tener encabezado formal con nombre, escuela, período y fecha
2. Sección de presentismo con análisis
3. Sección de desempeño académico por área
4. Sección de desenvolvimiento personal y social
5. Conclusión y recomendaciones
6. Firma del docente al pie

Usá lenguaje pedagógico formal bonaerense. El informe debe poder ser impreso y presentado a la familia."""

                try:
                    completion = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile",
                        temperature=0.3,
                    )
                    informe = completion.choices[0].message.content
                    st.success("✅ Informe generado.")
                    st.markdown("---")
                    st.markdown(informe)
                    st.download_button(
                        label="📥 Descargar Informe (.txt)",
                        data=informe.encode("utf-8"),
                        file_name=f"Informe_{alumno_sel.replace(' ','_')}_{periodo_inf.replace(' ','_')}.txt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"Error: {str(e)}")