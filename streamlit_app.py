import json
import random
from pathlib import Path
import streamlit as st

# ==============================
# CONFIG
# ==============================

st.set_page_config(
    page_title="Fiscalidad Trainer",
    layout="centered"
)

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

# ==============================
# STATE INIT
# ==============================

if "current_question" not in st.session_state:
    st.session_state.current_question = random.choice(QUESTIONS)

if "score" not in st.session_state:
    st.session_state.score = 0

if "total" not in st.session_state:
    st.session_state.total = 0

if "answered" not in st.session_state:
    st.session_state.answered = False

if "selected" not in st.session_state:
    st.session_state.selected = None

# ==============================
# FUNCTIONS
# ==============================

def new_question():
    st.session_state.current_question = random.choice(QUESTIONS)
    st.session_state.answered = False
    st.session_state.selected = None

# ==============================
# UI
# ==============================

st.title("Fiscalidad Trainer")

# Score
st.subheader(f"Puntuación: {st.session_state.score} / {st.session_state.total}")

q = st.session_state.current_question

st.markdown(f"### {q['question']}")

# Options
options = q["options"]

choice = st.radio(
    "Selecciona una opción:",
    list(options.keys()),
    format_func=lambda x: f"{x}: {options[x]}",
    index=None
)

# Submit
if st.button("Responder") and not st.session_state.answered:
    if choice is None:
        st.warning("Selecciona una opción")
    else:
        st.session_state.answered = True
        st.session_state.selected = choice
        st.session_state.total += 1

        if choice == q["answer"]:
            st.session_state.score += 1
            st.success("Correcto")
        else:
            st.error(f"Incorrecto. Respuesta correcta: {q['answer']}")

# Explanation
if st.session_state.answered:
    st.markdown("### Explicación")
    st.write(q["explanation"])

    st.markdown("**Referencia:**")
    st.write(q["reference"])

    if st.button("Siguiente pregunta"):
        new_question()
        st.rerun()
