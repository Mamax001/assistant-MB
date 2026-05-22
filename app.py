import streamlit as st
import requests
import tempfile
import os
import time
from google import genai

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Assistant MDB", layout="wide", page_icon="🏗️")
st.title("🏗️ Assistant Marchand de Biens")

# --- RÉCUPÉRATION SÉCURISÉE DES CLÉS (STREAMLIT SECRETS) ---
try:
    api_key_gemini = st.secrets["GEMINI_API_KEY"]
    notion_token = st.secrets["NOTION_TOKEN"]
    database_id = st.secrets["NOTION_DATABASE_ID"]
except KeyError as e:
    st.error(f"Erreur : La clé {e} est manquante dans les Secrets de Streamlit.")
    st.stop()

# --- ONGLETS ---
tab1, tab2, tab3 = st.tabs(["1. Urbanisme (PLU)", "2. Risques Naturels", "3. Bilan Financier & Notion"])

# --- MODULE 1 : ANALYSE PLU MULTI-FICHIERS ---
with tab1:
    st.header("Analyse de PLU avec Gemini")
    
    # Correction : accept_multiple_files est bien activé ici
    fichiers_pdf = st.file_uploader("Téléverse un ou plusieurs fichiers PLU (PDF)", type="pdf", accept_multiple_files=True)
    
    if st.button("Analyser les documents") and fichiers_pdf:
        client = genai.Client(api_key=api_key_gemini)
        
        for fichier_pdf in fichiers_pdf:
            st.subheader(f"📄 Analyse de : {fichier_pdf.name}")
            
            with st.spinner(f"Lecture de {fichier_pdf.name}..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(fichier_pdf.getvalue())
                    tmp_path = tmp_file.name

                try:
                    # Téléversement brut
                    fichier_upload = client.files.upload(file=tmp_path)
                    
                    # Sécurité : On attend activement que Google ait fini de traiter le gros fichier
                    statut = client.files.get(name=fichier_upload.name)
                    while statut.state.name == "PROCESSING":
                        time.sleep(2)
                        statut = client.files.get(name=fichier_upload.name)
                    
                    if statut.state.name != "ACTIVE":
                        st.error(f"Le fichier {fichier_pdf.name} n'a pas pu être traité.")
                        continue
                    
                    prompt = """
                    Agis comme un expert en urbanisme. Analyse ce document (PLU) et réponds avec précision :
                    1. Quelle est l'emprise au sol maximale (CES) autorisée ?
                    2. Quelle est la hauteur maximale autorisée au faîtage ?
                    3. Est-il possible de surélever un bâtiment existant ?
                    4. Combien de places de stationnement sont exigées pour créer un logement ?
                    Cite les numéros d'articles du PLU qui justifient tes réponses.
                    """
                    
                    # Appel corrigé pour la nouvelle API
                    reponse = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[fichier_upload, prompt]
                    )
                    
                    st.success(f"Analyse de {fichier_pdf.name} terminée")
                    st.write(reponse.text)
                    st.divider()
                    
                    client.files.delete(name=fichier_upload.name)
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse : {e}")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

# --- MODULE 2 : RISQUES (CORRIGÉ) ---
with tab2:
    st.header("Vérification des Risques Naturels")
    adresse = st.text_input("Saisis l'adresse exacte du projet")
    
    if st.button("Vérifier les risques") and adresse:
        with st.spinner("Recherche des données géographiques..."):
            try:
                res_adresse = requests.get(f"https://api-adresse.data.gouv.fr/search/?q={adresse}&limit=1").json()
                if not res_adresse.get('features'):
                    st.error("Adresse introuvable.")
                else:
                    lon, lat = res_adresse['features'][0]['geometry']['coordinates']
                    st.write(f"**Coordonnées GPS :** {lat}, {lon}")
                    
                    url_georisques = f"https://georisques.gouv.fr/api/v1/gaspar/risques?latlon={lon},{lat}&rayon=1000"
                    res_georisques = requests.get(url_georisques).json()
                    
                    if res_georisques.get('data'):
                        st.success("Risques identifiés dans un rayon de 1km :")
                        for risque in res_georisques['data']:
                            # Correction du bug d'affichage ici
                            libelle = risque.get('libelle_risque_long', 'Inconnu')
                            etat = risque.get('etat_arrete', 'N/A')
                            st.write(f"- {libelle} (État : {etat})")
                    else:
                        st.info("Aucun risque majeur trouvé ou API indisponible.")
            except Exception as e:
                st.error(f"Erreur avec l'API Géorisques : {e}")

# --- MODULE 3 : BILAN & SAUVEGARDE NOTION ---
with tab3:
    st.header("Simulateur MDB et Sauvegarde")
    
    col1, col2 = st.columns(2)
    with col1:
        nom_projet = st.text_input("Nom du projet", value="Projet Pro")
        prix_achat = st.number_input("Prix d'achat net vendeur (€)", value=100000)
        cout_travaux = st.number_input("Travaux estimés (€)", value=30000)
    with col2:
        prix_revente = st.number_input("Prix de revente estimé (€)", value=180000)
        frais_notaire_pct = st.number_input("Frais de notaire (%)", value=2.5)
        tva_marge_pct = st.number_input("TVA sur marge (%)", value=20.0)

    frais_notaire = prix_achat * (frais_notaire_pct / 100)
    prix_revient = prix_achat + frais_notaire + cout_travaux
    marge_brute = prix_revente - prix_revient
    tva_marge = marge_brute * (tva_marge_pct / (100 + tva_marge_pct)) if marge_brute > 0 else 0
    marge_nette = marge_brute - tva_marge
    rentabilite = (marge_nette / prix_revient) * 100 if prix_revient > 0 else 0

    st.subheader("Synthèse Financière")
    st.write(f"**Prix de revient global :** {prix_revient:,.0f} €")
    st.write(f"**Marge Nette après TVA :** {marge_nette:,.0f} €")
    st.write(f"**Rentabilité brute sur l'opération :** {rentabilite:.2f} %")

    st.divider()

    if st.button("Enregistrer définitivement dans Notion"):
        url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        data = {
            "parent": {"database_id": database_id},
            "properties": {
                "Nom": {"title": [{"text": {"content": nom_projet}}]},
                "Prix d'achat": {"number": prix_achat},
                "Marge Nette": {"number": float(marge_nette)},
                "Rentabilité": {"number": float(rentabilite)}
            }
        }
        
        with st.spinner("Envoi des données vers Notion..."):
            reponse = requests.post(url, headers=headers, json=data)
            if reponse.status_code == 200:
                st.success("✅ Données sauvegardées de manière permanente dans ton tableau Notion !")
            else:
                st.error(f"Erreur lors de la liaison avec Notion : {reponse.text}")
