import pandas as pd
import os
import re

def salva_csv(dati, file_path):
    df = pd.read_csv(file_path) if os.path.exists(file_path) else pd.DataFrame()
    df = pd.concat([df, pd.DataFrame([dati])], ignore_index=True)
    df.to_csv(file_path, index=False)

def carica_csv(file_path, columns):
    return pd.read_csv(file_path) if os.path.exists(file_path) else pd.DataFrame(columns=columns)

def elimina_riga_csv(file_path, condizione):
    if not os.path.exists(file_path): return
    df = pd.read_csv(file_path)
    df = df[~condizione(df)]
    df.to_csv(file_path, index=False)

def aggiorna_nota(file_path, index, nuovi_dati):
    if not os.path.exists(file_path): return
    df = pd.read_csv(file_path)
    for chiave, valore in nuovi_dati.items():
        df.at[index, chiave] = valore
    df.to_csv(file_path, index=False)



def estrai_coordinate(link):
    # Match tipo: @45.4642,9.19 o q=45.4642,9.19
    match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', link)
    if not match:
        match = re.search(r'q=(-?\d+\.\d+),(-?\d+\.\d+)', link)
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))
        return lat, lon
    return None, None
