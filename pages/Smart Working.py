import streamlit as st
import pandas as pd
#from utils.gspread_utils import carica_calendario

def carica_calendario(sheet_url, sheet_name, client):
    sheet = client.open_by_url(sheet_url).worksheet(sheet_name)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df
    
st.set_page_config( page_title="Smart Working",
                    layout="wide",
                    page_icon="favicon.ico")
                    
st.title("📅 Calendario Smart Working – Marti & Vali ")
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

creds_dict = dict(st.secrets["google_service_account"])

# Crea oggetto credentials
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

client = gspread.authorize(creds)

SHEET_NAME="https://docs.google.com/spreadsheets/d/1DfXFpEZudFg3aXOXTr5pdWRfLAH0wCZd2vqZI9t4NPo/edit?gid=0#gid=0"
WORKSHEET_NAME = "smartworking"

# Carica il foglio in formato long (una riga per persona+mese)
df = carica_calendario(SHEET_NAME, WORKSHEET_NAME, client)


# Opzioni disponibili (mesi unici)
mesi = df["mese"].unique()
mese_sel = st.selectbox("🗓️ Seleziona mese", mesi)

# Filtra solo le righe per il mese selezionato
df_mese = df[df["mese"] == mese_sel].reset_index(drop=True)

if df_mese.empty:
    st.warning("Nessun dato disponibile per questo mese.")
else:
    # Togliamo la colonna "mese"
    df_mese = df_mese.drop(columns=["mese"])

    # Trasformiamo da wide a long: ogni riga = persona + giorno
    df_long = df_mese.melt(id_vars=["persona"], var_name="giorno", value_name="luogo")

    # Pivot per avere una colonna per persona, riga per giorno
    tabella = df_long.pivot(index="giorno", columns="persona", values="luogo")

    # Ordina i giorni in modo numerico (da "01" a "31")
    tabella = tabella.reindex(sorted(tabella.index, key=lambda x: int(x)), axis=0)

    # Funzione di colorazione celle
    def colora_celle(val):
        colori = {
            "Casa": "background-color: #d4edda; color: black",       # Verdino chiaro
            "Ufficio": "background-color: #f8d7da; color: black",    # Rossino chiaro
            "Ferie": "background-color: #ffeeba; color: black",      # Arancione
            "Jolly": "background-color: #e2d6f3; color: black",      # Viola chiaro
            "Trasferta": "background-color: #cce5ff; color: black",  # Azzurro
            "-": "background-color: #f1f1f1; color: black",
            "": "background-color: #f1f1f1; color: black"
        }
        return colori.get(val, "")

    # Applica colori e visualizza
    styled_tab = tabella.style.applymap(colora_celle).set_properties(**{"text-align": "center"})
    st.dataframe(styled_tab, use_container_width=True, height=1150)
