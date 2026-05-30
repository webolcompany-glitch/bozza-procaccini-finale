import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from supabase import create_client


def pasqua(anno):
    """Calcolo Pasqua (algoritmo di Gauss)"""
    a = anno % 19
    b = anno // 100
    c = anno % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mese = (h + l - 7 * m + 114) // 31
    giorno = ((h + l - 7 * m + 114) % 31) + 1
    return datetime(anno, mese, giorno)


def festivi_italiani(anno):
    pasqua_date = pasqua(anno)
    pasquetta = pasqua_date + timedelta(days=1)

    return set([
        datetime(anno, 1, 1),
        datetime(anno, 1, 6),
        datetime(anno, 4, 25),
        datetime(anno, 5, 1),
        datetime(anno, 6, 2),
        datetime(anno, 8, 15),
        datetime(anno, 11, 1),
        datetime(anno, 12, 8),
        datetime(anno, 12, 25),
        datetime(anno, 12, 26),
        pasqua_date,
        pasquetta
    ])


def prossimo_giorno_lavorativo(data=None):
    if data is None:
        data = datetime.now()

    giorno = data + timedelta(days=1)
    festivi = festivi_italiani(giorno.year)

    while giorno.weekday() >= 5 or giorno.replace(
        hour=0, minute=0, second=0, microsecond=0
    ) in festivi:
        giorno += timedelta(days=1)
        festivi = festivi_italiani(giorno.year)

    return giorno


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
        data_invio = datetime.now()
        data_scarico = prossimo_giorno_lavorativo()

        giorni = [
            "Lunedì", "Martedì", "Mercoledì",
            "Giovedì", "Venerdì", "Sabato", "Domenica"
        ]
        giorno_nome = giorni[data_scarico.weekday()]
        data = f"{giorno_nome} {data_scarico.strftime('%d/%m/%Y')}"

        testo = template \
            .replace("{prezzo}", f"{prezzo:.3f}") \
            .replace("{nome}", nome) \
            .replace("{data}", data)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"OFFERTA CARBURANTE - PREZZI VALIDI PER {data}"
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
        server.sendmail(EMAIL_MITTENTE, lista_email, msg.as_string())
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
        df["Nome"].astype(str).str.contains(search, case=False, na=False)
        | df["PIVA"].astype(str).str.contains(search, case=False, na=False)
        | df["Telefono"].astype(str).str.contains(search, case=False, na=False)
    ]


# =========================
# 💾 DATA
# =========================

def load_data():
    res = supabase.table("clienti").select("*").execute()
    data = res.data

    if not data:
        return pd.DataFrame(columns=[
            "ID", "Nome", "PIVA", "Telefono", "Email",
            "Margine", "Trasporto", "UltimoPrezzo"
        ])

    df = pd.DataFrame(data)

    return df.rename(columns={
        "id": "ID",
        "nome": "Nome",
        "piva": "PIVA",
        "telefono": "Telefono",
        "email": "Email",
        "margine": "Margine",
        "trasporto": "Trasporto",
        "ultimo_prezzo": "UltimoPrezzo"
    })


def save_data(df):
    records = df.rename(columns={
        "ID": "id",
        "Nome": "nome",
        "PIVA": "piva",
        "Telefono": "telefono",
        "Email": "email",
        "Margine": "margine",
        "Trasporto": "trasporto",
        "UltimoPrezzo": "ultimo_prezzo"
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
    st.session_state.email_template = """<div>..."""
    
if "wa_template" not in st.session_state:
    st.session_state.wa_template = """..."""

df = st.session_state.clienti
