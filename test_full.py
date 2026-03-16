from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 900})
    page.goto('http://localhost:5180/knowledge')
    page.wait_for_load_state('networkidle')

    # Click on the knowledge base card
    card = page.locator('.database-card').first
    card.click()
    page.wait_for_timeout(1000)

    # Scroll down to see Test Query
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)

    # Take full page screenshot
    page.screenshot(path='knowledge_full.png', full_page=True)
    print("Full screenshot saved to knowledge_full.png")

    browser.close()
