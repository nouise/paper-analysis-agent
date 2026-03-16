from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Capture console logs
    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))

    # Capture page errors
    page_errors = []
    page.on("pageerror", lambda err: page_errors.append(str(err)))

    page.goto('http://localhost:5180/knowledge')
    page.wait_for_load_state('networkidle')

    print("=== Console Logs ===")
    for log in console_logs:
        print(log)

    print("\n=== Page Errors ===")
    for err in page_errors:
        print(err)

    # Try clicking on the database card
    try:
        card = page.locator('.database-card').first
        if card.is_visible():
            card.click()
            page.wait_for_timeout(2000)

            print("\n=== Console Logs After Click ===")
            for log in console_logs:
                if "console" in log.lower() or "error" in log.lower():
                    print(log)

            print("\n=== Page Content ===")
            content = page.content()
            print(content[:5000])  # Print first 5000 chars
        else:
            print("Card not visible")
    except Exception as e:
        print(f"Error: {e}")

    browser.close()
