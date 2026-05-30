import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="FuelCRM",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# SUPABASE
# =========================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# =========================
# DATA
# =========================
def load_data():
    res = supabase.table("clienti").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

df = load_data()

# =========================
# STYLE (TUO DESIGN MIGLIORATO)
# =========================
st.markdown("""
<style>

/* MAIN */
.block-container {
    padding: 1.5rem 2rem;
    background-color: #f6f7fb;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background-color: #0f172a;
}

[data-testid="stSidebar"] * {
    color: white;
    font-weight: 500;
}

/* HEADER */
.header-title {
    font-size: 28px;
    font-weight: 800;
}

.subtext {
    color: #6b7280;
    margin-top: -8px;
}

/* MENU STYLE */
.menu {
    padding: 10px 12px;
    border-radius: 10px;
    margin-bottom: 8px;
}

/* KPI */
.kpi-card {
    background: white;
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.06);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.kpi-title {
    font-size: 14px;
    color: #6b7280;
}

.kpi-value {
    font-size: 22px;
    font-weight: 800;
}

.icon-box {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* EMPTY */
.empty-box {
    background: white;
    border-radius: 16px;
    padding: 60px;
    text-align: center;
    box-shadow: 0 6px 20px rgba(0,0,0,0.06);
}

</style>
""", unsafe_allow_html=True)

# =========================
# SESSION STATE NAV
# =========================
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

# =========================
# SIDEBAR (NAV VERA)
# =========================
with st.sidebar:

    st.markdown("## ⛽ FuelCRM")

    if st.button("📊 Dashboard"):
        st.session_state.page = "dashboard"

    if st.button("👤 Clienti"):
        st.session_state.page = "clienti"

    if st.button("➕ Nuovo Cliente"):
        st.session_state.page = "nuovo"

    st.write("")

    if st.button("🚪 Esci"):
        st.stop()

# =========================
# HEADER
# =========================
st.markdown('<div class="header-title">Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtext">Gestione prezzi e invio offerte</div>', unsafe_allow_html=True)

# =========================
# PAGES
# =========================

# =========================
# DASHBOARD
# =========================
if st.session_state.page == "dashboard":

    col1, col2, col3 = st.columns([3,1,1])

    with col2:
        prezzo_base = st.text_input("Prezzo Base (€/L)", "1.0000")

    with col3:
        st.write("")
        st.button("📩 Invia a Tutti")

    st.write("---")

    # KPI CALC
    clienti = len(df)
    margine = df["margine"].mean() if not df.empty else 0
    prezzo_medio = 1.0 + margine

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-title">Clienti</div>
                <div class="kpi-value">{clienti}</div>
            </div>
            <div class="icon-box" style="background:#e0e7ff;">👤</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-title">Margine Medio</div>
                <div class="kpi-value">€{margine:.3f}</div>
            </div>
            <div class="icon-box" style="background:#ffedd5;">📈</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-title">Prezzo Medio</div>
                <div class="kpi-value">€{prezzo_medio:.3f}</div>
            </div>
            <div class="icon-box" style="background:#dcfce7;">💲</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")

    st.markdown("### Clienti")

    if df.empty:
        st.markdown("""
        <div class="empty-box">
            <div style="font-size:40px;">⛽</div>
            <h3>Nessun cliente ancora</h3>
            <p style="color:#6b7280;">Aggiungi il primo cliente per iniziare</p>
        </div>
        """, unsafe_allow_html=True)

    else:
        for _, c in df.iterrows():
            st.markdown(f"""
            <div class="kpi-card">
                <div>
                    <b>{c['nome']}</b><br>
                    {c['email']}
                </div>
                <div class="icon-box" style="background:#e0e7ff;">👤</div>
            </div>
            """, unsafe_allow_html=True)

# =========================
# CLIENTI
# =========================
elif st.session_state.page == "clienti":

    st.markdown("### Clienti")

    for _, c in df.iterrows():
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <b>{c['nome']}</b><br>
                {c['email']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# =========================
# NUOVO CLIENTE
# =========================
elif st.session_state.page == "nuovo":

    st.markdown("### Nuovo Cliente")

    with st.form("f"):

        nome = st.text_input("Nome")
        email = st.text_input("Email")
        tel = st.text_input("Telefono")
        margine = st.number_input("Margine", value=0.0, step=0.001)

        ok = st.form_submit_button("Salva")

        if ok:
            supabase.table("clienti").insert({
                "nome": nome,
                "email": email,
                "telefono": tel,
                "margine": margine
            }).execute()

            st.success("Cliente creato")
            st.rerun()
