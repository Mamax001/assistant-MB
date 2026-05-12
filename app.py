import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Investisseur PEA Pro", layout="wide")

# Liste de tickers éligibles PEA (Tu peux en ajouter d'autres ici)
TICKERS = ["AIR.PA", "MC.PA", "OR.PA", "TTE.PA", "SAN.PA", "ASML.AS", "SAP.DE", "BNP.PA"]

# --- FONCTIONS DE RÉCUPÉRATION ---
def get_historical_data(ticker, period):
    mapping = {"30 jours": "1mo", "2 mois": "2mo", "4 mois": "4mo", "6 mois": "6mo"}
    data = yf.download(ticker, period=mapping[period], interval="1d", progress=False)
    return data

def get_signal(ticker):
    data = yf.download(ticker, period="60d", interval="1d", progress=False)
    current_price = data['Close'].iloc[-1]
    ma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
    signal = "ACHAT" if current_price > ma_20 else "VENTE"
    return signal, current_price

# --- INTERFACE UTILISATEUR ---
st.title("📈 Dashboard Décisionnel & Historique PEA")

# SECTION 1 : SIGNAUX RAPIDES
st.subheader("⚡ Signaux en 1 clic")
if st.button("Lancer l'analyse du marché"):
    cols = st.columns(len(TICKERS))
    for i, t in enumerate(TICKERS):
        signal, price = get_signal(t)
        with cols[i]:
            st.metric(t, f"{price:.2f} €")
            if signal == "ACHAT":
                st.success(signal)
            else:
                st.error(signal)

st.divider()

# SECTION 2 : SIMULATEUR & GRAPHIQUE HISTORIQUE
st.subheader("🔍 Analyse détaillée et simulation")

c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
with c1:
    selected_stock = st.selectbox("Choisir une action", TICKERS)
with c2:
    buy_price = st.number_input("Prix d'achat moyen (€)", min_value=0.1, value=150.0)
with c3:
    quantity = st.number_input("Quantité détenue", min_value=1, value=5)
with c4:
    period_choice = st.selectbox("Période d'historique", ["30 jours", "2 mois", "4 mois", "6 mois"])

# Récupération des données pour le graphique
hist_data = get_historical_data(selected_stock, period_choice)
live_price = hist_data['Close'].iloc[-1]

# Calculs de performance
total_invested = buy_price * quantity
current_value = live_price * quantity
profit_loss = current_value - total_invested
percent = (profit_loss / total_invested) * 100

# Affichage des métriques de simulation
m1, m2, m3 = st.columns(3)
m1.metric("Prix Actuel", f"{live_price:.2f} €")
m2.metric("Plus/Moins-value", f"{profit_loss:.2f} €", delta=f"{percent:.2f} %")
m3.metric("Valeur du Portefeuille", f"{current_value:.2f} €")

# --- GRAPHIQUE D'ÉVOLUTION ---
hist_data['Portfolio_Value'] = hist_data['Close'] * quantity
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=hist_data.index, 
    y=hist_data['Portfolio_Value'],
    mode='lines',
    name='Valeur Portefeuille',
    line=dict(color='#00ff00' if profit_loss > 0 else '#ff0000', width=3)
))

# Seuil de rentabilité (Ligne du capital investi)
fig.add_hline(y=total_invested, line_dash="dash", line_color="white", 
              annotation_text="Capital Investi", annotation_position="top left")

fig.update_layout(
    title=f"Évolution sur {selected_stock} ({period_choice})",
    template="plotly_dark",
    hovermode="x unified"
)
st.plotly_chart(fig, use_container_width=True)
