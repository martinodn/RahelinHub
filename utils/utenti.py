import hashlib
import streamlit as st

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login(username, password):
    st.write("ciao")
    st.write(st.secrets["password"])
    st.write(username, password)
    return st.secrets['password'][username]==hash_password(password)
