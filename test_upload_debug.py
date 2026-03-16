from playwright.sync_api import sync_playwright
import os

# Create a simple test file
test_file_path = os.path.join(os.path.dirname(__file__), 'test_upload.txt')
with open(test_file_path, 'w', encoding='utf-8') as f:
    f.write("This is a test document for knowledge base upload testing.\n")
    f.write("It contains some sample content that can be parsed and indexed.\n")
    f.write("The quick brown fox jumps over the lazy dog.\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Set to False to see browser
    page = browser.new_page(viewport={'width': 1400, 'height': 900})

    # Capture console logs
    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

    # Capture page errors
    page_errors = []
    page.on("pageerror", lambda err: page_errors.append(str(err)))

    print("=" * 60)
    print("Step 1: Navigate to knowledge base page")
    print("=" * 60)

    page.goto('http://localhost:5180/knowledge')
    page.wait_for_load_state('networkidle')
    page.screenshot(path='debug_01_initial.png')

    print("\n" + "=" * 60)
    print("Step 2: Click on knowledge base card")
    print("=" * 60)

    card = page.locator('.database-card').first
    card.click()
    page.wait_for_timeout(1500)
    page.screenshot(path='debug_02_selected.png')

    print("\n" + "=" * 60)
    print("Step 3: Click on upload zone to trigger file input")
    print("=" * 60)

    # Click on the upload zone
    upload_zone = page.locator('.upload-zone').first
    print(f"Upload zone visible: {upload_zone.is_visible()}")

    if upload_zone.is_visible():
        upload_zone.click()
        print("Clicked upload zone")
        page.wait_for_timeout(1000)

        # Now find file input
        file_input = page.locator('input[type="file"]').first
        print(f"File input exists: {file_input.count() > 0}")
        print(f"File input visible: {file_input.is_visible()}")

        if file_input.count() > 0:
            print(f"Uploading file: {test_file_path}")
            file_input.set_input_files(test_file_path)
            print("File selected, waiting for upload...")

            page.wait_for_timeout(5000)
            page.screenshot(path='debug_03_after_upload.png')

            # Check for upload queue
            queue = page.locator('.upload-queue').first
            print(f"Upload queue visible: {queue.is_visible()}")

            if queue.is_visible():
                print("Upload queue found!")
                page.screenshot(path='debug_04_queue.png')

                # Check for Add to KB button
                add_btn = page.locator('button.add-btn').first
                print(f"Add to KB button visible: {add_btn.is_visible()}")

                if add_btn.is_visible():
                    print("Clicking Add to KB button...")
                    add_btn.click()
                    page.wait_for_timeout(3000)
                    page.screenshot(path='debug_05_after_add.png')
                else:
                    print("Add to KB button NOT found")
                    # Check what status is shown
                    status_badges = page.locator('.status-badge').all()
                    for i, badge in enumerate(status_badges):
                        print(f"Status badge {i}: {badge.text_content()}")
            else:
                print("Upload queue NOT found")
        else:
            print("File input NOT found after clicking")
    else:
        print("Upload zone NOT visible")

    print("\n" + "=" * 60)
    print("Console Logs:")
    print("=" * 60)
    for log in console_logs:
        if 'error' in log.lower() or 'warning' in log.lower():
            print(log)

    print("\n" + "=" * 60)
    print("Page Errors:")
    print("=" * 60)
    for err in page_errors:
        print(err)

    browser.close()
