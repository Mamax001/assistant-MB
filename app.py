import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="Mon Journal PEA Pro", layout="wide")

# --- INITIALISATION DE L'HISTORIQUE DES TRADES ---
if 'historique_trades' not in st.session_state:
    st.session_state.historique_trades = []

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
st.title("📊 Assistant PEA & Journal de Bord")
st.sidebar.header("⚙️ Nouveau Trade")

nom_saisi = st.sidebar.text_input("Nom de l'entreprise", value="Air Liquide")
budget_total = st.sidebar.number_input("Budget (€)", min_value=10, value=1000)

if nom_saisi:
    ticker = trouver_ticker(nom_saisi)
    
    if ticker:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")

        if not hist.empty:
            prix_actuel = float(hist['Close'].iloc[-1])
            nb_actions = int(budget_total // prix_actuel)
            total_reel = nb_actions * prix_actuel
            isin = info.get('isin', 'N/A')

            # --- RÉCAPITULATIF BOURSOBANK ---
            st.subheader(f"🏢 Ordre BoursoBank : {info.get('longName', nom_saisi)}")
            c1, c2, c3 = st.columns(3)
            c1.info(f"**Code ISIN**\n\n{isin}")
            c2.info(f"**Ticker**\n\n{ticker}")
            c3.info(f"**Cours actuel**\n\n{prix_actuel:.2f} €")

            # --- STRATÉGIE ---
            st.markdown("### 💡 Stratégie suggérée")
            s1, s2, s3 = st.columns(3)
            s1.metric("Quantité", f"{nb_actions} actions")
            s2.metric("Total à investir", f"{total_reel:.2f} €")
            
            ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            signal = "ACHAT" if prix_actuel > ma20 else "ATTENTE"
            couleur = "green" if signal == "ACHAT" else "orange"
            s3.markdown(f"**Signal :** <span style='color:{couleur}; font-weight:bold;'>{signal}</span>", unsafe_allow_html=True)

            # --- BOUTON D'AJOUT AU TABLEAU ---
            if st.button("➕ Ajouter ce trade au tableau récapitulatif"):
                nouveau_trade = {
                    "Date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                    "Entreprise": info.get('longName', nom_saisi),
                    "ISIN": isin,
                    "Quantité": nb_actions,
                    "Prix Achat (€)": round(prix_actuel, 2),
                    "Total (€)": round(total_reel, 2),
                    "Signal": signal
                }
                st.session_state.historique_trades.append(nouveau_trade)
                st.success("Trade ajouté au tableau ci-dessous !")

            # --- GRAPHIQUE ---
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], line=dict(color="#00D4FF")))
            fig.update_layout(title="Cours sur 1 an", template="plotly_dark", height=300)
            st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- TABLEAU RÉCAPITULATIF DES TRADES ---
st.subheader("📋 Historique des trades analysés")

if st.session_state.historique_trades:
    df_recap = pd.DataFrame(st.session_state.historique_trades)
    st.table(df_recap)
    
    if st.button("🗑️ Effacer l'historique"):
        st.session_state.historique_trades = []
        st.rerun()
else:
    st.write("Aucun trade ajouté pour le moment.")
