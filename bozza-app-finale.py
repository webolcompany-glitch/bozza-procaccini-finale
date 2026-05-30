import streamlit as st
import pandas as pd
from supabase import create_client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

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
# DATA
# =========================
def load_data():
    res = supabase.table("clienti").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

df = load_data()

# =========================
# EMAIL
# =========================
def send_email(to_email, nome, prezzo):

    msg = MIMEMultipart()
    msg["Subject"] = "Offerta Carburante"
    msg["From"] = EMAIL
    msg["To"] = to_email

    body = f"""
    Gentile {nome},

    prezzo carburante: {prezzo:.3f} €/L

    Cordiali saluti
    """

    msg.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL, PASS)
    server.sendmail(EMAIL, to_email, msg.as_string())
    server.quit()

# =========================
# UI STYLE (SAAS CLEAN)
# =========================
st.markdown("""
<style>

/* MAIN */
.block-container {
    padding: 1.2rem 2rem;
    background: #f4f6fb;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: #0f172a;
}

[data-testid="stSidebar"] * {
    color: white;
}

/* HEADER */
.header-title {
    font-size: 30px;
    font-weight: 900;
}

.subtext {
    color: #6b7280;
    margin-top: -5px;
}

/* KPI */
.kpi-card {
    background: white;
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.06);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.kpi-title {
    font-size: 13px;
    color: #6b7280;
}

.kpi-value {
    font-size: 24px;
    font-weight: 900;
}

.icon-box {
    width: 44px;
    height: 44px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* CARD CLIENT */
.client-card {
    background: white;
    padding: 14px;
    border-radius: 14px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.05);
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# SESSION NAV
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
        st.session_state.page = "new"

    st.write("")

    if st.button("🚪 Esci"):
        st.stop()

# =========================
# HEADER
# =========================
st.markdown('<div class="header-title">FuelCRM</div>', unsafe_allow_html=True)
st.markdown('<div class="subtext">Gestione clienti e offerte carburante</div>', unsafe_allow_html=True)

# =========================
# DASHBOARD
# =========================
if st.session_state.page == "dashboard":

    col1, col2, col3 = st.columns([3,1,1])

    with col2:
        base_price = st.text_input("Prezzo Base", "1.000")

    with col3:
        st.button("📩 Invia a tutti")

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
        st.info("Nessun cliente ancora")
    else:
        for _, c in df.iterrows():

            col1, col2 = st.columns([3,1])

            with col1:
                st.markdown(f"""
                <div class="client-card">
                    <b>{c['nome']}</b><br>
                    {c['email']}
                </div>
                """, unsafe_allow_html=True)

            with col2:
                if st.button("📧", key=f"mail_{c['id']}"):
                    prezzo_send = 1 + float(c["margine"])
                    send_email(c["email"], c["nome"], prezzo_send)
                    st.success("Email inviata")

# =========================
# CLIENTI
# =========================
elif st.session_state.page == "clienti":

    st.markdown("### Clienti")

    for _, c in df.iterrows():
        st.write(f"**{c['nome']}** - {c['email']}")

# =========================
# NUOVO CLIENTE
# =========================
elif st.session_state.page == "new":

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
