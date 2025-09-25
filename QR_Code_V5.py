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
    Liste_choix_Qr_code = ['Vide','Emplacement', 'QR Code MGB','Autres QR Codes', 'EAN']
    Liste_allée = {
        "Ambiant": ['1','2','3','4','5','6','7','8','9','10','11','12'],
        "Frais": ['19','20','21','22','23','24','25','26'],
        "FL": ['30','31','32','33'],
        "Surgelé": ['38','39','40','41','42','43'],
        "Marée": ['50','51','52','53']
    }
    Liste_rangée = [str(i) for i in range(1, 41)]
    Liste_niveau = {
        "Ambiant": ['A1','A2','A3','A4','B1','C1','D1'],
        "Frais": ['A1','A2','A3','A4','B1'],
        "FL": ['A1','A2','A3','A4','B1'],
        "Surgelé": ['A1','A2','A3','A4','B1','C1','D1'],
        "Marée": ['A1','A2','A3','A4']
    }
    Liste_emplacement = [str(i) for i in range(1, 11)]

    # Choix du type de QR Code
    option = st.selectbox('Choix type de QR Code ou Code Barre :', options= Liste_choix_Qr_code)
    
    if option == "Emplacement":
        # --- Choix du format ---
        nb_qr_format = st.radio("Choisir le format :", ["Grand Format", "Petit Format"])
        nb_qr_serie = st.radio("Choisir types :", ["Unités", "Série"])
        if nb_qr_serie == "Unités":
            if nb_qr_format == "Grand Format":
                qr_count = st.selectbox("Nombre de QR Codes :", range(1, 4))  # 1 à 3
                cols_per_row = 1
                font_size = 38
                frame_width = A4[0] - 20
                frame_height = 273
                spacing = 1
            else:
                qr_count = st.selectbox("Nombre de QR Codes :", range(1, 11))  # 1 à 10
                cols_per_row = 2
                font_size = 12
                frame_width = (A4[0] - 130) / 2
                frame_height = 130
                spacing = 30
        else :
            if nb_qr_format == "Grand Format":
                qr_count = 3
                cols_per_row = 1
                font_size = 38
                frame_width = A4[0] - 20
                frame_height = 273
                spacing = 1
            else:
                qr_count = 10
                cols_per_row = 2
                font_size = 12
                frame_width = (A4[0] - 130) / 2
                frame_height = 130
                spacing = 30

        # --- Définir le chemin de la police ---
        FONT_PATH = Path(__file__).parent / "fonts" / "DejaVuSans-Bold.ttf"
        try:
            font = ImageFont.truetype(str(FONT_PATH), font_size)
        except Exception as e:
            st.error(f"Erreur police: {e}")
            font = ImageFont.load_default()

        # --- Sélection des QR Codes ---
        st.subheader("Choisir les QR Codes")
        qr_infos = []

        if nb_qr_serie == "Unités":
            for i in range(qr_count):
                st.markdown(f"**QR Code #{i+1}**")
                cellule = st.selectbox(f"Cellule", options=list(Liste_allée.keys()), key=f"Cellule_{i}")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    allée = st.selectbox(f"Allée", options=Liste_allée[cellule], key=f"Allée_{i}")
                with col2:
                    rangée = st.selectbox(f"Rangée", options=Liste_rangée, key=f"Rangée_{i}")
                with col3:
                    niveau = st.selectbox(f"Niveau", options=Liste_niveau[cellule], key=f"Niveau_{i}")
                with col4:
                    colonne = st.selectbox(f"Colonne", options=Liste_emplacement, key=f"Colonne_{i}")
                qr_infos.append({
                    "Cellule": cellule,
                    "Allée": allée,
                    "Rangée": rangée,
                    "Niveau": niveau,
                    "Colonne": colonne
                })
        
        else:
            col1, col2, col3 = st.columns(3)
            # Sélections communes
            with col1:
                cellule = st.selectbox("Cellule", options=list(Liste_allée.keys()), key="Cellule")
            with col2:
                allée = st.selectbox("Allée", options=Liste_allée[cellule], key="Allée")
            with col3:
                rangée = st.selectbox("Rangée", options=Liste_rangée, key="Rangée")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Choisi les Niveaux**")
                niveau_start = st.selectbox("Niveau début", options=Liste_niveau[cellule], key="Niveau_start")
                niveau_end = st.selectbox("Niveau fin", options=Liste_niveau[cellule], key="Niveau_end")
            with col3:
                st.markdown(f"**Choisi les Colonnes**")
                col_start = st.selectbox("Colonne début", options=Liste_emplacement, key="Colonne_start")
                col_end = st.selectbox("Colonne fin", options=Liste_emplacement, key="Colonne_end")

            # Construire les plages
            niveaux = Liste_niveau[cellule]
            colonnes = Liste_emplacement

            try:
                start_idx_niv = niveaux.index(niveau_start)
                end_idx_niv = niveaux.index(niveau_end)
                start_idx_col = colonnes.index(col_start)
                end_idx_col = colonnes.index(col_end)

                niveaux_range = niveaux[min(start_idx_niv, end_idx_niv): max(start_idx_niv, end_idx_niv)+1]
                colonnes_range = colonnes[min(start_idx_col, end_idx_col): max(start_idx_col, end_idx_col)+1]

                total_etiquettes = len(niveaux_range) * len(colonnes_range)

                if total_etiquettes > qr_count:
                    st.error(f"⚠️ Trop d’étiquettes ({total_etiquettes}), maximum autorisé : {qr_count}")
                else:
                    for niv in niveaux_range:
                        for col in colonnes_range:
                            qr_infos.append({
                                "Cellule": cellule,
                                "Allée": allée,
                                "Rangée": rangée,
                                "Niveau": niv,
                                "Colonne": col
                            })
                            

            except ValueError:
                st.error("Erreur : les valeurs choisies ne sont pas dans les listes disponibles.")

        # --- Génération PDF ---
        if st.button("Générer le PDF A4"):
            pdf_buffer = BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=A4)
            page_width, page_height = A4

            margin_top = 10 if nb_qr_format == "Grand Format" else 30
            margin_bottom = 10 if nb_qr_format == "Grand Format" else 30
            margin_left = 10 if nb_qr_format == "Grand Format" else 50

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

                # Préfixe selon cellule
                prefix = ""
                if info["Cellule"] in ["Ambiant", "Frais", "FL"]:
                    prefix = "MEAT_SPECIAL_HANDLING-"
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
                if nb_qr_format == "Grand Format" :
                    qr_width = int(frame_width * 0.55)
                    qr_height = int(frame_height * 1.15)
                else :
                    qr_width = int(frame_width * 0.62)
                    qr_height = int(frame_height * 1.15)
                qr_offset = -20 if nb_qr_format == "Grand Format" else -10
                text_x0 = max(qr_width + qr_offset, 0)
                text_x1 = frame_width

                draw = ImageDraw.Draw(combined)
                draw.rectangle([(text_x0, 0), (text_x1, frame_height)], fill=text_bg_color)

                qr_img = qrcode.make(contenu_qr).convert("RGB")
                qr_img = qr_img.resize((qr_width, qr_height))
                combined.paste(qr_img, (-20, -20) if nb_qr_format == "Grand Format" else (-10, -10))

                # Utiliser la police embarquée pour Render
                try:
                    font = ImageFont.truetype(str(FONT_PATH), font_size)
                except Exception as e:
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
        
        # Initialisation des états si pas encore définis
        if 'MGB' not in st.session_state:
            st.session_state['MGB'] = ""
        if 'confirm_11' not in st.session_state:
            st.session_state['confirm_11'] = False

        st.subheader("MGB :")
        
        st.session_state['MGB'] = st.text_input(
            "Entrer le numéro du MGB",
            value=st.session_state.get('MGB', ''),
            key="mgb_input"
        )


        def generate_qr(MGB):
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
                if st.button("Effacer le QR Code"):
                    st.session_state['MGB'] = ""
                    st.session_state['confirm_11'] = False

        # Bouton principal
        if st.button("Générer le QR Code"):
            MGB = st.session_state['MGB']
            if not MGB.isdigit():
                st.error("Le MGB doit être un nombre.")
            elif len(MGB) == 12:
                generate_qr(MGB)
            elif len(MGB) == 11:
                st.warning("Es-tu sûr que ton MGB n'a pas 12 chiffres ?")
                st.session_state['confirm_11'] = True
            else:
                st.error("Le MGB doit avoir 11 ou 12 chiffres.")

        # Si confirmation pour 11 chiffres
        if st.session_state['confirm_11']:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Oui, générer le QR Code"):
                    generate_qr(st.session_state['MGB'])
                    st.session_state['confirm_11'] = False
            with col2:
                if st.button("Non, corriger le MGB"):
                    st.info("Merci de remplir le champ correctement.")
                    st.session_state['confirm_11'] = False
    
    
    elif option == 'Autres QR Codes':

        st.title("Autres QR Codes")

        # Champ texte pour saisir l'URL ou le texte
        user_input = st.text_input("Entrez le texte ou l'URL à encoder :")

        if user_input:
            # Générer le QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(user_input)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Afficher le QR code dans Streamlit
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), caption="Votre QR Code")

            # Bouton de téléchargement
            st.download_button(
                label="📥 Télécharger le QR Code",
                data=buf.getvalue(),
                file_name="qrcode.png",
                mime="image/png"
            )



    elif option == 'EAN':
        st.subheader("EAN :")
        
        EAN_input = st.text_input("Entrez un code EAN (13 chiffres)")

        if st.button("Générer le Code Barre"): 
            if not EAN_input.isdigit() or len(EAN_input) != 13:
                # Cas invalide → on sort ici, aucune autre ligne ne s'exécute
                st.error("Le code EAN doit être un nombre de 13 chiffres.")
            
            else:
                try:
                    # Cas valide → génération du code-barres
                    ean = EAN13(EAN_input, writer=ImageWriter())

                    buffer = BytesIO()
                    ean.write(buffer)
                    buffer.seek(0)

                    st.image(buffer, caption=f"Code barre du EAN {EAN_input}", use_container_width=True)

                except Exception as e:
                    # Ici on intercepte toute autre erreur
                    st.error("Une erreur est survenue lors de la génération du code barre.")

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
    
    IMAGE_PATH_1 = Path(__file__).parent / "images" / "logo_IDL.jpg"
    st.sidebar.image(str(IMAGE_PATH_1), use_container_width=True)
    st.sidebar.header("Navigation")
    selected_tab = st.sidebar.radio("", list(tabs.keys()))
    tabs[selected_tab]()

    # Sidebar images
    
    IMAGE_PATH_2 = Path(__file__).parent / "images" / "Logo_Metro.webp"
    st.sidebar.image(str(IMAGE_PATH_2), use_container_width=True)
    
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
