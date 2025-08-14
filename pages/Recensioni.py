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


st.set_page_config( layout="wide",
                    page_icon="favicon.ico")


if not st.session_state.get("logged_in", False):
    st.error("Effettua il login dalla home.")
    st.stop()

st.title("🍽️ Vota i ristoranti!")

SPREADSHEET_NAME = "recensioni"
WORKSHEET_NAME = "recensioni"
df = carica_df_da_sheet(SPREADSHEET_NAME, WORKSHEET_NAME)

if df.empty:
    st.info("Nessuna recensione presente.")
    df = pd.DataFrame(columns=["utente", "ristorante", "recensione", "voto", "link", "lat", "lon", "data"])

# Tabs
tab_lista, tab_mappa = st.tabs(["📋 Ristoranti", "🗺️ Mappa"])

with tab_lista:
    col_left, col_right = st.columns([2, 1])  # sinistra più larga, destra più stretta

    with col_left:
        st.subheader("🍴 Ristoranti per voto medio")

        # Campo di ricerca testuale
        filtro_nome = st.text_input("🔍 Cerca ristorante per nome")

        # Calcolo media voti per ristorante
        media_voti = df.groupby("ristorante")["voto"].mean().reset_index().rename(columns={"voto": "voto_medio"})

        # Applica filtro per nome se presente
        if filtro_nome:
            media_voti = media_voti[media_voti["ristorante"].str.contains(filtro_nome, case=False, na=False)]

        ranking_cols = st.columns(2)
        
        with ranking_cols[1]:
            rank = st.radio("Ordina le recensioni:", ["Top 10", "Flop 10"])

        with ranking_cols[0]:
            # Ordina in base alla selezione
            if rank == "Flop 10":
                media_voti = media_voti.sort_values("voto_medio", ascending=True)
            else:
                media_voti = media_voti.sort_values("voto_medio", ascending=False)

            # Mostra solo i primi 10 risultati
            media_voti = media_voti.head(10)

            # Visualizza risultati
            for _, row in media_voti.iterrows():
                st.markdown(f"**{row['ristorante']}** – ⭐ {row['voto_medio']:.2f}")

                
    st.subheader("📝 Tutte le recensioni")
    col1, col2, col3 = st.columns(3)

    with col1:
        filtro_ristorante = st.text_input("Filtra per ristorante (testo)")
    with col2:
        utenti = ["Tutti"] + sorted(df["utente"].dropna().unique().tolist())
        filtro_utente = st.selectbox("Filtra per utente", utenti)
    with col3:
        voto_minimo = st.slider("Voto minimo", 1, 10, 1)

    # Applica i filtri
    df_filtrato = df.copy()

    if filtro_ristorante.strip():
        df_filtrato = df_filtrato[
            df_filtrato["ristorante"].str.contains(filtro_ristorante, case=False, na=False)
        ]

    if filtro_utente != "Tutti":
        df_filtrato = df_filtrato[df_filtrato["utente"] == filtro_utente]

    df_filtrato = df_filtrato[df_filtrato["voto"] >= voto_minimo]

    # sort by most recents
    df_filtrato=df_filtrato.sort_values('data',ascending=False)
    
    if (filtro_ristorante=="") & (filtro_utente == "Tutti") & (voto_minimo==1):
        df_filtrato=df_filtrato.iloc[:10,:]
        st.info('Visualizzazione limitata alle 10 recensioni più recenti. Utilizzare i filtri per cercare le recensioni.')
    
    if df_filtrato.empty:
        st.warning("Nessuna recensione trovata con i filtri selezionati.")
    else:
        for idx, row in df_filtrato.sort_values("data", ascending=False).iterrows():
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

        # 🧼 Pulizia del form (da fare prima di visualizzare i widget)
        if st.session_state.get("clear_form", False):
            st.session_state["nuovo_link"] = ""
            st.session_state["nuova_recensione"] = ""
            st.session_state["nuovo_voto"] = 5
            del st.session_state["clear_form"]

        scelta = st.selectbox("Recensisci un nuovo ristorante o scegline uno già presente:", opzioni)

        lat, lon, link, ristorante = None, None, "", ""

        if scelta == "🆕 Nuovo ristorante":
            link = st.text_input("Link Google Maps (formato browser):", key="nuovo_link")
            if link:
                lat, lon = estrai_coordinate_da_link(link)
                ristorante = estrai_nome_ristorante_da_link(link)
                if ristorante and ristorante != "Ristorante sconosciuto":
                    st.markdown(f"📍 Ristorante rilevato: **{ristorante}**")
        else:
            ristorante = scelta
            prima_rec = df[df["ristorante"] == scelta].iloc[0]
            link = prima_rec["link"]
            lat, lon = prima_rec["lat"], prima_rec["lon"]
            st.session_state["nuovo_link"] = link
            st.info("Coordinate e link recuperati automaticamente.")

        recensione = st.text_area("La tua recensione:", key="nuova_recensione")
        voto = st.slider("Voto", 1, 10, key="nuovo_voto")

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
                    if ristorante == "Ristorante sconosciuto":
                        st.error("Impossibile ottenere il nome del ristorante.")
                    elif (lat is None) or (lon is None):
                        st.warning("Impossibile ottenere le coordinate.")
                    else:
                        df = pd.concat([df, pd.DataFrame([nuova_riga])], ignore_index=True)
                        salva_df_su_sheet(df, SPREADSHEET_NAME, WORKSHEET_NAME)
                        st.success("Recensione salvata!")

                        st.session_state["clear_form"] = True
                        st.rerun()
            
    # ===== Modifica/Elimina recensioni utente (con filtri) =====
    user_df = df[df["utente"] == st.session_state.username]
    st.write('#')
    if not user_df.empty:
        st.subheader("📋 Visualizza e modifica le tue recensioni")

        col1, col2 = st.columns(2)

        with col1:
            filtro_mio_ristorante = st.text_input("Filtra per ristorante (testo)", key="filtro_mio_ristorante")
        with col2:
            mio_voto_minimo = st.slider("Voto minimo", 1, 10, 1, key="mio_voto_minimo")

        # Applica i filtri
        user_df_filtrato = user_df.copy()

        if filtro_mio_ristorante.strip():
            user_df_filtrato = user_df_filtrato[
                user_df_filtrato["ristorante"].str.contains(filtro_mio_ristorante, case=False, na=False)
            ]

        user_df_filtrato = user_df_filtrato[user_df_filtrato["voto"] >= mio_voto_minimo]

        # sort by most recents
        user_df_filtrato=user_df_filtrato.sort_values('data',ascending=False)
        
        if (filtro_mio_ristorante=="") & (mio_voto_minimo==1):
            user_df_filtrato=user_df_filtrato.iloc[:10,:]
            st.info('Visualizzazione limitata alle 10 recensioni più recenti. Utilizzare i filtri per cercare le recensioni.')
            
        if user_df_filtrato.empty:
            st.info("Non hai recensioni che corrispondono ai filtri.")
        else:
            for idx, row in user_df_filtrato.iterrows():
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
                            st.rerun()


with tab_mappa:
    df_map = df.dropna(subset=["lat", "lon"])
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
                #center=dict(lat=grp["lat"].mean(), lon=grp["lon"].mean()),
                center=dict(lat=41.9559971, lon=12.5492583),
                zoom=11
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            height=550
        )

        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})
