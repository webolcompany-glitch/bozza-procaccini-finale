import streamlit as st

# =====================
# CONFIG PAGE
# =====================
st.set_page_config(
    page_title="FuelCRM",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================
# CSS (LOOK MODERNO)
# =====================
st.markdown("""
<style>

.block-container {
    padding-top: 1.5rem;
}

h1 {
    font-size: 28px;
    font-weight: 700;
}

/* KPI cards */
.kpi {
    background: white;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    text-align: center;
}

/* sidebar */
[data-testid="stSidebar"] {
    background-color: #0f172a;
}

[data-testid="stSidebar"] * {
    color: white;
}

/* button */
.stButton>button {
    border-radius: 10px;
    background-color: #f59e0b;
    color: black;
    font-weight: 600;
    border: none;
}

.stButton>button:hover {
    background-color: #fbbf24;
    color: black;
}

</style>
""", unsafe_allow_html=True)


# =====================
# SIDEBAR
# =====================
with st.sidebar:
    st.markdown("## ⛽ FuelCRM")

    menu = st.radio(
        "",
        ["📊 Dashboard", "👤 Clienti", "➕ Nuovo Cliente"]
    )

    st.write("---")

    if st.button("🚪 Esci"):
        st.warning("Logout simulato")
        st.stop()


# =====================
# DASHBOARD
# =====================
st.title("Dashboard")
st.caption("Gestione prezzi e invio offerte")

col1, col2 = st.columns([3, 1])

with col1:
    prezzo_base = st.text_input("Prezzo Base (€/L)", "1.0000")

with col2:
    st.write("")
    st.write("")
    st.button("📩 Invia a Tutti")


st.write("---")


# =====================
# KPI
# =====================
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown('<div class="kpi">', unsafe_allow_html=True)
    st.subheader("Clienti")
    st.title("0")
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="kpi">', unsafe_allow_html=True)
    st.subheader("Margine Medio")
    st.title("€0.0000/L")
    st.markdown('</div>', unsafe_allow_html=True)

with c3:
    st.markdown('<div class="kpi">', unsafe_allow_html=True)
    st.subheader("Prezzo Medio")
    st.title("€0.0000/L")
    st.markdown('</div>', unsafe_allow_html=True)


st.write("---")


# =====================
# CLIENTI SECTION
# =====================
st.subheader("Clienti (0)")

st.info("⛽ Nessun cliente ancora\n\nAggiungi il primo cliente per iniziare a gestire le offerte.")
