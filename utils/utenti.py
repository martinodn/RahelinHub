import hashlib
import streamlit as st

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login(username, password):
    return st.secrets['password'][username]==hash_password(password)

