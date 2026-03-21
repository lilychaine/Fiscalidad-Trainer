from pathlib import Path
import json
from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "materials" / "raw"
OUT_DIR = BASE_DIR / "data" / "extracted_text"

SUBJECT_MAP = {
    "introduccion_fiscalidad": "Introducción a la fiscalidad",
    "tributacion_local": "Tributación local",
    "impuesto_valor_anadido": "Impuesto sobre el Valor Añadido",
    "itp_ajd": "Impuesto sobre Transmisiones Patrimoniales y Actos Jurídicos Documentados",
    "sucesiones_donaciones": "Impuesto sobre Sucesiones y Donaciones",
    "irpf": "Impuesto sobre la Renta de las Personas Físicas",
    "impuesto_sociedades": "Impuesto sobre Sociedades",
}

OUT_DIR.mkdir(parents=True, exist_ok=True)

for folder in RAW_DIR.iterdir():
    if not folder.is_dir():
        continue

    subject = SUBJECT_MAP.get(folder.name, folder.name)
    subject_dir = OUT_DIR / folder.name
    subject_dir.mkdir(parents=True, exist_ok=True)

    for pdf_path in folder.glob("*.pdf"):
        reader = PdfReader(str(pdf_path))
        pages = []

        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = " ".join(text.split())
            pages.append({
                "page": i,
                "text": text
            })

        out_file = subject_dir / f"{pdf_path.stem}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({
                "subject": subject,
                "source_file": pdf_path.name,
                "pages": pages
            }, f, ensure_ascii=False, indent=2)

print("Extracción completada.")