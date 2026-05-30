import streamlit as st
import pandas as pd
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client
import urllib.parse

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="FuelCRM", layout="wide")

# =========================
# SUPABASE
# =========================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

EMAIL = st.secrets["EMAIL_MITTENTE"]
PASSW = st.secrets["PASSWORD_APP"]

# =========================
# STATE
# =========================
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "base" not in st.session_state:
    st.session_state.base = 1.000


# =========================
# LOAD DATA
# =========================
def load():
    res = supabase.table("clienti").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

def save(df):
    supabase.table("clienti").upsert(df.to_dict("records")).execute()

df = load()

# =========================
# UTIL
# =========================
def calc(base, m):
    return round(base + float(m), 3)

def next_workday():
    d = datetime.now() + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


# =========================
# EMAIL
# =========================
def send_email(to, subject, html):
    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    s = smtplib.SMTP("smtp.gmail.com", 587)
    s.starttls()
    s.login(EMAIL, PASSW)
    s.send_message(msg)
    s.quit()


# =========================
# UI STYLE
# =========================
st.markdown("""
<style>

.block-container {padding: 1.5rem; background:#f4f6fb;}

[data-testid="stSidebar"] {background:#0b1324;}

.kpi {
    background:white;
    padding:18px;
    border-radius:16px;
    box-shadow:0 6px 18px rgba(0,0,0,0.06);
}

.title {font-size:28px;font-weight:800;}
.sub {color:#6b7280;margin-top:-6px;}

.card {
    background:white;
    padding:15px;
    border-radius:14px;
    box-shadow:0 6px 18px rgba(0,0,0,0.05);
}

button {
    border-radius:10px !important;
}

</style>
""", unsafe_allow_html=True)


# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("## ⛽ FuelCRM")

    if st.button("📊 Dashboard"):
        st.session_state.page = "dashboard"

    if st.button("👤 Clienti"):
        st.session_state.page = "clienti"

    if st.button("➕ Nuovo"):
        st.session_state.page = "new"

    st.write("---")

    if st.button("🚪 Esci"):
        st.stop()


# =========================
# DASHBOARD
# =========================
if st.session_state.page == "dashboard":

    st.markdown('<div class="title">Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub">Gestione prezzi e invio offerte</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3,1])

    with col1:
        base = st.number_input("Prezzo base €/L", value=st.session_state.base)

    with col2:
        st.write("")
        st.button("📩 Invia a tutti")

    st.session_state.base = base

    st.write("")

    # KPI
    clienti = len(df)
    margine = df["margine"].mean() if not df.empty else 0
    prezzo = base + margine

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"<div class='kpi'><b>Clienti</b><h2>{clienti}</h2></div>", unsafe_allow_html=True)

    with c2:
        st.markdown(f"<div class='kpi'><b>Margine</b><h2>€{margine:.3f}</h2></div>", unsafe_allow_html=True)

    with c3:
        st.markdown(f"<div class='kpi'><b>Prezzo medio</b><h2>€{prezzo:.3f}</h2></div>", unsafe_allow_html=True)

    st.write("---")

    st.markdown("### Clienti")

    if df.empty:
        st.info("Nessun cliente ancora")
    else:
        for _, c in df.iterrows():

            price = calc(base, c["margine"])
            data = next_workday().strftime("%d/%m/%Y")

            st.markdown(f"""
            <div class='card'>
            <b>{c['nome']}</b><br>
            📧 {c['email']}<br>
            💰 {price} €/L
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                msg = f"Offerta carburante {price} €/L per il {data}"
                wa = f"https://wa.me/{c['telefono']}?text={urllib.parse.quote(msg)}"
                st.link_button("WhatsApp", wa)

            with col2:
                if st.button("Email", key=c["id"]):
                    html = f"<h3>Offerta carburante</h3><p>Prezzo: {price} €/L</p>"
                    send_email(c["email"], "Offerta carburante", html)
                    st.success("Inviata")


# =========================
# CLIENTI
# =========================
elif st.session_state.page == "clienti":

    st.markdown("### Clienti")

    for _, c in df.iterrows():
        st.markdown(f"""
        <div class='card'>
        <b>{c['nome']}</b><br>
        {c['email']} - {c['telefono']}
        </div>
        """, unsafe_allow_html=True)


# =========================
# NEW CLIENT
# =========================
elif st.session_state.page == "new":

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
