# --- MODULE 1 : ANALYSE PLU ---
with tab1:
    st.header("Analyse de PLU avec Gemini")
    
    # AJOUT DE L'OPTION MULTI-FICHIERS ICI
    fichiers_pdf = st.file_uploader("Téléverse un ou plusieurs fichiers PLU (PDF)", type="pdf", accept_multiple_files=True)
    
    if st.button("Analyser les documents") and fichiers_pdf:
        client = genai.Client(api_key=api_key_gemini)
        
        # Boucle pour traiter chaque fichier de la liste
        for fichier_pdf in fichiers_pdf:
            st.subheader(f"📄 Analyse de : {fichier_pdf.name}")
            
            with st.spinner(f"Lecture et analyse de {fichier_pdf.name} en cours..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(fichier_pdf.getvalue())
                    tmp_path = tmp_file.name

                try:
                    fichier_upload = client.files.upload(file=tmp_path, config={'mime_type': 'application/pdf'})
                    
                    prompt = """
                    Agis comme un expert en urbanisme. Analyse ce document (PLU) et réponds avec précision :
                    1. Quelle est l'emprise au sol maximale (CES) autorisée ?
                    2. Quelle est la hauteur maximale autorisée au faîtage ?
                    3. Est-il possible de surélever un bâtiment existant ?
                    4. Combien de places de stationnement sont exigées pour créer un logement ?
                    Cite les numéros d'articles du PLU qui justifient tes réponses.
                    """
                    
                    reponse = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[fichier_upload, prompt]
                    )
                    st.success(f"Analyse de {fichier_pdf.name} terminée")
                    st.write(reponse.text)
                    st.divider() # Ligne de séparation visuelle entre les fichiers
                    
                    client.files.delete(name=fichier_upload.name)
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse de {fichier_pdf.name} : {e}")
                finally:
                    os.remove(tmp_path)
