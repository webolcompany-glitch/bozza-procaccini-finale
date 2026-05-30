import streamlit as st
import pandas as pd
from supabase import create_client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

EMAIL = st.secrets["EMAIL_MITTENTE"]
PASS = st.secrets["PASSWORD_APP"]

# =========================
# LOAD DATA
# =========================
def load_data():
    res = supabase.table("clienti").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

df = load_data()

# =========================
# EMAIL
# =========================
def invia_email(email, nome, prezzo):

    msg = MIMEMultipart()
    msg["Subject"] = "Offerta Carburante"
    msg["From"] = EMAIL
    msg["To"] = email

    body = f"""
    Gentile {nome},

    la nostra offerta carburante è: {prezzo:.4f} €/L

    Cordiali saluti
    """

    msg.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL, PASS)
    server.sendmail(EMAIL, email, msg.as_string())
    server.quit()

# =========================
# STYLE (UI IDENTICA SCREENSHOT)
# =========================
st.markdown("""
<style>

/* BACKGROUND */
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
}

/* HEADER */
.header-title {
    font-size: 28px;
    font-weight: 800;
}

.subtext {
    color: #6b7280;
    margin-top: -6px;
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
    border: 1px solid rgba(0,0,0,0.04);
}

.kpi-title {
    font-size: 13px;
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

/* CLIENT CARD */
.client-card {
    background: white;
    padding: 14px;
    border-radius: 14px;
    box-shadow: 0 6px 15px rgba(0,0,0,0.05);
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
}

/* EMPTY */
.empty-box {
    background: white;
    border-radius: 18px;
    padding: 60px;
    text-align: center;
    box-shadow: 0 6px 20px rgba(0,0,0,0.05);
}

</style>
""", unsafe_allow_html=True)

# =========================
# NAV STATE
# =========================
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

# =========================
# SIDEBAR
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
# HEADER (COME SCREENSHOT)
# =========================
st.markdown('<div class="header-title">Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtext">Gestione prezzi e invio offerte</div>', unsafe_allow_html=True)

# =========================
# DASHBOARD
# =========================
if st.session_state.page == "dashboard":

    # TOP BAR
    col1, col2, col3 = st.columns([3,1,1])

    with col2:
        prezzo_base = st.text_input("Prezzo Base (€/L)", "1.0000")

    with col3:
        st.button("📩 Invia a Tutti")

    st.write("---")

    clienti = len(df)
    margine = df["margine"].mean() if not df.empty else 0
    prezzo_medio = 1 + margine

    # KPI
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
                <div class="kpi-value">€{margine:.4f}/L</div>
            </div>
            <div class="icon-box" style="background:#ffedd5;">📈</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-title">Prezzo Medio</div>
                <div class="kpi-value">€{prezzo_medio:.4f}/L</div>
            </div>
            <div class="icon-box" style="background:#dcfce7;">💲</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")

    # CLIENTI
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

            col1, col2 = st.columns([3,1])

            with col1:
                st.markdown(f"""
                <div class="client-card">
                    <div>
                        <b>{c['nome']}</b><br>
                        <span style="color:#6b7280">{c['email']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                if st.button("📧", key=f"mail_{c['id']}"):
                    prezzo_send = 1 + float(c["margine"])
                    invia_email(c["email"], c["nome"], prezzo_send)
                    st.success("Email inviata")

# =========================
# CLIENTI PAGE
# =========================
elif st.session_state.page == "clienti":

    st.markdown("### Clienti")

    for _, c in df.iterrows():
        st.write(f"**{c['nome']}** - {c['email']}")

# =========================
# NUOVO CLIENTE
# =========================
elif st.session_state.page == "nuovo":

    st.markdown("### Nuovo Cliente")

    with st.form("form"):

        nome = st.text_input("Nome")
        email = st.text_input("Email")
        margine = st.number_input("Margine", 0.0, step=0.001)

        submit = st.form_submit_button("Salva")

        if submit:
            supabase.table("clienti").insert({
                "nome": nome,
                "email": email,
                "margine": margine
            }).execute()

            st.success("Cliente creato")
            st.rerun()
