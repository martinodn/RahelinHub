import streamlit as st
import pandas as pd
import datetime
import pydeck as pdk
from data_utils import salva_csv, carica_csv, elimina_riga_csv, aggiorna_nota, estrai_coordinate

FILE_RECENSIONI = "recensioni.csv"

if not st.session_state.get("logged_in", False):
    st.error("Effettua il login dalla home.")
    st.stop()

st.title("🍽️ Recensioni Ristoranti")

# Carica tutte le recensioni
df = carica_csv(FILE_RECENSIONI, ["utente", "ristorante", "recensione", "voto", "link", "lat", "lon", "data"])
if df.empty:
    st.info("Nessuna recensione presente. Inizia a scriverne una!")
    df = pd.DataFrame(columns=["utente","ristorante","recensione","voto","link","lat","lon","data"])

# Tab: Lista e recensioni
tab_lista, tab_mappa = st.tabs(["📋 Lista ristoranti e recensioni", "🗺️ Mappa ristoranti"])

with tab_lista:
    # Calcola voto medio per ristorante
    media_voti = df.groupby("ristorante")["voto"].mean().reset_index().rename(columns={"voto": "voto_medio"})
    media_voti = media_voti.sort_values("voto_medio", ascending=False)

    st.subheader("🍴 Ristoranti ordinati per voto medio")
    for _, row in media_voti.iterrows():
        st.markdown(f"**{row['ristorante']}** - ⭐ {row['voto_medio']:.2f}")

    st.markdown("---")
    st.subheader("📝 Recensioni")

    # Lista recensioni con autore
    for idx, row in df.sort_values("data", ascending=False).iterrows():
        with st.expander(f"{row['ristorante']} - ⭐ {row['voto']} (di {row['utente']})"):
            st.write(row["recensione"])
            st.caption(f"Data: {row['data']}")
            # Se link e coordinate validi, mostra link google maps
            if row.get("link") and pd.notna(row.get("lat")) and pd.notna(row.get("lon")):
                st.markdown(f"[📍 Google Maps]({row['link']})")

with tab_mappa:
    df_map = df.dropna(subset=["lat", "lon"])
    if df_map.empty:
        st.info("Nessuna recensione con coordinate per mostrare la mappa.")
    else:
        grp = df_map.groupby("ristorante").agg({
            "lat": "mean",
            "lon": "mean",
            "voto": "mean"
        }).reset_index()

        grp["lat"] = pd.to_numeric(grp["lat"])
        grp["lon"] = pd.to_numeric(grp["lon"])
        grp["info"] = grp.apply(lambda r: f"🍴 {r['ristorante']}<br>⭐ Voto medio: {r['voto']:.2f}", axis=1)

        ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/e/ed/Map_pin_icon.svg"

        grp["icon_data"] = [{
            "url": ICON_URL,
            "width": 40,
            "height": 55,
            "anchorY": 55
        }] * len(grp)

        layer = pdk.Layer(
            "IconLayer",
            data=grp,
            get_icon="icon_data",
            get_size=4,
            size_scale=10,
            get_position='[lon, lat]',
            pickable=True,
            auto_highlight=True,
        )

        midpoint = (grp["lat"].mean(), grp["lon"].mean())
        view_state = pdk.ViewState(
            latitude=midpoint[0],
            longitude=midpoint[1],
            zoom=11,
            pitch=0,
        )

        tooltip = {
            "html": "{info}",
            "style": {
                "backgroundColor": "steelblue",
                "color": "white",
                "fontSize": "14px",
                "padding": "10px",
                "borderRadius": "5px"
            }
        }

        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/streets-v11",
            initial_view_state=view_state,
            layers=[layer],
            tooltip=tooltip,
        ))


# ===== Nuova recensione =====
with st.expander("➕ Scrivi una nuova recensione"):
    ristoranti_esistenti = df["ristorante"].dropna().unique().tolist()
    ristoranti_esistenti.sort()
    ristoranti_opzioni = ["🆕 Scrivi un nuovo ristorante"] + ristoranti_esistenti

    scelta_ristorante = st.selectbox("Scegli un ristorante o scrivine uno nuovo", ristoranti_opzioni)

    if scelta_ristorante == "🆕 Scrivi un nuovo ristorante":
        ristorante = st.text_input("Nome del ristorante")
    else:
        ristorante = scelta_ristorante

    recensione = st.text_area("La tua recensione")
    voto = st.slider("Voto", 1, 10)
    maps_link = st.text_input("Link Google Maps (opzionale)")

    if st.button("Invia recensione"):
        if not ristorante:
            st.warning("Inserisci il nome del ristorante.")
        elif not recensione:
            st.warning("Inserisci la recensione.")
        else:
            # Controllo recensione duplicata utente-ristorante
            already_reviewed = ((df["utente"] == st.session_state.username) & (df["ristorante"].str.lower() == ristorante.lower())).any()
            if already_reviewed:
                st.error("Hai già scritto una recensione per questo ristorante.")
            else:
                lat, lon = estrai_coordinate(maps_link)
                salva_csv({
                    "utente": st.session_state.username,
                    "ristorante": ristorante,
                    "recensione": recensione,
                    "voto": voto,
                    "link": maps_link,
                    "lat": lat,
                    "lon": lon,
                    "data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                }, FILE_RECENSIONI)
                st.success("Recensione salvata!")
                st.experimental_rerun()


# ===== Le recensioni dell'utente loggato per modifica/eliminazione =====
user_df = df[df["utente"] == st.session_state.username]
if user_df.empty:
    st.info("Non hai ancora scritto recensioni.")
else:
    st.subheader("🛠️ Le tue recensioni (modifica o elimina)")

    for idx, row in user_df.iterrows():
        with st.expander(f"{row['ristorante']} - ⭐ {row['voto']}"):
            nuovo_ristorante = st.text_input("🍴 Nome ristorante", value=row["ristorante"], key=f"res_{idx}")
            nuova_recensione = st.text_area("📝 Recensione", value=row["recensione"], key=f"rev_{idx}")
            nuovo_voto = st.slider("⭐ Voto", 1, 10, value=int(row["voto"]), key=f"voto_{idx}")
            nuovo_link = st.text_input("📍 Link Google Maps", value=row.get("link", ""), key=f"link_{idx}")
            lat, lon = estrai_coordinate(nuovo_link)

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("💾 Salva modifiche", key=f"mod_rec_{idx}"):
                    aggiorna_nota(FILE_RECENSIONI, idx, {
                        "ristorante": nuovo_ristorante,
                        "recensione": nuova_recensione,
                        "voto": nuovo_voto,
                        "link": nuovo_link,
                        "lat": lat,
                        "lon": lon
                    })
                    st.success("Recensione modificata.")
                    st.experimental_rerun()
            with col2:
                if st.button("🗑️ Elimina", key=f"del_rec_{idx}"):
                    elimina_riga_csv(FILE_RECENSIONI, lambda df: (df.index == idx) & (df["utente"] == st.session_state.username))
                    st.success("Recensione eliminata.")
                    st.experimental_rerun()
