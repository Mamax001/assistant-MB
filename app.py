import streamlit as st
import requests
from google import genai
from google.genai import types

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Assistant MDB", layout="wide", page_icon="🏗️")
st.title("🏗️ Assistant Marchand de Biens")

# --- VÉRIFICATION DES CLÉS ---
try:
    api_key_gemini = st.secrets["GEMINI_API_KEY"]
    notion_token = st.secrets["NOTION_TOKEN"]
    database_id = st.secrets["NOTION_DATABASE_ID"]
except KeyError as e:
    st.error(f"Arrêt : La clé {e} est introuvable dans les paramètres secrets de Streamlit.")
    st.stop()

# --- INITIALISATION DES ONGLETS ---
tab1, tab2, tab3 = st.tabs(["1. Faisabilité du Projet", "2. Risques Naturels", "3. Bilan Financier & Notion"])

# --- MODULE 1 : ÉTUDE DE FAISABILITÉ ---
with tab1:
    st.header("Analyse de Faisabilité d'Opération")
    
    col_gauche, col_droite = st.columns(2)

    with col_gauche:
        adresse_projet = st.text_input("Adresse du projet", placeholder="ex: 12 rue de la Gare, 92700 Colombes")
        url_plu = st.text_input("Lien internet du PLU", placeholder="https://...")
    
    with col_droite:
        description_projet = st.text_area(
            "Description précise du projet", 
            placeholder="ex: Surélévation d'un étage pour créer 2 appartements de 40m². Emprise supplémentaire de 15m². 0 place de parking créée.",
            height=150
        )

    if st.button("Lancer l'étude de faisabilité") and url_plu and description_projet and adresse_projet:
        client = genai.Client(api_key=api_key_gemini)
        
        with st.spinner("Analyse des règles d'urbanisme en cours..."):
            try:
                prompt = f"""
                Agis comme un expert en urbanisme. 
                
                Projet :
                - Adresse : {adresse_projet}
                - Description : {description_projet}
                
                Mission : Lis le règlement du PLU via ce lien internet ({url_plu}) et détermine si le projet est réalisable.
                
                Structure ta réponse :
                1. VERDICT : [FAISABLE], [À MODIFIER] ou [IMPOSSIBLE].
                2. ANALYSE : Compare le projet avec les règles du PLU concernant l'emprise au sol, la hauteur et le stationnement.
                3. RÉFÉRENCES : Cite les articles exacts du PLU.
                4. CONSEILS : Propose des solutions si le projet est bloqué.
                """
                
                reponse = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                )
                
                st.success("Analyse terminée.")
                st.markdown(reponse.text)
                
            except Exception as e:
                st.error(f"Échec de l'analyse IA : {e}")

# --- MODULE 2 : RISQUES NATURELS ---
with tab2:
    st.header("Vérification des Risques Naturels")
    adresse_risques = st.text_input("Adresse de la parcelle", value=adresse_projet)
    
    if st.button("Vérifier les risques") and adresse_risques:
        with st.spinner("Interrogation des bases de l'État..."):
            try:
                res_adresse = requests.get(f"https://api-adresse.data.gouv.fr/search/?q={adresse_risques}&limit=1")
                res_adresse.raise_for_status()
                data_adresse = res_adresse.json()
                
                if not data_adresse.get('features'):
                    st.error("Adresse non reconnue par le système.")
                else:
                    lon, lat = data_adresse['features'][0]['geometry']['coordinates']
                    st.write(f"**Coordonnées GPS :** {lat}, {lon}")
                    
                    url_georisques = f"https://georisques.gouv.fr/api/v1/gaspar/risques?latlon={lon},{lat}&rayon=1000"
                    res_georisques = requests.get(url_georisques)
                    res_georisques.raise_for_status()
                    data_georisques = res_georisques.json()
                    
                    if data_georisques.get('data'):
                        st.success("Risques recensés dans un rayon de 1 km :")
                        for risque in data_georisques['data']:
                            libelle = risque.get('libelle_risque_long', 'Non défini')
                            etat = risque.get('etat_arrete', 'Inconnu')
                            st.write(f"- {libelle} (État : {etat})")
                    else:
                        st.info("Aucun risque majeur signalé à cette adresse.")
            except requests.exceptions.RequestException as e:
                st.error(f"Erreur réseau avec les API gouvernementales : {e}")

# --- MODULE 3 : BILAN FINANCIER & NOTION ---
with tab3:
    st.header("Simulateur Financier et Export Notion")
    
    col1, col2 = st.columns(2)
    with col1:
        nom_projet = st.text_input("Nom de l'opération", value="Projet 1")
        prix_achat = st.number_input("Prix d'achat net vendeur (€)", value=100000, step=1000)
        cout_travaux = st.number_input("Budget travaux estimé (€)", value=30000, step=1000)
    with col2:
        prix_revente = st.number_input("Prix de revente estimé (€)", value=180000, step=1000)
        frais_notaire_pct = st.number_input("Frais de notaire (%)", value=2.5, step=0.1)
        tva_marge_pct = st.number_input("TVA sur marge (%)", value=20.0, step=0.1)

    frais_notaire = prix_achat * (frais_notaire_pct / 100)
    prix_revient = prix_achat + frais_notaire + cout_travaux
    marge_brute = prix_revente - prix_revient
    tva_marge = marge_brute * (tva_marge_pct / (100 + tva_marge_pct)) if marge_brute > 0 else 0
    marge_nette = marge_brute - tva_marge
    rentabilite = (marge_nette / prix_revient) * 100 if prix_revient > 0 else 0

    st.subheader("Synthèse")
    st.write(f"**Prix de revient global :** {prix_revient:,.0f} €")
    st.write(f"**Marge Nette (après TVA) :** {marge_nette:,.0f} €")
    st.write(f"**Rentabilité :** {rentabilite:.2f} %")

    st.divider()

    if st.button("Enregistrer l'opération dans Notion"):
        url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # Les noms des propriétés ("Nom", "Prix d'achat", "Marge Nette", "Rentabilité") doivent correspondre EXACTEMENT aux colonnes de ton Notion.
        data = {
            "parent": {"database_id": database_id},
            "properties": {
                "Nom": {"title": [{"text": {"content": nom_projet}}]},
                "Prix d'achat": {"number": prix_achat},
                "Marge Nette": {"number": float(marge_nette)},
                "Rentabilité": {"number": float(rentabilite)}
            }
        }
        
        with st.spinner("Connexion à Notion..."):
            try:
                reponse = requests.post(url, headers=headers, json=data)
                reponse.raise_for_status()
                st.success("Sauvegarde confirmée dans Notion.")
            except requests.exceptions.HTTPError as err:
                st.error(f"Rejet de l'API Notion. Vérifie que le nom des colonnes correspond exactement au code : {err.response.text}")
            except Exception as e:
                st.error(f"Erreur de communication : {e}")
