#!/usr/bin/env python3
"""Test the complete upload and add to knowledge base flow"""

import requests
import os

BASE_URL = "http://localhost:8003"
DB_ID = "kb_b6fbe3d3f9933339e1a3016dafcf54a3"

# Step 1: Upload a file
print("=" * 60)
print("Step 1: Upload file")
print("=" * 60)

# Create a test file
test_content = """This is a test document for knowledge base.
It contains information about machine learning and AI.
Machine learning is a subset of artificial intelligence.
"""
test_file_path = "test_upload_ml.txt"
with open(test_file_path, "w") as f:
    f.write(test_content)

# Upload
with open(test_file_path, "rb") as f:
    files = {"file": ("test_ml.txt", f, "text/plain")}
    params = {"db_id": DB_ID}
    response = requests.post(f"{BASE_URL}/knowledge/files/upload", files=files, params=params)

print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")

if response.status_code == 200:
    upload_result = response.json()
    file_path = upload_result.get("file_path")
    print(f"\nFile uploaded to: {file_path}")

    # Step 2: Add to knowledge base
    print("\n" + "=" * 60)
    print("Step 2: Add to knowledge base")
    print("=" * 60)

    add_data = {
        "items": [file_path],
        "params": {"content_type": "file"}
    }

    response = requests.post(
        f"{BASE_URL}/knowledge/databases/{DB_ID}/documents",
        json=add_data
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:1000]}")

    # Step 3: Check database info
    print("\n" + "=" * 60)
    print("Step 3: Check database info")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/knowledge/databases/{DB_ID}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        db_info = response.json()
        print(f"Files: {db_info.get('files', {})}")
        print(f"Row count: {db_info.get('row_count', 0)}")
