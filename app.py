"""Streamlit entry point for the Digital Twin app.

Run with: `streamlit run app.py`
"""

from datetime import date

import streamlit as st
from dotenv import load_dotenv

from digital_twin import db
from digital_twin.agent import chat
from digital_twin.models import CATEGORIES, HORIZONS, PRIORITIES, STATUSES

load_dotenv()
db.init_db()

st.set_page_config(page_title="Digital Twin", page_icon=None, layout="wide")
st.title("Digital Twin")
st.caption("Coach personnel pour tes objectifs pro et perso.")

tab_objectives, tab_chat = st.tabs(["Objectifs", "Chat avec le Twin"])


# ---------- Objectives tab ----------
with tab_objectives:
    col_list, col_form = st.columns([2, 1])

    with col_form:
        st.subheader("Nouvel objectif")
        with st.form("add_objective", clear_on_submit=True):
            title = st.text_input("Titre", max_chars=120)
            description = st.text_area("Description", height=80)
            category = st.selectbox("Catégorie", CATEGORIES)
            priority = st.selectbox("Priorité", PRIORITIES, index=1)
            horizon = st.selectbox("Horizon", HORIZONS, index=1)
            status = st.selectbox("Statut", STATUSES, index=0)
            deadline = st.date_input("Deadline (optionnelle)", value=None)
            kpi = st.text_input("KPI / mesure de succès", max_chars=160)
            submitted = st.form_submit_button("Ajouter")
            if submitted:
                if not title.strip():
                    st.error("Le titre est obligatoire.")
                else:
                    db.upsert_objective(
                        title=title.strip(),
                        description=description.strip() or None,
                        category=category,
                        priority=priority,
                        horizon=horizon,
                        status=status,
                        deadline=deadline if isinstance(deadline, date) else None,
                        kpi=kpi.strip() or None,
                    )
                    st.success("Objectif ajouté.")
                    st.rerun()

    with col_list:
        st.subheader("Mes objectifs")
        filter_status = st.selectbox(
            "Filtrer par statut", ["(tous)", *STATUSES], index=1, key="filter_status"
        )
        filter_category = st.selectbox(
            "Filtrer par catégorie", ["(toutes)", *CATEGORIES], index=0, key="filter_category"
        )
        objectives = db.list_objectives(
            status=None if filter_status == "(tous)" else filter_status,
            category=None if filter_category == "(toutes)" else filter_category,
        )
        if not objectives:
            st.info("Aucun objectif. Ajoute-en un via le formulaire à droite.")
        for obj in objectives:
            with st.container(border=True):
                row = st.columns([4, 1, 1, 1, 1])
                row[0].markdown(f"**{obj.title}**  \n_{obj.description or ''}_")
                row[1].caption(f"prio: {obj.priority}")
                row[1].caption(f"cat: {obj.category}")
                row[2].caption(f"horizon: {obj.horizon}")
                row[2].caption(f"statut: {obj.status}")
                row[3].caption(f"deadline: {obj.deadline or '-'}")
                row[3].caption(f"kpi: {obj.kpi or '-'}")
                if row[4].button("Supprimer", key=f"del_{obj.id}"):
                    db.delete_objective(obj.id)
                    st.rerun()


# ---------- Chat tab ----------
with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.caption(
        "Le Twin a accès en lecture/écriture à ta liste d'objectifs et te recadrera "
        "si tu dérives vers du non-prioritaire."
    )

    if st.button("Réinitialiser la conversation", type="secondary"):
        st.session_state.messages = []
        st.rerun()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Parle à ton Digital Twin..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Réflexion..."):
                response = chat(st.session_state.messages)
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
