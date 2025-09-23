import streamlit as st
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

st.title("Test PDF")

if st.button("Générer PDF"):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.drawString(100, 800, "Hello Streamlit Cloud")
    c.save()
    buffer.seek(0)
    st.download_button("Télécharger PDF", data=buffer, file_name="test.pdf", mime="application/pdf")
