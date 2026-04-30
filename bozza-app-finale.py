import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from supabase import create_client

# ✅ AGGIUNTA
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
        # ✅ MODIFICA QUI
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
    st.session_state.email_template = """<div style="font-family: Serif, Arial, sans-serif; font-size:14px; line-height:1.5; color:#000000;">

Gentile cliente,<br><br>

con la presente le formuliamo la nostra migliore offerta sui prodotti utilizzati dalla Vostra azienda ''ipotizzando'' un presunto scarico per la giornata in oggetto.<br><br>

<b>Gasolio per autotrazione = {prezzo}/litro + Iva</b><br><br>

Per via delle attuali fluttuazioni di mercato i prezzi in elenco avranno una validità giornaliera.<br><br>

Le consegne dei prodotti avverranno entro il giorno dopo alla data di effettuazione dell'ordine.<br><br>

<b>ATTENZIONE!!!</b> GLI ORDINI DOVRANNO PERVENIRE ENTRO LE ORE 14:00 RISPONDENDO ALLA PRESENTE OPPURE CHIAMANDO AL NUMERO DI TELEFONO<br><br>

Enrico Procaccini - 3892159094
</div>
"""

if "wa_template" not in st.session_state:
    st.session_state.wa_template = """Gentile cliente {nome},

Data: {data}

Gasolio per autotrazione = {prezzo}/litro + Iva
"""

df = st.session_state.clienti

# =========================
# DASHBOARD
# =========================
if st.session_state.page == "dashboard":

    prezzo_base = st.number_input("Prezzo base", value=float(st.session_state.prezzo_base), step=0.001)

    for _, c in df.iterrows():

        prezzo = calc_price(prezzo_base, c["Margine"], c["Trasporto"])

        import urllib.parse

        tel = str(c["Telefono"]).replace("+", "").replace(" ", "")

        # ✅ MODIFICA QUI
        msg = st.session_state.wa_template \
            .replace("{prezzo}", format_euro(prezzo)) \
            .replace("{nome}", c["Nome"]) \
            .replace("{data}", data_operativa())

        wa = f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}"

        st.link_button("WhatsApp", wa)
