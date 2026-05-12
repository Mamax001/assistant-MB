import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

# --- CONFIGURATION PRO ---
st.set_page_config(page_title="PEA Terminal Pro", layout="wide", initial_sidebar_state="expanded")

if 'portefeuille' not in st.session_state:
    st.session_state.portefeuille = []

# --- MOTEUR DE RECHERCHE & CALCULS ---
def recherche_universelle(nom):
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={nom}&quotesCount=1"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = res.json()
        if data['quotes']:
            return data['quotes'][0]['symbol'], data['quotes'][0].get('longname', nom)
    except: return None, None
    return None, None

def calculer_frais(montant):
    # Simulation tarif 'Découverte' BoursoBank (adaptable)
    if montant <= 500: return 1.99
    return montant * 0.005 # 0.5% au-delà

def analyse_expert_ia(info, hist):
    prix = float(hist['Close'].iloc[-1])
    ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
    ma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
    rendement = info.get('dividendRate', 0)
    
    score = 0
    if prix > ma20: score += 1
    if ma20 > ma50: score += 1
    if info.get('returnOnEquity', 0) > 0.15: score += 1
    
    # Verdict
    if score >= 2: verdict, couleur = "ACHAT FORT ✅", "green"
    elif score == 1: verdict, couleur = "OBSERVATION ⏳", "orange"
    else: verdict, couleur = "VENTE / ATTENTE ⚠️", "red"
    
    # Texte de stratégie
    stop_loss = prix * 0.92 # -8% par défaut
    objectif = prix * 1.15 # +15%
    
    synthèse = f"""
    **Analyse Fondamentale & Technique :**
    - **Tendance :** {"Haussière" if prix > ma20 else "Baissière/Neutre"}.
    - **Rentabilité :** {info.get('sector', 'N/A')} avec un rendement dividende de {info.get('dividendYield', 0)*100:.2f}%.
    - **Sécurité :** Stop-loss conseillé à **{stop_loss:.2f} €**. Objectif de sortie à **{objectif:.2f} €**.
    """
    return verdict, couleur, synthèse, stop_loss

# --- INTERFACE PRINCIPALE ---
st.title("🏛️ Terminal PEA Expert : Décisionnel & Exécution")

with st.sidebar:
    st.header("🔍 Recherche & Budget")
    nom_saisi = st.text_input("Nom de l'entreprise", placeholder="Ex: LVMH, Total, Air Liquide...")
    budget = st.number_input("Budget d'investissement (€)", min_value=50, value=1000, step=50)
    st.divider()
    st.info("💡 Utilisez ce terminal pour valider vos ordres BoursoBank en 10 secondes.")

if nom_saisi:
    ticker, nom_propre = recherche_universelle(nom_saisi)
    if ticker:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        
        if not hist.empty:
            info = stock.info
            prix_actuel = float(hist['Close'].iloc[-1])
            verdict, couleur, synthese, stop_loss = analyse_expert_ia(info, hist)
            
            # --- ZONE DE DÉCISION ---
            st.subheader(f"💎 Analyse Stratégique : {nom_propre}")
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown(f"<h2 style='color:{couleur};'>{verdict}</h2>", unsafe_allow_html=True)
                st.metric("Prix Direct", f"{prix_actuel:.2f} €")
            with c2:
                st.markdown(synthese)

            # --- CALCULATEUR D'ORDRE BOURSOBANK ---
            st.subheader("📝 Préparation de l'ordre (BoursoBank)")
            frais = calculer_frais(budget)
            nb_actions = int((budget - frais) // prix_actuel)
            total_reel = (nb_actions * prix_actuel) + frais
            
            df_ordre = pd.DataFrame({
                "Paramètre d'exécution": ["Code ISIN", "Quantité à saisir", "Prix Limite conseillé", "Frais estimés", "Coût total réel"],
                "Valeur": [info.get('isin', 'N/A'), nb_actions, f"{prix_actuel:.2f} €", f"{frais:.2f} €", f"{total_reel:.2f} €"]
            })
            st.table(df_ordre)

            if st.button("📈 Enregistrer dans le journal de bord"):
                st.session_state.portefeuille.append({
                    "Date": pd.Timestamp.now().strftime("%d/%m/%Y"),
                    "Entreprise": nom_propre,
                    "ISIN": info.get('isin', 'N/A'),
                    "Secteur": info.get('sector', 'N/A'),
                    "Quantité": nb_actions,
                    "PRU": round(prix_actuel, 2),
                    "Stop-Loss": f"{stop_loss:.2f}€"
                })
                st.success("Trade mémorisé !")

            # Graphique interactif
            st.plotly_chart(go.Figure(go.Scatter(x=hist.index, y=hist['Close'], line=dict(color="#00D4FF"))).update_layout(height=300, template="plotly_dark", margin=dict(l=0,r=0,t=0,b=0)), use_container_width=True)
    else:
        st.error("Entreprise introuvable. Soyez plus spécifique.")

st.divider()

# --- DASHBOARD DE SUIVI & EXPORT ---
st.subheader("📋 Dashboard de Session & Diversification")
if st.session_state.portefeuille:
    df_recap = pd.DataFrame(st.session_state.portefeuille)
    
    col_tab, col_pie = st.columns([2, 1])
    with col_tab:
        st.dataframe(df_recap, use_container_width=True)
    with col_pie:
        fig_pie = go.Figure(data=[go.Pie(labels=df_recap['Secteur'], hole=.3)])
        fig_pie.update_layout(title="Répartition Sectorielle", height=300, template="plotly_dark", showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Export spécial Notion
    md_table = df_recap.to_markdown(index=False)
    export_notion = f"# 📘 Journal de Trading PEA\n\n{md_table}\n\n*Analyse générée le {pd.Timestamp.now().strftime('%d/%m/%Y')}*"
    
    st.download_button("📥 Exporter vers Notion (.md)", data=export_notion, file_name="pea_notion_export.md")
else:
    st.info("Aucun trade dans le journal pour le moment.")
