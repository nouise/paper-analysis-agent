#!/usr/bin/env python3
"""Debug document list display"""

from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 900})

    # Capture console logs
    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

    print("Navigate to Knowledge Base page")
    page.goto('http://localhost:5180/knowledge')
    page.wait_for_load_state('networkidle')

    print("\nClick on first knowledge base card")
    card = page.locator('.database-card').first
    card.click()
    page.wait_for_timeout(2000)

    print("\nCheck DocumentList items")
    page.screenshot(path='debug_doclist.png', full_page=True)

    # Get document items details
    doc_items = page.locator('.document-item').all()
    print(f"Found {len(doc_items)} document items")

    for i, doc in enumerate(doc_items):
        print(f"\n--- Document {i} ---")

        # Try to get inner HTML
        try:
            html = doc.inner_html()
            print(f"HTML: {html[:500]}")
        except Exception as e:
            print(f"Error getting HTML: {e}")

        # Try to get text content
        try:
            text = doc.inner_text()
            print(f"Text: {text}")
        except Exception as e:
            print(f"Error getting text: {e}")

    print("\n=== Console Logs ===")
    for log in console_logs:
        print(log)

    browser.close()
