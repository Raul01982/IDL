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
import glob
import os
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from fpdf import FPDF
import io
from datetime import datetime




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
    Liste_emplacement = [str(i) for i in range(1, 13)]

    # Choix du type de QR Code
    option = st.selectbox('Choix type de QR Code ou Code Barre :', options= Liste_choix_Qr_code)
    
    if option == "Emplacement":
        # --- Choix du format ---
        nb_qr_format = st.radio("Choisir le format :", ["Grand Format", "Petit Format"])
        nb_qr_serie = st.radio("Choisir types :", ["Unités", "Série"])
        if nb_qr_serie == "Unités":
            if nb_qr_format == "Grand Format":
                qr_count = st.selectbox("Nombre de QR Codes :", range(1, 101))
                cols_per_row = 1
                font_size = 38
                frame_width = A4[0] - 20
                frame_height = 273
                spacing = 1
            else:
                qr_count = st.selectbox("Nombre de QR Codes :", range(1, 101))
                cols_per_row = 2
                font_size = 12
                frame_width = (A4[0] - 130) / 2
                frame_height = 130
                spacing = 30
        else :
            if nb_qr_format == "Grand Format":
                qr_count_serie = st.selectbox("Nombre de Série de QR Codes :", range(1, 11))
                qr_count = 101
                cols_per_row = 1
                font_size = 38
                frame_width = A4[0] - 20
                frame_height = 273
                spacing = 1
            else:
                qr_count_serie = st.selectbox("Nombre de Série de QR Codes :", range(1, 11))
                qr_count = 101
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
            for i in range(qr_count_serie):
                st.markdown(f"**Serie #{i+1}**")
                col1, col2, col3 = st.columns(3)
                # Sélections communes
                with col1:
                    cellule = st.selectbox("Cellule", options=list(Liste_allée.keys()), key=f"Cellule_{i}")
                with col2:
                    allée = st.selectbox("Allée", options=Liste_allée[cellule], key=f"Allée_{i}")
                with col3:
                    rangée = st.selectbox("Rangée", options=Liste_rangée, key=f"Rangée_{i}")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Choisi les Niveaux**")
                    niveau_start = st.selectbox("Niveau début", options=Liste_niveau[cellule], key=f"Niveau_start_{i}")
                    niveau_end = st.selectbox("Niveau fin", options=Liste_niveau[cellule], key=f"Niveau_end_{i}")
                with col3:
                    st.markdown(f"**Choisi les Colonnes**")
                    col_start = st.selectbox("Colonne début", options=Liste_emplacement, key=f"Colonne_start_{i}")
                    col_end = st.selectbox("Colonne fin", options=Liste_emplacement, key=f"Colonne_end_{i}")

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
                    prefix = "DEEP_FROZEN-"

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

        # Initialiser session_state
        if "MGB" not in st.session_state:
            st.session_state["MGB"] = ""

        user_input = st.text_input("Entrez le texte ou l'URL :", st.session_state["MGB"])

        # Bouton Générer
        if st.button("Générer le QR Code"):
            st.session_state["MGB"] = user_input  # on garde la valeur en mémoire

        # Affichage du QR Code si on a une valeur
        if st.session_state["MGB"]:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(st.session_state["MGB"])
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), caption="Votre QR Code")

            st.download_button(
                label="📥 Télécharger le QR Code",
                data=buf.getvalue(),
                file_name="qrcode.png",
                mime="image/png"
            )
            # Bouton Effacer
            if st.button("Effacer le QR Code"):
                st.session_state["MGB"] = ""
                st.rerun()




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



