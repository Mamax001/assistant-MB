import streamlit as st
import requests
import tempfile
import os
import time
from google import genai

st.set_page_config(page_title="Test Assistant", layout="wide")
st.title("🏗️ Test de l'Assistant")

# Vérification brute des clés d'accès
try:
    api_key_gemini = st.secrets["GEMINI_API_KEY"]
except Exception as e:
    st.error(f"Erreur de configuration des clés : {e}")
    st.stop()

tab1, tab2 = st.tabs(["1. Test Multi-PDF", "2. Test Adresse"])

# --- ONGLET 1 : MULTI-PDF ---
with tab1:
    st.header("Test d'envoi de documents multiples")
    
    # Zone d'envoi configurée explicitement pour plusieurs fichiers
    fichiers_pdf = st.file_uploader(
        "Dépose plusieurs fichiers ici", 
        type="pdf", 
        accept_multiple_files=True,
        key="test_uploader"
    )
    
    if fichiers_pdf:
        st.success(f"Nombre de fichiers détectés par l'interface : {len(fichiers_pdf)}")
        for f in fichiers_pdf:
            st.write(f"🟢 Fichier prêt : **{f.name}** ({f.size / 1024 / 1024:.2f} Mo)")
            
        if st.button("Lancer l'analyse de test"):
            client = genai.Client(api_key=api_key_gemini)
            
            for fichier_pdf in fichiers_pdf:
                with st.spinner(f"Envoi de {fichier_pdf.name} à Google..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(fichier_pdf.getvalue())
                        tmp_path = tmp.name
                    
                    try:
                        # Envoi brut au serveur
                        blob = client.files.upload(file=tmp_path)
                        
                        # Suivi de la validation
                        statut = client.files.get(name=blob.name)
                        while statut.state.name == "PROCESSING":
                            time.sleep(2)
                            statut = client.files.get(name=blob.name)
                            
                        if statut.state.name == "ACTIVE":
                            st.info(f"Analyse IA pour : {fichier_pdf.name}")
                            reponse = client.models.generate_content(
                                model="gemini-2.5-flash",
                                contents=[blob, "Fais un résumé de trois lignes de ce document."]
                            )
                            st.write(reponse.text)
                        else:
                            st.error(f"Le fichier a le statut : {statut.state.name}")
                            
                        client.files.delete(name=blob.name)
                    except Exception as e:
                        st.error(f"Erreur technique : {e}")
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)

# --- ONGLET 2 : ADRESSE ---
with tab2:
    st.header("Test du moteur d'adresse")
    adresse_test = st.text_input("Entre une adresse (ex: 10 rue de la Paix Paris)")
    
    if st.button("Tester l'adresse") and adresse_test:
        with st.spinner("Requête en cours..."):
            try:
                # Étape 1 : Traduction de l'adresse en coordonnées GPS
                url_adresse = f"https://api-adresse.data.gouv.fr/search/?q={adresse_test}&limit=1"
                res_addr = requests.get(url_adresse).json()
                
                if not res_addr.get('features'):
                    st.error("L'API du gouvernement ne trouve pas cette adresse.")
                else:
                    lon, lat = res_addr['features'][0]['geometry']['coordinates']
                    st.success(f"Adresse trouvée ! Coordonnées GPS : {lat}, {lon}")
                    
                    # Étape 2 : Appel à Géorisques
                    url_risques = f"https://georisques.gouv.fr/api/v1/gaspar/risques?latlon={lon},{lat}&rayon=1000"
                    res_risq = requests.get(url_risques).json()
                    
                    if res_risq.get('data'):
                        st.write("### Liste des risques trouvés :")
                        for r in res_risq['data']:
                            st.write(f"- {r.get('libelle_risque_long', 'Nom inconnu')}")
                    else:
                        st.warning("Aucun risque recensé ou format de réponse vide.")
            except Exception as e:
                st.error(f"Le système de recherche a planté : {e}")
