import json, os
import pandas as pd
import streamlit as st

DATA_DIR    = os.path.join(os.path.dirname(__file__), "data")
CABLES_PATH = os.path.join(DATA_DIR, "cables.json")
LP_PATH     = os.path.join(DATA_DIR, "landing_points.json")

def _to_list(v):
    if isinstance(v, list):
        return v
    if isinstance(v, str) and v:
        return [o.strip() for o in v.split(",") if o.strip()]
    return []


_MISSING_MSG = (
    "Les données locales sont absentes. "
    "Lance d'abord :\n\n```\npython fetch_data.py\n```"
)


@st.cache_data(show_spinner="Chargement des câbles…")
def load_cables_df() -> pd.DataFrame:
    if not os.path.exists(CABLES_PATH):
        st.error(_MISSING_MSG)
        st.stop()
    with open(CABLES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return pd.DataFrame([{
        "id":       c.get("id", ""),
        "name":     c.get("name", ""),
        "rfs":      c.get("rfs", ""),
        "rfs_year": c.get("rfs_year"),
        "length":   c.get("length", ""),
        "owners":   _to_list(c.get("owners", [])),
        "n_owners": len(_to_list(c.get("owners", []))),
        "n_lp":     c.get("n_lp", len(c.get("landing_points", []))),
        "is_planned": c.get("is_planned", False),
        "landing_point_ids": [lp["id"] if isinstance(lp, dict) else lp
                              for lp in c.get("landing_points", [])],
    } for c in raw])


@st.cache_data(show_spinner="Chargement des points d'atterrissage…")
def load_lp_df() -> pd.DataFrame:
    if not os.path.exists(LP_PATH):
        st.error(_MISSING_MSG)
        st.stop()
    with open(LP_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return pd.DataFrame([{
        "id":       lp.get("id", ""),
        "name":     lp.get("name", ""),
        "country":  lp.get("country", ""),
        "lat":      float(lp.get("lat") or 0),
        "lon":      float(lp.get("lon") or 0),
        "n_cables": lp.get("n_cables", len(lp.get("cables", []))),
        "cables":   lp.get("cables", []),
    } for lp in raw])
