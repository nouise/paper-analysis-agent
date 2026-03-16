#!/usr/bin/env python3
"""Debug document list display"""

from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 900})

    page.goto('http://localhost:5180/knowledge')
    page.wait_for_load_state('networkidle')

    card = page.locator('.database-card').first
    card.click()
    page.wait_for_timeout(2000)

    # Get document meta info via JS
    meta_info = page.evaluate('''() => {
        const items = document.querySelectorAll('.document-item')
        return Array.from(items).map(item => {
            const name = item.querySelector('.document-name')
            const meta = item.querySelector('.document-meta')
            return {
                name: name ? name.textContent : 'N/A',
                meta: meta ? meta.textContent : 'N/A'
            }
        })
    }''')

    with open('doclist_debug.json', 'w', encoding='utf-8') as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(meta_info)} documents to doclist_debug.json")

    browser.close()
