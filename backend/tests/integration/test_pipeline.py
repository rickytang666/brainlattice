import pytest
import requests
import os
from pathlib import Path

# config
BASE_URL = "http://localhost:8000"
BACKEND_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BACKEND_DIR / "data"
OUTPUT_DIR = BACKEND_DIR / "output"

@pytest.fixture(scope="session", autouse=True)
def setup_output():
    """create output dir"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

@pytest.fixture
def sample_pdf():
    """find first pdf in data dir"""
    pdfs = list(DATA_DIR.glob("*.pdf"))
    if not pdfs:
        pytest.skip("no pdfs found in data/")
    return pdfs[0]

def test_health():
    """check if api is alive"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    except requests.exceptions.ConnectionError:
        pytest.fail("api server not running")

def test_pipeline_e2e(sample_pdf):
    """test full pipeline with real pdf"""
    print(f"\ntesting pipeline with: {sample_pdf.name}")

    # 1. extract
    with open(sample_pdf, 'rb') as f:
        files = {'file': (sample_pdf.name, f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/api/extract", files=files)
    
    assert response.status_code == 200
    extract_data = response.json()
    assert extract_data['success']
    text = extract_data['text']
    assert len(text) > 0

    # 2. digest
    response = requests.post(
        f"{BASE_URL}/api/digest",
        json={'text': text[:2000]}
    )
    assert response.status_code == 200
    digest_data = response.json()
    assert digest_data['success']

    # 3. relationships
    response = requests.post(
        f"{BASE_URL}/api/relationships",
        json={'structured_data': digest_data['digest_data']}
    )
    assert response.status_code == 200
    graph_data = response.json()
    assert graph_data['success']
