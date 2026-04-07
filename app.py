import streamlit as st
import qrcode
from io import BytesIO

st.title("QR test")
url = "https://example.com"
qr = qrcode.QRCode(box_size=5)
qr.add_data(url)
qr.make()
img = qr.make_image()
buf = BytesIO()
img.save(buf, format="PNG")
st.image(buf.getvalue())
