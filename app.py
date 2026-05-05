import streamlit as st
import pandas as pd
from collections import Counter
from utils import load_cables_df, load_lp_df

st.set_page_config(
    page_title="Submarine Cables Intelligence",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 2rem; color: #00d4ff; font-weight: 800; }
[data-testid="stMetricLabel"] { font-size: 0.85rem; color: #aac4de; }
.story-box {
    background: linear-gradient(135deg, #0d1b2a 0%, #1b3a5c 100%);
    border-left: 4px solid #00d4ff;
    border-radius: 8px;
    padding: 20px 25px;
    margin: 10px 0;
}
.nav-box {
    background: #111827;
    border: 1px solid #2a4a6c;
    border-radius: 10px;
    padding: 18px 22px;
}
</style>
""", unsafe_allow_html=True)

# ─── Data Loading ──────────────────────────────────────────────────────────────
df_cables = load_cables_df()
df_lp     = load_lp_df()

all_owners = []
for owners in df_cables["owners"]:
    all_owners.extend(owners)

# ─── Header ──────────────────────────────────────────────────────────────────
st.title("🌊 Submarine Cables Intelligence")
st.markdown(
    "*99% du trafic internet mondial transite par des câbles sous-marins. "
    "Cette analyse explore leur géographie, leurs acteurs et leurs vulnérabilités.*"
)
st.divider()

# ─── KPIs ────────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("🔌 Câbles répertoriés", len(df_cables))
c2.metric("📍 Points d'atterrissage", len(df_lp))
c3.metric("🌍 Pays connectés", df_lp["country"].nunique())
c4.metric("🏢 Propriétaires uniques", len(set(all_owners)))
c5.metric("📡 Source", "TeleGeography")
st.divider()

# ─── Story + Nav ─────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("🎯 Pourquoi ce sujet ?")
    st.markdown("""
<div class="story-box">

**Des fils invisibles au fond des océans** — et pourtant, sans eux, internet s'arrête.

Les câbles sous-marins constituent l'infrastructure la plus critique et la moins visible
de l'économie numérique mondiale. Cette analyse data soulève des enjeux concrets :

- 🛡️ **Géopolitique** : La Chine, les USA et l'Europe se livrent une guerre des câbles
- 💰 **Économique** : Google, Meta et Amazon financent leurs propres câbles privés
- ⚠️ **Sécurité** : Des points de rupture concentrent des dizaines de câbles (Détroit de Malacca, Suez…)
- 🌊 **Environnemental** : 400+ câbles reposent au fond des océans
</div>
    """, unsafe_allow_html=True)

with col2:
    st.subheader("📌 Pages de l'application")
    st.markdown("""
<div class="nav-box">

**🗺️ Carte Mondiale**
→ Visualisation des points d'atterrissage et routes

**📈 Évolution Temporelle**
→ Histoire des déploiements par décennie

**🏢 Acteurs Majeurs**
→ Top propriétaires, GAFAM vs opérateurs télécoms

**⚠️ Points Critiques**
→ Hubs de concentration, zones de vulnérabilité
</div>
    """, unsafe_allow_html=True)

st.divider()

# ─── Quick facts ─────────────────────────────────────────────────────────────
st.subheader("📊 Aperçu rapide")
col1, col2, col3 = st.columns(3)

with col1:
    top_countries = df_lp.groupby("country")["n_cables"].sum().nlargest(5).reset_index()
    top_countries.columns = ["Pays", "Nb câbles"]
    st.markdown("**🌍 Top 5 pays connectés**")
    st.dataframe(top_countries, hide_index=True, use_container_width=True)

with col2:
    owner_counts = Counter(all_owners).most_common(5)
    df_top_owners = pd.DataFrame(owner_counts, columns=["Propriétaire", "Nb câbles"])
    st.markdown("**🏢 Top 5 propriétaires**")
    st.dataframe(df_top_owners, hide_index=True, use_container_width=True)

with col3:
    st.markdown("**📅 Câbles récents (2023+)**")
    recent = df_cables[
        df_cables["rfs"].str.contains(r"202[3-9]|203", na=False, regex=True)
    ][["name", "rfs", "n_lp"]].head(5)
    recent.columns = ["Câble", "Mise en service", "Points"]
    st.dataframe(recent, hide_index=True, use_container_width=True)
