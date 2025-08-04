import pandas as pd
import os
import re
from urllib.parse import unquote, urlparse

def salva_csv(dati, file_path):
    df = pd.read_csv(file_path) if os.path.exists(file_path) else pd.DataFrame()
    df = pd.concat([df, pd.DataFrame([dati])], ignore_index=True)
    df.to_csv(file_path, index=False, float_format="%.7f")

def carica_csv(file_path, columns):
    if os.path.exists(file_path):
        return pd.read_csv(file_path, dtype={'lat': 'float64', 'lon': 'float64'})
    else:
        return pd.DataFrame(columns=columns)


def elimina_riga_csv(file_path, condizione):
    if not os.path.exists(file_path): return
    df = pd.read_csv(file_path)
    df = df[~condizione(df)]
    df.to_csv(file_path, index=False)

def aggiorna_nota(file_path, index, nuovi_dati):
    if not os.path.exists(file_path): return
    df = pd.read_csv(file_path)
    for chiave, valore in nuovi_dati.items():
        df.loc[index, chiave] = valore
    df.to_csv(file_path, index=False)


def estrai_coordinate(link):
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
    Estrae un nome leggibile del ristorante dal link Google Maps.
    """
    try:
        if "/place/" in link:
            # Es. https://www.google.com/maps/place/Pizzeria+Roma/@...
            path = urlparse(link).path
            nome = path.split("/place/")[1].split("/")[0]
            nome = unquote(nome.replace("+", " ")).strip()
            return nome
    except Exception:
        pass
    return "Ristorante sconosciuto"
