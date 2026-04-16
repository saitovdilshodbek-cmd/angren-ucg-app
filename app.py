import streamlit as st

st.set_page_config(page_title="Geo-Lab Jeofizik", layout="wide")

try:
    with open("index.html", "r", encoding="utf-8") as f:
        html_code = f.read()
    st.components.v1.html(html_code, height=1300, scrolling=True)
except FileNotFoundError:
    st.error("❌ 'index.html' dosyası bulunamadı.")
    st.info("Lütfen aşağıdaki dosya yapısını oluşturun:")
    st.code("""
angren-ucg-app/
├── app.py
├── index.html
└── requirements.txt
    """)
