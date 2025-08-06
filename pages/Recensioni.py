
import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
from utils.gspread_utils import (
    carica_df_da_sheet,
    salva_df_su_sheet,
    aggiorna_recensione,
    elimina_recensione,
    estrai_coordinate_da_link,
    estrai_nome_ristorante_da_link
)


st.set_page_config(layout="wide")


SPREADSHEET_NAME = "recensioni"
WORKSHEET_NAME = "recensioni"

if not st.session_state.get("logged_in", False):
    st.error("Effettua il login dalla home.")
    st.stop()

st.title("🍽️ Vota i ristoranti!")

# Carica recensioni da Google Sheets
df = carica_df_da_sheet(SPREADSHEET_NAME, WORKSHEET_NAME)

if df.empty:
    st.info("Nessuna recensione presente.")
    df = pd.DataFrame(columns=["utente", "ristorante", "recensione", "voto", "link", "lat", "lon", "data"])

# Tabs
tab_lista, tab_mappa = st.tabs(["📋 Ristoranti", "🗺️ Mappa"])

with tab_lista:
    col_left, col_right = st.columns([2, 1])  # sinistra più larga, destra più stretta

    with col_left:
        media_voti = df.groupby("ristorante")["voto"].mean().reset_index().rename(columns={"voto": "voto_medio"})
        media_voti = media_voti.sort_values("voto_medio", ascending=False)
        
        st.subheader("🍴 Ristoranti per voto medio")
        ranking_cols=st.columns(2)
        with ranking_cols[1]:
            rank = st.radio("Ordina le recensioni:", ["Top", "Flop"])
        with ranking_cols[0]:
            if rank=="Flop":
                media_voti=media_voti.sort_values("voto_medio", ascending=True)
            media_voti=media_voti.head(10)
            for _, row in media_voti.iterrows():
                st.markdown(f"**{row['ristorante']}** – ⭐ {row['voto_medio']:.2f}")

        st.markdown("---")
        st.subheader("📝 Tutte le recensioni")
        for idx, row in df.sort_values("data", ascending=False).iterrows():
            with st.expander(f"{row['ristorante']} – ⭐ {row['voto']} (di {row['utente']})"):
                st.write(row["recensione"])
                st.caption(f"Data: {row['data']}")
                if row.get("link") and pd.notna(row.get("lat")) and pd.notna(row.get("lon")):
                    st.markdown(f"[📍 Google Maps]({row['link']})")

    with col_right:
        st.subheader("➕ Nuova recensione")
        ristoranti_esistenti = df["ristorante"].dropna().unique().tolist()
        ristoranti_esistenti.sort()
        opzioni = ["🆕 Nuovo ristorante"] + ristoranti_esistenti

        scelta = st.selectbox("Recensisci un nuovo ristorante o scegline uno già presente:", opzioni)

        if scelta == "🆕 Nuovo ristorante":
            link = st.text_input("Link Google Maps (formato browser):")
            lat, lon = estrai_coordinate_da_link(link)
            ristorante = estrai_nome_ristorante_da_link(link)
            st.markdown(f"📍 Ristorante rilevato: **{ristorante}**")
        else:
            ristorante = scelta
            prima_rec = df[df["ristorante"] == scelta].iloc[0]
            link = prima_rec["link"]
            lat, lon = prima_rec["lat"], prima_rec["lon"]
            st.info("Coordinate e link recuperati automaticamente.")

        
        recensione = st.text_area("La tua recensione:")
        voto = st.slider("Voto", 1, 10)

        if st.button("Invia recensione"):
            if not link:
                st.warning("Inserisci un link valido.")
            elif not recensione:
                st.warning("Inserisci la recensione.")
            else:
                già_fatto = ((df["utente"] == st.session_state.username) & (df["ristorante"].str.lower() == ristorante.lower())).any()
                if già_fatto:
                    st.error("Hai già recensito questo ristorante.")
                else:
                    nuova_riga = {
                        "utente": st.session_state.username,
                        "ristorante": ristorante,
                        "recensione": recensione,
                        "voto": voto,
                        "link": link,
                        "lat": lat,
                        "lon": lon,
                        "data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    df = pd.concat([df, pd.DataFrame([nuova_riga])], ignore_index=True)
                    salva_df_su_sheet(df, SPREADSHEET_NAME, WORKSHEET_NAME)
                    st.success("Recensione salvata!")
                    st.rerun()
with tab_mappa:
    df_map = df.dropna(subset=["lat", "lon"])
    st.write(df_map)
    if df_map.empty:
        st.info("Nessuna recensione con coordinate.")
    else:
        # Raggruppa per ristorante e calcola coordinate e voto medio
        grp = df_map.groupby("ristorante").agg({
            "lat": "mean",
            "lon": "mean",
            "voto": "mean"
        }).reset_index()

        # Hover text personalizzato
        grp["hover"] = grp["ristorante"] + " – ⭐ " + grp["voto"].round(2).astype(str)

        # Crea figura Plotly con Scattermap (nuovo)
        fig = go.Figure(go.Scattermap(
            lat=grp["lat"],
            lon=grp["lon"],
            mode='markers',
            marker=dict(
                size=18,
                color=grp["voto"],
                colorscale="RdYlGn",
                cmin=1,
                cmax=10,
                colorbar=dict(title="Voto"),
                opacity=1
            ),
            text=grp["hover"],
            hoverinfo='text'
        ))

        # Layout aggiornato con map invece di mapbox
        fig.update_layout(
            map=dict(
                style="carto-positron",  # o "carto-positron", "stamen-terrain"
                center=dict(lat=grp["lat"].mean(), lon=grp["lon"].mean()),
                zoom=10
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0}
        )

        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})



# ===== Modifica/Elimina recensioni utente =====
user_df = df[df["utente"] == st.session_state.username]
st.write('#')
if not user_df.empty:
    st.subheader("🛠️ Le tue recensioni")
    for idx, row in user_df.iterrows():
        with st.expander(f"{row['ristorante']} – ⭐ {row['voto']}"):
            nuovo_ristorante = st.text_input("🍴 Nome ristorante", value=row["ristorante"], key=f"res_{idx}")
            nuova_recensione = st.text_area("📝 Recensione", value=row["recensione"], key=f"rev_{idx}")
            nuovo_voto = st.slider("⭐ Voto", 1, 10, value=int(row["voto"]), key=f"voto_{idx}")
            nuovo_link = row["link"]
            lat, lon = row["lat"], row["lon"]

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Salva modifiche", key=f"mod_{idx}"):
                    aggiorna_recensione(df, idx, {
                        "ristorante": nuovo_ristorante,
                        "recensione": nuova_recensione,
                        "voto": nuovo_voto,
                        "link": nuovo_link,
                        "lat": lat,
                        "lon": lon
                    }, SPREADSHEET_NAME, WORKSHEET_NAME)
                    st.success("Recensione modificata.")
                    st.rerun()
            with col2:
                if st.button("🗑️ Elimina", key=f"del_{idx}"):
                    df = elimina_recensione(df, idx, SPREADSHEET_NAME, WORKSHEET_NAME)
                    st.success("Recensione eliminata.")
