import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Terminal PEA & BoursoBank", layout="wide")

# --- FONCTION DE RECHERCHE & RÉCAP ---
@st.cache_data(ttl=300)
def obtenir_infos_entreprise(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info
    except:
        return None

# --- INTERFACE ---
st.title("📈 Assistant Investissement PEA")
st.sidebar.header("🔍 Recherche de Titre")

# Saisie du Ticker
ticker_input = st.sidebar.text_input("Ticker (ex: AI.PA, MC.PA, TTE.PA)", value="AI.PA").upper()

if ticker_input:
    # Récupération des données
    data = yf.download(ticker_input, period="6mo", interval="1d", progress=False)
    details = obtenir_infos_entreprise(ticker_input)

    if not data.empty and details:
        # --- BLOC RÉCAPITULATIF BOURSOBANK ---
        st.subheader(f"🏢 Récapitulatif : {details.get('longName', ticker_input)}")
        
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            st.info(f"**Code ISIN (BoursoBank)**\n\n{details.get('isin', 'Non trouvé')}")
        with col_b2:
            st.info(f"**Symbole / Ticker**\n\n{ticker_input}")
        with col_b3:
            st.info(f"**Secteur d'activité**\n\n{details.get('sector', 'N/A')}")

        st.markdown("---")

        # --- ANALYSE DES PERFORMANCES ---
        prix_actuel = data['Close'].iloc[-1]
        ma20 = data['Close'].rolling(window=20).mean().iloc[-1]
        signal = "ACHAT" if prix_actuel > ma20 else "VENTE"
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Prix Actuel", f"{prix_actuel:.2f} €")
        m2.metric("Moyenne Mobile (20j)", f"{ma20:.2f} €")
        
        color = "green" if signal == "ACHAT" else "red"
        m3.markdown(f"**Signal de tendance :**\n<h2 style='color:{color};'>{signal}</h2>", unsafe_allow_html=True)

        # --- GRAPHIQUE ---
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Cours de clôture", line=dict(color="#00ffcc")))
        fig.update_layout(title=f"Évolution 6 mois - {details.get('longName')}", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        
        # --- DESCRIPTION DE L'ENTREPRISE ---
        with st.expander("En savoir plus sur cette entreprise"):
            st.write(details.get('longBusinessSummary', 'Pas de description disponible.'))
    else:
        st.error("Erreur : Impossible de trouver ce ticker. Vérifiez qu'il s'agit bien d'une action cotée (ex: ajoutez .PA pour Paris).")

st.sidebar.markdown("""
**Aide BoursoBank :**
Pour trouver une action, utilisez le **Code ISIN** affiché dans le récapitulatif. C'est la méthode la plus fiable.
""")
