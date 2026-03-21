import json
import random
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
QUESTIONS_PATH = BASE_DIR / "data" / "questions.json"

st.set_page_config(page_title="Fiscalidad Trainer", layout="centered")


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
    "Repaso adaptativo",
]


def init_state():
    defaults = {
        "started": False,
        "mode": "Estudio por bloque",
        "subject": SUBJECTS[0] if SUBJECTS else "",
        "topic": "",
        "queue": [],
        "index": 0,
        "selected": None,
        "answered": False,
        "score_ok": 0,
        "score_bad": 0,
        "wrong_ids": [],
        "history": [],
        "weak_topics": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_questions_by_subject_and_topic(subject=None, topic=None):
    items = QUESTIONS
    if subject:
        items = [q for q in items if q["subject"] == subject]
    if topic:
        items = [q for q in items if q["topic"] == topic]
    return items


def build_study_queue(subject, topic):
    items = get_questions_by_subject_and_topic(subject, topic)
    random.shuffle(items)
    return items


def build_exam_queue():
    items = QUESTIONS[:]
    random.shuffle(items)
    return items[:20]


def build_adaptive_queue():
    wrong_ids = st.session_state.wrong_ids
    weak_topics = st.session_state.weak_topics

    wrong_questions = [q for q in QUESTIONS if q["id"] in wrong_ids]

    priority_topics = sorted(
        weak_topics.items(),
        key=lambda x: x[1],
        reverse=True
    )
    topic_names = [name for name, _ in priority_topics[:5]]

    extra_questions = [q for q in QUESTIONS if q["topic"] in topic_names and q["id"] not in wrong_ids]
    random.shuffle(extra_questions)

    mixed = wrong_questions + extra_questions[: max(0, 20 - len(wrong_questions))]
    if len(mixed) < 20:
        remaining = [q for q in QUESTIONS if q["id"] not in {x["id"] for x in mixed}]
        random.shuffle(remaining)
        mixed.extend(remaining[: 20 - len(mixed)])

    random.shuffle(mixed)
    return mixed[:20]


def start_quiz():
    mode = st.session_state.mode
    subject = st.session_state.subject
    topic = st.session_state.topic

    if mode == "Estudio por bloque":
        queue = build_study_queue(subject, topic)
    elif mode == "Simulacro de examen":
        queue = build_exam_queue()
    else:
        queue = build_adaptive_queue()

    st.session_state.queue = queue
    st.session_state.index = 0
    st.session_state.selected = None
    st.session_state.answered = False
    st.session_state.score_ok = 0
    st.session_state.score_bad = 0
    st.session_state.started = True


def current_question():
    if 0 <= st.session_state.index < len(st.session_state.queue):
        return st.session_state.queue[st.session_state.index]
    return None


def register_result(question, selected):
    correct = selected == question["answer"]

    st.session_state.history.append(
        {
            "id": question["id"],
            "subject": question["subject"],
            "topic": question["topic"],
            "correct": correct,
        }
    )

    if correct:
        st.session_state.score_ok += 1
    else:
        st.session_state.score_bad += 1
        if question["id"] not in st.session_state.wrong_ids:
            st.session_state.wrong_ids.append(question["id"])

        topic_key = f"{question['subject']} | {question['topic']}"
        st.session_state.weak_topics[topic_key] = st.session_state.weak_topics.get(topic_key, 0) + 1


def reset_to_menu():
    st.session_state.started = False
    st.session_state.queue = []
    st.session_state.index = 0
    st.session_state.selected = None
    st.session_state.answered = False


def next_question():
    st.session_state.index += 1
    st.session_state.selected = None
    st.session_state.answered = False


init_state()

st.title("Fiscalidad Trainer")

with st.sidebar:
    st.subheader("Progreso")
    total = st.session_state.score_ok + st.session_state.score_bad
    percentage = round((st.session_state.score_ok / total) * 100, 2) if total else 0.0
    st.write(f"Aciertos: {st.session_state.score_ok}")
    st.write(f"Errores: {st.session_state.score_bad}")
    st.write(f"Porcentaje: {percentage}%")
    st.write(f"Preguntas falladas acumuladas: {len(st.session_state.wrong_ids)}")

    if st.session_state.started and st.session_state.queue:
        position = min(st.session_state.index + 1, len(st.session_state.queue))
        st.write(f"Pregunta: {position}/{len(st.session_state.queue)}")
        st.progress(st.session_state.index / len(st.session_state.queue))

if not st.session_state.started:
    st.subheader("Configuración inicial")

    mode = st.selectbox("Modalidad", MODES, index=MODES.index(st.session_state.mode))
    st.session_state.mode = mode

    if mode == "Estudio por bloque":
        subject = st.selectbox("Materia", SUBJECTS, index=SUBJECTS.index(st.session_state.subject))
        st.session_state.subject = subject

        topics = TOPICS_BY_SUBJECT.get(subject, [])
        if topics:
            default_topic_index = 0
            if st.session_state.topic in topics:
                default_topic_index = topics.index(st.session_state.topic)
            topic = st.selectbox("Bloque", topics, index=default_topic_index)
            st.session_state.topic = topic
        else:
            st.session_state.topic = ""
            st.warning("No hay bloques disponibles para esta materia.")

    elif mode == "Simulacro de examen":
        st.info("Se mezclarán 20 preguntas de todas las materias.")

    elif mode == "Repaso adaptativo":
        st.info("Se priorizarán preguntas falladas y bloques débiles.")
        if not st.session_state.wrong_ids:
            st.warning("Todavía no hay preguntas falladas acumuladas. Haz primero estudio por bloque o simulacro.")

    if st.button("Empezar"):
        start_quiz()
        st.rerun()

else:
    q = current_question()

    if q is None:
        st.subheader("Test finalizado")

        total = st.session_state.score_ok + st.session_state.score_bad
        percentage = round((st.session_state.score_ok / total) * 100, 2) if total else 0.0

        st.write(f"Aciertos: {st.session_state.score_ok}")
        st.write(f"Errores: {st.session_state.score_bad}")
        st.write(f"Porcentaje: {percentage}%")

        if st.session_state.weak_topics:
            st.subheader("Bloques débiles")
            sorted_weak = sorted(
                st.session_state.weak_topics.items(),
                key=lambda x: x[1],
                reverse=True
            )
            for name, count in sorted_weak[:5]:
                st.write(f"- {name}: {count} errores")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Volver al menú"):
                reset_to_menu()
                st.rerun()

        with col2:
            if st.button("Repetir misma modalidad"):
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
            key=f"q_{q['id']}_{st.session_state.index}"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Responder") and not st.session_state.answered:
                st.session_state.selected = selected
                st.session_state.answered = True
                register_result(q, selected)
                st.rerun()

        with col2:
            if st.button("Salir al menú"):
                reset_to_menu()
                st.rerun()

        if st.session_state.answered:
            if st.session_state.selected == q["answer"]:
                st.success(f"Correcta. Respuesta: {q['answer']}")
            else:
                st.error(f"Incorrecta. Respuesta correcta: {q['answer']}")

            st.write("Explicación:", q["explanation"])
            st.write("Referencia:", q["reference"])

            if st.button("Siguiente pregunta"):
                next_question()
                st.rerun()