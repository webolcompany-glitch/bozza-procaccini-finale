import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from supabase import create_client

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="FuelCRM",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# GLOBAL CSS (UI SaaS STYLE)
# =========================
st.markdown("""
<style>

/* ========== MAIN ========== */
.block-container {
    padding: 1.5rem 2rem;
    background-color: #f6f7fb;
}

/* ========== SIDEBAR ========== */
[data-testid="stSidebar"] {
    background-color: #f59e0b;
}

[data-testid="stSidebar"] * {
    color: white;
    font-weight: 500;
}

/* logo/title */
.sidebar-title {
    font-size: 22px;
    font-weight: 800;
    margin-bottom: 20px;
}

/* ========== TOP HEADER ========== */
.header-title {
    font-size: 28px;
    font-weight: 800;
}

.subtext {
    color: #6b7280;
    margin-top: -8px;
    margin-bottom: 20px;
}

/* ========== KPI CARDS ========== */
.kpi-card {
    background: white;
    border-radius: 16px;
    padding: 18px 18px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.06);
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.kpi-title {
    font-size: 14px;
    color: #6b7280;
}

.kpi-value {
    font-size: 22px;
    font-weight: 800;
}

/* icon box */
.icon-box {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
}

/* ========== CLIENT BOX ========== */
.empty-box {
    background: white;
    border-radius: 16px;
    padding: 60px;
    text-align: center;
    box-shadow: 0 6px 20px rgba(0,0,0,0.06);
}

.client-card{
    background:white;
    padding:18px;
    border-radius:16px;
    box-shadow:0 6px 20px rgba(0,0,0,.05);
    margin-bottom:12px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# 🏢 AZIENDA
# =========================
azienda = st.query_params.get("azienda", "demo")
if isinstance(azienda, list):
    azienda = azienda[0]

FILE = f"clienti_{azienda}.csv"

# =========================
# 📧 EMAIL
# =========================
EMAIL_MITTENTE = st.secrets["EMAIL_MITTENTE"]
PASSWORD_APP = st.secrets["PASSWORD_APP"]

def invia_email(destinatari, prezzo, template, nome=""):
    try:
        data = datetime.now().strftime("%d/%m/%Y")

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
Enrico Procaccini - 3892159094 &nbsp;&nbsp;&nbsp;
<br><br><br>
<div style="font-family: Verdana, sans-serif; font-size:11px; line-height:1.4; color:#2F5496; margin-top:10px;">
<p><b>Long Life Consulting</b></p>
<p>Enrico Procaccini<br><br>Corso Italia, 46 – 80011 Acerra (NA)</p>
<p>Mob: 3892159094<br><br>Info: eprocaccini@longlifecons.com</p>
<br><br><br>
<p>Wholeses Fuels - Fuel Cards - Coupons<br><br><b>Agente di</b><br><br>
<img src="https://longlifecons.com/wp-content/Prodotti/Tamoil.svg.png" width="90"></p>
<p>Via Andrea Costa, 17 20131 Milano, ITALIA</p>
<p>Tel: 800 11 33 30</p>
</div>
<br>
<div style="font-family: Verdana, Arial, sans-serif; font-size:11px; color:#000000; line-height:1.4;">
<i>La presente comunicazione, con le informazioni in essa contenute...</i>
</div>
</div>
"""

if "wa_template" not in st.session_state:
    st.session_state.wa_template = """Gentile cliente {nome},
con la presente le formuliamo la nostra migliore offerta...
Data: {data}
Gasolio per autotrazione = {prezzo}/litro + Iva
"""

df = st.session_state.clienti

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown('<div class="sidebar-title">⛽ FuelCRM</div>', unsafe_allow_html=True)
    st.markdown(f"🏢 Azienda: **{azienda.upper()}**")
    st.write("---")

    if st.button("📊 Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"

    if st.button("👤 Clienti", use_container_width=True):
        st.session_state.page = "clienti"

    if st.button("➕ Nuovo Cliente", use_container_width=True):
        st.session_state.page = "cliente"

# =========================
# CARD COMPONENT
# =========================
def card(title, value, icon, color):
    return f"""
    <div class="kpi-card">
        <div>
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
        </div>
        <div class="icon-box" style="background:{color};">
            {icon}
        </div>
    </div>
    """

# =========================================================
# 📊 DASHBOARD
# =========================================================
if st.session_state.page == "dashboard":

    st.markdown('<div class="header-title">Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtext">Gestione prezzi e invio offerte</div>', unsafe_allow_html=True)

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

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(card("Prezzo Base", f"€ {format_euro(prezzo_base)}", "⛽", "#dbeafe"), unsafe_allow_html=True)
    with c2:
        st.markdown(card("Clienti", clienti_count, "👤", "#e0e7ff"), unsafe_allow_html=True)
    with c3:
        st.markdown(card("Margine Medio", f"€ {format_euro(media_margine)}", "📈", "#ffedd5"), unsafe_allow_html=True)
    with c4:
        st.markdown(card("Prezzo Medio", f"€ {format_euro(prezzo_medio)}", "💰", "#dcfce7"), unsafe_allow_html=True)

    st.write("---")
    st.markdown("### ✉️ Messaggio Email")
    
    template = st.text_area(
        "Modifica il messaggio",
        value=st.session_state.email_template,
        height=300
    )
    st.session_state.email_template = template

    if st.button("📧 Invia email a tutti", type="primary"):
        count = 0
        for _, c in df.iterrows():
            if c["Email"] and pd.notna(c["Email"]):
                prezzo = calc_price(prezzo_base, c["Margine"], c["Trasporto"])
                invia_email(c["Email"], prezzo, template, c["Nome"])
                st.session_state.clienti.loc[
                    st.session_state.clienti["ID"] == c["ID"],
                    "UltimoPrezzo"
                ] = prezzo
                count += 1

        save_data(st.session_state.clienti)
        st.success(f"Email inviate con successo a {count} clienti!")

    st.write("---")
    st.markdown("### 👤 Clienti")

    search_dash = st.text_input("🔍 Cerca rapida", key="search_dashboard")
    df_view = filtra_clienti(df, search_dash)

    if df_view.empty:
        st.markdown("""
        <div class="empty-box">
            <div style="font-size:40px;">⛽</div>
            <h3>Nessun cliente trovato</h3>
            <p style="color:#6b7280;">Aggiungi il primo cliente per iniziare a gestire le offerte.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for _, c in df_view.iterrows():
            prezzo = calc_price(prezzo_base, c["Margine"], c["Trasporto"])
            ultimo = c["UltimoPrezzo"]
            ultimo_txt = "Nessun invio" if pd.isna(ultimo) else format_euro(ultimo) + " €/L"

            st.markdown(f"""
            ### 👤 {c['Nome']}
            📄 P.IVA: {c['PIVA']}  
            💰 Oggi: {format_euro(prezzo)} €/L  
            📌 Ultimo: **{ultimo_txt}**
            """)

            col1, col2, col3 = st.columns(3)

            with col1:
                import urllib.parse
                tel = str(c["Telefono"]).replace("+", "").replace(" ", "")
                data = datetime.now().strftime("%d/%m/%Y")
                msg = st.session_state.wa_template.replace("{prezzo}", format_euro(prezzo)).replace("{nome}", c["Nome"]).replace("{data}", data)
                msg_encoded = urllib.parse.quote(msg)
                wa = f"https://wa.me/{tel}?text={msg_encoded}"
                st.link_button("📲 WhatsApp", wa)

            with col2:
                if c["Email"] and pd.notna(c["Email"]):
                    if st.button("📧 Email", key=f"mail_{c['ID']}"):
                        prezzo_send = calc_price(prezzo_base, c["Margine"], c["Trasporto"])
                        invia_email(c["Email"], prezzo_send, template, c["Nome"])
                        st.session_state.clienti.loc[st.session_state.clienti["ID"] == c["ID"], "UltimoPrezzo"] = prezzo_send
                        save_data(st.session_state.clienti)
                        st.success("Email inviata")

            with col3:
                if st.button("🗑️ Elimina", key=f"del_{c['ID']}"):
                    st.session_state.clienti = df[df["ID"] != c["ID"]]
                    save_data(st.session_state.clienti)
                    st.rerun()

            st.write("---")

# =========================================================
# 👤 CLIENTI PAGE
# =========================================================
elif st.session_state.page == "clienti":

    st.markdown('<div class="header-title">👤 Gestione Clienti</div>', unsafe_allow_html=True)

    search = st.text_input("🔍 Cerca cliente per Nome, P.IVA o Telefono")
    df_view = filtra_clienti(df, search)

    if df_view.empty:
         st.markdown("""
        <div class="empty-box">
            <div style="font-size:40px;">👥</div>
            <h3>Lista vuota</h3>
            <p style="color:#6b7280;">Non ci sono clienti che corrispondono alla ricerca.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for _, c in df_view.iterrows():
            ultimo_txt = "Nessun invio" if pd.isna(c["UltimoPrezzo"]) else format_euro(c["UltimoPrezzo"]) + " €/L"
            prezzo = calc_price(st.session_state.prezzo_base, c["Margine"], c["Trasporto"])

            st.markdown(f"""
            <div class="client-card">
            <h4 style="margin-top:0;">👤 {c['Nome']}</h4>
            📄 P.IVA: {c['PIVA']}<br>
            📞 {c['Telefono']}<br>
            💰 Prezzo Oggi: <b>{format_euro(prezzo)} €/L</b><br>
            📌 Ultimo Invio: <span style="color:#6b7280;">{ultimo_txt}</span>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)

            with col1:
                if st.button("✏️ Modifica", key=f"edit_{c['ID']}"):
                    st.session_state.edit_id = c["ID"]
                    st.session_state.page = "cliente"
                    st.rerun() 

            with col2:
                if st.button("🗑️ Elimina", key=f"del_list_{c['ID']}"):
                    st.session_state.clienti = df[df["ID"] != c["ID"]]
                    save_data(st.session_state.clienti)
                    st.rerun()

# =========================================================
# ➕ CLIENTE PAGE
# =========================================================
elif st.session_state.page == "cliente":

    editing = st.session_state.edit_id is not None
    titolo_pagina = "Modifica Cliente" if editing else "Nuovo Cliente"
    
    st.markdown(f'<div class="header-title">{"✏️" if editing else "➕"} {titolo_pagina}</div>', unsafe_allow_html=True)

    if editing:
        c = df[df["ID"] == st.session_state.edit_id].iloc[0]
    else:
        c = {"Nome":"","PIVA":"","Telefono":"","Email":"","Margine":0.0,"Trasporto":0.0}

    with st.container():
        st.markdown('<div class="client-card">', unsafe_allow_html=True)
        nome = st.text_input("Nome Ragione Sociale", value=c["Nome"])
        piva = st.text_input("Partita IVA", value=c["PIVA"])
        tel = st.text_input("Telefono", value=c["Telefono"])
        email = st.text_input("Email", value=c["Email"], placeholder="es: principale@mail.com, cc@mail.com")
        st.caption("ℹ️ Scrivi prima l'email principale. Le successive separate da virgola saranno usate come CC (conoscenza).")
        
        col_m, col_t = st.columns(2)
        with col_m:
            margine = st.number_input("Margine (€/L)", value=float(c["Margine"]), step=0.001, format="%.3f")
        with col_t:
            trasporto = st.number_input("Trasporto (€/L)", value=float(c["Trasporto"]), step=0.001, format="%.3f")
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("💾 Salva Cliente", type="primary"):

        if editing:
            idx = st.session_state.clienti["ID"] == st.session_state.edit_id
            st.session_state.clienti.loc[idx, "Nome"] = nome
            st.session_state.clienti.loc[idx, "PIVA"] = piva
            st.session_state.clienti.loc[idx, "Telefono"] = tel
            st.session_state.clienti.loc[idx, "Email"] = email
            st.session_state.clienti.loc[idx, "Margine"] = margine
            st.session_state.clienti.loc[idx, "Trasporto"] = trasporto
            st.session_state.edit_id = None
        else:
            new_id = 1 if df.empty else int(df["ID"].max()) + 1
            new = pd.DataFrame([{
                "ID": new_id, "Nome": nome, "PIVA": piva, 
                "Telefono": tel, "Email": email, "Margine": margine, 
                "Trasporto": trasporto, "UltimoPrezzo": None
            }])
            st.session_state.clienti = pd.concat([df, new], ignore_index=True)

        save_data(st.session_state.clienti)
        st.success("Cliente salvato con successo!")
        st.session_state.page = "clienti"
        st.rerun()
