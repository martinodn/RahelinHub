import streamlit as st
from utils.utenti import login
from PIL import Image


st.set_page_config(page_title="RaheLink", layout="wide")
st.sidebar.title("🔐 Login")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if username not in st.secrets["password"]:
        st.warning("Nome utente non esistente")
    else:
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

st.title("Benvenuto su RaheLink! 🤗")
if st.session_state.logged_in:
    st.info("Usa il menu a sinistra per navigare tra le pagine.")
    col1, col2, col3 = st.columns([1,3,1])
    with col2:
        image = Image.open("data/Rahel.PNG")
        st.image(image, use_container_width=True)
else:
    st.warning("Effettua il login per accedere.")
    col1, col2, col3 = st.columns([1,3,1])
    with col2:
        image = Image.open("data/Rahel.PNG")
        st.image(image, use_container_width=True)
