import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials

# === CONFIG ===
GS_SPREADSHEET_NAME = "note"  # Nome del file Google Sheet
GS_WORKSHEET_NAME = "note"    # Nome del foglio dentro il file

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

COLONNE = ["utente", "titolo", "contenuto", "data"]

# === FUNZIONI ===

@st.cache_resource(ttl=3600)
def connetti_gs():
    creds_dict = dict(st.secrets["google_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open(GS_SPREADSHEET_NAME).worksheet(GS_WORKSHEET_NAME)
    return sheet

def carica_gs():
    sheet = connetti_gs()
    dati = sheet.get_all_records()
    if not dati:
        return pd.DataFrame(columns=COLONNE)
    return pd.DataFrame(dati)

def salva_gs(nuova_riga: dict):
    sheet = connetti_gs()
    riga = [nuova_riga.get(c, "") for c in COLONNE]
    sheet.append_row(riga)

def aggiorna_gs(indice: int, nuova_info: dict):
    sheet = connetti_gs()
    riga_sheets = indice + 2  # +1 per header, +1 per zero-based
    for col_idx, col_name in enumerate(COLONNE, start=1):
        if col_name in nuova_info:
            sheet.update_cell(riga_sheets, col_idx, nuova_info[col_name])

def elimina_gs(indice: int):
    sheet = connetti_gs()
    riga_sheets = indice + 2
    sheet.delete_rows(riga_sheets)

# === AUTENTICAZIONE ===

if not st.session_state.get("logged_in", False):
    st.error("Effettua il login dalla home.")
    st.stop()

# === INIZIALIZZAZIONE VARIABILI DI STATO ===

if "nuovo_titolo" not in st.session_state:
    st.session_state["nuovo_titolo"] = ""
if "nuovo_contenuto" not in st.session_state:
    st.session_state["nuovo_contenuto"] = ""
if "nota_salvata" not in st.session_state:
    st.session_state["nota_salvata"] = False

# === SALVATAGGIO NUOVA NOTA ===

def salva_nota():
    if st.session_state["nuovo_titolo"] and st.session_state["nuovo_contenuto"]:
        salva_gs({
            "utente": st.session_state.username,
            "titolo": st.session_state["nuovo_titolo"],
            "contenuto": st.session_state["nuovo_contenuto"],
            "data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        st.session_state["nota_salvata"] = True
    else:
        st.warning("Compila titolo e contenuto.")

# === RESET INPUT DOPO SALVATAGGIO ===

if st.session_state["nota_salvata"]:
    st.session_state["nuovo_titolo"] = ""
    st.session_state["nuovo_contenuto"] = ""
    st.session_state["nota_salvata"] = False
    st.success("Nota salvata!")

# === LAYOUT INTERFACCIA ===

st.title("📝 Note condivise")
st.markdown("---")

col_sx, col_dx = st.columns([2, 1])  # Note a sinistra, form a destra

# --- COLONNA DESTRA: Form nuova nota ---
with col_dx:
    st.markdown("### ➕ Nuova nota")
    st.text_input("Titolo", key="nuovo_titolo")
    st.text_area("Contenuto", key="nuovo_contenuto")
    st.button("Salva nota", on_click=salva_nota)

# --- COLONNA SINISTRA: Note esistenti ---
with col_sx:
    df = carica_gs()
    if df.empty:
        st.info("Nessuna nota ancora.")
    else:
        st.subheader("📄 Tutte le note")
        filter_cols=st.columns(2)
        with filter_cols[0]:
            ordine = st.selectbox("Ordina per:", ["data", "utente"], index=0)
            ordine_crescente = st.checkbox("Ordine crescente", value=False)
            
        df = df.sort_values(by=ordine, ascending=ordine_crescente)

        for idx, row in df.iterrows():
            with st.expander(f"{row['titolo']} - da {row['utente']}"):
                st.write(row["contenuto"])
                st.caption(f"Data: {row['data']}")

                if row["utente"] == st.session_state.username:
                    nuovo_titolo = st.text_input("✏️ Titolo", value=row["titolo"], key=f"tit_{idx}")
                    nuovo_contenuto = st.text_area("📝 Contenuto", value=row["contenuto"], key=f"cont_{idx}")

                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("💾 Salva modifiche", key=f"mod_{idx}"):
                            aggiorna_gs(idx, {
                                "titolo": nuovo_titolo,
                                "contenuto": nuovo_contenuto
                            })
                            st.success("Nota modificata.")
                            st.rerun()
                    with col2:
                        if st.button("🗑️ Elimina nota", key=f"del_{idx}"):
                            elimina_gs(idx)
                            st.success("Nota eliminata.")
                            st.rerun()
