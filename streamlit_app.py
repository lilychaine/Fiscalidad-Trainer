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

MODES = [
    "Simulacro de examen",
    "Repaso de errores"
]

# ==============================
# STATE
# ==============================

def init_state():
    defaults = {
        "started": False,
        "mode": MODES[0],
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

def build_exam():
    q = QUESTIONS[:]
    random.shuffle(q)
    return q[:20]

def build_errors():
    q = [x for x in QUESTIONS if x["id"] in st.session_state.wrong_ids]
    random.shuffle(q)
    return q[:20] if len(q) > 20 else q

def start():
    if st.session_state.mode == "Simulacro de examen":
        st.session_state.queue = build_exam()
    else:
        st.session_state.queue = build_errors()

    st.session_state.index = 0
    st.session_state.answered = False
    st.session_state.selected = None
    st.session_state.score_ok = 0
    st.session_state.score_bad = 0
    st.session_state.started = True

def next_q():
    st.session_state.index += 1
    st.session_state.answered = False
    st.session_state.selected = None

def reset():
    st.session_state.started = False

# ==============================
# SIDEBAR
# ==============================

with st.sidebar:
    st.subheader("Progreso")

    total = st.session_state.score_ok + st.session_state.score_bad
    pct = round((st.session_state.score_ok / total) * 100, 2) if total else 0

    st.write(f"Aciertos: {st.session_state.score_ok}")
    st.write(f"Errores: {st.session_state.score_bad}")
    st.write(f"%: {pct}")
    st.write(f"Falladas acumuladas: {len(st.session_state.wrong_ids)}")

# ==============================
# MAIN
# ==============================

st.title("Fiscalidad Trainer")

# ==============================
# MENU
# ==============================

if not st.session_state.started:

    st.subheader("Modo de entrenamiento")

    st.session_state.mode = st.selectbox("Selecciona modo", MODES)

    if st.session_state.mode == "Simulacro de examen":
        st.info("20 preguntas tipo examen real")

    if st.session_state.mode == "Repaso de errores":
        if st.session_state.wrong_ids:
            st.info("Se usarán preguntas falladas")
        else:
            st.warning("No hay preguntas falladas todavía")

    if st.button("Empezar"):
        start()
        st.rerun()

# ==============================
# QUIZ
# ==============================

else:
    if st.session_state.index >= len(st.session_state.queue):

        st.subheader("Test finalizado")

        total = st.session_state.score_ok + st.session_state.score_bad
        pct = round((st.session_state.score_ok / total) * 100, 2) if total else 0

        st.write(f"Aciertos: {st.session_state.score_ok}")
        st.write(f"Errores: {st.session_state.score_bad}")
        st.write(f"%: {pct}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Menú"):
                reset()
                st.rerun()

        with col2:
            if st.button("Repetir"):
                start()
                st.rerun()

    else:
        q = st.session_state.queue[st.session_state.index]

        st.caption(q["subject"])
        st.subheader(f"Pregunta {st.session_state.index + 1}")

        st.write(q["question"])

        selected = st.radio(
            "Respuesta",
            ["A", "B", "C", "D"],
            format_func=lambda x: f"{x}) {q['options'][x]}",
            key=f"q_{q['id']}_{st.session_state.index}"
        )

        if st.button("Responder") and not st.session_state.answered:
            st.session_state.selected = selected
            st.session_state.answered = True

            if selected == q["answer"]:
                st.session_state.score_ok += 1
                st.success("Correcto")
            else:
                st.session_state.score_bad += 1
                st.error(f"Incorrecto → {q['answer']}")

                if q["id"] not in st.session_state.wrong_ids:
                    st.session_state.wrong_ids.append(q["id"])

            st.rerun()

        if st.session_state.answered:
            st.markdown("### Explicación")
            st.write(q["explanation"])

            st.markdown("**Referencia:**")
            st.write(q["reference"])

            if st.button("Siguiente"):
                next_q()
                st.rerun()
