import streamlit as st
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import qrcode
from barcode.ean import EAN13
from barcode.writer import ImageWriter
from pathlib import Path

def tab_home():
    st.title("Accueil")
    
def tab_QR_Codes():
    st.title("QR Codes et Code Barre")

    # --- Listes ---
    Liste_choix_Qr_code = ['Vide','Emplacement', 'QR Code MGB', 'EAN']
    Liste_allée = {
        "Ambiant": ['1','2','3','4','5','6','7','8','9','10','11','12'],
        "Frais": ['19','20','21','22','23','24','25','26'],
        "FL": ['30','31','32','33'],
        "Surgelé": ['38','39','40','41','42','43'],
        "Marée": ['50','51','52','53']
    }
    Liste_rangée = [str(i) for i in range(1, 41)]
    Liste_niveau = ['A1','A2','A3','A4','B1','C1','D1']
    Liste_emplacement = [str(i) for i in range(1, 11)]

    # Choix du type de QR Code
    option = st.selectbox('Choix type de QR Code ou Code Barre :', options= Liste_choix_Qr_code)
    
    if option == "Vide":
        st.warning('Tu dois choisir une option pour générer un QR Code ou un Code Barre !')
        
    elif option == "Emplacement":
        
        # --- Choix du format ---
        nb_qr_format = st.radio("Choisir le format :", ["Grand Format", "Petit Format"])

        if nb_qr_format == "Grand Format":
            qr_count = st.selectbox("Nombre de QR Codes :", range(1, 4))  # 1 à 3
            cols_per_row = 1
            font_size = 48
            frame_width = A4[0] - 20
            frame_height = 273
            spacing = 1
        else:
            qr_count = st.selectbox("Nombre de QR Codes :", range(1, 11))  # 1 à 10
            cols_per_row = 2
            font_size = 20
            frame_width = (A4[0] - 130) / 2
            frame_height = 130
            spacing = 30
        
        # Définir le chemin de la police
        FONT_PATH = Path(__file__).parent / "fonts" / "DejaVuSans-Bold.ttf"
        try:
            font = ImageFont.truetype(str(FONT_PATH), font_size)
        except Exception as e:
            st.error(f"Erreur police: {e}")
            font = ImageFont.load_default()
        
        # --- Sélection des QR Codes ---
        st.subheader("Choisir les QR Codes")
        qr_infos = []

        for i in range(qr_count):
            st.markdown(f"**QR Code #{i+1}**")
            cellule = st.selectbox(f"Cellule", options=list(Liste_allée.keys()), key=f"Cellule_{i}")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                allée = st.selectbox(f"Allée", options=Liste_allée[cellule], key=f"Allée_{i}")
            with col2:
                rangée = st.selectbox(f"Rangée", options=Liste_rangée, key=f"Rangée_{i}")
            with col3:
                niveau = st.selectbox(f"Niveau", options=Liste_niveau, key=f"Niveau_{i}")
            with col4:
                colonne = st.selectbox(f"Colonne", options=Liste_emplacement, key=f"Colonne_{i}")
            qr_infos.append({
                "Cellule": cellule,
                "Allée": allée,
                "Rangée": rangée,
                "Niveau": niveau,
                "Colonne": colonne
            })

        # --- Génération PDF ---
        if st.button("Générer le PDF A4"):
            pdf_buffer = BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=A4)
            page_width, page_height = A4

            if nb_qr_format == "Grand Format":
                margin_top = 10
                margin_bottom = 10
                margin_left = 10
            else:
                margin_top = 30
                margin_bottom = 30
                margin_left = 50

            usable_height = page_height - margin_top - margin_bottom
            rows_per_page = max(1, int((usable_height + spacing) // (frame_height + spacing)))
            items_per_page = rows_per_page * cols_per_row
            top_y = page_height - margin_top
            current_page = 0

            for idx, info in enumerate(qr_infos):
                page_index = idx // items_per_page
                if page_index > current_page:
                    c.showPage()
                    current_page = page_index

                idx_in_page = idx % items_per_page
                row = idx_in_page // cols_per_row
                col = idx_in_page % cols_per_row
                x = margin_left + col * (frame_width + spacing)
                y = top_y - (row * (frame_height + spacing)) - frame_height

                prefix = ""
                if info["Cellule"] in ["Ambiant", "Frais", "FL"]:
                    prefix = "MEAT_SPECIAL_HANDING-"
                elif info["Cellule"] == "Marée":
                    prefix = "FISH-"
                elif info["Cellule"] == "Surgelé":
                    prefix = "DEEP-FROZEN-"

                texte_affiche = f"{info['Allée']}-{info['Rangée']}-{info['Niveau']}-{info['Colonne']}"
                contenu_qr = prefix + texte_affiche

                # Couleur fond texte selon niveau
                if info["Niveau"] == "D1":
                    text_bg_color = "yellow"
                elif info["Niveau"] == "C1":
                    text_bg_color = "red"
                elif info["Niveau"] == "B1":
                    text_bg_color = "lightgreen"
                else:
                    text_bg_color = "white"

                combined = Image.new("RGB", (int(frame_width), int(frame_height)), "white")
                qr_width = int(frame_width * 0.55)
                qr_height = int(frame_height * 1.15)
                qr_offset = -20 if nb_qr_format == "Grand Format" else -10
                text_x0 = max(qr_width + qr_offset, 0)
                text_x1 = frame_width

                draw = ImageDraw.Draw(combined)
                draw.rectangle([(text_x0, 0), (text_x1, frame_height)], fill=text_bg_color)

                qr_img = qrcode.make(contenu_qr).convert("RGB")
                qr_img = qr_img.resize((qr_width, qr_height))
                combined.paste(qr_img, (-20, -20) if nb_qr_format == "Grand Format" else (-10, -10))

                try:
                    font = ImageFont.truetype("arialbd.ttf", font_size)
                except:
                    font = ImageFont.load_default()

                bbox = draw.textbbox((0, 0), texte_affiche, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                text_x = text_x0 + (frame_width - text_x0 - text_width) // 2
                text_y = (frame_height - text_height) // 2
                draw.text((text_x, text_y), texte_affiche, fill="black", font=font)
                draw.rectangle([(0, 0), (int(frame_width)-1, int(frame_height)-1)], outline="black", width=2)

                img_byte_arr = BytesIO()
                combined.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                c.drawImage(ImageReader(img_byte_arr), float(x), float(y), width=float(frame_width), height=float(frame_height))

            c.save()
            pdf_buffer.seek(0)
            st.download_button(
                label="📥 Télécharger PDF",
                data=pdf_buffer,
                file_name="QR_Codes_A4.pdf",
                mime="application/pdf"
            )

    elif option == 'QR Code MGB':
        st.subheader("MGB :")
        MGB = st.text_input("Entrer le numéro du MGB")

        if st.button("Générer le QR Code"):
            if not MGB.isdigit() or len(MGB) != 12:
                st.error("Le MGB doit être un chiffre de 12 digits.")
            else:
                qr_img = qrcode.make(MGB).convert("RGB")
                qr_img = qr_img.resize((250, 250))
                st.image(qr_img, caption="QR Code du MGB", use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    buffer = BytesIO()
                    qr_img.save(buffer, format="PNG")
                    buffer.seek(0)
                    st.download_button(
                        label="Télécharger le QR Code",
                        data=buffer,
                        file_name=f"QR_Code_{MGB}.png",
                        mime="image/png"
                    )
                with col2:
                    st.button("Effacer le QR Code")
                    MGB = ""
        
    elif option == 'EAN':
        st.subheader("EAN :")
        EAN_input = st.text_input("Entrer le code EAN")

        if st.button("Générer le code barre"):
                if not EAN_input.isdigit() or len(EAN_input) != 13:
                        st.error("Le code EAN doit être un chiffre de 13 digits.")
                else:
                        # Créer le code barre EAN13 avec ImageWriter
                        ean = EAN13(EAN_input, writer=ImageWriter())
                        
                        # Sauvegarder dans un buffer
                        buffer = BytesIO()
                        ean.write(buffer)
                        buffer.seek(0)

                        # Afficher le code barre dans Streamlit
                        st.image(buffer, caption=f"Code barre du EAN {EAN_input}", use_container_width=True)

                # Boutons pour téléchargement et effacer
                col1, col2 = st.columns(2)
                with col1:
                        st.download_button(
                        label="Télécharger le code barre",
                        data=buffer,
                        file_name=f"Code_barre_{EAN_input}.png",
                        mime="image/png"
                        )
                with col2:
                        if st.button("Effacer le code barre"):
                                st.experimental_rerun()



def tab_acteurs():   
    st.title("Réalisateurs")
    
def tab_realisateurs():
    st.title("Réalisateurs")

# Configuration des onglets
tabs = {
    "Accueil": tab_home,
    "QR Codes et Code Barre": tab_QR_Codes,
    "X2": tab_acteurs,
    "X3": tab_realisateurs
}

def main():
    st.sidebar.image(r"C:\Users\aurel\Desktop\dossier Id Logistics\logo IDL.jpg", use_container_width=True)
    st.sidebar.header("Navigation")
    selected_tab = st.sidebar.radio("", list(tabs.keys()))
    tabs[selected_tab]()

    # Sidebar images
    st.sidebar.image(r"C:\Users\aurel\Desktop\dossier Id Logistics\Logo_Metro.webp", use_container_width=True)
    
    # Sidebar color
    st.markdown("""
    <style>
        [data-testid=stSidebar] {
            background-color : #D9DDFF;
            background-size: cover;
        }
    </style>
    """, unsafe_allow_html=True)

    # Background image
    st.markdown("""
    <style>
        [data-testid="stAppViewContainer"]{
            background-color : #D9DDFF ;
            background-size: cover;
        }
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
