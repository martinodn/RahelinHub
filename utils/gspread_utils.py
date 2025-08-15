import gspread, re 
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
from urllib.parse import urlparse, parse_qs, unquote,unquote_plus
import requests
from PIL import Image
from datetime import datetime

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

creds_dict = dict(st.secrets["google_service_account"])

# Crea oggetto credentials
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

client = gspread.authorize(creds)


        
def apri_sheet(spreadsheet_name, worksheet_name):
    sh = client.open(spreadsheet_name)
    worksheet = sh.worksheet(worksheet_name)
    return worksheet

def carica_df_da_sheet(spreadsheet_name, worksheet_name):
    worksheet = apri_sheet(spreadsheet_name, worksheet_name)
    dati = worksheet.get_all_records()
    if not dati:
        return pd.DataFrame(columns=["utente","ristorante", "recensione", "voto", "link", "lat", "lon", "data"])
    return pd.DataFrame(dati)

def salva_df_su_sheet(df, spreadsheet_name, worksheet_name):
    worksheet = apri_sheet(spreadsheet_name, worksheet_name)
    new_data = [df.columns.values.tolist()] + df.values.tolist()
    
    try:
        # Tenta di aggiornare subito, senza cancellare prima
        worksheet.update(new_data)
    except Exception as e:
        st.error("❌ Errore durante l'update:", e)
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
    
@st.cache_data
def load_image():
    with open("data/Rahel.PNG", "rb") as f:
        image=Image.open(f)
        image=image.copy()
        return image

def aggiorna_ultimo_login(username, spreadsheet_name="LoginDB", worksheet_name="login"):
    df = carica_df_da_sheet(spreadsheet_name, worksheet_name)
    ora_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if "utente" not in df.columns or df.empty:
        df = pd.DataFrame(columns=["utente", "ultimo_login"])

    idx = df.index[df["utente"] == username].tolist()

    if idx:
        df.at[idx[0], "ultimo_login"] = ora_login
    else:
        nuovo = {"utente": username, "ultimo_login": ora_login}
        df = pd.concat([df, pd.DataFrame([nuovo])], ignore_index=True)

    salva_df_su_sheet(df, spreadsheet_name, worksheet_name)

# === CONFIG ===
GS_SPREADSHEET_NAME = "note"  # Nome del file Google Sheet
GS_WORKSHEET_NAME = "note"    # Nome del foglio dentro il file
COLONNE = ["utente", "titolo", "contenuto", "data"]

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

def carica_calendario(sheet_url, sheet_name):

    sheet = client.open_by_url(sheet_url).worksheet(sheet_name)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df
