import os
import io
import time
import logging
import pytesseract
from PIL import Image
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, expect
from SRC.download_and_process_page import download_all_pages, process_page

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s (Line %(lineno)d in %(filename)s)",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("submissions.log", encoding="utf-8"),
    ]
)

logger = logging.getLogger()

# Add all the submission URLs you want to process:
SUBMISSION_URLS = [
    "https://moodlecse.iitkgp.ac.in/moodle/mod/assign/view.php?id=1535&action=grading",
    # "https://moodlecse.iitkgp.ac.in/moodle/mod/assign/view.php?id=1493&action=grading",
    # "https://moodlecse.iitkgp.ac.in/moodle/mod/assign/view.php?id=1491&action=grading",
    # "https://moodlecse.iitkgp.ac.in/moodle/mod/assign/view.php?id=1530&action=grading",
]

DOWNLOAD_DIRECTORY = "PDS_SEC_2"

if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)


import re

def solve_captcha(page):
    """
    Solve CAPTCHA using pytesseract OCR
    Returns the extracted text from the CAPTCHA image
    """
    try:
        # Take a screenshot of the CAPTCHA image
        captcha_element = page.locator("#captcha-image")
        captcha_screenshot = captcha_element.screenshot()

        # Convert screenshot to PIL Image
        image = Image.open(io.BytesIO(captcha_screenshot))

        # Use pytesseract to extract text
        captcha_text = pytesseract.image_to_string(
            image, config='--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789').strip()

        print(f"OCR extracted CAPTCHA text: '{captcha_text}'")
        return captcha_text
    except Exception as e:
        print(f"Error solving CAPTCHA with OCR: {e}")
        return None

def run(playwright):
    # Use headless=False to see the browser
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # --- 1. Login ---
    page.goto(os.getenv("MOODLE_URL"))
    page.get_by_label("Username").fill(os.getenv("MODULENAME"))
    page.get_by_label("Password").fill(os.getenv("PASSWORD"))

    # --- The CAPTCHA Challenge ---
    print("Attempting to solve CAPTCHA automatically...")

    login_successful = False
    max_retries = 3

    for attempt in range(max_retries):
        print(f"CAPTCHA attempt {attempt + 1}/{max_retries}...")

        # Try to solve CAPTCHA using OCR
        captcha_text = solve_captcha(page)

        if captcha_text:
            # Fill the CAPTCHA input field
            captcha_input = page.locator("input[name='captcha']")
            captcha_input.fill(captcha_text)

            # Click the login button
            login_button = page.get_by_role("button", name="Log in")
            login_button.click()

            try:
                # Wait for successful login (dashboard page)
                page.wait_for_url("**/moodle/", timeout=2000)
                print(f"Login successful with OCR on attempt {attempt + 1}!")
                login_successful = True
                break
            except:
                print(f"OCR CAPTCHA solution failed on attempt {attempt + 1}.")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    # Go back to login page for retry
                    page.goto(os.getenv("MOODLE_URL"))
                    page.get_by_label("Username").fill(os.getenv("MODULENAME"))
                    page.get_by_label("Password").fill(os.getenv("PASSWORD"))
                    time.sleep(1)  # Brief pause before retry
        else:
            print(f"Could not extract CAPTCHA text on attempt {attempt + 1}.")
            if attempt < max_retries - 1:
                print("Retrying...")
                # Refresh the page to get a new CAPTCHA
                page.reload()
                page.get_by_label("Username").fill(os.getenv("MODULENAME"))
                page.get_by_label("Password").fill(os.getenv("PASSWORD"))
                time.sleep(1)  # Brief pause before retry

    # If all OCR attempts failed, fall back to manual solving
    if not login_successful:
        print("All OCR attempts failed. Please solve CAPTCHA manually.")
        page.get_by_label("Username").fill(os.getenv("MODULENAME"))
        page.get_by_label("Password").fill(os.getenv("PASSWORD"))
        page.wait_for_url("**/moodle/", timeout=300000)
        print("Login successful!")

    # --- 3. Process Submission URLs ---
    print(f"Processing {len(SUBMISSION_URLS)} submission URLs...")

    if not SUBMISSION_URLS:
        print("No submission URLs configured! Check SUBMISSION_URLS configuration.")
        return

    total_students_processed = 0

    logger.info(f"\n\n+++++++++++++++++++++Starting processing of submission URLs.+++++++++++++++++++++++++\n")
    # Process each submission URL
    for url_index, submission_url in enumerate(SUBMISSION_URLS, 1):
        print(
            f"\n--- Processing Submission URL {url_index}/{len(SUBMISSION_URLS)} ---")
        print(f"URL: {submission_url}")

        # Navigate to the submission URL
        try:
            page.goto(submission_url)
            print(f"Successfully navigated to submission URL {url_index}")
        except Exception as e:
            print(f"Error navigating to URL {url_index}: {e}")
            continue

        download_all_pages(page)
        # process_page(page, 1)

    print(f"\n--- Automation Complete ---")
    print(f"Total students processed: {total_students_processed}")
    print(f"URLs processed: {len(SUBMISSION_URLS)}")

    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
