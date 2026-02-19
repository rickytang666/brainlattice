import os
import sys
from pathlib import Path

# add backend to path so we can import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pdf_service import PDFService

def main():
    if len(sys.argv) < 2:
        print("usage: python scripts/parse_pdf.py <filename_in_data_folder>")
        sys.exit(1)

    filename = sys.argv[1]
    data_dir = Path("data")
    pdf_path = data_dir / filename
    
    if not pdf_path.exists():
        print(f"error: {pdf_path} not found.")
        sys.exit(1)

    print(f"parsing {pdf_path}...")
    pdf_service = PDFService()
    markdown_content = pdf_service.extract_content(str(pdf_path))
    
    output_path = pdf_path.with_suffix(".md")
    with open(output_path, "w") as f:
        f.write(markdown_content)
    
    print(f"saved to {output_path}")

if __name__ == "__main__":
    main()