def Analyse_stock():   
    today = datetime.today().strftime("%d/%m/%Y")
    st.set_page_config(layout="wide")

    # --- Fonction pour charger les fichiers Excel ---
    @st.cache_data
    def load_data():
        # Dossier racine du projet
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # Définition des sous-dossiers
        dossier_mvt_stock = os.path.join(BASE_DIR, "Data", "Mvt_Stock")
        dossier_reception = os.path.join(BASE_DIR, "Data", "Historique_Réception")
        dossier_sorties = os.path.join(BASE_DIR,  "Data", "Historique_des_Sorties")
        dossier_ecart_stock = os.path.join(BASE_DIR, "Data", "Ecart_Stock")

        # Fonction utilitaire pour charger et concaténer tous les fichiers Excel d’un dossier
        def concat_excel_from_folder(folder, nom_dossier):
            fichiers = glob.glob(os.path.join(folder, "*.xlsx"))
            if not fichiers:
                return pd.DataFrame()
            else:
                return pd.concat((pd.read_excel(f) for f in fichiers), ignore_index=True)

        # Charger les fichiers Excel par dossier
        df_mvt_stock   = concat_excel_from_folder(dossier_mvt_stock, "Mvt_Stock")
        df_reception   = concat_excel_from_folder(dossier_reception, "Historique_Réception")
        df_sorties     = concat_excel_from_folder(dossier_sorties, "Historique_des_Sorties")
        
        files = [f for f in os.listdir(dossier_ecart_stock) if f.endswith(".xlsx")]

        # Si moins de 2 fichiers, on ne peut pas comparer
        if len(files) < 2:
            st.warning("Pas assez de fichiers pour comparer.")
        else:
            # Trier par date de modification
            files.sort(key=lambda x: os.path.getmtime(os.path.join(dossier_ecart_stock, x)))

            # Prendre les deux derniers fichiers
            file_prev = os.path.join(dossier_ecart_stock, files[-2])
            file_last = os.path.join(dossier_ecart_stock, files[-1])

            # Charger les fichiers Excel
            df_ecart_stock_prev = pd.read_excel(file_prev)
            df_ecart_stock_last = pd.read_excel(file_last)

        # Dossier où se trouvent les fichiers principaux
        base_path = Path(BASE_DIR) / "data"

        # Vérification des fichiers principaux
        file_article = base_path / "Article_€.xlsx"
        file_inventaire = base_path / "Inventory_21_09_2025.xlsx"

        if file_inventaire.exists():
            df_inventaire = pd.read_excel(file_inventaire, header=None)
        else:
            df_inventaire = pd.DataFrame()

        if file_article.exists():
            df_article_euros = pd.read_excel(file_article, header=None)
        else:
            df_article_euros = pd.DataFrame()

        return df_mvt_stock, df_reception, df_sorties, df_inventaire, df_ecart_stock_last, df_ecart_stock_prev, df_article_euros, file_last



    # --- Supprimer les colonnes dupliquées ---
    def remove_duplicate_columns(df):
        if not df.empty:
            return df.loc[:, ~df.columns.duplicated()]
        return df


    # --- Fonction de retraitement des données ---
    @st.cache_data
    def preprocess_data(df_ecart_stock_prev, df_ecart_stock_last, df_reception, df_sorties, df_inventaire, df_article_euros, df_mvt_stock):  

        # --- ECART STOCK ---
        df_ecart_stock_prev = df_ecart_stock_prev.drop(columns=['Var','Locations','MMS Stock (1 piece)','WMS Stock (1 piece)',
                                                    'Pick qty (1 piece)','Pick qty','Difference (1 piece)'], errors='ignore')
        df_ecart_stock_prev = df_ecart_stock_prev.rename(columns={
            "Article Name": "Désignation",
            "Article number (MGB)": "MGB_6",
            "MMS Stock": "MMS_Stock",
            "WMS Stock": "WMS_Stock",
            "Difference": "Difference_MMS-WMS"
        })
        df_ecart_stock_prev['MGB_6'] = df_ecart_stock_prev['MGB_6'].astype(str)

        for col in ["MMS_Stock","WMS_Stock","Difference_MMS-WMS"]:
            df_ecart_stock_prev[col] = pd.to_numeric(df_ecart_stock_prev[col], errors='coerce')

        df_ecart_stock_last = df_ecart_stock_last.drop(columns=['Var','Locations','MMS Stock (1 piece)','WMS Stock (1 piece)',
                                                    'Pick qty (1 piece)','Pick qty','Difference (1 piece)'], errors='ignore')
        df_ecart_stock_last = df_ecart_stock_last.rename(columns={
            "Article Name": "Désignation",
            "Article number (MGB)": "MGB_6",
            "MMS Stock": "MMS_Stock",
            "WMS Stock": "WMS_Stock",
            "Difference": "Difference_MMS-WMS"
        })
        df_ecart_stock_last['MGB_6'] = df_ecart_stock_last['MGB_6'].astype(str)

        colonnes_a_ajouter = ["Date_Dernier_Commentaire", "Commentaire"]

        for col in colonnes_a_ajouter:
            if col not in df_ecart_stock_last.columns:
                df_ecart_stock_last[col] = None
            else:
            # S'assurer que les valeurs manquantes restent NaN au lieu de réinitialiser
                df_ecart_stock_last[col] = df_ecart_stock_last[col].where(df_ecart_stock_last[col].notna(), None) 

        for col in ["MMS_Stock","WMS_Stock","Difference_MMS-WMS"]:
            df_ecart_stock_last[col] = pd.to_numeric(df_ecart_stock_last[col], errors='coerce')

        df_ecart_stock_last['Deja_Present'] = df_ecart_stock_last['MGB_6'].isin(df_ecart_stock_prev['MGB_6'])

        # --- INVENTAIRE ---
        # Split de la première colonne
        df_inventaire = df_inventaire[0].str.split(',', expand=True)

        # Optionnel : si tu sais que la première ligne contient les noms de colonnes
        df_inventaire.columns = df_inventaire.iloc[0]   # définit la première ligne comme header
        df_inventaire = df_inventaire[1:].reset_index(drop=True)

        df_inventaire = df_inventaire.rename(columns={
            "SubSys": "Ref_MERTO",
            "Initial Quantity": "Initial_Quantity",
            "Final Quantity": "Inventaire_Final_Quantity",
            "Difference (%)": "Difference_%"
        })
        df_inventaire['Inventaire_Final_Quantity'] = pd.to_numeric(df_inventaire['Inventaire_Final_Quantity'], errors='coerce')

        if 'MGB' in df_inventaire.columns:
            df_inventaire['MGB'] = df_inventaire['MGB'].astype(str)
            df_inventaire['MGB_6'] = df_inventaire['MGB'].str[:-6]

        remplacement = {"Å“": "œ", "Ã‚": "â", "Ã´": "ô", "Ã¨": "ë", "Ã¢": "â", "Ã§": "ç",
                        "Ãª": "ê", "Ã®": "î", "Ã©": "é", "Â°": "°", "Ã": "à", "¤": "", "«": "", "»": ""}
        for ancien, nouveau in remplacement.items():
            df_inventaire["Description"] = df_inventaire["Description"].str.replace(ancien, nouveau, regex=False)

        # --- MVT STOCK ---
        df_mvt_stock = df_mvt_stock.drop(columns=[
            'day_id','ste_nr','SGA','SSGA','colis_non_homogene','art_cont_gross','art_cont_gross_unit',
            'art_weight_gross_cust','type_mvt','qty_bb','pallet_homogene_count','unites_mvt_ccaf_pc','unites_mvt_ccvm_pc'
            ], errors='ignore')

        df_mvt_stock[["Date", "Heure"]] = df_mvt_stock["stk_mvt_datetime"].str.split(" ", expand=True)
        df_mvt_stock = df_mvt_stock.drop(columns=['stk_mvt_datetime'])
        df_mvt_stock["stk_chg_desc_details"] = df_mvt_stock["stk_chg_desc_details"].fillna("")
        df_mvt_stock["Code_Mouvement"] = df_mvt_stock["stk_chg_desc_details"].str.extract(r":(\d+)")
        df_mvt_stock["Intituler_Mouvement"] = df_mvt_stock["stk_chg_desc_details"].str.extract(r"::([^:]+)$")
        df_mvt_stock = df_mvt_stock.drop(columns=['stk_chg_desc_details'])
        df_mvt_stock["Code_Agent"] = df_mvt_stock["emp_email"].str.split(".", expand=True)[0]
        df_mvt_stock = df_mvt_stock.drop(columns=['emp_email'])
        df_mvt_stock[["prefix_emplacement", "Emplacement"]] = df_mvt_stock["location_nr"].str.split("-", n=1, expand=True)
        df_mvt_stock = df_mvt_stock.drop(columns=['location_nr'])

        df_mvt_stock = df_mvt_stock.rename(columns={
            "art_name": "Désignation",
            "Subsys": "Ref_MERTO",
            "art_weight_ind": "Au_Kg",
            "sscc": "SSCC",
            "qty": "Qty_Mouvement",
            "CCVM": "Conditionnement_Vente",
            "CCAF": "Conditionnement_Fournisseur",
            "stk_mvt_type": "Type_Mouvement",
            "stk_chg_desc": "Info_Mouvement",
            "cellule": "Cellule",
            'stk_sync_mms_ind':'Synchro_MMS',
            'MGB' : 'MGB_6',
            "art_mgb12": "MGB"
        })

        # Liste des colonnes dans l'ordre souhaité
        nouvel_ordre = ["Date", "Heure", "Code_Agent","MGB","MGB_6", "Désignation", "SV", "SA", "GA", "Ref_MERTO", "Au_Kg", "SSCC", "Type_Mouvement","Code_Mouvement",
                        "Intituler_Mouvement", "Info_Mouvement", 'Synchro_MMS',"Cellule", "Conditionnement_Vente", "Conditionnement_Fournisseur", "Cellule",'prefix_emplacement',"Emplacement",
                        "Qty_Mouvement"]

        # Réordonner les colonnes
        df_mvt_stock = df_mvt_stock[nouvel_ordre]

        # remplacer dans df_mvt_stock['Synchro_MMS'] le 1 par oui et le 0 par non :
        df_mvt_stock['Synchro_MMS'] = df_mvt_stock['Synchro_MMS'].replace({1: 'Oui', 0: 'Non'})

        df_mvt_stock['Type_Mouvement'] = df_mvt_stock['Type_Mouvement'].replace({
            'DELETE_STOCK': 'Modification_Stock',
            'EDIT_QUANTITY': 'Suppression_Stock',
            'CREATE_STOCK_FROM_MOBILE': 'Creation_Stock',
            'GR_SPLIT': 'Separation_Palette',
            'GR_MANUAL': 'Reception_Manuel'
        })
        df_mvt_stock['Info_Mouvement'] = df_mvt_stock['Info_Mouvement'].str.upper()
        df_mvt_stock['MGB_6'] = df_mvt_stock['MGB_6'].astype(str)
            
        # --- RECEPTION ---
        df_reception = df_reception.drop(columns=['ste_nr','SSGA','job_type_fr','job_id','job_begin_datetime','job_started_datetime',
            'var_nr','bdl_nr','SGA','art_weight_gross','art_weight_gross_cust','art_weight_net',
            'art_weight_unit','art_weight_ind.1','art_volume_net','art_volume_unit',
            'job_line_duration_minutes','job_qty_pc','job_qty_gross_avg','gr_qty','pallet_homogene_count',
            'colis_non_homogene','unites_recues_ccaf_pc','unites_recues_ccvm_pc'], errors='ignore')

        df_reception[["Date", "Heure"]] = df_reception["job_done_datetime"].str.split(",", expand=True)
        df_reception = df_reception.drop(columns=['job_done_datetime'])
        df_reception[["MGB","Désignation"]] = df_reception["art_name"].str.split("-",n=1, expand=True)
        df_reception = df_reception.drop(columns=['art_name'])
        df_reception["Code_Agent"] = df_reception["emp_upn"].str.split(".", expand=True)[0]
        df_reception = df_reception.drop(columns=['emp_upn'])
        
            # Renommer les colonnes
        df_reception = df_reception.rename(columns={
            "art_subsys": "Ref_MERTO",
            "CCVM": "Conditionnement_Vente",
            "CCAF": "Conditionnement_Fournisseur",
            "gr_date": "Date_Camion",
            "delivery_id": "N°_Camion",
            "job_qty": "Qty_Reception",
            "job_qty_ccaf": "Qty_Colis_Reception",
            "cellule": "Cellule",
            "art_weight_ind": "Au_Kg",
            "sscc": "SSCC",
            "type_recep": "Type_Recep"
        })

        #créer des MGB_6 dans tout les df :
        df_reception['MGB'] = df_reception['MGB'].astype(str)
        df_reception['MGB_6'] = df_reception['MGB'].str[:-6]

        # Liste des colonnes dans l'ordre souhaité
        nouvel_ordre = [
            "Date", "Heure", "Code_Agent", "MGB","MGB_6", "Désignation","SV", "SA", "GA",
            "Ref_MERTO", "Conditionnement_Vente", "Conditionnement_Fournisseur","Au_Kg", "SSCC",
            "Date_Camion", "N°_Camion", "Cellule",  "Type_Recep","Qty_Reception", "Qty_Colis_Reception"
        ]

        # Réordonner les colonnes
        df_reception = df_reception[nouvel_ordre]        

        # --- SORTIES ---
        df_sorties = df_sorties.drop(columns=[
            'sto_nr','ord_nr','ord_datetime','cus_sto_nr','cus_nr','ord_status_datetime','inv_date','art_cont_gross','art_cont_gross_unit',
            'ord_line_code','ord_qty_follow','art_pick_tool','art_pick_area','art_pick_id','type_UO','unites_pickees','nb_UO',
            'cre_date','upd_date','art_weight_gross_cust'
        ], errors='ignore')


        df_sorties[["Date", "Heure"]] = df_sorties["art_pick_datetime"].str.split(" ", expand=True)
        df_sorties = df_sorties.drop(columns=['art_pick_datetime'])
        df_sorties["Emplacement"] = df_sorties["art_pick_pos"].str.split("-", n=1, expand=True)[1]
        df_sorties = df_sorties.drop(columns=["art_pick_pos"])
        df_sorties["Code_Agent"] = df_sorties["art_picker_upn"].str.split(".", expand=True)[0]
        df_sorties = df_sorties.drop(columns=['art_picker_upn'])
        df_sorties['Qty/Article/Poids'] = pd.to_numeric(df_sorties['art_pick_qty'], errors='coerce')

        # Renommer les colonnes
        df_sorties = df_sorties.rename(columns={
            'dlv_date': "Date_de_livraison",
            'ord_qty' : "Qty_Commandé",
            "ord_picked_qty" : "Qty_Total_Préparé",
            "art_subsys" : "Ref_MERTO",
            "art_name" : "Désignation",
            "art_weight_ind": "Au_Kg",
            "cellule" : "Cellule"
        })

        df_sorties['MGB'] = df_sorties['art_mgb12'].astype(str)
        df_sorties['MGB_6'] = df_sorties['MGB'].str[:-6]

        # Liste des colonnes dans l'ordre souhaité
        nouvel_ordre_s = [
            "Date", "Heure", "Date_de_livraison", "Code_Agent", "MGB","MGB_6", "Désignation","SV",
            "Ref_MERTO","Au_Kg","Qty_Commandé","Qty_Total_Préparé","Qty/Article/Poids", "Cellule",  "Emplacement"
        ]

        # Réordonner les colonnes
        df_sorties = df_sorties[nouvel_ordre_s]

        # --- ARTICLES €---
        # Optionnel : si tu sais que la première ligne contient les noms de colonnes
        df_article_euros.columns = df_article_euros.iloc[0]   # définit la première ligne comme header
        df_article_euros = df_article_euros[1:].reset_index(drop=True)
        df_article_euros = df_article_euros.rename(columns= {"€ Unitaire" : "Prix_Unitaire"})

        # --- Supprimer les colonnes dupliquées après preprocess ---
        df_mvt_stock = remove_duplicate_columns(df_mvt_stock)
        df_reception = remove_duplicate_columns(df_reception)
        df_sorties = remove_duplicate_columns(df_sorties)
        df_inventaire = remove_duplicate_columns(df_inventaire)
        df_ecart_stock_last = remove_duplicate_columns(df_ecart_stock_last)
        df_ecart_stock_prev = remove_duplicate_columns(df_ecart_stock_prev)
        df_article_euros = remove_duplicate_columns(df_article_euros)

        return df_ecart_stock_prev, df_ecart_stock_last, df_reception, df_sorties, df_inventaire, df_article_euros, df_mvt_stock

