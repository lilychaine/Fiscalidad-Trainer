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

TOPICS_BY_SUBJECT = {
    subject: sorted({q["topic"] for q in QUESTIONS if q["subject"] == subject})
    for subject in SUBJECTS
}

MODES = [
    "Estudio por bloque",
    "Simulacro de examen",
    "Repaso de errores",
]

# ==============================
# STATE INIT
# ==============================

def init_state():
    defaults = {
        "started": False,
        "mode": MODES[0],
        "subject": SUBJECTS[0] if SUBJECTS else "",
        "topic": "",
        "queue": [],
        "index": 0,
        "answered": False,
        "selected": None,
        "score_ok": 0,
        "score_bad": 0,
        "wrong_ids": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

# ==============================
# FUNCTIONS
# ==============================

def reset_quiz():
    st.session_state.queue = []
    st.session_state.index = 0
    st.session_state.answered = False
    st.session_state.selected = None
    st.session_state.score_ok = 0
    st.session_state.score_bad = 0

def build_block_queue(subject, topic):
    items = [
        q for q in QUESTIONS
        if q["subject"] == subject and q["topic"] == topic
    ]
    random.shuffle(items)
    return items

def build_exam_queue():
    items = QUESTIONS[:]
    random.shuffle(items)
    return items[:20]

def build_error_queue():
    items = [q for q in QUESTIONS if q["id"] in st.session_state.wrong_ids]
    random.shuffle(items)
    return items[:20] if len(items) > 20 else items

def start_quiz():
    mode = st.session_state.mode

    if mode == "Estudio por bloque":
        st.session_state.queue = build_block_queue(
            st.session_state.subject,
            st.session_state.topic
        )
    elif mode == "Simulacro de examen":
        st.session_state.queue = build_exam_queue()
    else:
        st.session_state.queue = build_error_queue()

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

def back_to_menu():
    st.session_state.started = False
    st.session_state.queue = []
    st.session_state.index = 0
    st.session_state.answered = False
    st.session_state.selected = None

# ==============================
# UI
# ==============================

st.title("Fiscalidad Trainer")

with st.sidebar:
    st.subheader("Marcador")
    total = st.session_state.score_ok + st.session_state.score_bad
    pct = round((st.session_state.score_ok / total) * 100, 2) if total else 0.0

    st.write(f"Aciertos: {st.session_state.score_ok}")
    st.write(f"Errores: {st.session_state.score_bad}")
    st.write(f"Porcentaje: {pct}%")
    st.write(f"Falladas acumuladas: {len(st.session_state.wrong_ids)}")

    if st.session_state.started and st.session_state.queue:
        pos = min(st.session_state.index + 1, len(st.session_state.queue))
        st.write(f"Pregunta: {pos}/{len(st.session_state.queue)}")
        st.progress(st.session_state.index / len(st.session_state.queue))

if not st.session_state.started:
    st.subheader("Configuración inicial")

    st.session_state.mode = st.selectbox(
        "Modalidad",
        MODES,
        index=MODES.index(st.session_state.mode)
    )

    if st.session_state.mode == "Estudio por bloque":
        st.session_state.subject = st.selectbox(
            "Materia",
            SUBJECTS,
            index=SUBJECTS.index(st.session_state.subject)
        )

        topics = TOPICS_BY_SUBJECT.get(st.session_state.subject, [])

        if topics:
            default_topic = topics[0]
            if st.session_state.topic in topics:
                default_topic = st.session_state.topic

            st.session_state.topic = st.selectbox(
                "Bloque",
                topics,
                index=topics.index(default_topic)
            )
        else:
            st.warning("No hay bloques disponibles para esta materia.")

    elif st.session_state.mode == "Simulacro de examen":
        st.info("Se mezclarán 20 preguntas de todas las materias.")

    elif st.session_state.mode == "Repaso de errores":
        if st.session_state.wrong_ids:
            st.info("Se usarán las preguntas falladas.")
        else:
            st.warning("Todavía no hay preguntas falladas.")

    if st.button("Empezar test"):
        start_quiz()
        st.rerun()

else:
    q = current_question()

    if q is None:
        st.subheader("Test finalizado")

        total = st.session_state.score_ok + st.session_state.score_bad
        pct = round((st.session_state.score_ok / total) * 100, 2) if total else 0.0

        st.write(f"Aciertos: {st.session_state.score_ok}")
        st.write(f"Errores: {st.session_state.score_bad}")
        st.write(f"Porcentaje: {pct}%")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Volver al menú"):
                back_to_menu()
                st.rerun()

        with col2:
            if st.button("Repetir"):
                start_quiz()
                st.rerun()

    else:
        st.caption(f"Materia: {q['subject']}")
        st.caption(f"Bloque: {q['topic']} | Subbloque: {q['subtopic']}")
        st.subheader(f"Pregunta {st.session_state.index + 1}")
        st.write(q["question"])

        selected = st.radio(
            "Selecciona una opción",
            ["A", "B", "C", "D"],
            format_func=lambda x: f"{x}) {q['options'][x]}",
            key=f"radio_{q['id']}_{st.session_state.index}"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Responder") and not st.session_state.answered:
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
            if st.button("Salir al menú"):
                back_to_menu()
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

            if st.button("Siguiente pregunta"):
                next_question()
                st.rerun()
