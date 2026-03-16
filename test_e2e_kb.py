#!/usr/bin/env python3
"""End-to-end test for knowledge base upload flow"""

from playwright.sync_api import sync_playwright
import time
import os

# Create test file
test_file_path = os.path.join(os.path.dirname(__file__), 'test_e2e.txt')
with open(test_file_path, 'w', encoding='utf-8') as f:
    f.write("Machine learning is a subset of artificial intelligence.\n")
    f.write("Deep learning is a subset of machine learning.\n")
    f.write("Neural networks are the foundation of deep learning.\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 900})

    # Capture console logs
    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

    print("Step 1: Navigate to Knowledge Base page")
    page.goto('http://localhost:5180/knowledge')
    page.wait_for_load_state('networkidle')
    page.screenshot(path='e2e_01_initial.png', full_page=True)
    print("  Screenshot saved: e2e_01_initial.png")

    print("\nStep 2: Click on first knowledge base card")
    card = page.locator('.database-card').first
    if card.count() == 0:
        print("  ERROR: No database cards found!")
    else:
        card.click()
        page.wait_for_timeout(1000)
        page.screenshot(path='e2e_02_selected.png', full_page=True)
        print("  Screenshot saved: e2e_02_selected.png")

    print("\nStep 3: Upload file")
    file_input = page.locator('input[type="file"]').first
    if file_input.count() == 0:
        print("  ERROR: No file input found!")
    else:
        file_input.set_input_files(test_file_path)
        page.wait_for_timeout(2000)
        page.screenshot(path='e2e_03_uploading.png', full_page=True)
        print("  Screenshot saved: e2e_03_uploading.png")

    print("\nStep 4: Wait for upload to complete")
    page.wait_for_timeout(3000)
    page.screenshot(path='e2e_04_uploaded.png', full_page=True)
    print("  Screenshot saved: e2e_04_uploaded.png")

    print("\nStep 5: Click 'Add to KB' button")
    add_btn = page.locator('button.add-btn').first
    if add_btn.count() == 0:
        print("  ERROR: No 'Add to KB' button found!")
        print("  Checking for upload queue items...")
        queue_items = page.locator('.queue-item').all()
        for i, item in enumerate(queue_items):
            status = item.locator('.status-badge').first
            print(f"    Queue item {i}: {status.inner_text() if status.count() > 0 else 'no status'}")
    else:
        print(f"  Found 'Add to KB' button, clicking...")
        add_btn.click()
        page.wait_for_timeout(2000)
        page.screenshot(path='e2e_05_adding.png', full_page=True)
        print("  Screenshot saved: e2e_05_adding.png")

    print("\nStep 6: Wait for processing to complete")
    page.wait_for_timeout(5000)
    page.screenshot(path='e2e_06_complete.png', full_page=True)
    print("  Screenshot saved: e2e_06_complete.png")

    print("\nStep 7: Check DocumentList")
    doc_items = page.locator('.document-item').all()
    print(f"  Found {len(doc_items)} documents in list")
    for i, doc in enumerate(doc_items):
        name = doc.locator('.document-name').first
        meta = doc.locator('.document-meta').first
        print(f"    Doc {i}: name='{name.inner_text() if name.count() > 0 else 'N/A'}', meta='{meta.inner_text() if meta.count() > 0 else 'N/A'}'")

    print("\n=== Console Logs (errors only) ===")
    for log in console_logs:
        if 'error' in log.lower() or 'warn' in log.lower():
            print(log)

    browser.close()
    print("\nTest complete!")
