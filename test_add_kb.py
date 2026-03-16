from playwright.sync_api import sync_playwright
import os

# Create test file
test_file_path = os.path.join(os.path.dirname(__file__), 'test_doc.txt')
with open(test_file_path, 'w', encoding='utf-8') as f:
    f.write("Machine learning is a subset of artificial intelligence.\n")
    f.write("Deep learning is a subset of machine learning.\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 900})

    # Capture console logs
    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

    # Capture page errors
    page_errors = []
    page.on("pageerror", lambda err: page_errors.append(str(err)))

    # Capture network
    network_logs = []
    page.on("response", lambda res: network_logs.append(f"{res.status} {res.url}") if res.url.contains('knowledge') else None)

    print("Step 1: Navigate to page")
    page.goto('http://localhost:5180/knowledge')
    page.wait_for_load_state('networkidle')

    print("Step 2: Click knowledge base card")
    card = page.locator('.database-card').first
    card.click()
    page.wait_for_timeout(1000)

    print("Step 3: Upload file")
    file_input = page.locator('input[type="file"]').first
    file_input.set_input_files(test_file_path)
    page.wait_for_timeout(3000)

    print("Step 4: Click Add to KB")
    add_btn = page.locator('button.add-btn').first
    if add_btn.is_visible():
        add_btn.click()
        print("Clicked Add to KB, waiting...")
        page.wait_for_timeout(5000)  # Wait for API call

    print("Step 5: Check final state")
    page.screenshot(path='test_final_state.png', full_page=True)

    print("\n=== Console Logs ===")
    for log in console_logs:
        if 'error' in log.lower() or 'warn' in log.lower():
            print(log)

    print("\n=== Page Errors ===")
    for err in page_errors:
        print(err)

    browser.close()
