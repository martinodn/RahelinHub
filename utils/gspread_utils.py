import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

CREDS_FILE = 'data/credentials.json'  

# Autenticazione e client
creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

def apri_sheet(spreadsheet_name, worksheet_name):
    sh = client.open(spreadsheet_name)
    worksheet = sh.worksheet(worksheet_name)
    return worksheet

def carica_df_da_sheet(spreadsheet_name, worksheet_name):
    worksheet = apri_sheet(spreadsheet_name, worksheet_name)
    dati = worksheet.get_all_records()
    return pd.DataFrame(dati)

def salva_df_su_sheet(df, spreadsheet_name, worksheet_name):
    worksheet = apri_sheet(spreadsheet_name, worksheet_name)
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

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
