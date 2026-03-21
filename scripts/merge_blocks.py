from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BLOCKS_DIR = BASE_DIR / "data" / "bloques"
OUTPUT_FILE = BASE_DIR / "data" / "questions.json"


def load_json_file(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    if not BLOCKS_DIR.exists():
        raise FileNotFoundError(f"No existe la carpeta: {BLOCKS_DIR}")

    block_files = sorted(BLOCKS_DIR.glob("*.json"))

    if not block_files:
        raise FileNotFoundError("No hay archivos JSON en data/bloques")

    merged_questions = []
    seen = set()

    for file_path in block_files:
        data = load_json_file(file_path)

        if not isinstance(data, list):
            raise ValueError(f"El archivo {file_path.name} no contiene una lista JSON")

        for q in data:
            if not isinstance(q, dict):
                raise ValueError(f"Pregunta inválida en {file_path.name}")

            required_keys = {
                "subject",
                "topic",
                "subtopic",
                "question",
                "options",
                "answer",
                "explanation",
                "reference",
                "difficulty",
                "question_type",
                "trap_level",
                "tags",
            }

            missing = required_keys - set(q.keys())
            if missing:
                raise ValueError(
                    f"Faltan campos en {file_path.name}: {', '.join(sorted(missing))}"
                )

            signature = (
                q["subject"],
                q["topic"],
                q["subtopic"],
                q["question"].strip(),
            )

            if signature in seen:
                continue

            seen.add(signature)
            merged_questions.append(q)

    # Renumerar ids
    for idx, q in enumerate(merged_questions, start=1):
        q["id"] = idx

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(merged_questions, f, ensure_ascii=False, indent=2)

    print(f"Bloques procesados: {len(block_files)}")
    print(f"Preguntas finales: {len(merged_questions)}")
    print(f"Archivo generado: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()