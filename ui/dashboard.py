import streamlit as st
import requests

st.title("Realtime Voice AI Dashboard")

api = st.text_input("API URL", "http://localhost:8000")

if st.button("Check Health"):
    r = requests.get(f"{api}/health")
    st.json(r.json())

st.subheader("Sessions")
if st.button("Refresh Sessions"):
    r = requests.get(f"{api}/sessions")
    st.json(r.json())
