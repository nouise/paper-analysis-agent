from playwright.sync_api import sync_playwright
import os

# Create a simple test file
test_file_path = os.path.join(os.path.dirname(__file__), 'test_upload.txt')
with open(test_file_path, 'w', encoding='utf-8') as f:
    f.write("This is a test document for knowledge base upload testing.\n")
    f.write("It contains some sample content that can be parsed and indexed.\n")
    f.write("The quick brown fox jumps over the lazy dog.\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 900})

    # Capture console logs
    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

    # Capture page errors
    page_errors = []
    page.on("pageerror", lambda err: page_errors.append(str(err)))

    # Capture network requests
    network_logs = []
    page.on("request", lambda req: network_logs.append(f"REQUEST: {req.method} {req.url}"))
    page.on("response", lambda res: network_logs.append(f"RESPONSE: {res.status} {res.url}"))

    print("=" * 60)
    print("Step 1: Navigate to knowledge base page")
    print("=" * 60)

    page.goto('http://localhost:5180/knowledge')
    page.wait_for_load_state('networkidle')
    page.screenshot(path='test_01_initial.png')
    print("Screenshot: test_01_initial.png")

    print("\n" + "=" * 60)
    print("Step 2: Click on knowledge base card")
    print("=" * 60)

    # Click on the database card
    card = page.locator('.database-card').first
    card.click()
    page.wait_for_timeout(1000)
    page.screenshot(path='test_02_selected.png')
    print("Screenshot: test_02_selected.png")

    print("\n" + "=" * 60)
    print("Step 3: Try to upload file")
    print("=" * 60)

    try:
        # Find file input
        file_input = page.locator('input[type="file"]').first

        if file_input.is_visible():
            print(f"File input found, uploading: {test_file_path}")
            file_input.set_input_files(test_file_path)
            print("File selected")

            # Wait for upload
            page.wait_for_timeout(3000)
            page.screenshot(path='test_03_uploaded.png')
            print("Screenshot: test_03_uploaded.png")

            # Check for Add to KB button
            add_btn = page.locator('button:has-text("Add to KB")').first
            if add_btn.is_visible():
                print("Add to KB button found, clicking...")
                add_btn.click()
                page.wait_for_timeout(2000)
                page.screenshot(path='test_04_added.png')
                print("Screenshot: test_04_added.png")
            else:
                print("Add to KB button NOT found")
        else:
            print("File input NOT visible")
    except Exception as e:
        print(f"Error during upload: {e}")

    print("\n" + "=" * 60)
    print("Console Logs:")
    print("=" * 60)
    for log in console_logs:
        print(log)

    print("\n" + "=" * 60)
    print("Page Errors:")
    print("=" * 60)
    for err in page_errors:
        print(err)

    print("\n" + "=" * 60)
    print("Network Logs:")
    print("=" * 60)
    for log in network_logs:
        if 'knowledge' in log.lower() or 'upload' in log.lower():
            print(log)

    browser.close()
