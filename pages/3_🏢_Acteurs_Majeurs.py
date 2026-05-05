import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
from utils import load_cables_df

st.set_page_config(page_title="Acteurs Majeurs", page_icon="🏢", layout="wide")

df = load_cables_df()

# ─── All owners flat list ─────────────────────────────────────────────────────
all_owners = []
for _, row in df.iterrows():
    for owner in row["owners"]:
        all_owners.append({"owner": owner, "cable": row["name"], "rfs": row["rfs"], "n_lp": row["n_lp"]})

owner_counts = Counter(o["owner"] for o in all_owners)
GAFAM = {"Google", "Meta", "Amazon", "Microsoft", "Apple"}

def get_category(owner):
    if owner in GAFAM:
        return "🔴 GAFAM"
    for kw in ["Telecom", "Telecoms", "Telekom", "Orange", "AT&T", "NTT", "Verizon",
               "BT ", "Deutsche", "Telia", "Singtel", "STC", "Vodafone", "China",
               "KDDI", "Softbank", "Lumen", "Zayo", "GTT"]:
        if kw.lower() in owner.lower():
            return "🔵 Opérateur Télécoms"
    return "🟡 Autre / Inconnu"

st.title("🏢 Acteurs Majeurs des Câbles Sous-Marins")
st.markdown("Qui finance, qui contrôle, et comment le pouvoir se redistribue entre GAFAM et opérateurs historiques.")

tab1, tab2, tab3 = st.tabs(["🏆 Top Propriétaires", "⚔️ GAFAM vs Télécoms", "🔍 Zoom sur un acteur"])

with tab1:
    n_top = st.slider("Nombre d'acteurs à afficher", 10, 40, 20)
    top_owners = pd.DataFrame(owner_counts.most_common(n_top), columns=["Propriétaire", "Nb câbles"])
    top_owners["Catégorie"] = top_owners["Propriétaire"].apply(get_category)

    color_map = {"🔴 GAFAM": "#ff4444", "🔵 Opérateur Télécoms": "#00d4ff", "🟡 Autre / Inconnu": "#ffa500"}

    fig = px.bar(
        top_owners, x="Nb câbles", y="Propriétaire", orientation="h",
        color="Catégorie", color_discrete_map=color_map,
        labels={"Propriétaire": "", "Nb câbles": "Nombre de câbles"},
    )
    fig.update_layout(
        paper_bgcolor="#0d1b2a", plot_bgcolor="#0d1b2a",
        font_color="white", height=620,
        yaxis={"categoryorder": "total ascending"},
        legend=dict(bgcolor="rgba(0,0,0,0)", title=""),
        xaxis=dict(showgrid=True, gridcolor="#1e3a5f"),
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    gafam_cables = sum(1 for o in all_owners if o["owner"] in GAFAM)
    telco_cables = sum(1 for o in all_owners if get_category(o["owner"]) == "🔵 Opérateur Télécoms")
    other_cables = len(all_owners) - gafam_cables - telco_cables

    col1, col2 = st.columns(2)
    with col1:
        fig2 = go.Figure(go.Pie(
            labels=["GAFAM", "Opérateurs Télécoms", "Autres"],
            values=[gafam_cables, telco_cables, other_cables],
            marker_colors=["#ff4444", "#00d4ff", "#ffa500"],
            hole=0.45,
            textinfo="label+percent",
        ))
        fig2.update_layout(
            title="Part des participations par type d'acteur",
            paper_bgcolor="#0d1b2a", font_color="white", height=380,
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        gafam_detail = {g: owner_counts.get(g, 0) for g in GAFAM if owner_counts.get(g, 0) > 0}
        if gafam_detail:
            fig3 = go.Figure(go.Bar(
                x=list(gafam_detail.keys()),
                y=list(gafam_detail.values()),
                marker_color=["#ff4444", "#4466ff", "#ff9900", "#00aa44", "#888"],
                text=list(gafam_detail.values()),
                textposition="outside",
            ))
            fig3.update_layout(
                title="Câbles GAFAM détaillés",
                paper_bgcolor="#0d1b2a", plot_bgcolor="#0d1b2a",
                font_color="white", height=380,
                yaxis=dict(showgrid=True, gridcolor="#1e3a5f"),
            )
            st.plotly_chart(fig3, use_container_width=True)

    st.info(
        "📌 **Enjeu stratégique** : Google possède ou co-finance +20 câbles. "
        "Cette verticalisation permet aux GAFAM de contrôler leur latence, "
        "leur bande passante et de réduire leur dépendance aux opérateurs traditionnels."
    )

with tab3:
    all_owner_names = sorted(owner_counts.keys())
    selected_owner = st.selectbox(
        "Choisir un acteur", all_owner_names,
        index=all_owner_names.index("Google") if "Google" in all_owner_names else 0,
    )

    owner_cables = df[df["owners"].apply(lambda owners: selected_owner in owners)].copy()

    if owner_cables.empty:
        st.warning("Aucun câble trouvé pour cet acteur.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("🔌 Câbles", len(owner_cables))
        col2.metric("📍 Moy. points / câble", f"{owner_cables['n_lp'].mean():.1f}")

        co_investors = []
        for _, row in owner_cables.iterrows():
            for o in row["owners"]:
                if o != selected_owner:
                    co_investors.append(o)

        col3.metric("🤝 Co-investisseurs uniques", len(set(co_investors)))

        st.markdown(f"### Câbles de **{selected_owner}**")
        display_df = owner_cables[["name", "rfs", "n_lp", "owners"]].copy()
        display_df["owners"] = display_df["owners"].apply(lambda x: ", ".join(x[:4]))
        display_df.columns = ["Câble", "Mise en service", "Points d'atterrissage", "Co-propriétaires"]
        st.dataframe(display_df.reset_index(drop=True), use_container_width=True)

        if co_investors:
            top_co = Counter(co_investors).most_common(10)
            df_co = pd.DataFrame(top_co, columns=["Partenaire", "Câbles partagés"])
            fig4 = px.bar(df_co, x="Câbles partagés", y="Partenaire", orientation="h",
                          color_discrete_sequence=["#00d4ff"],
                          title=f"Top partenaires de {selected_owner}")
            fig4.update_layout(
                paper_bgcolor="#0d1b2a", plot_bgcolor="#0d1b2a",
                font_color="white", height=350,
                yaxis={"categoryorder": "total ascending"},
            )
            st.plotly_chart(fig4, use_container_width=True)
