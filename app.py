import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="Terminal PEA Intelligent", layout="wide")

# --- FONCTION MAGIQUE : NOM -> TICKER ---
def trouver_ticker_par_nom(nom):
    try:
        # On interroge l'API de suggestion de Yahoo Finance
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={nom}&quotesCount=1"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = res.json()
        if data['quotes']:
            return data['quotes'][0]['symbol']
    except:
        return None
    return None

# --- INTERFACE ---
st.title("🚀 Terminal PEA : Recherche par Nom")
st.sidebar.header("🔍 Quelle entreprise ?")

nom_saisi = st.sidebar.text_input("Nom de l'entreprise", value="Air Liquide")

if nom_saisi:
    # 1. On cherche le ticker correspondant
    ticker_officiel = trouver_ticker_par_nom(nom_saisi)
    
    if ticker_officiel:
        # 2. On télécharge les données avec le ticker trouvé
        stock = yf.Ticker(ticker_officiel)
        info = stock.info
        hist = stock.history(period="6mo")

        if not hist.empty:
            # --- RÉCAPITULATIF POUR BOURSOBANK ---
            st.subheader(f"✅ Résultat pour : {info.get('longName', nom_saisi)}")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.success(f"**Code ISIN**\n\n{info.get('isin', 'À vérifier sur Bourso')}")
            with c2:
                st.success(f"**Ticker à utiliser**\n\n{ticker_officiel}")
            with c3:
                st.success(f"**Place boursière**\n\n{info.get('exchange', 'N/A')}")

            st.divider()

            # --- ANALYSE DÉCISIONNELLE ---
            prix_actuel = hist['Close'].iloc[-1]
            ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            signal = "ACHAT" if prix_actuel > ma20 else "VENTE"
            couleur = "green" if signal == "ACHAT" else "red"

            m1, m2, m3 = st.columns(3)
            m1.metric("Prix Actuel", f"{prix_actuel:.2f} €")
            m2.metric("Moyenne Mobile (20j)", f"{ma20:.2f} €")
            m3.markdown(f"**Signal Trade :**\n<h2 style='color:{couleur};'>{signal}</h2>", unsafe_allow_html=True)

            # --- GRAPHIQUE ---
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name="Cours", line=dict(color="#00D4FF", width=2)))
            fig.update_layout(title="Historique 6 mois", template="plotly_dark", height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # --- INFOS COMPLÉMENTAIRES ---
            with st.expander("📝 Détails de l'entreprise"):
                st.write(info.get('longBusinessSummary', 'Pas de résumé.'))
        else:
            st.error("Données de marché indisponibles pour ce titre.")
    else:
        st.error("Impossible de trouver cette entreprise. Essayez d'être plus précis (ex: 'LVMH' au lieu de 'Louis Vuitton').")

st.sidebar.warning("Vérifiez toujours que le Code ISIN correspond bien sur BoursoBank avant de passer l'ordre.")
