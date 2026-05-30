import streamlit as st
import pandas as pd
import smtplib
import urllib.parse

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from supabase import create_client


# =========================
# 📅 FESTIVI
# =========================

def pasqua(anno):
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

    return {
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
        pasquetta,
    }


def prossimo_giorno_lavorativo(data=None):
    if data is None:
        data = datetime.now()

    giorno = data + timedelta(days=1)

    while True:
        festivi = festivi_italiani(giorno.year)

        if (
            giorno.weekday() < 5
            and giorno.replace(hour=0, minute=0, second=0, microsecond=0) not in festivi
        ):
            return giorno

        giorno += timedelta(days=1)


# =========================
# 🔗 SUPABASE
# =========================

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
# 📧 EMAIL
# =========================

EMAIL_MITTENTE = st.secrets["EMAIL_MITTENTE"]
PASSWORD_APP = st.secrets["PASSWORD_APP"]


def invia_email(destinatari, prezzo, template, nome=""):
    try:
        data_scarico = prossimo_giorno_lavorativo()

        giorni = ["Lunedì","Martedì","Mercoledì","Giovedì","Venerdì","Sabato","Domenica"]
        giorno_nome = giorni[data_scarico.weekday()]
        data = f"{giorno_nome} {data_scarico.strftime('%d/%m/%Y')}"

        testo = (
            template
            .replace("{prezzo}", f"{prezzo:.3f}")
            .replace("{nome}", nome)
            .replace("{data}", data)
        )

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
# 🔧 UTILS
# =========================

def format_euro(x):
    if x is None or pd.isna(x):
        return "0,000"
    return f"{float(x):.3f}".replace(".", ",")


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
            "ID","Nome","PIVA","Telefono","Email",
            "Margine","Trasporto","UltimoPrezzo",
            "Prodotto"
        ])

    df = pd.DataFrame(data)

    return df.rename(columns={
        "id":"ID",
        "nome":"Nome",
        "piva":"PIVA",
        "telefono":"Telefono",
        "email":"Email",
        "margine":"Margine",
        "trasporto":"Trasporto",
        "ultimo_prezzo":"UltimoPrezzo"
    })


def save_data(df):
    records = df.rename(columns={
        "ID":"id",
        "Nome":"nome",
        "PIVA":"piva",
        "Telefono":"telefono",
        "Email":"email",
        "Margine":"margine",
        "Trasporto":"trasporto",
        "UltimoPrezzo":"ultimo_prezzo",
        "Prodotto":"prodotto"
    }).to_dict("records")

    if records:
        supabase.table("clienti").upsert(records).execute()


# =========================
# 🚀 INIT
# =========================

if "clienti" not in st.session_state:
    st.session_state.clienti = load_data()

if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

if "prezzi_base" not in st.session_state:
    st.session_state.prezzi_base = {
        "Auto": 1.000,
        "Riscaldamento": 1.000,
        "Agricolo": 1.000,
        "Benzina": 1.000
    }

df = st.session_state.clienti


# =========================
# 🧭 NAV
# =========================

c1, c2, c3 = st.columns(3)

with c1:
    if st.button("📊 Dashboard"):
        st.session_state.page = "dashboard"

with c2:
    if st.button("👤 Clienti"):
        st.session_state.page = "clienti"

with c3:
    if st.button("➕ Nuovo"):
        st.session_state.page = "cliente"

st.divider()


# =========================
# 📊 DASHBOARD
# =========================

