import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="Terminal PEA Universel", layout="wide")

# --- INITIALISATION ---
if 'portefeuille' not in st.session_state:
    st.session_state.portefeuille = []

# --- RECHERCHE UNIVERSELLE (NOM -> TICKER) ---
def recherche_intelligente(nom):
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={nom}&quotesCount=1"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = res.json()
        if data['quotes']:
            return data['quotes'][0]['symbol'], data['quotes'][0].get('longname', nom)
    except:
        return None, None
    return None, None

# --- IA DE DIAGNOSTIC ---
def analyse_ia_interne(info, hist):
    prix = float(hist['Close'].iloc[-1])
    ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
    
    # Analyse de tendance
    if prix > ma20 * 1.03:
        verdict = "ACHAT ✅"
        explication = "Le titre montre une force acheteuse supérieure à sa moyenne. C'est un bon point d'entrée."
    elif prix < ma20 * 0.97:
        verdict = "ATTENTE ⚠️"
        explication = "Le cours chute sous ses supports. Risque de baisse plus profonde, attendez une stabilisation."
    else:
        verdict = "OBSERVATION ⏳"
        explication = "Le prix stagne. Pas de direction claire, mieux vaut patienter."
    
    return verdict, explication

# --- INTERFACE ---
st.title("🚀 Terminal PEA Universel")
st.sidebar.header("🔍 Recherche Rapide")

nom_saisi = st.sidebar.text_input("Tapez le nom d'une entreprise (ex: Total, Apple, LVMH)")
budget = st.sidebar.number_input("Budget (€)", min_value=10, value=1000)

if nom_saisi:
    ticker, nom_propre = recherche_intelligente(nom_saisi)
    
    if ticker:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        
        if not hist.empty:
            prix_actuel = float(hist['Close'].iloc[-1])
            isin = stock.info.get('isin', 'N/A')
            
            # --- BLOC IA ---
            verdict, raison = analyse_ia_interne(stock.info, hist)
            st.subheader(f"🏢 Analyse : {nom_propre}")
            
            c1, c2 = st.columns([1, 2])
            c1.metric("Conseil Stratégique", verdict)
            c2.info(f"**Pourquoi ?** {raison}")

            # --- TABLEAU BOURSOBANK ---
            st.markdown("### 🛒 Infos pour ton ordre BoursoBank")
            nb_actions = int(budget // prix_actuel)
            df_ordre = pd.DataFrame({
                "Paramètre Bourso": ["Code ISIN", "Symbole", "Quantité", "Prix Limite"],
                "Valeur à saisir": [isin, ticker, nb_actions, f"{prix_actuel:.2f} €"]
            })
            st.table(df_ordre)

            if st.button("➕ Enregistrer ce trade"):
                st.session_state.portefeuille.append({
                    "Entreprise": nom_propre,
                    "ISIN": isin,
                    "Prix": f"{prix_actuel:.2f}€",
                    "Décision": verdict
                })
                st.success("Ajouté au tableau ci-dessous !")

            st.plotly_chart(go.Figure(go.Scatter(x=hist.index, y=hist['Close'], line=dict(color="#00D4FF"))).update_layout(height=250, template="plotly_dark"), use_container_width=True)
    else:
        st.error("Entreprise introuvable. Essayez d'être plus précis ou utilisez le Ticker (ex: AI.PA).")

st.divider()

# --- TABLEAU RÉCAPITULATIF ---
st.subheader("📋 Historique de la session")
if st.session_state.portefeuille:
    st.dataframe(pd.DataFrame(st.session_state.portefeuille), use_container_width=True)
    if st.button("🗑️ Vider l'historique"):
        st.session_state.portefeuille = []; st.rerun()
