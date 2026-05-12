import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="Assistant PEA Stratégique", layout="wide")

# --- FONCTION DE RECHERCHE INTELLIGENTE ---
def trouver_ticker(nom):
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={nom}&quotesCount=1"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = res.json()
        if data['quotes']:
            return data['quotes'][0]['symbol']
    except:
        return None
    return None

# --- INTERFACE ---
st.title("🚀 Mon Assistant PEA Intelligent")
st.sidebar.header("⚙️ Paramètres du Trade")

nom_saisi = st.sidebar.text_input("Nom de l'entreprise (ex: Air Liquide, LVMH)", value="Air Liquide")
budget_total = st.sidebar.number_input("Budget total pour cette ligne (€)", min_value=10, value=1000)

if nom_saisi:
    ticker = trouver_ticker(nom_saisi)
    
    if ticker:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y") # On prend 1 an pour une meilleure strat

        if not hist.empty:
            prix_actuel = hist['Close'].iloc[-1]
            
            # --- RÉCAPITULATIF BOURSOBANK ---
            st.subheader(f"🏢 Infos pour BoursoBank : {info.get('longName', nom_saisi)}")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.info(f"**Code ISIN** (à copier)\n\n{info.get('isin', 'Non disponible')}")
            with c2:
                st.info(f"**Symbole / Ticker**\n\n{ticker}")
            with c3:
                st.info(f"**Place de cotation**\n\n{info.get('exchange', 'N/A')}")

            st.divider()

            # --- STRATÉGIE D'INVESTISSEMENT ---
            st.subheader("💡 Stratégie d'investissement conseillée")
            
            # Calculs stratégiques
            nb_actions = int(budget_total // prix_actuel)
            ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            volatilite = hist['Close'].pct_change().std() * 100
            
            s1, s2, s3 = st.columns(3)
            s1.metric("Quantité à acheter", f"{nb_actions} actions")
            s2.metric("Montant estimé", f"{(nb_actions * prix_actuel):.2f} €")
            
            # Durée suggérée selon la volatilité
            duree = "Long terme (5 ans+)" if volatilite < 2 else "Moyen terme (1-3 ans)"
            s3.metric("Horizon suggéré", duree)

            # Signal Technique
            signal = "ACHAT" if prix_actuel > ma20 else "ATTENTE / VENTE"
            couleur = "green" if signal == "ACHAT" else "orange"
            st.markdown(f"**Conseil immédiat :** <span style='color:{couleur}; font-weight:bold; font-size:20px;'>{signal}</span>", unsafe_allow_html=True)
            
            st.warning(f"👉 **Méthode d'ordre sur BoursoBank :** Utilisez un 'Ordre à cours limité' à **{prix_actuel:.2f} €** pour maîtriser votre prix d'entrée.")

            # --- GRAPHIQUE ---
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name="Cours", line=dict(color="#00D4FF")))
            fig.update_layout(title="Historique du cours (1 an)", template="plotly_dark", height=400)
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.error("Impossible de récupérer les prix historiques.")
    else:
        st.error("Entreprise non trouvée. Essayez d'être plus précis.")
