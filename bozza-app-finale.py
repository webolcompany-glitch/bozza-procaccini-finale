import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from supabase import create_client

# =========================
# IMPOSTAZIONI GLOBALI
# =========================
TIPI_CARBURANTE = ["Gasolio Autotrazione", "Gasolio Riscaldamento", "Gasolio Agricolo", "Benzina"]

st.set_page_config(
    page_title="FuelCRM",
    layout="wide",
    initial_sidebar_state="expanded"
)

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# =========================
# GLOBAL CSS (UI SaaS STYLE)
# =========================
st.markdown("""
<style>
/* ========== MAIN ========== */
.block-container { padding: 1.5rem 2rem; background-color: #f6f7fb; }
/* ========== SIDEBAR ========== */
[data-testid="stSidebar"] { background-color: #0f172a; }
[data-testid="stSidebar"] * { color: white; font-weight: 500; }
.sidebar-title { font-size: 22px; font-weight: 800; margin-bottom: 20px; }
[data-testid="stSidebar"] .stButton > button { background-color: #1e293b; color: #ffffff; border: 1px solid #334155; border-radius: 10px; transition: all 0.3s ease; }
[data-testid="stSidebar"] .stButton > button:hover { background-color: #f59e0b; color: #000000 !important; border-color: #f59e0b; }
/* ========== TOP HEADER ========== */
.header-title { font-size: 28px; font-weight: 800; }
.subtext { color: #6b7280; margin-top: -8px; margin-bottom: 20px; }
/* ========== KPI CARDS ========== */
.kpi-card { background: white; border-radius: 16px; padding: 18px 18px; box-shadow: 0 6px 20px rgba(0,0,0,0.06); display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.kpi-title { font-size: 14px; color: #6b7280; }
.kpi-value { font-size: 22px; font-weight: 800; }
.icon-box { width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
/* ========== CLIENT BOX ========== */
.empty-box { background: white; border-radius: 16px; padding: 60px; text-align: center; box-shadow: 0 6px 20px rgba(0,0,0,0.06); }
.client-card { background: white; padding: 18px; border-radius: 16px; box-shadow: 0 6px 20px rgba(0,0,0,.05); margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

# =========================
# 🏢 AZIENDA
# =========================
azienda = st.query_params.get("azienda", "demo")
if isinstance(azienda, list):
    azienda = azienda[0]

# =========================
# 📧 EMAIL & UTILS
# =========================
EMAIL_MITTENTE = st.secrets["EMAIL_MITTENTE"]
PASSWORD_APP = st.secrets["PASSWORD_APP"]

def invia_email(destinatari, elenco_offerte_html, template, nome=""):
    try:
        data = datetime.now().strftime("%d/%m/%Y")
        testo = template \
            .replace("{elenco_offerte}", elenco_offerte_html) \
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
        server.sendmail(EMAIL_MITTENTE, lista_email, msg.as_string())
        server.quit()
    except Exception as e:
        st.error(f"Errore email: {e}")

def format_euro(x):
    if x is None or pd.isna(x): return "0,000"
    return f"{round(float(x), 3):.3f}".replace(".", ",")

def calc_price(base, margine, trasporto):
    return round(float(base) + float(margine) + float(trasporto), 3)

def genera_testo_offerte(cliente, prezzi_globali, formato="html"):
    prodotti_str = str(cliente.get("Prodotti", ""))
    prodotti = [p.strip() for p in prodotti_str.split(",")] if prodotti_str and prodotti_str.lower() != "nan" else ["Gasolio Autotrazione"]
    
    righe = []
    for p in prodotti:
        p_base = prezzi_globali.get(p, 0.0) 
        p_fin = calc_price(p_base, cliente.get("Margine", 0), cliente.get("Trasporto", 0))
        
        if formato == "html":
            righe.append(f"<b>{p}</b>: {format_euro(p_fin)} €/L + Iva")
        else: # WhatsApp
            righe.append(f"{p}: {format_euro(p_fin)} €/L + Iva")
            
    separator = "<br><br>" if formato == "html" else "\n\n"
    return separator.join(righe)

def filtra_clienti(df, search, base_filter="Tutte"):
    res = df
    if base_filter != "Tutte":
        if "Base" in res.columns:
            res = res[res["Base"] == base_filter]
    
    if search:
        res = res[
            res["Nome"].astype(str).str.contains(search, case=False, na=False) |
            res["PIVA"].astype(str).str.contains(search, case=False, na=False) |
            res["Telefono"].astype(str).str.contains(search, case=False, na=False)
        ]
    return res

# =========================
# 💾 DATA
# =========================
def load_data():
    res = supabase.table("clienti").select("*").execute()
    data = res.data

    if not data:
        return pd.DataFrame(columns=[
            "ID","Nome","PIVA","Telefono","Email",
            "Margine","Trasporto","UltimoPrezzo","Base","Prodotti"
        ])

    df = pd.DataFrame(data)
    df = df.rename(columns={
        "id":"ID", "nome":"Nome", "piva":"PIVA", "telefono":"Telefono",
        "email":"Email", "margine":"Margine", "trasporto":"Trasporto",
        "ultimo_prezzo":"UltimoPrezzo", "base":"Base", "prodotti":"Prodotti"
    })
    
    if "Base" not in df.columns: df["Base"] = "Nessuna"
    if "Prodotti" not in df.columns: df["Prodotti"] = "Gasolio Autotrazione"
    
    df["Base"] = df["Base"].fillna("Nessuna")
    df["Prodotti"] = df["Prodotti"].fillna("Gasolio Autotrazione")
    
    return df

def save_data(df):
    # 🛡️ FIX: Trasforma i valori NaN in None per non far bloccare Supabase
    df_clean = df.where(pd.notnull(df), None)
    
    records = df_clean.rename(columns={
        "ID":"id", "Nome":"nome", "PIVA":"piva", "Telefono":"telefono",
        "Email":"email", "Margine":"margine", "Trasporto":"trasporto",
        "UltimoPrezzo":"ultimo_prezzo", "Base":"base", "Prodotti":"prodotti"
    }).to_dict(orient="records")

    if records:
        supabase.table("clienti").upsert(records).execute()

def delete_client(client_id):
    try:
        supabase.table("clienti").delete().eq("id", client_id).execute()
    except Exception as e:
        st.error(f"Errore durante l'eliminazione nel database: {e}")

# =========================
# INIT SESSION STATE
# =========================
if "clienti" not in st.session_state: 
    st.session_state.clienti = load_data()

if "Base" not in st.session_state.clienti.columns:
    st.session_state.clienti["Base"] = "Nessuna"
if "Prodotti" not in st.session_state.clienti.columns:
    st.session_state.clienti["Prodotti"] = "Gasolio Autotrazione"

if "page" not in st.session_state: st.session_state.page = "dashboard"
if "edit_id" not in st.session_state: st.session_state.edit_id = None
if "show_success" not in st.session_state: st.session_state.show_success = False

if "prezzi_base" not in st.session_state:
    st.session_state.prezzi_base = {p: 1.000 for p in TIPI_CARBURANTE}

if "email_template" not in st.session_state:
    st.session_state.email_template = """<div style="font-family: Serif, Arial, sans-serif; font-size:14px; line-height:1.5; color:#000000;">
Gentile cliente,<br><br>
con la presente le formuliamo la nostra migliore offerta sui prodotti utilizzati dalla Vostra azienda ''ipotizzando'' un presunto scarico per la giornata in oggetto:<br><br>
{elenco_offerte}<br><br>
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
con la presente le formuliamo la nostra migliore offerta:
Data: {data}

{elenco_offerte}

Cordiali saluti,
Enrico Procaccini - 3892159094
"""

df = st.session_state.clienti

basi_esistenti = ["Tutte"]
if not df.empty and "Base" in df.columns:
    basi_uniche = df["Base"].dropna().unique().tolist()
    basi_esistenti.extend([b for b in basi_uniche if b and b != "Tutte"])

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown('<div class="sidebar-title">⛽ FuelCRM</div>', unsafe_allow_html=True)
    st.markdown(f"🏢 Azienda: **{azienda.upper()}**")
    st.write("---")
    if st.button("📊 Dashboard", use_container_width=True): st.session_state.page = "dashboard"
    if st.button("👤 Clienti", use_container_width=True): st.session_state.page = "clienti"
    if st.button("➕ Nuovo Cliente", use_container_width=True): st.session_state.page = "cliente"

# =========================
# CARD COMPONENT
# =========================
def card(title, value, icon, color):
    return f"""
    <div class="kpi-card">
        <div><div class="kpi-title">{title}</div><div class="kpi-value">{value}</div></div>
        <div class="icon-box" style="background:{color};">{icon}</div>
    </div>
    """

# =========================================================
# 📊 DASHBOARD
# =========================================================
if st.session_state.page == "dashboard":

    st.markdown('<div class="header-title">Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtext">Gestione quotazioni, filtri Base e invio offerte</div>', unsafe_allow_html=True)

    if st.session_state.get("show_success"):
        st.success(st.session_state.show_success)
        st.session_state.show_success = False 

    st.markdown("### ⛽ Prezzi Base Odierni (€/L)")
    cols = st.columns(len(TIPI_CARBURANTE))
    for i, prodotto in enumerate(TIPI_CARBURANTE):
        with cols[i]:
            nuovo_prezzo = st.number_input(
                prodotto,
                value=float(st.session_state.prezzi_base.get(prodotto, 1.000)),
                step=0.001, format="%.3f"
            )
            st.session_state.prezzi_base[prodotto] = nuovo_prezzo

    clienti_count = len(df)
    media_margine = round(df["Margine"].mean(), 3) if not df.empty else 0
    c1, c2 = st.columns(2)
    with c1: st.markdown(card("Clienti Totali", clienti_count, "👤", "#e0e7ff"), unsafe_allow_html=True)
    with c2: st.markdown(card("Margine Medio", f"€ {format_euro(media_margine)}", "📈", "#ffedd5"), unsafe_allow_html=True)

    # ==========================================
    # 🧩 MODALS PER ANTEPRIMA
    # ==========================================
    @st.dialog("👁️ Anteprima e Conferma Invio Massivo")
    def modal_anteprima_tutti(df_clienti, dict_prezzi, template_msg):
        st.write(f"Stai per inviare l'offerta a tutti i clienti attualmente filtrati ({len(df_clienti)} clienti).")
        st.write("Ecco l'anteprima basata sul primo cliente utile:")
        
        preview_c = None
        for _, cl in df_clienti.iterrows():
            if pd.notna(cl["Email"]) and str(cl["Email"]).strip() != "":
                preview_c = cl
                break
                
        if preview_c is not None:
            html_offerte = genera_testo_offerte(preview_c, dict_prezzi, formato="html")
            data_es = datetime.now().strftime("%d/%m/%Y")
            testo_es = template_msg.replace("{elenco_offerte}", html_offerte).replace("{nome}", preview_c["Nome"]).replace("{data}", data_es)
            
            st.markdown(f'<div style="background:white; padding:20px; border-radius:10px; border:1px solid #e2e8f0; max-height: 350px; overflow-y: auto; font-size: 14px;">{testo_es}</div>', unsafe_allow_html=True)
            st.write("---")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("❌ Annulla", use_container_width=True): st.rerun() 
            with col_b:
                if st.button("🚀 Conferma e Invia", type="primary", use_container_width=True):
                    count = 0
                    for _, c_all in df_clienti.iterrows():
                        if pd.notna(c_all["Email"]) and str(c_all["Email"]).strip() != "":
                            html_off = genera_testo_offerte(c_all, dict_prezzi, formato="html")
                            invia_email(c_all["Email"], html_off, template_msg, c_all["Nome"])
                            
                            # 🛡️ FIX: Salviamo -1.0 come indicatore numerico al posto della stringa
                            st.session_state.clienti.loc[st.session_state.clienti["ID"] == c_all["ID"], "UltimoPrezzo"] = -1.0
                            count += 1
                    save_data(st.session_state.clienti)
                    st.session_state.show_success = f"✅ Email inviate con successo a {count} clienti!"
                    st.rerun()
        else:
            st.warning("Nessun cliente valido nella lista attuale.")

    @st.dialog("👁️ Anteprima Email - Singolo Cliente")
    def modal_anteprima_singola(c_singolo, dict_prezzi, template_msg):
        st.write(f"Invia a: **{c_singolo.get('Nome', 'Sconosciuto')}** ({c_singolo.get('Email', '')})")
        
        html_offerte = genera_testo_offerte(c_singolo, dict_prezzi, formato="html")
        data_es = datetime.now().strftime("%d/%m/%Y")
        testo_es = template_msg.replace("{elenco_offerte}", html_offerte).replace("{nome}", c_singolo.get("Nome", "")).replace("{data}", data_es)
        
        st.markdown(f'<div style="background:white; padding:20px; border-radius:10px; border:1px solid #e2e8f0; max-height: 350px; overflow-y: auto; font-size: 14px;">{testo_es}</div>', unsafe_allow_html=True)
        st.write("---")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("❌ Annulla", use_container_width=True): st.rerun()
        with col_b:
            if st.button("🚀 Conferma e Invia", type="primary", use_container_width=True):
                invia_email(c_singolo["Email"], html_offerte, template_msg, c_singolo["Nome"])
                
                # 🛡️ FIX: Salviamo -1.0 come indicatore numerico al posto della stringa
                st.session_state.clienti.loc[st.session_state.clienti["ID"] == c_singolo["ID"], "UltimoPrezzo"] = -1.0
                save_data(st.session_state.clienti)
                st.session_state.show_success = f"✅ Email inviata con successo a {c_singolo['Nome']}!"
                st.rerun()

    # ==========================================
    # SEZIONE EMAIL ED ESPANSORE
    # ==========================================
    st.write("---")
    with st.expander("✉️ Mostra / Modifica Template Email"):
        st.info("⚠️ ATTENZIONE: Usa la variabile {elenco_offerte} per far inserire al sistema in automatico tutti i prodotti del cliente completi di prezzo.")
        st.session_state.email_template = st.text_area("Modifica il messaggio", value=st.session_state.email_template, height=300)

    # ==========================================
    # LISTA CLIENTI RAPIDA E FILTRI
    # ==========================================
    st.write("---")
    st.markdown("### 👤 Azioni Rapide")

    col_filtro1, col_filtro2 = st.columns(2)
    with col_filtro1: base_sel = st.selectbox("📍 Filtra per Base", basi_esistenti, key="dash_base")
    with col_filtro2: search_dash = st.text_input("🔍 Cerca rapida", key="search_dashboard")
    
    df_view = filtra_clienti(df, search_dash, base_sel)

    if st.button(f"📧 Invia email ai {len(df_view)} clienti visualizzati", type="primary"):
        modal_anteprima_tutti(df_view, st.session_state.prezzi_base, st.session_state.email_template)

    st.write("")
    
    if df_view.empty:
        st.markdown('<div class="empty-box"><div style="font-size:40px;">⛽</div><h3>Nessun cliente trovato</h3></div>', unsafe_allow_html=True)
    else:
        for _, c in df_view.iterrows():
            # 🛡️ FIX: Traduce il numero -1.0 nella stringa voluta per l'UI
            ultimo_val = c.get("UltimoPrezzo")
            if pd.isna(ultimo_val) or ultimo_val is None:
                ultimo_txt = "Nessun invio"
            elif ultimo_val == -1.0:
                ultimo_txt = "Offerta Inviata"
            else:
                ultimo_txt = f"{format_euro(ultimo_val)} €/L"

            prod_lista = c.get("Prodotti", "")

            st.markdown(f"""
            <div class="client-card" style="padding:15px; margin-bottom: 0px;">
                <h4 style="margin:0;">👤 {c.get('Nome', 'Sconosciuto')} <span style="font-size:14px; font-weight:normal; color:#6b7280;">(Base: {c.get('Base', 'Nessuna')})</span></h4>
                <div style="font-size:14px; margin-top:5px;">
                    🛍️ Prodotti: <b>{prod_lista}</b><br>
                    📌 Ultimo Invio: {ultimo_txt}
                </div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                import urllib.parse
                tel = str(c.get("Telefono", "")).replace("+", "").replace(" ", "")
                data = datetime.now().strftime("%d/%m/%Y")
                wa_offerte = genera_testo_offerte(c, st.session_state.prezzi_base, formato="testo")
                msg = st.session_state.wa_template.replace("{elenco_offerte}", wa_offerte).replace("{nome}", c.get("Nome", "")).replace("{data}", data)
                msg_encoded = urllib.parse.quote(msg)
                st.link_button("📲 Invia WhatsApp", f"https://wa.me/{tel}?text={msg_encoded}")

            with col2:
                if c.get("Email") and pd.notna(c.get("Email")):
                    if st.button("📧 Invia Email", key=f"mail_{c['ID']}"):
                        modal_anteprima_singola(c, st.session_state.prezzi_base, st.session_state.email_template)

            with col3:
                if st.button("🗑️ Elimina", key=f"del_{c['ID']}"):
                    delete_client(c["ID"])
                    st.session_state.clienti = df[df["ID"] != c["ID"]]
                    st.rerun()
            st.write("---")

# =========================================================
# 👤 CLIENTI PAGE
# =========================================================
elif st.session_state.page == "clienti":

    st.markdown('<div class="header-title">👤 Gestione Clienti</div>', unsafe_allow_html=True)

    col_filtro1, col_filtro2 = st.columns(2)
    with col_filtro1: base_sel = st.selectbox("📍 Filtra per Base", basi_esistenti, key="clienti_base")
    with col_filtro2: search = st.text_input("🔍 Cerca cliente (Nome, P.IVA, Tel)")
    
    df_view = filtra_clienti(df, search, base_sel)

    if df_view.empty:
         st.markdown('<div class="empty-box"><div style="font-size:40px;">👥</div><h3>Lista vuota</h3></div>', unsafe_allow_html=True)
    else:
        for _, c in df_view.iterrows():
            # 🛡️ FIX: Traduce il numero -1.0 nella stringa voluta per l'UI
            ultimo_val = c.get("UltimoPrezzo")
            if pd.isna(ultimo_val) or ultimo_val is None:
                ultimo_txt = "Nessun invio"
            elif ultimo_val == -1.0:
                ultimo_txt = "Offerta Inviata"
            else:
                ultimo_txt = f"{format_euro(ultimo_val)} €/L"

            st.markdown(f"""
            <div class="client-card">
            <h4 style="margin-top:0;">👤 {c.get('Nome', 'Sconosciuto')} <span style="font-size:14px; font-weight:normal; color:#6b7280;">(Base: {c.get('Base', 'Nessuna')})</span></h4>
            📄 P.IVA: {c.get('PIVA', '')}<br>
            📞 {c.get('Telefono', '')}<br>
            🛍️ Prodotti Richiesti: <b>{c.get('Prodotti', 'Nessun Prodotto')}</b><br>
            📌 Stato Offerte: <span style="color:#6b7280;">{ultimo_txt}</span>
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
                    delete_client(c["ID"])
                    st.session_state.clienti = df[df["ID"] != c["ID"]]
                    st.rerun()

# =========================================================
# ➕ CLIENTE PAGE (NUOVO / MODIFICA)
# =========================================================
elif st.session_state.page == "cliente":

    editing = st.session_state.edit_id is not None
    titolo_pagina = "Modifica Cliente" if editing else "Nuovo Cliente"
    
    st.markdown(f'<div class="header-title">{"✏️" if editing else "➕"} {titolo_pagina}</div>', unsafe_allow_html=True)

    if editing:
        c = df[df["ID"] == st.session_state.edit_id].iloc[0]
        prod_selezionati = [p.strip() for p in str(c.get("Prodotti", "")).split(",")] if pd.notna(c.get("Prodotti")) else ["Gasolio Autotrazione"]
        base_attuale = c.get("Base", "Nessuna")
    else:
        c = {"Nome":"","PIVA":"","Telefono":"","Email":"","Margine":0.0,"Trasporto":0.0}
        prod_selezionati = ["Gasolio Autotrazione"]
        base_attuale = "Nessuna"

    with st.container():
        st.markdown('<div class="client-card">', unsafe_allow_html=True)
        
        st.subheader("Dati Principali")
        nome = st.text_input("Nome Ragione Sociale", value=c.get("Nome", ""))
        piva = st.text_input("Partita IVA", value=c.get("PIVA", ""))
        tel = st.text_input("Telefono", value=c.get("Telefono", ""))
        email = st.text_input("Email", value=c.get("Email", ""), placeholder="es: principale@mail.com, cc@mail.com")
        
        st.write("---")
        st.subheader("Configurazione Commerciale")
        base = st.text_input("📍 Base di riferimento (es. Napoli, Roma, Taranto)", value=base_attuale)
        
        prodotti = st.multiselect(
            "🛍️ Prodotti Acquistati dal Cliente",
            options=TIPI_CARBURANTE,
            default=[p for p in prod_selezionati if p in TIPI_CARBURANTE]
        )
        
        col_m, col_t = st.columns(2)
        with col_m: margine = st.number_input("Margine (€/L)", value=float(c.get("Margine", 0.0)), step=0.001, format="%.3f")
        with col_t: trasporto = st.number_input("Trasporto (€/L)", value=float(c.get("Trasporto", 0.0)), step=0.001, format="%.3f")
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("💾 Salva Cliente", type="primary"):
        prodotti_str = ", ".join(prodotti)
        if not base.strip(): base = "Nessuna"

        if editing:
            idx = st.session_state.clienti["ID"] == st.session_state.edit_id
            st.session_state.clienti.loc[idx, "Nome"] = nome
            st.session_state.clienti.loc[idx, "PIVA"] = piva
            st.session_state.clienti.loc[idx, "Telefono"] = tel
            st.session_state.clienti.loc[idx, "Email"] = email
            st.session_state.clienti.loc[idx, "Margine"] = margine
            st.session_state.clienti.loc[idx, "Trasporto"] = trasporto
            st.session_state.clienti.loc[idx, "Prodotti"] = prodotti_str
            st.session_state.clienti.loc[idx, "Base"] = base
            st.session_state.edit_id = None
        else:
            new_id = 1 if df.empty else int(df["ID"].max()) + 1
            new = pd.DataFrame([{
                "ID": new_id, "Nome": nome, "PIVA": piva, "Telefono": tel, "Email": email,
                "Margine": margine, "Trasporto": trasporto, "UltimoPrezzo": None,
                "Prodotti": prodotti_str, "Base": base
            }])
            st.session_state.clienti = pd.concat([df, new], ignore_index=True)

        save_data(st.session_state.clienti)
        st.success("Cliente salvato con successo!")
        st.session_state.page = "clienti"
        st.rerun()
