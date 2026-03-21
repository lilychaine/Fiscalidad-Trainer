from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
IN_DIR = BASE_DIR / "data" / "extracted_text"
OUT_DIR = BASE_DIR / "data" / "prompts"

OUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_CHARS = 12000

for subject_dir in IN_DIR.iterdir():
    if not subject_dir.is_dir():
        continue

    out_subject = OUT_DIR / subject_dir.name
    out_subject.mkdir(parents=True, exist_ok=True)

    for json_file in subject_dir.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            doc = json.load(f)

        chunks = []
        current = ""
        start_page = None
        end_page = None

        for page in doc["pages"]:
            page_text = f"\n\n[PÁGINA {page['page']}]\n{page['text']}"
            if len(current) + len(page_text) > MAX_CHARS and current:
                chunks.append({
                    "subject": doc["subject"],
                    "source_file": doc["source_file"],
                    "start_page": start_page,
                    "end_page": end_page,
                    "text": current.strip()
                })
                current = ""
                start_page = None

            if start_page is None:
                start_page = page["page"]
            end_page = page["page"]
            current += page_text

        if current.strip():
            chunks.append({
                "subject": doc["subject"],
                "source_file": doc["source_file"],
                "start_page": start_page,
                "end_page": end_page,
                "text": current.strip()
            })

        for idx, chunk in enumerate(chunks, start=1):
            out_file = out_subject / f"{json_file.stem}_chunk_{idx}.txt"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(chunk["text"])

print("Fragmentación completada.")