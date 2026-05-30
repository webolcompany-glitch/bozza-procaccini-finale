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

def load():
    res = supabase.table("clienti").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

df = load()

# =========================
# UI IMPROVED (SAAS LEVEL)
# =========================
st.markdown("""
<style>

/* BACKGROUND */
.block-container {
    padding: 1.2rem 2rem;
    background: #f4f6fb;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b1324 0%, #0f172a 100%);
}

[data-testid="stSidebar"] * {
    color: #e5e7eb;
}

/* LOGO */
.logo {
    font-size: 22px;
    font-weight: 900;
    padding: 10px 0 20px 0;
}

/* NAV BUTTON STYLE */
.stButton>button {
    width: 100%;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.08);
    background: transparent;
    color: #e5e7eb;
    padding: 10px;
    transition: 0.2s;
}

.stButton>button:hover {
    background: rgba(255,255,255,0.08);
    transform: translateX(2px);
}

/* HEADER */
.header-title {
    font-size: 32px;
    font-weight: 900;
    letter-spacing: -0.5px;
}

.subtext {
    color: #6b7280;
    margin-top: -6px;
}

/* KPI CARD (MODERN SAAS) */
.kpi-card {
    background: white;
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.06);
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: 0.2s;
    border: 1px solid rgba(0,0,0,0.04);
}

.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 14px 35px rgba(0,0,0,0.08);
}

.kpi-title {
    font-size: 13px;
    color: #6b7280;
}

.kpi-value {
    font-size: 24px;
    font-weight: 900;
    color: #111827;
}

.icon-box {
    width: 44px;
    height: 44px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
}

/* CLIENT CARD */
.client-card {
    background: white;
    padding: 16px;
    border-radius: 16px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.05);
    border: 1px solid rgba(0,0,0,0.04);
    margin-bottom: 10px;
    transition: 0.2s;
}

.client-card:hover {
    transform: scale(1.01);
}

/* EMPTY STATE */
.empty-box {
    background: white;
    border-radius: 18px;
    padding: 70px;
    text-align: center;
    box-shadow: 0 10px 25px rgba(0,0,0,0.05);
}

/* INPUT */
input {
    border-radius: 12px !important;
}

</style>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR (MOLTO PIÙ SAAS)
# =========================
with st.sidebar:

    st.markdown("<div class='logo'>⛽ FuelCRM</div>", unsafe_allow_html=True)

    if st.button("📊 Dashboard"):
        st.session_state.page = "dashboard"

    if st.button("👤 Clienti"):
        st.session_state.page = "clienti"

    if st.button("➕ Nuovo Cliente"):
        st.session_state.page = "new"

    st.write("")

    if st.button("🚪 Logout"):
        st.stop()

# =========================
# HEADER
# =========================
st.markdown('<div class="header-title">Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtext">Gestione prezzi e invio offerte carburante</div>', unsafe_allow_html=True)

# =========================
# DASHBOARD
# =========================
if st.session_state.page == "dashboard":

    col1, col2, col3 = st.columns([3,1,1])

    with col2:
        base = st.text_input("Prezzo Base €/L", "1.0000")

    with col3:
        st.write("")
        st.button("📩 Invia")

    st.write("---")

    clienti = len(df)
    margine = df["margine"].mean() if not df.empty else 0
    prezzo = 1 + margine

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
                <div class="kpi-value">€{prezzo:.3f}</div>
            </div>
            <div class="icon-box" style="background:#dcfce7;">💲</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")

    st.markdown("### Clienti")

    if df.empty:
        st.markdown("""
        <div class="empty-box">
            <h2>⛽ Nessun cliente</h2>
            <p style="color:#6b7280;">Aggiungi il primo cliente per iniziare</p>
        </div>
        """, unsafe_allow_html=True)

    else:
        for _, c in df.iterrows():
            st.markdown(f"""
            <div class="client-card">
                <b>{c['nome']}</b><br>
                <span style="color:#6b7280">{c['email']}</span>
            </div>
            """, unsafe_allow_html=True)
