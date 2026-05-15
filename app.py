import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Terminal PEA Pro", layout="wide")

# --- STYLE ET CONFIG ---
st.markdown("""<style> .main { background-color: #0e1117; } </style>""", unsafe_allow_html=True)

with st.sidebar:
    st.header("🏛️ Paramètres d'Achat")
    ticker_input = st.text_input("Ticker (ex: CS.PA, AI.PA)", value="CS.PA").upper()
    prix_achat = st.number_input("Mon Prix d'Achat (€)", min_value=0.0, value=39.24, step=0.01)
    date_achat = st.date_input("Date d'Achat")
    budget = st.number_input("Budget Total (€)", min_value=10, value=1000)
    lancer = st.button("🚀 Calculer Rentabilité")

st.title("📈 Suivi de Rentabilité & Prévisions")

if lancer:
    with st.spinner('Analyse en cours...'):
        stock = yf.Ticker(ticker_input)
        hist = stock.history(period="1y")

        if not hist.empty:
            prix_actuel = float(hist['Close'].iloc[-1])
            
            tab1, tab2, tab3 = st.tabs(["📊 Performance Réelle", "🔮 Prévisions", "📝 Ordre Bourso"])

            with tab1:
                # --- CALCULS DE RENTABILITÉ ---
                performance = ((prix_actuel - prix_achat) / prix_achat) * 100
                frais_estimes = 1.99 if budget < 500 else budget * 0.005
                point_mort = prix_achat + (frais_estimes / (budget / prix_achat))
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Prix Actuel", f"{prix_actuel:.2f} €", f"{performance:.2f} %")
                c2.metric("Point Mort (Break-even)", f"{point_mort:.2f} €")
                c3.metric("Frais Bourso Est.", f"{frais_estimes:.2f} €")

                # Indicateur visuel
                if prix_actuel >= point_mort:
                    st.success(f"✅ Tu es RENTABLE. Gain net estimé : {((prix_actuel - point_mort) * (budget/prix_achat)):.2f} €")
                else:
                    st.warning(f"⚠️ Tu es en perte de {((point_mort - prix_actuel) * (budget/prix_achat)):.2f} € (Frais inclus)")

                # --- STRATÉGIE DE SORTIE ---
                st.subheader("🎯 Objectifs de Sortie")
                col_s1, col_s2, col_s3 = st.columns(3)
                col_s1.write(f"**Sécurité (Stop-Loss -5%)** : {prix_achat * 0.95:.2f} €")
                col_s2.write(f"**Objectif 1 (+10%)** : {prix_achat * 1.10:.2f} €")
                col_s3.write(f"**Objectif 2 (+20%)** : {prix_achat * 1.20:.2f} €")

            with tab2:
                # --- TON TRUC (PRÉVISIONS) ---
                df = hist[['Close']].reset_index()
                df['n'] = range(len(df))
                X = df[['n']].values[-100:]; y = df['Close'].values[-100:]
                model = LinearRegression().fit(X, y)
                futur = np.array(range(len(df), len(df) + 30)).reshape(-1, 1)
                preds = model.predict(futur)
                
                fig_pred = go.Figure()
                fig_pred.add_trace(go.Scatter(y=y, name="Récent", line=dict(color="#00D4FF")))
                fig_pred.add_trace(go.Scatter(x=list(range(100, 130)), y=preds, name="Projection", line=dict(color="orange", dash="dash")))
                fig_pred.update_layout(template="plotly_dark", height=350)
                st.plotly_chart(fig_pred, use_container_width=True)
                
                diff = ((preds[-1] - prix_actuel) / prix_actuel) * 100
                st.write(f"**Tendance estimée à 30 jours :** {diff:+.2f}%")

            with tab3:
                st.info(f"Pour sortir rentable (frais inclus), tu dois revendre au-dessus de **{point_mort:.2f} €**.")
                st.write(f"Date d'achat enregistrée : {date_achat}")
        else:
            st.error("Ticker introuvable.")
