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
            return nome_pulito
    except Exception as e:
        print(f"Errore durante l'estrazione del nome: {e}")
    return "Ristorante sconosciuto"
    
    
#def estrai_coordinate_da_link(link):
#    """
#    Estrae le coordinate (latitudine, longitudine) da un link Google Maps.
#    Supporta sia link corto (maps.app.goo.gl) che link lungo con @lat,lon.
#    """
#    def estrai_coordinate(url):
#        #match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
#        match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', link)
#        if match:
#            lat, lon = float(match.group(1)), float(match.group(2))
#            return lat, lon
#        return None, None
#
#    # Segui redirect se è un link corto
#    st.write(link)
#    if "maps.app.goo.gl" in link:
#        try:
#            resp = requests.get(link, allow_redirects=True, timeout=10)
#            st.write(resp.url)
#            return estrai_coordinate(resp.url)
#        except Exception as e:
#            print(f"[DEBUG - coordinate] Errore nel redirect: {e}")
#
#    # Se è un link lungo, prova direttamente
#    if "google.com/maps" in link:
#        return estrai_coordinate(link)
#
#    return None, None



#def estrai_nome_ristorante_da_link(shortlink):
#    try:
#        # 1. Segui il redirect dal link abbreviato
#        response = requests.get(shortlink, allow_redirects=True)
#        final_url = response.url
#
#        # 2. Decodifica il link finale
#        decoded_url = unquote(final_url)
#
#        # 3. Estrai il parametro "q" dal parametro "continue"
#        parsed = urlparse(decoded_url)
#        params = parse_qs(parsed.query)
#
#        continue_url = params.get('continue')
#        if continue_url:
#            # Decodifica anche il valore di "continue"
#            inner_url = unquote(continue_url[0])
#            inner_parsed = urlparse(inner_url)
#            inner_params = parse_qs(inner_parsed.query)
#            query_name = inner_params.get('q')
#            if query_name:
#                # Rimuove eventuali virgole e indirizzi dopo la virgola
#                nome_attivita = query_name[0].split(',')[0]
#                return nome_attivita.replace('+', ' ').strip()
#
#        return "Nome attività non trovato."
#
#    except Exception as e:
#        return f"Errore: {e}"



#def estrai_nome_ristorante_da_link(link):
#    """
#    Estrae un nome leggibile del ristorante da un link Google Maps.
#    Supporta sia link corto (maps.app.goo.gl) che link lungo (/place/...).
#    """
#    def estrai_nome(url):
#        try:
#            if "/place/" in url:
#                path = urlparse(url).path
#                nome = path.split("/place/")[1].split("/")[0]
#                nome = unquote(nome.replace("+", " ")).strip()
#                return nome
#        except Exception:
#            pass
#        return "Ristorante sconosciuto"
#
#    # Segui il redirect se è un link corto
#    st.write("maps.app.goo.gl" in link)
#    if "maps.app.goo.gl" in link:
#        st.write('qui')
#        try:
#            resp = requests.get(link, allow_redirects=True, timeout=10)
#            st.write(resp)
#            return estrai_nome(resp.url)
#        except Exception as e:
#            print(f"[DEBUG - nome] Errore nel redirect: {e}")
#
#    # Se è un link lungo, prova direttamente
#    if "google.com/maps" in link:
#        return estrai_nome(link)
#
#    return "Ristorante sconosciuto"
#



#def estrai_coordinate_da_link(link):
#    """
#    Estrae le coordinate (latitudine, longitudine) da un link Google Maps.
#    Supporta sia link corti (maps.app.goo.gl) che lunghi (consent.google.com).
#    """
#    try:
#        if "maps.app.goo.gl" in link:
#            resp = requests.get(link, allow_redirects=True, timeout=10)
#            final_url = resp.url
#        elif "consent.google.com" in link:
#            parsed = urlparse(link)
#            continue_url = parse_qs(parsed.query).get("continue", [None])[0]
#            if not continue_url:
#                return None, None
#            final_url = unquote(continue_url)
#        else:
#            return None, None
#
#        # Cerca le coordinate nella forma @lat,lon
#        match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)',final_url)
#        if match:
#            lat, lon = match.groups()
#            return float(lat), float(lon)
#
#        return None, None
#
#    except Exception as e:
#        print(f"Errore estrazione coordinate: {e}")
#        return None, None

#def separa_nome_e_indirizzo(q_string):
#    # Rimuove + e spazi doppi
#    q_string = q_string.replace('+', ' ').replace('  ', ' ').strip()
#
#    # Divide in blocchi (frammenti) usando la virgola
#    blocchi = [b.strip() for b in q_string.split(',')]
#
#    # Criteri: cerca il primo blocco con un numero (civico o CAP)
#    index_indirizzo = -1
#    for i, blocco in enumerate(blocchi):
#        if any(char.isdigit() for char in blocco):
#            index_indirizzo = i
#            break
#
#    if index_indirizzo == -1:
#        # Se non troviamo nulla con numeri, consideriamo tutto come indirizzo
#        return None, q_string
#
#    nome = ', '.join(blocchi[:index_indirizzo])
#    indirizzo = ', '.join(blocchi[index_indirizzo:])
#
#    return nome.strip(), indirizzo.strip()


#def estrai_coordinate_da_link(shortlink):
#    try:
#        # 1. Segui il redirect
#        response = requests.get(shortlink, allow_redirects=True)
#        final_url = unquote(response.url)
#
#        # 2. Estrai il parametro "q" dall'URL annidato
#        parsed = urlparse(final_url)
#        params = parse_qs(parsed.query)
#        continue_url = params.get('continue')
#
#        if not continue_url:
#            return None, None
#
#        else:
#            inner_url = unquote(continue_url[0])
#            inner_parsed = urlparse(inner_url)
#            inner_params = parse_qs(inner_parsed.query)
#            query_place = inner_params.get('q')
#
#            if query_place:
#                nome_e_indirizzo = query_place[0].replace('+', ' ').strip()
#                nome, indirizzo=separa_nome_e_indirizzo(nome_e_indirizzo)
#                # 3. Richiesta a Nominatim per geocodifica
#                geocode_url = "https://nominatim.openstreetmap.org/search"
#                response = requests.get(geocode_url, params={
#                    "q": indirizzo,
#                    "format": "json"
#                }, headers={"User-Agent": "streamlit-app"})
#
#                st.write(response)
#                data = response.json()
#                st.write(data)
#
#                if data:
#                    lat = data[0]['lat']
#                    lon = data[0]['lon']
#                    return lat, lon
#                else:
#                    return "Coordinate non trovate."
#
#        return "Coordinate non trovate nel link."
#
#    except Exception as e:
#        return f"Errore: {e}"
#
#
