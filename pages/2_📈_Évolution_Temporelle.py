import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
from utils import load_cables_df

st.set_page_config(page_title="Évolution Temporelle", page_icon="📈", layout="wide")

df = load_cables_df()

# ─── Parse year ──────────────────────────────────────────────────────────────
def extract_year(rfs_str):
    if not rfs_str:
        return None
    m = re.search(r"(1[89]\d{2}|20[0-3]\d)", str(rfs_str))
    return int(m.group(1)) if m else None

df["year"] = df["rfs"].apply(extract_year)
df_dated = df[df["year"].notna()].copy()
df_dated["year"] = df_dated["year"].astype(int)
df_dated["decade"] = (df_dated["year"] // 10 * 10).astype(str) + "s"

st.title("📈 Évolution Temporelle des Câbles Sous-Marins")
st.markdown("Comment le réseau mondial a évolué — de l'ère téléphonique à l'explosion internet.")

if df_dated.empty:
    st.warning("Aucune donnée temporelle disponible.")
    st.stop()

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Options")
    year_min = int(df_dated["year"].min())
    year_max = int(df_dated["year"].max())
    year_range = st.slider(
        "Période",
        year_min,
        year_max,
        (max(1990, year_min), year_max),
    )
    show_cumul = st.checkbox("Afficher la courbe cumulée", value=True)

df_filtered = df_dated[df_dated["year"].between(*year_range)]

# ─── Tab layout ──────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Déploiements par année", "🗓️ Analyse par décennie", "🏢 Évolution des acteurs"])

with tab1:
    yearly = df_filtered.groupby("year").size().reset_index(name="count")
    yearly["cumul"] = yearly["count"].cumsum()

    if show_cumul:
        fig = go.Figure()
        fig.add_bar(x=yearly["year"], y=yearly["count"], name="Nouveaux câbles",
                    marker_color="#00d4ff", opacity=0.8)
        fig.add_scatter(x=yearly["year"], y=yearly["cumul"], name="Total cumulé",
                        line=dict(color="#ff6b6b", width=2.5), yaxis="y2")
        fig.update_layout(
            yaxis=dict(title="Nouveaux câbles / an"),
            yaxis2=dict(title="Total cumulé", overlaying="y", side="right"),
        )
    else:
        fig = px.bar(yearly, x="year", y="count",
                     labels={"year": "Année", "count": "Nouveaux câbles"},
                     color_discrete_sequence=["#00d4ff"])

    fig.update_layout(
        paper_bgcolor="#0d1b2a", plot_bgcolor="#0d1b2a",
        font_color="white", height=420,
        xaxis=dict(showgrid=False),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig, use_container_width=True)

    peak_year  = int(yearly.loc[yearly["count"].idxmax(), "year"])
    peak_count = int(yearly["count"].max())
    st.success(
        f"📌 **Pic de déploiement : {peak_year}** avec **{peak_count} câbles** mis en service — "
        "coïncide avec l'explosion des besoins en bande passante (cloud, streaming, 5G)."
    )

with tab2:
    decade_df = df_filtered.groupby("decade").agg(
        count=("name", "count"),
        avg_lp=("n_lp", "mean"),
        avg_owners=("n_owners", "mean"),
    ).reset_index()

    col1, col2 = st.columns(2)
    with col1:
        fig2 = px.bar(decade_df, x="decade", y="count",
                      labels={"decade": "Décennie", "count": "Nombre de câbles"},
                      color="count", color_continuous_scale="Blues",
                      title="Câbles déployés par décennie")
        fig2.update_layout(paper_bgcolor="#0d1b2a", plot_bgcolor="#0d1b2a",
                           font_color="white", showlegend=False, height=350)
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        fig3 = go.Figure()
        fig3.add_bar(x=decade_df["decade"], y=decade_df["avg_lp"].round(1),
                     name="Moy. points d'atterrissage", marker_color="#00d4ff")
        fig3.add_bar(x=decade_df["decade"], y=decade_df["avg_owners"].round(1),
                     name="Moy. propriétaires", marker_color="#ff6b6b")
        fig3.update_layout(
            title="Complexité moyenne des câbles",
            barmode="group",
            paper_bgcolor="#0d1b2a", plot_bgcolor="#0d1b2a",
            font_color="white", height=350,
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("""
    > 💡 **Observation** : Les câbles modernes (2010+) connectent davantage de pays
    et impliquent plus de co-investisseurs — signe de la complexification géopolitique du secteur.
    """)

with tab3:
    gafam = {"Google", "Meta", "Amazon", "Microsoft", "Apple"}

    def classify_owner(owners_list):
        if any(g in owners_list for g in gafam):
            return "GAFAM"
        elif len(owners_list) > 3:
            return "Consortium public"
        elif len(owners_list) == 0:
            return "Inconnu"
        else:
            return "Opérateur Télécoms"

    df_filtered = df_filtered.copy()
    df_filtered["type"] = df_filtered["owners"].apply(classify_owner)
    type_year = df_filtered.groupby(["year", "type"]).size().reset_index(name="count")

    color_map = {
        "GAFAM": "#ff6b6b",
        "Consortium public": "#00d4ff",
        "Opérateur Télécoms": "#ffa500",
        "Inconnu": "#888",
    }

    fig4 = px.bar(type_year, x="year", y="count", color="type",
                  color_discrete_map=color_map, barmode="stack",
                  labels={"year": "Année", "count": "Câbles", "type": "Type d'acteur"},
                  title="Montée en puissance des GAFAM dans les câbles sous-marins")
    fig4.update_layout(
        paper_bgcolor="#0d1b2a", plot_bgcolor="#0d1b2a",
        font_color="white", height=440,
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig4, use_container_width=True)
    st.warning(
        "📌 **Tendance clé** : Depuis 2016, Google, Meta et Amazon financent des câbles entiers — "
        "une rupture avec le modèle historique des consortiums de télécoms."
    )
