import pytest
import requests
import os
from datetime import datetime

# config
BASE_URL = "http://localhost:8000"
# relative to project root or set from env
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(CUR_DIR, "..", "test", "math.pdf")
OUTPUT_DIR = os.path.join(CUR_DIR, "..", "output")

@pytest.fixture(scope="session", autouse=True)
def setup_output():
    """create output dir"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def test_health():
    """check if api is alive"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_pipeline_e2e():
    """test full pdf extraction and processing pipeline"""
    # 1. extract
    with open(PDF_PATH, 'rb') as f:
        files = {'file': ('math.pdf', f, 'application/pdf')}
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
