from pathlib import Path
import math

BASE_DIR = Path(__file__).resolve().parent.parent
IN_DIR = BASE_DIR / "data" / "prompts"
OUT_DIR = BASE_DIR / "data" / "prompt_packs"

OUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_CHARS_PER_PACK = 45000

PROMPT_TEMPLATE = """A partir EXCLUSIVAMENTE del siguiente contenido, genera exactamente {n_questions} preguntas tipo test.

Reglas obligatorias:

- No uses conocimiento externo
- No inventes contenido
- Si una regla no aparece claramente en el texto, no la conviertas en pregunta
- No hagas preguntas cuya respuesta sea únicamente el número de artículos
- No uses abreviaturas en el contenido visible
- Nivel profesional alto
- Mezcla conceptos técnicos, mini casos y preguntas trampa
- Devuelve exclusivamente un JSON válido
- No añadas comentarios ni texto fuera del JSON

Formato obligatorio:

[
  {{
    "id": 1,
    "subject": "{subject}",
    "topic": "...",
    "subtopic": "...",
    "question": "...",
    "options": {{
      "A": "...",
      "B": "...",
      "C": "...",
      "D": "..."
    }},
    "answer": "A",
    "explanation": "...",
    "reference": "Nombre del PDF o bloque del que sale la regla",
    "difficulty": "alta",
    "question_type": "concepto/caso/trampa",
    "trap_level": "bajo/medio/alto",
    "tags": ["...", "..."]
  }}
]

Contenido fuente:
"""

for subject_dir in IN_DIR.iterdir():
    if not subject_dir.is_dir():
        continue

    txt_files = sorted(subject_dir.glob("*.txt"))
    if not txt_files:
        continue

    subject_name = subject_dir.name
    out_subject_dir = OUT_DIR / subject_name
    out_subject_dir.mkdir(parents=True, exist_ok=True)

    packs = []
    current_pack = ""
    current_sources = []

    for txt_file in txt_files:
        content = txt_file.read_text(encoding="utf-8")
        block = f"\n\n===== FUENTE: {txt_file.name} =====\n{content}"

        if len(current_pack) + len(block) > MAX_CHARS_PER_PACK and current_pack:
            packs.append((current_pack.strip(), current_sources[:]))
            current_pack = ""
            current_sources = []

        current_pack += block
        current_sources.append(txt_file.name)

    if current_pack.strip():
        packs.append((current_pack.strip(), current_sources[:]))

    n_packs = len(packs)
    questions_per_pack = max(8, math.ceil(20 / n_packs))

    for idx, (pack_text, sources) in enumerate(packs, start=1):
        prompt_text = PROMPT_TEMPLATE.format(
            n_questions=questions_per_pack,
            subject=subject_name.replace("_", " ").title()
        ) + "\n" + pack_text

        prompt_file = out_subject_dir / f"pack_{idx}.txt"
        prompt_file.write_text(prompt_text, encoding="utf-8")

        sources_file = out_subject_dir / f"pack_{idx}_sources.txt"
        sources_file.write_text("\n".join(sources), encoding="utf-8")

print("Packs de prompt generados.")