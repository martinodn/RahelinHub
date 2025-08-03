import streamlit as st
from data_utils import salva_csv, carica_csv, elimina_riga_csv, aggiorna_nota
import datetime

FILE_NOTE = "note.csv"
COLONNE = ["utente", "titolo", "contenuto", "data"]

if not st.session_state.get("logged_in", False):
    st.error("Effettua il login dalla home.")
    st.stop()

st.title("📝 Note condivise")

# ===== Inserimento nuova nota =====
with st.expander("➕ Aggiungi nuova nota"):
    titolo = st.text_input("Titolo")
    contenuto = st.text_area("Contenuto")

    if st.button("Salva nota"):
        if titolo and contenuto:
            salva_csv({
                "utente": st.session_state.username,
                "titolo": titolo,
                "contenuto": contenuto,
                "data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }, FILE_NOTE)
            st.success("Nota salvata!")
            st.experimental_rerun()
        else:
            st.warning("Compila titolo e contenuto.")

# ===== Visualizzazione e gestione note =====
df = carica_csv(FILE_NOTE, COLONNE)

if df.empty:
    st.info("Nessuna nota ancora.")
else:
    st.subheader("📄 Tutte le note")
    
    # Ordinamento
    ordine = st.selectbox("Ordina per:", ["data", "utente"], index=0)
    ordine_crescente = st.checkbox("Ordine crescente", value=False)
    df = df.sort_values(by=ordine, ascending=ordine_crescente).reset_index(drop=True)

    for idx, row in df.iterrows():
        with st.expander(f"{row['titolo']} - da {row['utente']}"):
            st.write(row["contenuto"])
            st.caption(f"Data: {row['data']}")

            if row["utente"] == st.session_state.username:
                # Mostra pulsanti di modifica/eliminazione fuori da altri expander
                nuovo_titolo = st.text_input("✏️ Titolo", value=row["titolo"], key=f"tit_{idx}")
                nuovo_contenuto = st.text_area("📝 Contenuto", value=row["contenuto"], key=f"cont_{idx}")

                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("💾 Salva modifiche", key=f"mod_{idx}"):
                        aggiorna_nota(FILE_NOTE, idx, {
                            "titolo": nuovo_titolo,
                            "contenuto": nuovo_contenuto
                        })
                        st.success("Nota modificata.")
                        st.experimental_rerun()

                with col2:
                    if st.button("🗑️ Elimina", key=f"del_note_{idx}"):
                        elimina_riga_csv(FILE_NOTE, lambda df: (df.index == idx) & (df["utente"] == st.session_state.username))
                        st.success("Nota eliminata.")
                        st.experimental_rerun()

