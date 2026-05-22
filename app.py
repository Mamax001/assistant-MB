import streamlit as st
import requests
import os
from google import genai
from google.genai import types

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
tab1, tab2, tab3 = st.tabs(["1. Urbanisme (Lien PLU)", "2. Risques Naturels", "3. Bilan Financier & Notion"])

# --- MODULE 1 : ANALYSE PLU VIA LIEN WEB ---
with tab1:
    st.header("Analyse de PLU via Lien Internet")
    st.write("Colle ci-dessous l'URL de la page web ou du document en ligne contenant le PLU à analyser.")
    
    url_plu = st.text_input("URL du document ou de la page du PLU (ex: https://mairie...)", placeholder="https://...")
    
    if st.button("Analyser le lien") and url_plu:
        client = genai.Client(api_key=api_key_gemini)
        
        with st.spinner("Gemini explore, navigue et analyse le lien fourni..."):
            try:
                prompt = f"""
                Agis comme un expert en urbanisme. Analyse avec précision les règles d'urbanisme applicables en visitant ce lien internet : {url_plu}
                Réponds ensuite de manière détaillée à ces questions :
                1. Quelle est l'emprise au sol maximale (CES) autorisée ?
                2. Quelle est la hauteur maximale autorisée au faîtage ?
                3. Est-il possible de surélever un bâtiment existant ?
                4. Combien de places de stationnement sont exigées pour créer un logement ?
                Cite scrupuleusement les numéros d'articles ou les sections du PLU qui justifient tes réponses.
                """
                
                # Correction majeure : Activation obligatoire de Google Search pour permettre la lecture d'URL externes
                reponse = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                )
                
                st.success("Analyse du lien terminée avec succès")
                st.write(reponse.text)
                
            except Exception as e:
                st.error(f"Erreur lors de l'analyse du lien : {e}")

# --- MODULE 2 : RISQUES ---
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
                            libelle = risque.get('libelle_risque_long', 'Inconnu')
                            etat = risque.get('etat_arrete', 'N/A')
                            st.write(f"- {libelle} (État : {制造 := etat})")
                    else:
                        st.info("Aucun risque majeur trouvé ou API indisponible.")
            except Exception as e:
                st.error(f"Erreur de connexion aux API d'État : {e}")

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

    # Calculs financiers automatisés
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
            try:
                reponse = requests.post(url, headers=headers, json=data)
                if reponse.status_code == 200:
                    st.success("✅ Données sauvegardées de manière permanente dans ton tableau Notion !")
                else:
                    st.error(f"Erreur lors de la liaison avec Notion : {reponse.text}")
            except Exception as e:
                st.error(f"Impossible de joindre l'API Notion : {e}")
