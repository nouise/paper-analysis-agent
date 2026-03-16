from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:5180/knowledge')
    page.wait_for_load_state('networkidle')

    # Take initial screenshot
    page.screenshot(path='knowledge_initial.png', full_page=True)
    print("Screenshot saved to knowledge_initial.png")

    # Click on the knowledge base card
    try:
        # Try to find and click the database card
        card = page.locator('.database-card').first
        if card.is_visible():
            card.click()
            print("Clicked on knowledge base card")
            page.wait_for_timeout(1000)  # Wait for animation

            # Take screenshot after click
            page.screenshot(path='knowledge_selected.png', full_page=True)
            print("Screenshot saved to knowledge_selected.png")

            # Check for components
            content = page.content()

            if "Upload Documents" in content:
                print("[OK] Upload Documents section found")
            else:
                print("[MISSING] Upload Documents section NOT found")

            if "Documents" in content:
                print("[OK] Documents section found")
            else:
                print("[MISSING] Documents section NOT found")

            if "Test Query" in content:
                print("[OK] Test Query section found")
            else:
                print("[MISSING] Test Query section NOT found")
        else:
            print("[ERROR] Knowledge base card not visible")
    except Exception as e:
        print(f"[ERROR] {e}")

    browser.close()
