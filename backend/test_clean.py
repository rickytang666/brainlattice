#!/usr/bin/env python3
"""
Clean BrainLattice Pipeline Test
PDF -> Extract -> AI Digest -> Knowledge Graph
Outputs all results to output/ folder for inspection
"""

import requests
import json
import os
from datetime import datetime

BASE_URL = "http://localhost:8000"
PDF_PATH = "/Users/rickytang/Coding/github/brainlattice/backend/test/math.pdf"

# Create output directory
OUTPUT_DIR = "/Users/rickytang/Coding/github/brainlattice/backend/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_output(filename, data):
    """Save data to output file"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        if isinstance(data, dict):
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            f.write(str(data))
    print(f"📁 Saved: {filename}")

def test_clean_pipeline():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("=" * 70)
    print("🧠 BRAINLATTICE CLEAN PIPELINE TEST")
    print("=" * 70)
    print(f"📅 Timestamp: {timestamp}")
    print(f"📂 Output directory: {OUTPUT_DIR}")

    try:
        # Step 1: Health Check
        print("\n1. 🔍 Health Check...")
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        assert response.status_code == 200
        print("✅ Health check passed")

        # Step 2: PDF Extraction
        print("\n2. 📄 PDF Extraction...")
        with open(PDF_PATH, 'rb') as f:
            files = {'file': ('math.pdf', f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/api/extract", files=files, timeout=30)

        assert response.status_code == 200
        extract_data = response.json()
        assert extract_data['success']
        extracted_text = extract_data['text']
        
        print(f"✅ PDF extraction: {len(extracted_text)} characters")
        print(f"   📄 Filename: {extract_data['filename']}")
        
        # Save extracted text
        save_output(f"{timestamp}_01_extracted_text.txt", extracted_text)

        # Step 3: AI Digest Creation (Direct from PDF text)
        print("\n3. 🧠 AI Digest Creation...")
        # Use first 4000 chars for good coverage but faster processing
        text_for_digest = extracted_text[:4000] if len(extracted_text) > 4000 else extracted_text
        print(f"   📝 Processing {len(text_for_digest)} characters...")
        
        response = requests.post(
            f"{BASE_URL}/api/digest",
            json={'text': text_for_digest},
            timeout=120
        )

        assert response.status_code == 200
        digest_data = response.json()
        assert digest_data['success']
        digest_json = digest_data['digest_data']
        
        concepts = digest_json.get('sequential_concepts', [])
        print(f"✅ AI Digest created: {len(concepts)} concepts")
        print(f"   📚 Course: {digest_json.get('course_info', {}).get('title', 'Unknown')}")
        
        # Save digest data
        save_output(f"{timestamp}_02_ai_digest.json", digest_json)

        # Step 4: Knowledge Graph Generation
        print("\n4. 🕸️  Knowledge Graph Generation...")
        response = requests.post(
            f"{BASE_URL}/api/relationships",
            json={'structured_data': digest_json},
            timeout=120
        )

        assert response.status_code == 200
        graph_data = response.json()
        assert graph_data['success']
        
        nodes = graph_data['graph_data']['nodes']
        print(f"✅ Knowledge graph created: {len(nodes)} nodes")
        
        # Save graph data
        save_output(f"{timestamp}_03_knowledge_graph.json", graph_data['graph_data'])

        # Step 5: Overview Generation
        print("\n5. 📝 Overview Generation...")
        response = requests.post(
            f"{BASE_URL}/api/overview",
            json={'graph_data': graph_data['graph_data']},
            timeout=60
        )

        assert response.status_code == 200
        overview_data = response.json()
        assert overview_data['success']
        
        overview_text = overview_data['overview_text']
        print(f"✅ Overview generated: {len(overview_text)} characters")
        
        # Save overview
        save_output(f"{timestamp}_04_overview.txt", overview_text)

        # Step 6: Firebase Storage
        print("\n6. 💾 Firebase Storage...")
        response = requests.post(
            f"{BASE_URL}/api/project/save",
            json={
                'digest_data': digest_json,
                'graph_data': graph_data['graph_data']
            },
            timeout=30
        )

        assert response.status_code == 200
        save_data = response.json()
        assert save_data['success']
        project_id = save_data['project_id']
        
        print(f"✅ Project saved to Firebase: {project_id}")
        
        # Test retrieval
        print("\n7. 🔍 Firebase Retrieval...")
        response = requests.get(f"{BASE_URL}/api/project/{project_id}", timeout=30)
        
        assert response.status_code == 200
        retrieve_data = response.json()
        assert retrieve_data['success']
        
        retrieved_project = retrieve_data['project_data']
        print(f"✅ Project retrieved from Firebase: {len(retrieved_project)} keys")
        
        # Save Firebase data
        save_output(f"{timestamp}_05_firebase_save.json", save_data)
        save_output(f"{timestamp}_05_firebase_retrieve.json", retrieve_data)

        # Summary
        print("\n" + "=" * 70)
        print("🎉 PIPELINE SUCCESS!")
        print("=" * 70)
        print(f"📄 PDF Text: {len(extracted_text):,} characters")
        print(f"🧠 AI Digest: {len(concepts)} concepts")
        print(f"🕸️  Knowledge Graph: {len(nodes)} nodes")
        print(f"📝 Overview: {len(overview_text):,} characters")
        print(f"💾 Firebase: Saved & Retrieved (Project ID: {project_id})")
        print(f"\n📂 All outputs saved to: {OUTPUT_DIR}")
        print(f"🕐 Timestamp: {timestamp}")
        print("\n🚀 Ready for frontend integration!")

    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_clean_pipeline()