if st.session_state.page == "dashboard":

    st.markdown("## ⛽ Prezzi base per prodotto")

    for k in st.session_state.prezzi_base:
        st.session_state.prezzi_base[k] = st.number_input(
            k,
            value=float(st.session_state.prezzi_base[k]),
            step=0.001,
            format="%.3f"
        )

    st.divider()

    search = st.text_input("🔍 Cerca cliente")
    df_view = filtra_clienti(df, search)

    # =========================
    # 📧 INVIA EMAIL A TUTTI
    # =========================
    if st.button("📧 Invia email a tutti"):
        count = 0

        for _, c in df.iterrows():

            if c["Email"] and pd.notna(c["Email"]):

                prodotti = c.get("Prodotto", ["Auto"])

                if isinstance(prodotti, str):
                    prodotti = [prodotti]

                base = st.session_state.prezzi_base.get(prodotti[0], 1.000)

                prezzo = calc_price(base, c["Margine"], c["Trasporto"])

                invia_email(
                    c["Email"],
                    prezzo,
                    st.session_state.email_template,
                    c["Nome"]
                )

                st.session_state.clienti.loc[
                    st.session_state.clienti["ID"] == c["ID"],
                    "UltimoPrezzo"
                ] = prezzo

                count += 1

        save_data(st.session_state.clienti)
        st.success(f"Email inviate: {count}")

    st.divider()

    st.markdown("### 👤 Clienti")

    for _, c in df_view.iterrows():

        prodotti = c.get("Prodotto", ["Auto"])
        if isinstance(prodotti, str):
            prodotti = [prodotti]

        base = st.session_state.prezzi_base.get(prodotti[0], 1.000)

        prezzo = calc_price(base, c["Margine"], c["Trasporto"])

        st.write(f"👤 {c['Nome']} - {prodotti} - {format_euro(prezzo)} €/L")

        tel = str(c["Telefono"]).replace("+", "").replace(" ", "")

        msg = f"{c['Nome']} - {prezzo} €/L"

        wa = f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}"

        st.link_button("WhatsApp", wa)

        if st.button("🗑️ Elimina", key=f"del_{c['ID']}"):
            st.session_state.clienti = st.session_state.clienti[
                st.session_state.clienti["ID"] != c["ID"]
            ]
            save_data(st.session_state.clienti)
            st.rerun()


# =========================
# 👤 CLIENTE
# =========================

elif st.session_state.page == "cliente":

    editing = st.session_state.edit_id is not None

    if editing:
        c = df[df["ID"] == st.session_state.edit_id].iloc[0]
    else:
        c = {
            "Nome":"",
            "PIVA":"",
            "Telefono":"",
            "Email":"",
            "Margine":0.0,
            "Trasporto":0.0,
            "Prodotto":["Auto"]
        }

    nome = st.text_input("Nome", value=c["Nome"])
    piva = st.text_input("PIVA", value=c["PIVA"])
    tel = st.text_input("Telefono", value=c["Telefono"])
    email = st.text_input("Email", value=c["Email"])

    margine = st.number_input("Margine", value=float(c["Margine"]), step=0.001)
    trasporto = st.number_input("Trasporto", value=float(c["Trasporto"]), step=0.001)

    prodotti = st.multiselect(
        "Prodotti associati al cliente",
        ["Auto","Riscaldamento","Agricolo","Benzina"],
        default=c.get("Prodotto", ["Auto"])
    )

    if st.button("💾 Salva"):

        if editing:
            idx = st.session_state.clienti["ID"] == st.session_state.edit_id

            st.session_state.clienti.loc[idx, "Nome"] = nome
            st.session_state.clienti.loc[idx, "PIVA"] = piva
            st.session_state.clienti.loc[idx, "Telefono"] = tel
            st.session_state.clienti.loc[idx, "Email"] = email
            st.session_state.clienti.loc[idx, "Margine"] = margine
            st.session_state.clienti.loc[idx, "Trasporto"] = trasporto
            st.session_state.clienti.loc[idx, "Prodotto"] = prodotti

        else:
            new_id = 1 if df.empty else int(df["ID"].max()) + 1

            new = pd.DataFrame([{
                "ID": new_id,
                "Nome": nome,
                "PIVA": piva,
                "Telefono": tel,
                "Email": email,
                "Margine": margine,
                "Trasporto": trasporto,
                "UltimoPrezzo": None,
                "Prodotto": prodotti
            }])

            st.session_state.clienti = pd.concat([df, new], ignore_index=True)

        save_data(st.session_state.clienti)
        st.session_state.page = "clienti"
        st.rerun()
