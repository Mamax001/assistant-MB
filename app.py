import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Terminal PEA Expert", layout="wide")

# --- INITIALISATION ---
if 'historique' not in st.session_state:
    st.session_state.historique = []

def generer_analyse_ia(info, hist):
    prix = hist['Close'].iloc[-1]
    ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
    diff = ((prix - ma20) / ma20) * 100
    
    if prix > ma20 * 1.02:
        return "ACHAT ✅", f"Tendance haussière confirmée (+{diff:.1f}% vs moyenne). Le momentum est bon pour entrer."
    elif prix < ma20 * 0.98:
        return "ATTENTE ⚠️", f"Le titre s'affaiblit ({diff:.1f}% vs moyenne). Risque de baisse continu, restez prudent."
    return "OBSERVATION ⏳", "Le titre consolide horizontalement. Attendez un signal plus franc."

# --- RECHERCHE ---
st.title("🚀 Mon Terminal PEA Intelligent")
st.sidebar.header("🔍 Analyse de Valeur")

nom_saisi = st.sidebar.text_input("Entreprise (ex: Air Liquide, LVMH, TTE.PA)")
budget = st.sidebar.number_input("Budget (€)", min_value=10, value=1000)

if nom_saisi:
    # Correspondance rapide pour faciliter la saisie
    dict_tickers = {"Air Liquide": "AI.PA", "LVMH": "MC.PA", "Total": "TTE.PA", "Hermes": "RMS.PA"}
    ticker = dict_tickers.get(nom_saisi, nom_saisi)
    
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1y")
    
    if not hist.empty:
        prix_actuel = float(hist['Close'].iloc[-1])
        isin = stock.info.get('isin', 'N/A')
        nom_complet = stock.info.get('longName', nom_saisi)
        
        # --- ANALYSE IA ---
        verdict, raison = generer_analyse_ia(stock.info, hist)
        st.subheader(f"🧠 Analyse Stratégique : {nom_complet}")
        
        c1, c2 = st.columns([1, 2])
        c1.metric("Conseil", verdict)
        c2.info(f"**Analyse de l'IA :** {raison}")

        # --- RECAP BOURSOBANK ---
        st.markdown("### 📝 Détails de l'ordre (BoursoBank)")
        nb_actions = int(budget // prix_actuel)
        df_ordre = pd.DataFrame({
            "Champ": ["Code ISIN", "Quantité", "Type d'ordre", "Prix Limite"],
            "Valeur": [isin, nb_actions, "À cours limité", f"{prix_actuel:.2f} €"]
        })
        st.table(df_ordre)

        if st.button("➕ Ajouter au tableau de suivi"):
            st.session_state.historique.append({
                "Date": pd.Timestamp.now().strftime("%d/%m/%Y"),
                "Valeur": nom_complet,
                "ISIN": isin,
                "Prix": f"{prix_actuel:.2f}€",
                "Conseil": verdict
            })

        st.plotly_chart(go.Figure(go.Scatter(x=hist.index, y=hist['Close'], line=dict(color="#00D4FF"))).update_layout(height=250, template="plotly_dark"), use_container_width=True)

st.divider()

# --- TABLEAU RÉCAPITULATIF ---
st.subheader("📋 Mon Journal de Bord (Session Actuelle)")
if st.session_state.historique:
    df_final = pd.DataFrame(st.session_state.historique)
    st.dataframe(df_final, use_container_width=True)
    
    # Bouton de sauvegarde CSV
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Télécharger mon historique (.csv)", data=csv, file_name="mon_pea_backup.csv", mime="text/csv")
    
    if st.button("🗑️ Vider le tableau"):
        st.session_state.historique = []; st.rerun()
else:
    st.write("Aucun trade enregistré pour le moment.")
