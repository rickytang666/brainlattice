import os
import sys
import pytest
import re
from pathlib import Path

# add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.pdf_service import extract_text_from_pdf

# paths
BACKEND_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BACKEND_DIR / "data"
OUTPUT_DIR = BACKEND_DIR / "output"

@pytest.fixture(scope="module")
def sample_pdf():
    """find first pdf in data dir"""
    pdfs = list(DATA_DIR.glob("*.pdf"))
    if not pdfs:
        pytest.skip("no pdfs found in data/")
    return pdfs[0]

@pytest.fixture(scope="module")
def extracted_text(sample_pdf):
    """extract text once for all tests"""
    with open(sample_pdf, "rb") as f:
        content = f.read()
    return extract_text_from_pdf(content)

def test_markdown_structure(extracted_text):
    """ensure output has valid markdown structure"""
    # check for headers
    headers = re.findall(r'^#{1,6}\s+.+$', extracted_text, re.MULTILINE)
    assert len(headers) > 0, "output should contain markdown headers"
    
    # check for list items (if expected in typical docs)
    # usually at least some lists exist in academic/tech pdfs
    lists = re.findall(r'^\s*[-*+]\s+.+$', extracted_text, re.MULTILINE)
    if len(extracted_text) > 1000:  # only enforce for decent sized docs
        assert len(lists) > 0, "output should likely contain list items"

def test_content_quality(extracted_text):
    """check for signs of poor extraction"""
    # 1. density check
    total_chars = len(extracted_text)
    assert total_chars > 0
    
    # 2. whitespace ratio (shouldn't be mostly empty)
    whitespace_count = sum(1 for c in extracted_text if c.isspace())
    whitespace_ratio = whitespace_count / total_chars
    assert whitespace_ratio < 0.4, f"too much whitespace: {whitespace_ratio:.2%}"
    
    # 3. weird character check (replacement chars)
    assert "\ufffd" not in extracted_text, "output contains replacement characters"
    
    # 4. broken hyphenation check (simple heuristic)
    # shouldn't have many words ending in hyphen at end of line
    broken_hyphens = re.findall(r'\w+-\n\w+', extracted_text)
    assert len(broken_hyphens) == 0, f"found broken hyphens: {broken_hyphens[:5]}"

def test_table_preservation(extracted_text):
    """check if tables are preserved as markdown"""
    # look for table syntax: | col | col |
    tables = re.findall(r'\|.*\|.*\|', extracted_text)
    # verify at least potential table row exists if pipe chars are present
    if "|" in extracted_text:
        assert len(tables) > 0, "pipes found but no valid table rows identified"

def test_save_debug_output(extracted_text, sample_pdf):
    """save output for manual inspection"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = OUTPUT_DIR / f"{sample_pdf.stem}_debug.md"
    
    with open(out_path, "w") as f:
        f.write(extracted_text)
    
    print(f"\nSaved debug output to: {out_path}")
    assert out_path.exists()
    assert out_path.stat().st_size > 0
