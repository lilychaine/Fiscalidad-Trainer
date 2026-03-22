import json
import random
from pathlib import Path

import streamlit as st

# ==============================
# CONFIG
# ==============================

st.set_page_config(page_title="Fiscalidad Trainer", layout="centered")

BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_PATH = BASE_DIR / "questions.json"

# ==============================
# LOAD DATA
# ==============================

@st.cache_data
def load_questions():
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

QUESTIONS = load_questions()
SUBJECTS = sorted({q["subject"] for q in QUESTIONS})

# ==============================
# STATE
# ==============================

def init_state():
    defaults = {
        "started": False,
        "mode": None,                 # "simulacro" | "errores"
        "subject": "Todas",
        "queue": [],
        "index": 0,
        "answered": False,
        "selected": None,
        "score_ok": 0,
        "score_bad": 0,
        "wrong_ids": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ==============================
# FUNCTIONS
# ==============================

def filter_questions_by_subject(subject):
    if subject == "Todas":
        return QUESTIONS[:]
    return [q for q in QUESTIONS if q["subject"] == subject]

def build_simulacro(subject, n=20):
    pool = filter_questions_by_subject(subject)
    random.shuffle(pool)
    return pool[:min(n, len(pool))]

def build_error_review(subject, n=20):
    pool = [q for q in QUESTIONS if q["id"] in st.session_state.wrong_ids]
    if subject != "Todas":
        pool = [q for q in pool if q["subject"] == subject]
    random.shuffle(pool)
    return pool[:min(n, len(pool))]

def start_simulacro(subject):
    st.session_state.mode = "simulacro"
    st.session_state.subject = subject
    st.session_state.queue = build_simulacro(subject)
    st.session_state.index = 0
    st.session_state.answered = False
    st.session_state.selected = None
    st.session_state.score_ok = 0
    st.session_state.score_bad = 0
    st.session_state.started = True

def start_errors(subject):
    st.session_state.mode = "errores"
    st.session_state.subject = subject
    st.session_state.queue = build_error_review(subject)
    st.session_state.index = 0
    st.session_state.answered = False
    st.session_state.selected = None
    st.session_state.score_ok = 0
    st.session_state.score_bad = 0
    st.session_state.started = True

def current_question():
    if 0 <= st.session_state.index < len(st.session_state.queue):
        return st.session_state.queue[st.session_state.index]
    return None

def next_question():
    st.session_state.index += 1
    st.session_state.answered = False
    st.session_state.selected = None

def back_to_home():
    st.session_state.started = False
    st.session_state.mode = None
    st.session_state.queue = []
    st.session_state.index = 0
    st.session_state.answered = False
    st.session_state.selected = None

# ==============================
# SIDEBAR
# ==============================

with st.sidebar:
    st.subheader("Progreso")

    total = st.session_state.score_ok + st.session_state.score_bad
    pct = round((st.session_state.score_ok / total) * 100, 2) if total else 0

    st.write(f"Aciertos: {st.session_state.score_ok}")
    st.write(f"Errores: {st.session_state.score_bad}")
    st.write(f"Porcentaje: {pct}%")
    st.write(f"Falladas acumuladas: {len(st.session_state.wrong_ids)}")

    if st.session_state.started and st.session_state.queue:
        pos = min(st.session_state.index + 1, len(st.session_state.queue))
        st.write(f"Pregunta: {pos}/{len(st.session_state.queue)}")
        st.progress(st.session_state.index / len(st.session_state.queue))

# ==============================
# HOME
# ==============================

st.title("Fiscalidad Trainer")

if not st.session_state.started:
    st.subheader("Entrenamiento")

    subject_options = ["Todas"] + SUBJECTS
    subject = st.selectbox("Materia", subject_options)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Simulacro")
        st.write("20 preguntas seguidas, sin interrupciones.")
        if st.button("Empezar simulacro", use_container_width=True):
            start_simulacro(subject)
            st.rerun()

    with col2:
        st.markdown("### Repaso de errores")
        st.write("Repite preguntas que has fallado.")
        disabled = len(st.session_state.wrong_ids) == 0
        if st.button("Repasar errores", use_container_width=True, disabled=disabled):
            start_errors(subject)
            st.rerun()

    if disabled:
        st.info("Todavía no hay preguntas falladas para repasar.")

# ==============================
# QUIZ
# ==============================

else:
    q = current_question()

    if q is None or len(st.session_state.queue) == 0:
        st.subheader("No hay preguntas disponibles")
        st.write("Prueba otra materia o vuelve al simulacro.")
        if st.button("Volver al inicio"):
            back_to_home()
            st.rerun()

    elif st.session_state.index >= len(st.session_state.queue):
        st.subheader("Test finalizado")

        total = st.session_state.score_ok + st.session_state.score_bad
        pct = round((st.session_state.score_ok / total) * 100, 2) if total else 0

        st.write(f"Aciertos: {st.session_state.score_ok}")
        st.write(f"Errores: {st.session_state.score_bad}")
        st.write(f"Porcentaje: {pct}%")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Inicio"):
                back_to_home()
                st.rerun()

        with col2:
            if st.button("Repetir"):
                if st.session_state.mode == "simulacro":
                    start_simulacro(st.session_state.subject)
                else:
                    start_errors(st.session_state.subject)
                st.rerun()

        with col3:
            if st.button("Repasar errores"):
                start_errors(st.session_state.subject)
                st.rerun()

    else:
        st.caption(q["subject"])
        st.subheader(f"Pregunta {st.session_state.index + 1}")
        st.write(q["question"])

        selected = st.radio(
            "Selecciona una opción",
            ["A", "B", "C", "D"],
            format_func=lambda x: f"{x}) {q['options'][x]}",
            key=f"radio_{q['id']}_{st.session_state.index}"
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("Responder", use_container_width=True) and not st.session_state.answered:
                st.session_state.selected = selected
                st.session_state.answered = True

                if selected == q["answer"]:
                    st.session_state.score_ok += 1
                else:
                    st.session_state.score_bad += 1
                    if q["id"] not in st.session_state.wrong_ids:
                        st.session_state.wrong_ids.append(q["id"])

                st.rerun()

        with col2:
            if st.button("Salir", use_container_width=True):
                back_to_home()
                st.rerun()

        if st.session_state.answered:
            if st.session_state.selected == q["answer"]:
                st.success(f"Correcta. Respuesta: {q['answer']}")
            else:
                st.error(f"Incorrecta. Respuesta correcta: {q['answer']}")

            st.markdown("### Explicación")
            st.write(q["explanation"])

            st.markdown("**Referencia:**")
            st.write(q["reference"])

            if st.button("Siguiente pregunta", use_container_width=True):
                next_question()
                st.rerun()