# --- Fonctions utilitaires ---

    # Ajouter une ligne TOTAL
    def ajouter_totaux(df, colonnes_totaux):
        if df.empty:
            return {col: 0 for col in colonnes_totaux}
        return {col: df[col].sum() if col in df.columns else 0 for col in colonnes_totaux}

    # Colorer les lignes selon Synchro_MMS
    def color_rows(row):
        if row.get('Synchro_MMS') == 'Oui':
            return ['background-color: lightgreen']*len(row)
        else:
            return ['background-color: lightcoral']*len(row)

    # Mettre à jour la colonne Emplacement selon prefix_emplacement
    def update_emplacement(row):
        if row.get('prefix_emplacement') == 'IN':
            return row['prefix_emplacement'] + "-" + row['Emplacement']
        elif row.get('prefix_emplacement') == 'UNLOADING':
            return 'DECHARGEMENT'
        elif row.get('prefix_emplacement') == 'INSPECTION':
            return 'LITIGES-' + row['Emplacement']
        else:
            return row.get('Emplacement', '')

    # Ajouter prix et valeur totale
    def add_price_and_value(df_target, df_price, target_key, price_key, quantity_col, value_col='Valeur_du_Stock', price_col='Prix_Unitaire', display_in_streamlit=True):
        if df_target.empty or df_price.empty:
            df_target[value_col] = 0
            return df_target

        df_target[target_key] = df_target[target_key].astype(str)
        df_price[price_key] = df_price[price_key].astype(str)

        df_target = df_target.merge(
            df_price[[price_key, price_col]],
            left_on=target_key,
            right_on=price_key,
            how='left'
        )
        df_target = df_target.drop(columns=[price_key])
        df_target[value_col] = df_target[quantity_col] * df_target[price_col]

        if display_in_streamlit:
            st.dataframe(df_target.style.format({price_col: "{:.2f}", value_col: "{:.2f}"}))

        return df_target
    
    # --- Main Streamlit ---

    st.title("Analyse des écarts de stock")

    # Charger et retraiter les données
    df_mvt_stock, df_reception, df_sorties, df_inventaire, df_ecart_stock_prev, df_ecart_stock_last, df_article_euros,file_last = load_data()
    df_ecart_stock_prev, df_ecart_stock_last, df_reception, df_sorties, df_inventaire, df_article_euros, df_mvt_stock = preprocess_data(df_ecart_stock_prev, df_ecart_stock_last, df_reception, df_sorties, df_inventaire, df_article_euros, df_mvt_stock)
    # Mettre à jour les emplacements
    if not df_mvt_stock.empty:
        df_mvt_stock['Emplacement'] = df_mvt_stock.apply(update_emplacement, axis=1)
        df_mvt_stock = df_mvt_stock.drop(columns=['prefix_emplacement'], errors='ignore')
    
    # Ajouter valeurs des stocks
    df_inventaire = add_price_and_value(df_inventaire, df_article_euros, 'Ref_MERTO', 'ref', 'Inventaire_Final_Quantity', display_in_streamlit=False)
    df_reception = add_price_and_value(df_reception, df_article_euros, 'Ref_MERTO', 'ref', 'Qty_Reception', display_in_streamlit=False)
    df_sorties = add_price_and_value(df_sorties, df_article_euros, 'Ref_MERTO', 'ref', 'Qty/Article/Poids', display_in_streamlit=False)
    df_mvt_stock = add_price_and_value(df_mvt_stock, df_article_euros, 'Ref_MERTO', 'ref', 'Qty_Mouvement', display_in_streamlit=False)

    # Créer des mappings MGB_6 -> € Unitaire depuis les 3 tableaux
    mapping_inventaire = df_inventaire[['MGB_6', 'Prix_Unitaire']].drop_duplicates()
    mapping_reception = df_reception[['MGB_6', 'Prix_Unitaire']].drop_duplicates()
    mapping_mvt = df_mvt_stock[['MGB_6', 'Prix_Unitaire']].drop_duplicates()

    # Concaténer les mappings pour faire un mapping global
    mapping_global = pd.concat([mapping_inventaire, mapping_reception, mapping_mvt])

    # Supprimer les doublons en gardant le premier (priorité inventaire > réception > mouvements)
    mapping_global = mapping_global.drop_duplicates(subset='MGB_6', keep='first')

    # Créer des mappings MGB_6 -> Au_Kg depuis les 3 tableaux
    mapping_aukg_reception = df_reception[['MGB_6', 'Au_Kg']].drop_duplicates()
    mapping_aukg_mvt = df_mvt_stock[['MGB_6', 'Au_Kg']].drop_duplicates()
    mapping_aukg_sorties = df_sorties[['MGB_6', 'Au_Kg']].drop_duplicates()

    # Concaténer les mappings pour faire un mapping global
    mapping_aukg_global = pd.concat([mapping_aukg_reception, mapping_aukg_mvt, mapping_aukg_sorties])

    # Supprimer les doublons en gardant le premier (priorité réception > mouvements > sorties)
    mapping_aukg_global = mapping_aukg_global.drop_duplicates(subset='MGB_6', keep='first')

    # Ajouter la colonne Au_Kg dans df_ecart_stock
    df_ecart_stock = df_ecart_stock_last.merge(
        mapping_aukg_global,
        on='MGB_6',
        how='left'
    )

    # Ajouter le prix dans df_ecart_stock
    df_ecart_stock = df_ecart_stock.merge(
        mapping_global,
        on='MGB_6',
        how='left'
    )
    # Ajouter le valeur de la differance 
    df_ecart_stock['Valeur_Difference'] = df_ecart_stock['Prix_Unitaire'] * df_ecart_stock['Difference_MMS-WMS']
    # Convertir en numérique, les valeurs invalides deviennent NaN
    df_ecart_stock['Valeur_Difference'] = pd.to_numeric(df_ecart_stock['Valeur_Difference'], errors='coerce')

    # Maintenant tu peux arrondir
    df_ecart_stock['Valeur_Difference'] = df_ecart_stock['Valeur_Difference'].round(2)

    # Liste des colonnes dans l'ordre souhaité
    nouvel_ordre = ["MGB_6", "Désignation", "MMS_Stock", "WMS_Stock", "Difference_MMS-WMS", 'Au_Kg',"Deja_Present",'Prix_Unitaire','Valeur_Difference', "Date_Dernier_Commentaire", "Commentaire"]

    # Réordonner les colonnes
    df_ecart_stock = df_ecart_stock[nouvel_ordre]

    # Afficher le tableau des écarts

    st.subheader("Tableau des écarts")

    # --- Colonnes pour les 4 premiers filtres ---
    cols = st.columns(5)

    # --- Options de filtrage ---
    options_1 = ["Toutes", "Positives", "Négatives", "Zéro"]
    options_2 = ["Tous", "Oui", "Non"]
    options_3 = ["Toutes","<5","5-10","10-15","15-20","20+"]
    options_4 = ["Toutes", "Positives", "Zéro"]
    options_5 = ["Toutes", "Positives", "Négatives"]

    filtres = {
        "WMS_Stock": {"col": cols[1], "options": options_1, "type": "numeric"},
        "MMS_Stock": {"col": cols[0], "options": options_4, "type": "numeric"},
        "Au_Kg": {"col": cols[2], "options": options_2, "type": "bool"},
        "Difference_MMS-WMS_Valeur": {"col": cols[3], "options": options_3, "type": "range", "df_col": "Difference_MMS-WMS"},
        "Difference_MMS-WMS_+/-": {"col": cols[4], "options": options_5, "type": "numeric", "df_col": "Difference_MMS-WMS"},
        }


    # --- Initialiser session_state pour chaque filtre ---
    for key, filt in filtres.items():
        state_key = f"filter_{key}"
        if state_key not in st.session_state:
            st.session_state[state_key] = filt["options"][0]

    # --- Bouton Réinitialiser les 4 premiers filtres ---
    def reset_filters():
        for key in filtres.keys():
            st.session_state[f"filter_{key}"] = filtres[key]["options"][0]

    
    # --- Selectboxes pour les 4 premiers filtres (utiliser key pour forcer la lecture depuis session_state) ---
    for key, filt in filtres.items():
        state_key = f"filter_{key}"
        filt["value"] = filt["col"].selectbox(
            key.replace("_", " "),
            filt["options"],
            index=filt["options"].index(st.session_state[state_key]),
            key=state_key  # clé obligatoire pour que la réinitialisation fonctionne
        )

    cols[0].button("Réinitialiser les filtres", on_click=reset_filters)

    # --- Filtre Deja_Present sous le bouton ---
    deja_present_options = ["Tous", "Oui", "Non"]
    if "filter_Deja_Present" not in st.session_state:
        st.session_state["filter_Deja_Present"] = deja_present_options[0]

    filter_choice_6 = cols[0].selectbox(
        "Deja_Present",
        deja_present_options,
        index=deja_present_options.index(st.session_state["filter_Deja_Present"]),
        key="filter_Deja_Present"
    )

    # --- Appliquer les filtres ---
    df_filtered = df_ecart_stock.copy()

    for key, filt in filtres.items():
        val = st.session_state[f"filter_{key}"]
        df_col = filt.get("df_col", key)  # si df_col n’existe pas, on garde key

        if filt["type"] == "numeric":
            if val == "Positives":
                df_filtered = df_filtered[df_filtered[df_col] > 0]
            elif val == "Négatives":
                df_filtered = df_filtered[df_filtered[df_col] < 0]
            elif val == "Zéro":
                df_filtered = df_filtered[df_filtered[df_col] == 0]

        elif filt["type"] == "range":
            ranges = {
                "<5": (0, 5),
                "5-10": (5, 10),
                "10-15": (10, 15),
                "15-20": (15, 20),
                "20+": (20, float("inf"))
            }
            if val in ranges:
                low, high = ranges[val]
                df_filtered = df_filtered[(df_filtered[df_col].abs() >= low) & (df_filtered[df_col].abs() < high)]

    # --- Filtre Deja_Present ---
    map_bool = {"Tous": None, "Oui": True, "Non": False}
    val_bool = map_bool[st.session_state["filter_Deja_Present"]]
    if val_bool is not None:
        df_filtered = df_filtered[df_filtered["Deja_Present"].astype(bool) == val_bool]

    # --- Affichage ---
    st.dataframe(df_filtered.style.format({
        '€_Unitaire': "{:.2f}",
        'Valeur_Difference': "{:.2f}"
    }))



    col1, col2 = st.columns(2)
    # compter le nombre de ligne :
    col1.subheader(f"Nombre de lignes : {len(df_filtered)}")

    # valeur total :
    total_value = df_filtered['Valeur_Difference'].sum()
    col2.subheader(f"Valeur total des écarts : {total_value:.2f} €")

    # separation :
    st.divider()

    # Menu déroulant MGB_6
    col1, col2 = st.columns(2)
    mgb_list = df_filtered['MGB_6'].dropna().unique() if not df_filtered.empty else []
    mgb_selected = col1.selectbox("Choisir un MGB", mgb_list)

    # Filtrer les DataFrames
    stock_info = df_ecart_stock[df_ecart_stock['MGB_6'] == mgb_selected]
    inventaire_info = df_inventaire[df_inventaire['MGB_6'] == mgb_selected]
    mvt_stock_info = df_mvt_stock[df_mvt_stock['MGB_6'] == mgb_selected]
    reception_info = df_reception[df_reception['MGB_6'] == mgb_selected]
    sorties_info = df_sorties[df_sorties['MGB_6'] == mgb_selected]

    # Calcul des totaux
    totaux_stock = ajouter_totaux(stock_info, ["MMS_Stock","WMS_Stock","Difference_MMS-WMS","Valeur_Difference"])
    totaux_inventaire = ajouter_totaux(inventaire_info, ["Inventaire_Final_Quantity"])
    totaux_mvt_stock = ajouter_totaux(mvt_stock_info, ["Qty_Mouvement"])
    totaux_reception = ajouter_totaux(reception_info, ["Qty_Reception"])
    totaux_sorties = ajouter_totaux(sorties_info, ["Qty/Article/Poids"])

    stock_theorique = (
        totaux_inventaire.get('Inventaire_Final_Quantity', 0)
        + totaux_mvt_stock.get('Qty_Mouvement', 0)
        + totaux_reception.get('Qty_Reception', 0)
        - totaux_sorties.get('Qty/Article/Poids', 0)
    )

    # Affichage des métriques
    st.subheader(f"Infos pour : {mgb_selected} - {stock_info.iloc[0]['Désignation'] if not stock_info.empty else ''}")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("MMS Stock", totaux_stock.get("MMS_Stock", 0))
    col2.metric("WMS Stock", totaux_stock.get("WMS_Stock", 0))
    col4.metric("Difference MMS-WMS", totaux_stock.get("Difference_MMS-WMS", 0))
    col5.metric("Valeur Difference €", totaux_stock.get("Valeur_Difference", 0),"€")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Inventaire", totaux_inventaire.get("Inventaire_Final_Quantity", 0))
    col2.metric("Mouvements", totaux_mvt_stock.get("Qty_Mouvement", 0))
    col3.metric("Réceptions", totaux_reception.get("Qty_Reception", 0))
    col4.metric("Sorties", totaux_sorties.get("Qty/Article/Poids", 0))
    col5.metric("Stock théorique", round(stock_theorique, 2))

    # Affichage des tableaux détaillés
    st.subheader("Tableau Inventaire")
    st.dataframe(inventaire_info, use_container_width=True)

    st.subheader("Tableau des mouvements de stock")
    st.dataframe(mvt_stock_info.style.apply(color_rows, axis=1), use_container_width=True)

    st.subheader("Tableau des réceptions")
    st.dataframe(reception_info, use_container_width=True)

    st.subheader("Tableau des sorties")
    st.dataframe(sorties_info, use_container_width=True)

    # separation :
    st.divider()


    # 1️⃣ Initialisation dans la session
    if "df_comments" not in st.session_state:
        if os.path.exists(file_last):
            df_existing = pd.read_excel(file_last)

            # Détecter la colonne MGB
            if "MGB_6" in df_existing.columns:
                df_existing['MGB_6'] = df_existing['MGB_6'].astype(str)
            elif "Article number (MGB)" in df_existing.columns:
                df_existing['MGB_6'] = df_existing["Article number (MGB)"].astype(str)
                # Supprimer l'ancienne colonne
                df_existing = df_existing.drop(columns="Article number (MGB)")
            else:
                st.warning("Impossible de trouver la colonne MGB. Création d'une colonne vide.")
                df_existing['MGB_6'] = ''

            # Assurer que df_ecart_stock_last a aussi MGB_6
            if 'MGB_6' not in df_ecart_stock_last.columns and "Article number (MGB)" in df_ecart_stock_last.columns:
                df_ecart_stock_last['MGB_6'] = df_ecart_stock_last["Article number (MGB)"].astype(str)
            df_ecart_stock_last['MGB_6'] = df_ecart_stock_last['MGB_6'].astype(str)

            # Colonnes à fusionner si elles existent dans df_existing
            cols_to_merge = [col for col in ['Commentaire', 'Date_Dernier_Commentaire'] if col in df_existing.columns]

            if cols_to_merge:
                # Fusionner avec df_ecart_stock_last
                df_merged = df_ecart_stock_last.merge(
                    df_existing[['MGB_6'] + cols_to_merge],
                    on='MGB_6',
                    how='left',
                    suffixes=('_new', '_old')
                )

                # Remplacer les valeurs existantes par les nouvelles si elles ne sont pas NaN
                for col in cols_to_merge:
                    df_merged[col] = df_merged[f'{col}_new'].combine_first(df_merged.get(f'{col}_old'))

                # Supprimer les colonnes intermédiaires
                df_merged = df_merged.drop(
                    columns=[f'{col}_new' for col in cols_to_merge] + 
                            [f'{col}_old' for col in cols_to_merge if f'{col}_old' in df_merged.columns]
                )

                st.session_state.df_comments = df_merged
            else:
                # Si pas de colonnes Commentaire/Date, on copie simplement
                st.session_state.df_comments = df_ecart_stock_last.copy()
        else:
            st.session_state.df_comments = df_ecart_stock_last.copy()


    # 2️⃣ Ajouter un commentaire
    st.title(f"Ajouter un commentaire à la ligne {mgb_selected} - {stock_info.iloc[0]['Désignation'] if not stock_info.empty else ''} ")

    commentaire = st.text_area("Écrire votre commentaire :")

    if st.button("Ajouter le commentaire"):
        df_temp = st.session_state.df_comments
        index = df_temp.index[df_temp["MGB_6"] == mgb_selected][0]
        today = datetime.today().strftime("%d-%m-%Y")

        # Mise à jour en mémoire
        df_temp.at[index, "Commentaire"] = commentaire
        df_temp.at[index, "Date_Dernier_Commentaire"] = today
        st.session_state.df_comments = df_temp

        st.success(f"✅ Commentaire ajouté pour {mgb_selected} - {stock_info.iloc[0]['Désignation']} avec la date {today} !")
    # --------------------------
    # 📄 Classe PDF personnalisée
    # --------------------------
    class PDF(FPDF):
        def __init__(self, headers, col_widths):
            super().__init__(orientation="L", unit="mm", format="A4")
            self.headers = headers
            self.col_widths = col_widths
            

        def header(self):
            self.set_font("Arial", "B", 14)
            self.cell(0, 10, f"Rapport Ecart {today} ", ln=True, align="C")
            self.ln(5)

            # En-têtes du tableau
            self.set_font("Arial", "B", 10)
            for i, col in enumerate(self.headers):
                self.cell(self.col_widths[i], 10, col, border=1, align="C")
            self.ln()

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.cell(0, 10, f"Page {self.page_no()}", align="C")

    # 3️⃣ Générer le PDF et sauvegarder Excel en même temps
    if st.button("Générer le PDF et sauvegarder Excel"):
        df_for_pdf = st.session_state.df_comments.fillna("")  # récupération de la copie à jour

        # 🔹 Export Excel
        df_for_pdf.to_excel(file_last, index=False)

        # 🔹 Génération PDF
        col_widths = [80, 20, 20, 40, 110]
        headers = ["Désignation", "MGB_6", "Difference", "Date Commentaire", "Commentaire"]

        pdf = PDF(headers, col_widths)
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        pdf.set_font("Arial", "", 9)

        for _, row in df_for_pdf.iterrows():
            pdf.cell(col_widths[0], 8, str(row["Désignation"]), border=1)
            pdf.cell(col_widths[1], 8, str(row["MGB_6"]), border=1, align="C")
            pdf.cell(col_widths[2], 8, str(round(row["Difference_MMS-WMS"], 2)), border=1, align="C")
            pdf.cell(col_widths[3], 8, str(row["Date_Dernier_Commentaire"]), border=1, align="C")

            x_before = pdf.get_x()
            y_before = pdf.get_y()
            pdf.multi_cell(col_widths[4], 8, str(row["Commentaire"]), border=1)
            y_after = pdf.get_y()
            pdf.set_xy(x_before + col_widths[4], y_before)
            pdf.ln(max(8, y_after - y_before))

        # Export PDF
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)

        st.download_button(
            label="📥 Télécharger le PDF",
            data=pdf_buffer,
            file_name="rapport_utilisateurs.pdf",
            mime="application/pdf"
        )

        st.success("✅ PDF généré et fichier Excel mis à jour !")

    
def tab_realisateurs():
    st.title("Réalisateurs")

# Configuration des onglets
tabs = {
    "Accueil": tab_home,
    "QR Codes et Code Barre": tab_QR_Codes,
    "Analyse Stock": Analyse_stock,
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
