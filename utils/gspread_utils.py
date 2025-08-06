import gspread, re 
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
from urllib.parse import urlparse, parse_qs, unquote,unquote_plus
import requests

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

creds_dict = dict(st.secrets["google_service_account"])
# Crea oggetto credentials
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)


#gs_creds_json = st.secrets["secrets"]
#gs_creds = json.loads(gs_creds_json)

# Autenticazione e client
#creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
#creds = Credentials.from_service_account_file(gs_creds)
client = gspread.authorize(creds)

def apri_sheet(spreadsheet_name, worksheet_name):
    sh = client.open(spreadsheet_name)
    worksheet = sh.worksheet(worksheet_name)
    return worksheet

def carica_df_da_sheet(spreadsheet_name, worksheet_name):
    worksheet = apri_sheet(spreadsheet_name, worksheet_name)
    dati = worksheet.get_all_records()
    return pd.DataFrame(dati)

#def salva_df_su_sheet(df, spreadsheet_name, worksheet_name):
    #worksheet = apri_sheet(spreadsheet_name, worksheet_name)
    #worksheet.clear()
    #worksheet.update([df.columns.values.tolist()] + df.values.tolist())

def salva_df_su_sheet(df, spreadsheet_name, worksheet_name):
    worksheet = apri_sheet(spreadsheet_name, worksheet_name)
    new_data = [df.columns.values.tolist()] + df.values.tolist()
    
    try:
        # Tenta di aggiornare subito, senza cancellare prima
        worksheet.update(new_data)
    except Exception as e:
        print("❌ Errore durante l'update:", e)
        # Se vuoi, loggalo o notifica via email/Slack
        
def aggiorna_recensione(df, idx, nuova_riga, spreadsheet_name, worksheet_name):
    # Modifica la riga con indice idx
    for col, val in nuova_riga.items():
        df.at[idx, col] = val
    salva_df_su_sheet(df, spreadsheet_name, worksheet_name)

def elimina_recensione(df, idx, spreadsheet_name, worksheet_name):
    # Elimina la riga con indice idx
    df = df.drop(idx).reset_index(drop=True)
    salva_df_su_sheet(df, spreadsheet_name, worksheet_name)
    return df

def estrai_coordinate_da_link(link):
    # Cerca coordinate da !3dLAT!4dLON
    match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', link)
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))
        return lat, lon

    # Fallback: usa le coordinate centrate nella vista (meno affidabili)
    match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', link)
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))
        return lat, lon

    return None, None

def estrai_nome_ristorante_da_link(link):
    """
    Estrae un nome leggibile del ristorante da un link di Google Maps.
    """
    try:
        path = urlparse(link).path
        if "/place/" in path:
            # Prende tutto dopo /place/ fino al prossimo /
            nome_grezzo = path.split("/place/")[1].split("/")[0]
            nome_pulito = unquote_plus(nome_grezzo).strip()
            return nome_pulito.split(",")[0]
    except Exception as e:
        print(f"Errore durante l'estrazione del nome: {e}")
    return "Ristorante sconosciuto"
    
