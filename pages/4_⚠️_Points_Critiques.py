import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils import load_cables_df, load_lp_df

st.set_page_config(page_title="Points Critiques", page_icon="⚠️", layout="wide")

df_cables = load_cables_df()
df_lp     = load_lp_df()

# Drop landing points without coordinates for map tabs
df_lp_geo = df_lp[(df_lp["lat"] != 0) | (df_lp["lon"] != 0)].copy()

# ─── Country-level aggregation ────────────────────────────────────────────────
country_stats = df_lp.groupby("country").agg(
    n_landing_points=("id", "count"),
    total_cables=("n_cables", "sum"),
    max_cables_per_point=("n_cables", "max"),
).reset_index().sort_values("total_cables", ascending=False)

# ─── Vulnerability score ─────────────────────────────────────────────────────
country_lp_count = df_lp.groupby("country")["id"].count()
df_lp_scored = df_lp_geo.copy()
df_lp_scored["country_lp_count"] = df_lp_scored["country"].map(country_lp_count)
df_lp_scored["vuln_score"] = (
    df_lp_scored["n_cables"] * (10 / df_lp_scored["country_lp_count"].clip(1))
).round(1)

st.title("⚠️ Points Critiques & Vulnérabilités")
st.markdown(
    "L'internet mondial repose sur quelques **hubs concentrant des dizaines de câbles**. "
    "Une rupture sur ces points peut couper des continents entiers."
)

tab1, tab2, tab3 = st.tabs(["🌡️ Carte de Chaleur", "📊 Top Hubs Critiques", "🌍 Analyse par Pays"])

with tab1:
    st.markdown("#### Concentration des câbles par point d'atterrissage")
    st.markdown("*Plus un point est rouge, plus il est stratégique — et vulnérable.*")

    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
        lat=df_lp_scored["lat"],
        lon=df_lp_scored["lon"],
        mode="markers",
        marker=dict(
            size=df_lp_scored["n_cables"].clip(4, 30),
            color=df_lp_scored["n_cables"],
            colorscale=[
                [0, "#003380"], [0.3, "#0066ff"],
                [0.6, "#ffaa00"], [0.85, "#ff4400"], [1.0, "#ff0000"],
            ],
            showscale=True,
            colorbar=dict(title="Nb câbles", x=0.92),
            opacity=0.85,
            line=dict(width=0.5, color="white"),
        ),
        text=(
            "<b>" + df_lp_scored["name"] + "</b><br>" +
            df_lp_scored["country"] + "<br>" +
            df_lp_scored["n_cables"].astype(str) + " câbles"
        ),
        hovertemplate="%{text}<extra></extra>",
    ))
    fig.update_layout(
        geo=dict(
            showland=True, landcolor="#1a2a3a",
            showocean=True, oceancolor="#071015",
            showcountries=True, countrycolor="#1e3a5f",
            bgcolor="#071015",
            projection_type="natural earth",
        ),
        paper_bgcolor="#071015",
        font_color="white",
        margin=dict(l=0, r=0, t=10, b=0),
        height=540,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.error(
        "🚨 **Points ultra-critiques identifiés** : Marseille, Singapour, Alexandrie, Mumbai et "
        "Tôkyô concentrent chacun entre 15 et 25 câbles — des points de défaillance unique (SPOF) "
        "pour des régions entières."
    )

with tab2:
    col1, col2 = st.columns([2, 1])

    with col1:
        top_hubs = df_lp_scored.nlargest(25, "n_cables")[
            ["name", "country", "n_cables", "vuln_score"]
        ].reset_index(drop=True)

        fig2 = go.Figure()
        fig2.add_bar(
            x=top_hubs["n_cables"],
            y=top_hubs["name"],
            orientation="h",
            marker=dict(
                color=top_hubs["n_cables"],
                colorscale=[[0, "#003380"], [0.5, "#ffaa00"], [1, "#ff0000"]],
                showscale=False,
            ),
            text=top_hubs["country"],
            textposition="outside",
        )
        fig2.update_layout(
            title="Top 25 points d'atterrissage (par nombre de câbles)",
            paper_bgcolor="#0d1b2a", plot_bgcolor="#0d1b2a",
            font_color="white", height=700,
            yaxis={"categoryorder": "total ascending"},
            xaxis=dict(showgrid=True, gridcolor="#1e3a5f"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown("### 🎯 Score de Vulnérabilité")
        st.markdown(
            "Formule : `nb_câbles × (10 / nb_points_du_pays)`\n\n"
            "Un score élevé = beaucoup de câbles + peu d'alternatives dans le pays."
        )
        top_vuln = df_lp_scored.nlargest(15, "vuln_score")[
            ["name", "country", "n_cables", "vuln_score"]
        ].reset_index(drop=True)
        top_vuln.columns = ["Point", "Pays", "Câbles", "Score"]
        st.dataframe(top_vuln, use_container_width=True)

        st.warning(
            "💡 Ce score simplifié illustre la logique d'analyse réseau. "
            "Une vraie analyse inclurait la géographie des fonds marins, "
            "la couverture satellite alternative et les taux de redondance."
        )

with tab3:
    n_countries = st.slider("Top N pays", 10, 40, 20)
    top_countries = country_stats.head(n_countries).copy()

    fig3 = px.bar(
        top_countries, x="country", y="total_cables",
        color="n_landing_points",
        color_continuous_scale="Blues",
        labels={
            "country": "Pays", "total_cables": "Total câbles",
            "n_landing_points": "Nb points d'atterrissage",
        },
        title=f"Top {n_countries} pays par concentration de câbles",
    )
    fig3.update_layout(
        paper_bgcolor="#0d1b2a", plot_bgcolor="#0d1b2a",
        font_color="white", height=420,
        xaxis=dict(tickangle=-35, showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#1e3a5f"),
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("#### 🗺️ Carte choroplèthe — Pays par nombre de câbles")
    fig4 = px.choropleth(
        country_stats,
        locations="country",
        locationmode="country names",
        color="total_cables",
        color_continuous_scale="YlOrRd",
        labels={"total_cables": "Total câbles", "country": "Pays"},
    )
    fig4.update_layout(
        paper_bgcolor="#0d1b2a", font_color="white",
        geo=dict(bgcolor="#0d1b2a", showframe=False),
        margin=dict(l=0, r=0, t=10, b=0),
        height=430,
        coloraxis_colorbar=dict(title="Câbles"),
    )
    st.plotly_chart(fig4, use_container_width=True)
