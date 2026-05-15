import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import requests

st.set_page_config(page_title="Terminal PEA Prédictif", layout="wide")

# --- INITIALISATION & RECHERCHE ---
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
    nom_saisi = st.text_input("Entreprise", value="LVMH")
    budget = st.number_input("Budget (€)", min_value=50, value=1000)
    st.divider()
    st.info("L'onglet 'Prévisions' utilise un modèle statistique pour projeter le cours à 30 jours.")

if nom_saisi:
    ticker = trouver_ticker(nom_saisi)
    if ticker:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2y") # 2 ans pour plus de précision statistique
        
        if not hist.empty:
            prix_actuel = float(hist['Close'].iloc[-1])
            
            # --- SYSTÈME D'ONGLETS ---
            tab1, tab2, tab3 = st.tabs(["🎯 Analyse & Ordre", "📈 Prévisions (30j)", "📋 Journal"])

            with tab1:
                st.subheader(f"Analyse de {ticker}")
                ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
                verdict = "ACHAT ✅" if prix_actuel > ma20 else "ATTENTE ⚠️"
                
                c1, c2 = st.columns(2)
                c1.metric("Prix Direct", f"{prix_actuel:.2f} €")
                c2.metric("Verdict IA", verdict)
                
                st.markdown("### 📝 Configuration BoursoBank")
                nb_actions = int(budget // prix_actuel)
                st.table(pd.DataFrame({
                    "Paramètre": ["ISIN", "Quantité", "Prix Limite"],
                    "Valeur": [stock.info.get('isin', ticker), nb_actions, f"{prix_actuel:.2f} €"]
                }))
                
                if st.button("➕ Ajouter au journal"):
                    st.session_state.portefeuille.append({"Valeur": ticker, "Prix": prix_actuel, "Verdict": verdict})

            with tab2:
                st.subheader("🔮 Projection Statistique à 30 jours")
                
                # --- MODÈLE DE PRÉDICTION ---
                df_pred = hist[['Close']].reset_index()
                df_pred['Ordinal'] = pd.to_datetime(df_pred['Date']).apply(lambda x: x.toordinal())
                
                # Entraînement sur les 6 derniers mois pour la tendance récente
                X = df_pred['Ordinal'].values[-120:].reshape(-1, 1)
                y = df_pred['Close'].values[-120:]
                model = LinearRegression().fit(X, y)
                
                # Génération des 30 prochains jours
                futur_ordinals = np.array([df_pred['Ordinal'].max() + i for i in range(1, 31)]).reshape(-1, 1)
                predictions = model.predict(futur_ordinals)
                dates_futures = pd.date_range(start=hist.index[-1], periods=31)[1:]
                
                # Graphique prédictif
                fig = go.Figure()
                # Historique
                fig.add_trace(go.Scatter(x=hist.index[-60:], y=hist['Close'][-60:], name="Historique (2 mois)", line=dict(color="#00D4FF")))
                # Prévision
                fig.add_trace(go.Scatter(x=dates_futures, y=predictions, name="Projection (30 jours)", line=dict(color="#FFA500", dash='dash')))
                
                fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=0,b=0))
                st.plotly_chart(fig, use_container_width=True)
                
                diff_prev = ((predictions[-1] - prix_actuel) / prix_actuel) * 100
                st.write(f"**Estimation :** Le modèle prévoit une variation potentielle de **{diff_prev:+.2f}%** d'ici un mois.")
                st.caption("Note : Cette projection est basée sur la tendance linéaire récente. Elle ne prend pas en compte les actualités soudaines.")

            with tab3:
                if st.session_state.portefeuille:
                    st.table(pd.DataFrame(st.session_state.portefeuille))
                else:
                    st.write("Journal vide.")
