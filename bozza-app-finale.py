import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from supabase import create_client

# =========================
# 🔧 DATA OPERATIVA
# =========================
def data_operativa():
    oggi = datetime.now()

    if oggi.weekday() == 4:  # venerdì
        prossima = oggi + timedelta(days=3)
    elif oggi.weekday() == 5:  # sabato
        prossima = oggi + timedelta(days=2)
    elif oggi.weekday() == 6:  # domenica
        prossima = oggi + timedelta(days=1)
    else:
        prossima = oggi + timedelta(days=1)

    giorni = [
        "Lunedì", "Martedì", "Mercoledì",
        "Giovedì", "Venerdì", "Sabato", "Domenica"
    ]

    return f"{giorni[prossima.weekday()]} {prossima.strftime('%d/%m/%Y')}"

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

FILE = f"clienti_{azienda}.csv"

st.markdown(f"## 🏢 Azienda: {azienda.upper()}")

# =========================
# 📧 EMAIL
# =========================
EMAIL_MITTENTE = st.secrets["EMAIL_MITTENTE"]
PASSWORD_APP = st.secrets["PASSWORD_APP"]

def invia_email(destinatari, prezzo, template, nome=""):
    try:
        data = data_operativa()

        testo = template \
            .replace("{prezzo}", f"{prezzo:.3f}") \
            .replace("{nome}", nome) \
            .replace("{data}", data)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"OFFERTA CARBURANTE - {data}"
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
# 💾 DATA
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

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

if "prezzo_base" not in st.session_state:
    st.session_state.prezzo_base = 1.000

if "email_template" not in st.session_state:
    st.session_state.email_template = """..."""  # lasciato IDENTICO

if "wa_template" not in st.session_state:
    st.session_state.wa_template = """..."""  # lasciato IDENTICO

df = st.session_state.clienti

# =========================
# NAV
# =========================
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("📊 Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"

with c2:
    if st.button("👤 Clienti", use_container_width=True):
        st.session_state.page = "clienti"

with c3:
    if st.button("➕ Nuovo", use_container_width=True):
        st.session_state.page = "cliente"

st.divider()

# =========================
# DASHBOARD
# =========================
if st.session_state.page == "dashboard":

    prezzo_base = st.number_input(
        "⛽ Prezzo base",
        value=float(st.session_state.prezzo_base),
        step=0.001,
        format="%.3f"
    )

    st.session_state.prezzo_base = prezzo_base

    if st.button("📧 Invia email a tutti"):
        for _, c in df.iterrows():
            if c["Email"] and pd.notna(c["Email"]):
                prezzo = calc_price(prezzo_base, c["Margine"], c["Trasporto"])
                invia_email(c["Email"], prezzo, st.session_state.email_template, c["Nome"])

    for _, c in df.iterrows():

        prezzo = calc_price(prezzo_base, c["Margine"], c["Trasporto"])

        col1, col2 = st.columns(2)

        with col1:
            import urllib.parse

            tel = str(c["Telefono"]).replace("+", "").replace(" ", "")

            msg = st.session_state.wa_template \
                .replace("{prezzo}", format_euro(prezzo)) \
                .replace("{nome}", c["Nome"]) \
                .replace("{data}", data_operativa())

            msg_encoded = urllib.parse.quote(msg)

            wa = f"https://wa.me/{tel}?text={msg_encoded}"

            st.link_button("📲 WhatsApp", wa)

        with col2:
            if c["Email"] and pd.notna(c["Email"]):
                if st.button("📧 Email", key=f"mail_{c['ID']}"):
                    invia_email(c["Email"], prezzo, st.session_state.email_template, c["Nome"])
                    st.success("Email inviata")
