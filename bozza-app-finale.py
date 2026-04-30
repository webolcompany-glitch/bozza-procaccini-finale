import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from supabase import create_client

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

st.set_page_config(page_title="Fuel SaaS", layout="wide")

# =========================
# 🏢 AZIENDA
# =========================
azienda = st.query_params.get("azienda", "demo")
if isinstance(azienda, list):
    azienda = azienda[0]

st.markdown(f"## 🏢 Azienda: {azienda.upper()}")

# =========================
# 📅 SCARICO LOGICA
# =========================
def calcola_data_scarico():
    oggi = datetime.now()

    # venerdì -> lunedì
    if oggi.weekday() == 4:
        return (oggi + timedelta(days=3)).strftime("%d/%m/%Y")
    else:
        return (oggi + timedelta(days=1)).strftime("%d/%m/%Y")

# =========================
# 📧 EMAIL
# =========================
EMAIL_MITTENTE = st.secrets["EMAIL_MITTENTE"]
PASSWORD_APP = st.secrets["PASSWORD_APP"]

def invia_email(destinatari, prezzo, template, nome=""):
    try:
        data = datetime.now().strftime("%d/%m/%Y")
        scarico = calcola_data_scarico()

        testo = template \
            .replace("{prezzo}", f"{prezzo:.3f}") \
            .replace("{nome}", nome) \
            .replace("{data}", data) \
            .replace("{scarico}", scarico)

        msg = MIMEMultipart("alternative")

        # 👉 OGGETTO EMAIL MODIFICATO COME RICHIESTO
        msg["Subject"] = f"OFFERTA CARBURANTE - PREZZI VALIDi PER SCARICO {scarico}"
        msg["From"] = EMAIL_MITTENTE

        lista_email = [e.strip() for e in destinatari.split(",") if e.strip()]
        if not lista_email:
            return

        msg["To"] = lista_email[0]
        if len(lista_email) > 1:
            msg["Cc"] = ", ".join(lista_email[1:])

        msg.attach(MIMEText(testo, "html", "utf-8"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_MITTENTE, PASSWORD_APP)

        server.sendmail(
            EMAIL_MITTENTE,
            lista_email,
            msg.as_string()
        )

        server.quit()

    except Exception as e:
        st.error(f"Errore email: {e}")

# =========================
# 🔒 UTIL
# =========================
def format_euro(x):
    if x is None or pd.isna(x):
        return "0,000"
    return f"{round(float(x), 3):.3f}".replace(".", ",")

def calc_price(base, margine, trasporto):
    return round(float(base) + float(margine) + float(trasporto), 3)

def filtra_clienti(df, search):
    if not search:
        return df
    return df[
        df["Nome"].astype(str).str.contains(search, case=False, na=False) |
        df["PIVA"].astype(str).str.contains(search, case=False, na=False) |
        df["Telefono"].astype(str).str.contains(search, case=False, na=False)
    ]

# =========================
# 🎴 CARD (FIX ERRORE)
# =========================
def card(title, value):
    return f"""
    <div style="padding:14px;border-radius:14px;background:#111827;
    color:white;text-align:center;margin:6px 0;">
        <div style="font-size:12px;opacity:0.7;">{title}</div>
        <div style="font-size:20px;font-weight:600">{value}</div>
    </div>
    """

# =========================
# 💾 DATA (SEMPLIFICATO MA INTEGRO)
# =========================
def load_data():
    res = supabase.table("clienti").select("*").execute()
    data = res.data

    if not data:
        return pd.DataFrame(columns=[
            "ID","Nome","PIVA","Telefono","Email",
            "Margine","Trasporto","UltimoPrezzo"
        ])

    df = pd.DataFrame(data)

    df = df.rename(columns={
        "id":"ID",
        "nome":"Nome",
        "piva":"PIVA",
        "telefono":"Telefono",
        "email":"Email",
        "margine":"Margine",
        "trasporto":"Trasporto",
        "ultimo_prezzo":"UltimoPrezzo"
    })

    return df

def save_data(df):
    records = df.rename(columns={
        "ID":"id",
        "Nome":"nome",
        "PIVA":"piva",
        "Telefono":"telefono",
        "Email":"email",
        "Margine":"margine",
        "Trasporto":"trasporto",
        "UltimoPrezzo":"ultimo_prezzo"
    }).to_dict(orient="records")

    if records:
        supabase.table("clienti").upsert(records).execute()

# =========================
# INIT
# =========================
if "clienti" not in st.session_state:
    st.session_state.clienti = load_data()

if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "prezzo_base" not in st.session_state:
    st.session_state.prezzo_base = 1.000

df = st.session_state.clienti

# =========================
# DASHBOARD
# =========================
if st.session_state.page == "dashboard":

    st.markdown("## ⛽ Dashboard operativa")

    prezzo_base = st.number_input(
        "⛽ Prezzo base",
        value=float(st.session_state.prezzo_base),
        step=0.001,
        format="%.3f"
    )

    st.session_state.prezzo_base = prezzo_base

    clienti_count = len(df)
    media_margine = round(df["Margine"].mean(), 3) if not df.empty else 0

    prezzo_medio = (
        calc_price(prezzo_base, df["Margine"].mean(), df["Trasporto"].mean())
        if not df.empty else prezzo_base
    )

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(card("⛽ Base", format_euro(prezzo_base)), unsafe_allow_html=True)

    with c2:
        st.markdown(card("👤 Clienti", clienti_count), unsafe_allow_html=True)
