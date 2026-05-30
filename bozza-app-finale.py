import streamlit as st

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="FuelCRM",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# STATE
# =========================
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

def set_page(page):
    st.session_state.page = page


# =========================
# CSS ULTRA UI
# =========================
st.markdown("""
<style>

/* GLOBAL */
.block-container {
    padding: 1.2rem 2rem;
    background: #f4f6fb;
    font-family: Inter, sans-serif;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: #0b1324;
}

.sidebar-logo {
    font-size: 22px;
    font-weight: 800;
    color: white;
    margin-bottom: 25px;
}

.nav-item {
    padding: 12px 14px;
    border-radius: 10px;
    margin-bottom: 8px;
    color: #cbd5e1;
    cursor: pointer;
    transition: 0.2s;
}

.nav-item:hover {
    background: rgba(255,255,255,0.08);
}

.nav-active {
    background: #f59e0b;
    color: black !important;
    font-weight: 700;
}

/* HEADER */
.title {
    font-size: 30px;
    font-weight: 800;
}

.subtitle {
    color: #6b7280;
    margin-top: -6px;
}

/* TOP BAR */
.topbar {
    background: white;
    padding: 14px;
    border-radius: 14px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.05);
}

/* KPI */
.kpi {
    background: white;
    padding: 18px;
    border-radius: 16px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    transition: 0.2s;
}

.kpi:hover {
    transform: translateY(-2px);
}

.kpi-title {
    font-size: 13px;
    color: #6b7280;
}

.kpi-value {
    font-size: 24px;
    font-weight: 800;
}

/* EMPTY STATE */
.empty {
    background: white;
    padding: 70px;
    border-radius: 16px;
    text-align: center;
    box-shadow: 0 6px 18px rgba(0,0,0,0.05);
}

.button-primary {
    background: #f59e0b;
    padding: 10px 14px;
    border-radius: 10px;
    color: black;
    font-weight: 700;
    text-align: center;
}

</style>
""", unsafe_allow_html=True)


# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown('<div class="sidebar-logo">⛽ FuelCRM</div>', unsafe_allow_html=True)

    if st.button("📊 Dashboard"):
        set_page("Dashboard")
    if st.button("👤 Clienti"):
        set_page("Clienti")
    if st.button("➕ Nuovo Cliente"):
        set_page("Nuovo")

    st.write("")
    if st.button("🚪 Esci"):
        st.stop()


# =========================
# DASHBOARD
# =========================
if st.session_state.page == "Dashboard":

    st.markdown('<div class="title">Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Gestione prezzi e invio offerte</div>', unsafe_allow_html=True)

    st.write("")

    # TOPBAR
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        pass

    with col2:
        st.text_input("Prezzo Base (€/L)", "1.0000")

    with col3:
        st.write("")
        st.button("📩 Invia a Tutti")

    st.write("")

    # KPI
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        <div class="kpi">
            <div class="kpi-title">Clienti</div>
            <div class="kpi-value">0</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="kpi">
            <div class="kpi-title">Margine Medio</div>
            <div class="kpi-value">€0.0000/L</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="kpi">
            <div class="kpi-title">Prezzo Medio</div>
            <div class="kpi-value">€0.0000/L</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # EMPTY STATE
    st.markdown("""
    <div class="empty">
        <div style="font-size:40px;">⛽</div>
        <h3>Nessun cliente ancora</h3>
        <p style="color:#6b7280;">Aggiungi il primo cliente per iniziare</p>
    </div>
    """, unsafe_allow_html=True)


# =========================
# CLIENTI
# =========================
elif st.session_state.page == "Clienti":
    st.markdown('<div class="title">Clienti</div>', unsafe_allow_html=True)
    st.write("Qui inseriremo tabella CRM vera (AgGrid / database)")

# =========================
# NUOVO CLIENTE
# =========================
elif st.session_state.page == "Nuovo":
    st.markdown('<div class="title">Nuovo Cliente</div>', unsafe_allow_html=True)

    with st.form("cliente"):
        nome = st.text_input("Nome Cliente")
        email = st.text_input("Email")
        prezzo = st.number_input("Prezzo personalizzato", value=1.0)

        submit = st.form_submit_button("Salva Cliente")

        if submit:
            st.success("Cliente salvato (demo)")
