import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import math

st.title("Générateur de QR Codes")

# --- Listes ---
Liste_choix_Qr_code = ['Emplacement', 'MGB', 'Autre']
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
option = st.selectbox(
    'Choix type de QR Code à générer :',
    options=Liste_choix_Qr_code,
    index=None
)
if option == "Emplacement":
    # --- Choix du format ---
    nb_qr_format = st.radio("Choisir le format :", ["Grand Format", "Petit Format"])

    # --- Choix du nombre de QR Codes en fonction du format ---
    if nb_qr_format == "Grand Format":
        qr_count = st.selectbox("Nombre de QR Codes :", range(1, 4))  # 1 à 3
        cols_per_row = 1
        font_size = 48
        frame_width = A4[0] - 20  # largeur quasi pleine page
        frame_height = 273        # hauteur fixe
        spacing = 1            # espacement vertical/horizontal
    else:
        qr_count = st.selectbox("Nombre de QR Codes :", range(1, 11))  # 1 à 12
        cols_per_row = 2
        font_size = 20
        frame_width = (A4[0] - 130) / 2   # deux colonnes
        frame_height = 130               # hauteur fixe
        spacing = 30                      # espacement serré

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
        

    # --- Génération PDF (position par index: colonne/ligne, avec pagination) ---
    if st.button("Générer le PDF A4"):
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        page_width, page_height = A4

        # --- Marges ---
        if nb_qr_format == "Grand Format":
            margin_top = 10
            margin_bottom = 10
            margin_left = 10
            margin_right = 10
        else :
            margin_top = 30
            margin_bottom = 30
            margin_left = 50
            margin_right = 40
        # Calcul du nombre de lignes possibles par page (au moins 1 ligne)
        usable_height = page_height - margin_top - margin_bottom
        rows_per_page = max(1, int((usable_height + spacing) // (frame_height + spacing)))
        items_per_page = rows_per_page * cols_per_row

        # position de départ en haut de page (coordonnées pour calcul)
        top_y = page_height - margin_top

        current_page = 0

        for idx, info in enumerate(qr_infos):
            # Quand on change de page, on crée une nouvelle page
            page_index = idx // items_per_page
            if page_index > current_page:
                c.showPage()
                current_page = page_index

            # position dans la page courante
            idx_in_page = idx % items_per_page
            row = idx_in_page // cols_per_row
            col = idx_in_page % cols_per_row

            # calculer x,y pour ce row/col
            x = margin_left + col * (frame_width + spacing)
            # y = top_y - row*(frame_height + spacing) - frame_height
            y = top_y - (row * (frame_height + spacing)) - frame_height

            # --- Préfixe QR ---
            prefix = ""
            if info["Cellule"] in ["Ambiant", "Frais", "FL"]:
                prefix = "MEAT_SPECIAL_HANDING-"
            elif info["Cellule"] == "Marée":
                prefix = "FISH-"
            elif info["Cellule"] == "Surgelé":
                prefix = "DEEP-FROZEN-"

            texte_affiche = f"{info['Allée']}-{info['Rangée']}-{info['Niveau']}-{info['Colonne']}"
            contenu_qr = prefix + texte_affiche
        
            # --- Couleur fond texte selon niveau ---
            if info["Niveau"] == "D1":
                text_bg_color = "yellow"
            elif info["Niveau"] == "C1":
                text_bg_color = "red"
            elif info["Niveau"] == "B1":
                text_bg_color = "lightgreen"  # vert clair
            else:
                text_bg_color = "white"

            # --- Création image combinée ---
            combined = Image.new("RGB", (int(frame_width), int(frame_height)), "white")  # fond général blanc

            # --- Dimensions du QR code ---
            qr_width = int(frame_width * 0.55)
            qr_height = int(frame_height * 1.15)

            # calcul du décalage selon le format
            qr_offset = -20 if nb_qr_format == "Grand Format" else -10

            # zone texte colorée commence à la fin réelle du QR code
            text_x0 = qr_width + qr_offset
            text_x0 = max(text_x0, 0)  # pour éviter valeur négative
            text_x1 = frame_width

            draw = ImageDraw.Draw(combined)
            draw.rectangle([(text_x0, 0), (text_x1, frame_height)], fill=text_bg_color)

            # --- QR code ---
            qr_img = qrcode.make(contenu_qr).convert("RGB")
            qr_img = qr_img.resize((qr_width, qr_height))
            if nb_qr_format == "Grand Format":
                combined.paste(qr_img, (-20, -20))
            else:
                combined.paste(qr_img, (-10, -10))

            # --- Texte centré horizontalement et verticalement ---
            try:
                font = ImageFont.truetype("arialbd.ttf", font_size)  # Arial Bold
            except:
                font = ImageFont.load_default()

            # calcul dimensions texte
            bbox = draw.textbbox((0, 0), texte_affiche, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # centrer horizontalement dans la zone texte
        
            text_zone_width = frame_width - text_x0
            text_x = text_x0 + (text_zone_width - text_width) // 2


            # centrer verticalement
            text_y = (frame_height - text_height) // 2

            draw.text((text_x, text_y), texte_affiche, fill="black", font=font)

            # --- Encadré autour de toute l'étiquette ---
            draw.rectangle([(0, 0), (int(frame_width)-1, int(frame_height)-1)], outline="black", width=2)

            # Convertir en bytes pour reportlab
            img_byte_arr = BytesIO()
            combined.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            # Draw onto PDF à la position (x, y)
            c.drawImage(ImageReader(img_byte_arr), float(x), float(y), width=float(frame_width), height=float(frame_height))

        c.save()
        pdf_buffer.seek(0)

        st.download_button(
            label="📥 Télécharger PDF",
            data=pdf_buffer,
            file_name="QR_Codes_A4.pdf",
            mime="application/pdf"
        )

elif option == 'MGB' :
    # --- Gestion des options ---
    st.title("Générateur de QR Codes MGB")
    
    # --- boxe texte pour noté le MGB ---
    st.subheader("MGB :")
    MGB = st.text_input("Entrer le numéro du MGB")
    if st.button("Générer le QR Code"):
        # --- Vérification du format du MGB ---
        if not MGB.isdigit() or len(MGB)!= 12:
            st.error("Le MGB doit être un chiffre de 12 digits.")
            
        # --- Création du QR code ---
        qr_img = qrcode.make(MGB).convert("RGB")
        qr_img = qr_img.resize((250, 250))
        st.image(qr_img, caption="QR Code du MGB")       

        col1, col2 = st.columns(2)
        
        # --- bouton pour télécharger le QR code ---
        with col1:
            st.download_button(
            label="Télécharger le QR Code",
            data=BytesIO(qr_img.tobytes()),
            file_name=f"QR_Code_{MGB}.png",
            mime="image/png"
            )
        
        # --- bouton pour effacer le QR Code ---
        with col2:
            st.button("Effacer le QR Code")
            MGB = ""

        
        
        
        
    
        

