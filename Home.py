import streamlit as st
from utils.utenti import login
from utils.gspread_utils import load_image,aggiorna_ultimo_login, carica_df_da_sheet
from datetime import datetime, timedelta


st.set_page_config(page_title="RaheLink", layout="wide")
st.sidebar.title("🔐 Login")

SPREADSHEET_NAME = "LoginDB"
WORKSHEET_NAME = "login"
df_login = carica_df_da_sheet(SPREADSHEET_NAME, WORKSHEET_NAME)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.login_time = None

if not st.session_state.logged_in:
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):

        if username not in st.secrets["password"]:
            st.sidebar.error("Inserire username corretto.")
        else:
            if login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.login_time = datetime.now()
                
                try:
                    aggiorna_ultimo_login(username, spreadsheet_name="LoginDB", worksheet_name="login")
                except Exception as e:
                    st.warning("⚠️ Errore salvataggio login: " + str(e))
                    
                st.rerun()
            else:
                st.sidebar.error("Credenziali errate")
else:
    st.sidebar.success("Loggato come: {}".format(st.session_state.username))
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.login_time = None
        st.rerun()

st.title("Benvenuto su RaheLink! 🤗")
if st.session_state.logged_in:
    st.info("Usa il menu a sinistra per navigare tra le pagine.")
    col1, col2, col3 = st.columns([1,3,1])
    with col2:
        image = load_image()
        st.image(image, use_container_width=True)
else:
    st.warning("Effettua il login per accedere.")
    col1, col2, col3 = st.columns([1,3,1])
    with col2:
        image = load_image()
        st.image(image, use_container_width=True)
