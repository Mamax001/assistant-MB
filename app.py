import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Terminal PEA Universel", layout="wide")

# --- FONCTION DE RÉCUPÉRATION ---
@st.cache_data(ttl=60) # Mise à jour automatique toutes les 60 secondes
def recuperer_donnees(ticker, periode):
    try:
        data = yf.download(ticker, period=periode, interval="1d", progress=False)
        return data if not data.empty else None
    except:
        return None

# --- INTERFACE ---
st.title("📈 Mon Terminal de Trading PEA")
st.sidebar.header("Configuration du Trade")

# Barre de recherche pour n'importe quel titre
ticker_input = st.sidebar.text_input("Entrer le Ticker (ex: AI.PA, MC.PA)", value="AI.PA").upper()

# Paramètres du simulateur
pru = st.sidebar.number_input("Ton PRU (Prix d'achat moyen)", min_value=0.0, value=150.0)
quantite = st.sidebar.number_input("Nombre d'actions", min_value=1, value=10)
periode_graph = st.sidebar.selectbox("Historique", ["1mo", "3mo", "6mo", "1y"], format_func=lambda x: {"1mo":"30 jours", "3mo":"3 mois", "6mo":"6 mois", "1y":"1 an"}[x])

if ticker_input:
    data = recuperer_donnees(ticker_input, periode_graph)
    
    if data is not None:
        prix_actuel = data['Close'].iloc[-1]
        
        # Calculs automatiques
        valeur_totale = prix_actuel * quantite
        investissement_initial = pru * quantite
        plus_value = valeur_totale - investissement_initial
        performance_pct = (plus_value / investissement_initial) * 100 if investissement_initial > 0 else 0

        # Affichage des Signaux et Métriques
        col1, col2, col3 = st.columns(3)
        
        # Signal Achat/Vente automatique (basé sur la moyenne mobile 20j)
        ma20 = data['Close'].rolling(window=20).mean().iloc[-1]
        signal = "ACHAT" if prix_actuel > ma20 else "VENTE"
        couleur_signal = "green" if signal == "ACHAT" else "red"
        
        col1.metric("Prix en Direct", f"{prix_actuel:.2f} €")
        col2.metric("Plus/Moins-value", f"{plus_value:.2f} €", delta=f"{performance_pct:.2f} %")
        
        with col3:
            st.write("**Signal Décisionnel :**")
            st.markdown(f"<h2 style='color:{couleur_signal};'>{signal}</h2>", unsafe_allow_html=True)

        st.divider()

        # Graphique d'Historique Interactif
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Cours", line=dict(color="#00D4FF")))
        fig.add_hline(y=pru, line_dash="dash", line_color="orange", annotation_text="Mon PRU")
        
        fig.update_layout(title=f"Évolution de {ticker_input}", template="plotly_dark", height=450)
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.error("Ticker invalide ou non trouvé. Pour Paris, ajoutez '.PA' (ex: ORA.PA).")

st.info("🔄 Les données se mettent à jour automatiquement à chaque actualisation de la page.")
