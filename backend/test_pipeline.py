#!/usr/bin/env python3
"""
End-to-end pipeline test for BrainLattice backend
Tests the complete flow: PDF -> Extract -> Structure -> Relationships -> Overview -> Audio Script -> Audio
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
PDF_PATH = "/Users/rickytang/Coding/github/brainlattice/backend/test/math.pdf"

def test_pipeline():
    print("=" * 60)
    print("BRAINLATTICE BACKEND END-TO-END PIPELINE TEST")
    print("=" * 60)

    # Step 1: Health Check
    print("\n1. Testing Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print("✓ Health check passed:", response.json())

    # Step 2: PDF Extraction
    print("\n2. Testing PDF Extraction...")
    with open(PDF_PATH, 'rb') as f:
        files = {'file': ('math.pdf', f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/api/extract", files=files)

    assert response.status_code == 200
    extract_data = response.json()
    assert extract_data['success']
    extracted_text = extract_data['text']
    print(f"✓ PDF extraction passed: {len(extracted_text)} characters extracted")
    print(f"  First 100 chars: {extracted_text[:100]}...")

    # Step 3: AI Digest Creation
    print("\n3. Testing AI Digest Creation (OpenRouter)...")
    response = requests.post(
        f"{BASE_URL}/api/digest",
        json={'text': extracted_text[:1000]},  # Limit for faster testing
        timeout=120
    )

    assert response.status_code == 200
    digest_data = response.json()
    assert digest_data['success']
    digest_json = digest_data['digest_data']
    print(f"✓ AI digest passed: {len(digest_json.get('sequential_concepts', []))} concepts identified")
    print(f"  Concepts: {[c.get('name', 'unnamed') for c in digest_json.get('sequential_concepts', [])[:3]]}...")

    # Step 4: Relationship Extraction
    print("\n4. Testing Relationship Extraction (Gemini)...")
    response = requests.post(
        f"{BASE_URL}/api/relationships",
        json={'structured_data': digest_json},
        timeout=120
    )

    assert response.status_code == 200
    relationships_data = response.json()
    assert relationships_data['success']
    graph_data = relationships_data['graph_data']
    print(f"✓ Relationship extraction passed:")
    print(f"  Nodes: {len(graph_data.get('nodes', []))}")
    print(f"  Edges: {len(graph_data.get('edges', []))}")

    # Step 5: Overview Generation
    print("\n5. Testing Overview Generation (OpenRouter/DeepSeek)...")
    response = requests.post(
        f"{BASE_URL}/api/overview",
        json={'graph_data': graph_data},
        timeout=120
    )

    assert response.status_code == 200
    overview_data = response.json()
    assert overview_data['success']
    overview_text = overview_data['overview_text']
    print(f"✓ Overview generation passed: {len(overview_text)} characters")
    print(f"  Preview: {overview_text[:150]}...")

    # Step 6: Audio Script Generation
    print("\n6. Testing Audio Script Generation (OpenRouter/DeepSeek)...")
    response = requests.post(
        f"{BASE_URL}/api/audio-script",
        json={'graph_data': graph_data},
        timeout=120
    )

    assert response.status_code == 200
    script_data = response.json()
    assert script_data['success']
    script_text = script_data['script_text']
    print(f"✓ Audio script generation passed: {len(script_text)} characters")
    print(f"  Preview: {script_text[:150]}...")

    # Step 7: Audio Generation
    print("\n7. Testing Audio Generation (ElevenLabs)...")
    response = requests.post(
        f"{BASE_URL}/api/audio",
        json={'script_text': script_text[:500]},  # Limit for testing
        timeout=30
    )

    assert response.status_code == 200
    audio_data = response.json()
    assert audio_data['success']
    audio_url = audio_data['audio_url']
    print(f"✓ Audio generation passed: {audio_url}")

    # Final Summary
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! ✓")
    print("=" * 60)
    print("\nPipeline Summary:")
    print(f"  1. PDF Extraction: ✓ ({len(extracted_text)} chars)")
    print(f"  2. Text Structuring: ✓ ({len(digest_json.get('concepts', []))} concepts)")
    print(f"  3. Relationship Extraction: ✓ ({len(graph_data.get('nodes', []))} nodes, {len(graph_data.get('edges', []))} edges)")
    print(f"  4. Overview Generation: ✓ ({len(overview_text)} chars)")
    print(f"  5. Audio Script: ✓ ({len(script_text)} chars)")
    print(f"  6. Audio URL: ✓ ({audio_url})")
    print("\nBackend is working perfectly! 🎉")

if __name__ == "__main__":
    try:
        test_pipeline()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
