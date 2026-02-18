import os
import sys
import pytest
from pathlib import Path

# add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.pdf_service import extract_text_from_pdf

# paths
BACKEND_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BACKEND_DIR / "data"

@pytest.fixture
def sample_pdf():
    """find first pdf in data dir"""
    pdfs = list(DATA_DIR.glob("*.pdf"))
    if not pdfs:
        pytest.skip("no pdfs found in data/")
    return pdfs[0]

def test_pdf_extraction_markdown(sample_pdf):
    """test parser returns markdown"""
    print(f"\ntesting with: {sample_pdf.name}")
    
    with open(sample_pdf, "rb") as f:
        content = f.read()
    
    text = extract_text_from_pdf(content)
    
    assert len(text) > 0
    assert isinstance(text, str)
    
    # check for markdown indicators
    has_markdown = (
        "#" in text or
        "|" in text or
        "**" in text or
        "-" in text
    )
    assert has_markdown, "output should contain markdown syntax"
