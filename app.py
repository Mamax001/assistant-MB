import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import requests

st.set_page_config(page_title="Terminal PEA Pro", layout="wide")

# --- INITIALISATION ---
if 'portefeuille' not in st.session_state:
    st.session_state.portefeuille = []

def trouver_ticker(nom):
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={nom}&quotesCount=1"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = res.json()
        return data['quotes']['symbol'] if data['quotes'] else None
    except: return None

# --- INTERFACE ---
st.title("🏛️ Terminal PEA : Analyse & Prévisions")

with st.sidebar:
    nom_saisi = st.sidebar.text_input("Entreprise", value="Air Liquide")
    budget = st.sidebar.number_input("Budget (€)", min_value=50, value=1000)

if nom_saisi:
    ticker = trouver_ticker(nom_saisi)
    if ticker:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        
        if not hist.empty:
            tab1, tab2 = st.tabs(["🎯 Analyse & Ordre", "🔮 Prévisions à 30j"])

            with tab1:
                prix_actuel = float(hist['Close'].iloc[-1])
                st.metric("Prix Actuel", f"{prix_actuel:.2f} €")
                
                st.subheader("📝 Ordre BoursoBank")
                nb_actions = int(budget // prix_actuel)
                st.table(pd.DataFrame({
                    "ISIN/Ticker": [ticker],
                    "Quantité": [nb_actions],
                    "Prix Limite": [f"{prix_actuel:.2f} €"]
                }))

            with tab2:
                try:
                    # Préparation des données
                    df = hist[['Close']].reset_index()
                    df['n'] = range(len(df))
                    
                    # Modèle simple
                    X = df[['n']].values[-100:] # On s'appuie sur les 100 derniers jours
                    y = df['Close'].values[-100:]
                    model = LinearRegression().fit(X, y)
                    
                    # Projection
                    futur = np.array(range(len(df), len(df) + 30)).reshape(-1, 1)
                    prev = model.predict(futur)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(y=y, name="Historique récent", line=dict(color="#00D4FF")))
                    fig.add_trace(go.Scatter(x=list(range(100, 130)), y=prev, name="Projection", line=dict(color="orange", dash="dash")))
                    fig.update_layout(template="plotly_dark", height=300)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    diff = ((prev[-1] - prix_actuel) / prix_actuel) * 100
                    st.write(f"**Tendance estimée :** {diff:+.2f}% d'ici 30 jours.")
                except:
                    st.warning("Calcul de prévision indisponible pour ce titre.")

# --- DIVERS DE SÉCURITÉ ---
if st.button("🗑️ Vider la session"):
    st.session_state.portefeuille = []; st.rerun()
