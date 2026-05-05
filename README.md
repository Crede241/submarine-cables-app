# 🌊 Submarine Cables Intelligence

Application Streamlit d'analyse des câbles sous-marins mondiaux.
Données en temps réel via l'API publique de [TeleGeography](https://www.submarinecablemap.com/).

## 📦 Installation

```bash
# 1. Créer un environnement virtuel (recommandé)
python -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer l'application
streamlit run app.py
```

L'application s'ouvre automatiquement sur http://localhost:8501

## 📂 Structure

```
submarine_cables_app/
├── app.py                          ← Page d'accueil + KPIs
├── pages/
│   ├── 1_🗺️_Carte_Mondiale.py      ← Carte interactive + routes
│   ├── 2_📈_Évolution_Temporelle.py ← Analyse temporelle
│   ├── 3_🏢_Acteurs_Majeurs.py      ← Top propriétaires, GAFAM vs Télécoms
│   └── 4_⚠️_Points_Critiques.py    ← Hubs et vulnérabilités
├── requirements.txt
└── README.md
```

## 🗂️ Source des données

- **API TeleGeography** : https://www.submarinecablemap.com/api/v3/
- Données chargées en temps réel, mises en cache 1h
- ~600 câbles répertoriés, ~1500 points d'atterrissage

## 🛠️ Stack technique

| Outil | Usage |
|---|---|
| `streamlit` | Interface web |
| `pandas` | Manipulation des données |
| `plotly` | Visualisations interactives |
| `requests` | Appels API |
