import streamlit as st
import pandas as pd
import datetime
from utils.gspread_utils import (
    connetti_gs,
    carica_gs,
    salva_gs,
    aggiorna_gs,
    elimina_gs
)
from google.oauth2.service_account import Credentials

st.set_page_config( layout="wide",
                    page_icon="favicon.ico")
                    
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# === AUTENTICAZIONE ===
if not st.session_state.get("logged_in", False):
    st.error("Effettua il login dalla home.")
    st.stop()

# === INIZIALIZZAZIONE VARIABILI DI STATO ===
for key in ["nuovo_titolo", "nuovo_contenuto", "nota_salvata", "mostra_successo"]:
    if key not in st.session_state:
        st.session_state[key] = "" if "titolo" in key or "contenuto" in key else False

# === RESET POST-SALVATAGGIO (prima dei widget) ===
if st.session_state["nota_salvata"]:
    # Imposta il flag per mostrare il messaggio dopo
    st.session_state["mostra_successo"] = True

    # Pulisce i campi per il prossimo render
    st.session_state["nuovo_titolo"] = ""
    st.session_state["nuovo_contenuto"] = ""
    st.session_state["nota_salvata"] = False
else:
    st.session_state["mostra_successo"] = False

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

    if st.session_state["mostra_successo"]:
        st.success("Nota salvata!")

# --- COLONNA SINISTRA: Note esistenti ---
with col_sx:
    df = carica_gs()
    if df.empty:
        st.info("Nessuna nota ancora.")
    else:
        st.subheader("📄 Tutte le note")
        filter_cols = st.columns(2)
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
