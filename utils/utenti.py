import hashlib
import streamlit as st

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login(username, password):
    if (username is None) | (password is None):
        st.warning("Inserire username e password.")
    else:
        return st.secrets['password'][username]==hash_password(password)
