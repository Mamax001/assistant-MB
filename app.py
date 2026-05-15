import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Terminal PEA Pro", layout="wide")

# --- STYLE ---
st.markdown("""<style> .main { background-color: #0e1117; } </style>""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🏛️ Paramètres")
    # On demande directement le Ticker pour éviter les bugs de recherche (ex: CS.PA pour AXA)
    ticker_input = st.text_input("Ticker (ex: CS.PA, AI.PA, MC.PA)", value="CS.PA").upper()
    budget = st.number_input("Budget (€)", min_value=10, value=120)
    lancer = st.button("🚀 Lancer l'Analyse")

st.title("📈 Terminal PEA : Analyse & Prévisions")

if lancer:
    with st.spinner('Analyse du marché en cours...'):
        stock = yf.Ticker(ticker_input)
        hist = stock.history(period="1y")

        if not hist.empty:
            prix_actuel = float(hist['Close'].iloc[-1])
            
            # --- ONGLETS ---
            tab1, tab2 = st.tabs(["🎯 Analyse & Ordre", "🔮 Prévisions 30j"])

            with tab1:
                col1, col2, col3 = st.columns(3)
                col1.metric("Prix Actuel", f"{prix_actuel:.2f} €")
                
                # ISIN (souvent disponible dans info)
                isin = stock.info.get('isin', 'À vérifier sur Bourso')
                col2.metric("Code ISIN", isin)
                
                # Stratégie Quantité
                nb_actions = int(budget // prix_actuel)
                col3.metric("Actions à acheter", nb_actions)

                st.success(f"**Ordre BoursoBank :** Acheter **{nb_actions}** actions **{ticker_input}** à cours limité (**{prix_actuel:.2f} €**).")
                
                # Graphique Simple
                fig_hist = go.Figure(go.Scatter(x=hist.index, y=hist['Close'], name="Cours", line=dict(color="#00D4FF")))
                fig_hist.update_layout(template="plotly_dark", height=350, margin=dict(l=0,r=0,t=20,b=0))
                st.plotly_chart(fig_hist, use_container_width=True)

            with tab2:
                # --- PRÉVISIONS ---
                df = hist[['Close']].reset_index()
                df['n'] = range(len(df))
                
                # Modèle
                X = df[['n']].values[-100:]
                y = df['Close'].values[-100:]
                model = LinearRegression().fit(X, y)
                
                # Projection
                futur = np.array(range(len(df), len(df) + 30)).reshape(-1, 1)
                preds = model.predict(futur)
                
                fig_pred = go.Figure()
                fig_pred.add_trace(go.Scatter(y=y, name="Récent", line=dict(color="#00D4FF")))
                fig_pred.add_trace(go.Scatter(x=list(range(100, 130)), y=preds, name="Prévision", line=dict(color="orange", dash="dash")))
                fig_pred.update_layout(template="plotly_dark", height=350)
                st.plotly_chart(fig_pred, use_container_width=True)
                
                diff = ((preds[-1] - prix_actuel) / prix_actuel) * 100
                st.write(f"**Tendance estimée à 30 jours :** {diff:+.2f}%")
                
        else:
            st.error("Données introuvables. Vérifiez le Ticker (n'oubliez pas le .PA pour Paris, ex: CS.PA pour AXA).")
else:
    st.info("Entrez un Ticker dans la barre latérale et cliquez sur 'Lancer l'Analyse' pour commencer.")
