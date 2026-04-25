# Digital Twin

Coach personnel basé sur le **Claude Agent SDK** pour suivre tes objectifs pro et perso.
Application Streamlit + SQLite, déployable en un clic.

## Stack

- **Streamlit** — UI web
- **claude-agent-sdk** (Python) — orchestration de l'agent + outils MCP in-process
- **SQLModel + SQLite** — persistance des objectifs

## Démarrage

```bash
# 1. Dépendances (avec uv ou pip)
pip install -e .

# 2. Variables d'environnement
cp .env.example .env
# édite .env et renseigne ANTHROPIC_API_KEY

# 3. Lancement
streamlit run app.py
```

L'app s'ouvre sur `http://localhost:8501` avec deux onglets :

- **Objectifs** : CRUD sur la liste d'objectifs (catégorie pro/perso, priorité P0/P1/P2,
  horizon, statut, deadline, KPI).
- **Chat avec le Twin** : conversation avec l'agent. Il peut lire et modifier les
  objectifs via les outils MCP (toujours après confirmation).

## Déploiement

- **Streamlit Community Cloud** : push sur GitHub, connecte le repo, ajoute
  `ANTHROPIC_API_KEY` dans les secrets.
- **Fly.io / Render** : `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`.

## Roadmap (v2+)

- Sous-agents spécialisés (`coach-carrière`, `gestion-temps`, `santé`, `finances`)
  délégués depuis le Twin principal.
- Connecteurs externes (calendrier, mails, Notion, GitHub).
- Revue hebdomadaire automatique des objectifs.
