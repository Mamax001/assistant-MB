import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="Terminal PEA Haute Efficacité", layout="wide")

# --- PERSISTENCE DE L'HISTORIQUE ---
if 'portefeuille' not in st.session_state:
    st.session_state.portefeuille = []

# --- FONCTIONS TECHNIQUES ---
def trouver_ticker(nom):
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={nom}&quotesCount=1"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = res.json()
        return data['quotes'][0]['symbol'] if data['quotes'] else None
    except:
        return None

def calculer_conseil(prix, ma20):
    if prix > ma20 * 1.02: return "ACHAT ✅"
    if prix < ma20 * 0.98: return "VENTE ⚠️"
    return "ATTENTE ⏳"

# --- INTERFACE DE RECHERCHE ---
st.title("🚀 Dashboard PEA Haute Performance")
st.sidebar.header("🔍 Nouvel Ordre")

nom_saisi = st.sidebar.text_input("Nom de l'entreprise", placeholder="Ex: Air Liquide...")
budget = st.sidebar.number_input("Budget (€)", min_value=10, value=1000, step=100)

if nom_saisi:
    ticker = trouver_ticker(nom_saisi)
    if ticker:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        
        if not hist.empty:
            prix_actuel = float(hist['Close'].iloc[-1])
            ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            nb_actions = int(budget // prix_actuel)
            isin = stock.info.get('isin', 'N/A')
            nom_reel = stock.info.get('longName', nom_saisi)

            # --- PANNEAU DE CONFIRMATION D'ORDRE ---
            st.subheader(f"✅ Configuration de l'ordre : {nom_reel}")
            
            # Tableau récapitulatif pour BoursoBank
            recap_ordre = {
                "Champ BoursoBank": ["Valeur / ISIN", "Quantité", "Type d'ordre", "Prix Limite"],
                "Donnée à saisir": [isin, nb_actions, "À cours limité", f"{prix_actuel:.2f} €"]
            }
            st.table(pd.DataFrame(recap_ordre))

            col_btn, col_msg = st.columns([1, 2])
            with col_btn:
                if st.button("📈 Ajouter au Dashboard de Suivi"):
                    st.session_state.portefeuille.append({"ticker": ticker, "nom": nom_reel, "pru": prix_actuel, "isin": isin})
                    st.success("Ajouté !")

            # Graphique rapide
            fig = go.Figure(go.Scatter(x=hist.index, y=hist['Close'], line=dict(color="#00D4FF")))
            fig.update_layout(height=250, margin=dict(l=0, r=0, t=0, b=0), template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- DASHBOARD DE SUIVI DYNAMIQUE ---
st.subheader("📊 Mon Dashboard de Suivi en Temps Réel")

if st.session_state.portefeuille:
    lignes_recap = []
    
    for item in st.session_state.portefeuille:
        # Mise à jour en direct des données pour chaque ligne
        s = yf.Ticker(item['ticker'])
        p_live = s.history(period="20d")['Close']
        prix_maintenant = p_live.iloc[-1]
        ma20_live = p_live.mean()
        
        perf = ((prix_maintenant - item['pru']) / item['pru']) * 100
        action_requise = calculer_conseil(prix_maintenant, ma20_live)
        
        lignes_recap.append({
            "Entreprise": item['nom'],
            "ISIN": item['isin'],
            "Prix Achat": f"{item['pru']:.2f} €",
            "Prix Actuel": f"{prix_maintenant:.2f} €",
            "Perf. (%)": f"{perf:+.2f}%",
            "ACTION REQUISE": action_requise
        })
    
    df_dashboard = pd.DataFrame(lignes_recap)
    
    # Affichage stylisé du tableau
    st.dataframe(df_dashboard.style.applymap(
        lambda x: 'color: #00ff00' if 'ACHAT' in str(x) else ('color: #ff4b4b' if 'VENTE' in str(x) else ''),
        subset=['ACTION REQUISE']
    ), use_container_width=True)

    if st.button("🗑️ Vider le Dashboard"):
        st.session_state.portefeuille = []
        st.rerun()
else:
    st.info("Recherchez une action pour l'ajouter à votre suivi dynamique.")
