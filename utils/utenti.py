import hashlib
import streamlit as st

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


USERS = {
    "ernest": "9280b6350842854f810c564c732ae22a83946c72fe781e9918a6665e750f2318",
    "monix": "916fa2c79ebc5bb13c03ff99188cce33a033e176f20c17e001b1bd5733a0b30d",
    "fedi": "cbce3b50567c0e69a6ccdb5d586a82e9cefa4a83a096518a99dadb59fba5b1a0",
    "vali": "ae30543c990452a812e583cdb1c5646e73763a321a410a83b59a445125f50960",
    "marti": "184563f3c6daeecd9e2338f44f63e16124c0c8130847a38059405f23975443f3"
}

def login(username, password):
    return USERS.get(username)==hash_password(password)
