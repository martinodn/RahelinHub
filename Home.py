import streamlit as st
from utils.utenti import login
st.set_page_config(page_title="App Recensioni", layout="centered")
st.sidebar.title("🔐 Login")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if login(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()
        else:
            st.sidebar.error("Credenziali errate")
else:
    st.sidebar.success("Loggato come: {}".format(st.session_state.username))
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

st.title("📋 App Personale")
if st.session_state.logged_in:
    st.info("Usa il menu a sinistra per navigare tra le pagine.")
else:
    st.warning("Effettua il login per accedere.")
