import streamlit as st

st.set_page_config(page_title="Geo-Lab Jeofizik", layout="wide")

html_code = """
<!DOCTYPE html>
<html lang="tr">
<head>
    ... (bu yerga to'liq HTML kodni joylang) ...
</head>
<body>...</body>
</html>
"""

st.components.v1.html(html_code, height=1300, scrolling=True)
