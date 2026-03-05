"""
Extract markdown from a PDF file. Useful for debugging PDF extraction without
running the full ingestion pipeline.

Usage:
  python scripts/parse_pdf.py <path_to_pdf>
  python scripts/parse_pdf.py data/sample.pdf   # from backend/
  python scripts/parse_pdf.py /abs/path/doc.pdf
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.pdf_service import PDFService


def main():
    if len(sys.argv) < 2:
        print("usage: python scripts/parse_pdf.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.is_absolute():
        # relative path: try data/ first, then cwd
        data_path = Path("data") / pdf_path
        pdf_path = data_path if data_path.exists() else pdf_path

    if not pdf_path.exists():
        print(f"error: {pdf_path} not found.")
        sys.exit(1)

    print(f"parsing {pdf_path}...")
    markdown_content = PDFService().extract_content(str(pdf_path))
    
    output_path = pdf_path.with_suffix(".md")
    with open(output_path, "w") as f:
        f.write(markdown_content)
    
    print(f"saved to {output_path}")

if __name__ == "__main__":
    main()
