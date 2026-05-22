import streamlit as st
import requests
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
tab1, tab2, tab3 = st.tabs(["1. Faisabilité du Projet", "2. Risques Naturels", "3. Bilan Financier & Notion"])

# --- MODULE 1 : ETUDE DE FAISABILITÉ GLOBALE ---
with tab1:
    st.header("Analyse de Faisabilité d'Opération")
    st.write("Renseigne les éléments du projet pour que l'IA valide la cohérence avec les règles d'urbanisme.")

    col_gauche, col_droite = st.columns(2)

    with col_gauche:
        adresse_projet = st.text_input("Adresse du projet", placeholder="ex: 12 rue de la Gare, 92700 Colombes")
        url_plu = st.text_input("URL de la page ou du document PLU", placeholder="https://...")
    
    with col_droite:
        # Correction ici : Remplacement de rows=4 par height=150
        description_projet = st.text_area(
            "Description de ton projet (Objectif)", 
            placeholder="ex: Je souhaite surélever l'immeuble existant d'un étage pour créer 2 appartements de 40m², avec une emprise au sol supplémentaire de 15m² et aucune création de place de parking.",
            height=150
        )

    if st.button("Lancer l'étude de faisabilité") and url_plu and description_projet:
        client = genai.Client(api_key=api_key_gemini)
        
        with st.spinner("Analyse du PLU et étude de faisabilité en cours..."):
            try:
                prompt = f"""
                Agis comme un expert pointu en urbanisme et un consultant pour marchand de biens. 
                
                Voici les détails de l'opération :
                - Adresse du bien : {adresse_projet}
                - Projet envisagé : {description_projet}
                
                Mission : Navigue sur ce lien internet contenant le règlement du PLU ({url_plu}) et analyse si le projet décrit est réalisable ou s'il va être refusé par le service de l'urbanisme.
                
                Structure ta réponse de manière très claire :
                1. **VERDICT** : Indique clairement si le projet semble [FAISABLE], [COMPLEXE / À MODIFIER] ou [IMPOSSIBLE].
                2. **ANALYSE DES CRITÈRES** :
                   - Emprise au sol (CES) : Ce que le projet prévoit vs ce que le PLU autorise.
                   - Hauteur / Gabarit : La hauteur prévue vs la hauteur maximale autorisée au faîtage ou à l'égout.
                   - Stationnement : Le nombre de places imposé par le PLU pour ce type de création vs le projet.
                   - Surélévation / Destination : Est-ce autorisé dans cette zone ?
                3. **RÉFÉRENCES JURIDIQUES** : Cite scrupuleusement les numéros d'articles du PLU (ex: Article 11, Article 12...) pour justifier chaque point.
                4. **CONSEILS / ALTERNATIVES** : Si le projet bloque, propose une alternative pour qu'il passe (ex: réduire la surface, acheter une place de parking à proximité...).
                """
                
                reponse = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                )
                
                st.success("Étude de faisabilité terminée")
                st.markdown(reponse.text)
                
            except Exception as e:
                st.error(f"Erreur lors de l'analyse : {e}")

# --- MODULE 2 : RISQUES NATURELS ---
with tab2:
    st.header("Vérification des Risques Naturels")
    adresse = st.text_input("Saisis l'adresse pour analyser les risques", value=adresse_projet if adresse_projet else "")
    
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

    # Calculs financiers
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
                    st.success("✅ Données sauvegardées dans ton tableau Notion !")
                else:
                    st.error(f"Erreur Notion : {reponse.text}")
            except Exception as e:
                st.error(f"Impossible de joindre Notion : {e}")
