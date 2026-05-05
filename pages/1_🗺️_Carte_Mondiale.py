import streamlit as st
import plotly.graph_objects as go
from utils import load_cables_df, load_lp_df

st.set_page_config(page_title="Carte Mondiale", page_icon="🗺️", layout="wide")

df_cables = load_cables_df()
df_lp     = load_lp_df()

# Drop landing points without coordinates
df_lp = df_lp[(df_lp["lat"] != 0) | (df_lp["lon"] != 0)]

# ─── Header ──────────────────────────────────────────────────────────────────
st.title("🗺️ Carte Mondiale des Câbles Sous-Marins")
st.markdown("Visualisation des **points d'atterrissage** et des **routes** des câbles.")

# ─── Sidebar filters ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Filtres")
    cable_options = ["(Tous les points d'atterrissage)"] + sorted(df_cables["name"].tolist())
    selected_cable = st.selectbox("🔌 Afficher un câble spécifique", cable_options)

    color_by = st.radio(
        "🎨 Colorier les points par",
        ["Nombre de câbles", "Pays"],
        horizontal=True,
    )
    st.divider()
    st.info("💡 Sélectionnez un câble pour mettre en évidence ses points d'atterrissage.")

# ─── Build map ───────────────────────────────────────────────────────────────
fig = go.Figure()

# -- Landing points --
if color_by == "Nombre de câbles":
    marker_color = df_lp["n_cables"]
    colorscale   = "Viridis"
    cbar_title   = "Nb câbles"
    showscale    = True
else:
    cats = df_lp["country"].astype("category")
    marker_color = cats.cat.codes
    colorscale   = "Turbo"
    cbar_title   = "Pays"
    showscale    = False

fig.add_trace(go.Scattergeo(
    lat=df_lp["lat"],
    lon=df_lp["lon"],
    mode="markers",
    marker=dict(
        size=df_lp["n_cables"].clip(3, 18),
        color=marker_color,
        colorscale=colorscale,
        showscale=showscale,
        colorbar=dict(title=cbar_title, x=0.92),
        line=dict(width=0.5, color="white"),
        opacity=0.85,
    ),
    text=df_lp["name"] + "<br>" + df_lp["country"] + "<br>" + df_lp["n_cables"].astype(str) + " câbles",
    hovertemplate="<b>%{text}</b><extra></extra>",
    name="Points d'atterrissage",
))

# -- Highlight selected cable's landing points --
if selected_cable != "(Tous les points d'atterrissage)":
    cable_row = df_cables[df_cables["name"] == selected_cable].iloc[0]
    lp_ids    = set(cable_row["landing_point_ids"])
    df_sel    = df_lp[df_lp["id"].isin(lp_ids)]

    fig.add_trace(go.Scattergeo(
        lat=df_sel["lat"],
        lon=df_sel["lon"],
        mode="markers",
        marker=dict(size=14, color="#ff6b6b", line=dict(width=1.5, color="white")),
        text=df_sel["name"] + "<br>" + df_sel["country"],
        hovertemplate="<b>%{text}</b><extra></extra>",
        name=selected_cable,
    ))

    owners_str = ", ".join(cable_row["owners"][:5]) or "N/A"
    st.info(
        f"**{selected_cable}** — Mise en service : `{cable_row['rfs'] or 'N/A'}` · "
        f"Points : `{cable_row['n_lp']}` · Propriétaires : {owners_str}"
    )

# ─── Layout ──────────────────────────────────────────────────────────────────
fig.update_layout(
    geo=dict(
        showland=True, landcolor="#1a2a3a",
        showocean=True, oceancolor="#0a1520",
        showcountries=True, countrycolor="#2a4a6c",
        showcoastlines=True, coastlinecolor="#3a6a9c",
        bgcolor="#0a1520",
        projection_type="natural earth",
    ),
    paper_bgcolor="#0a1520",
    plot_bgcolor="#0a1520",
    font_color="white",
    margin=dict(l=0, r=0, t=10, b=0),
    height=620,
    legend=dict(bgcolor="rgba(0,0,0,0)", font_color="white"),
)

st.plotly_chart(fig, use_container_width=True)

# ─── Top hubs table ──────────────────────────────────────────────────────────
with st.expander("📋 Top 20 des points d'atterrissage les plus connectés"):
    top_lp = df_lp.nlargest(20, "n_cables")[["name", "country", "n_cables"]].reset_index(drop=True)
    top_lp.columns = ["Point d'atterrissage", "Pays", "Nombre de câbles"]
    st.dataframe(top_lp, use_container_width=True)
