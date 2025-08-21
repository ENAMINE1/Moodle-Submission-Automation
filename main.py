import os
import re
import time
import pytesseract
from PIL import Image
import io
from playwright.sync_api import sync_playwright, expect

import os
import logging

# --- Setup logger ---
logger = logging.getLogger("submission_downloader")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

# Log to file + console
file_handler = logging.FileHandler("submissions.log", encoding="utf-8")
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# --- Configuration ---
USERNAME = "kshashwat"
PASSWORD = "Moodle@l43"
DOWNLOAD_DIRECTORY = "PDS_SEC_2"


MOODLE_URL = "https://moodlecse.iitkgp.ac.in/moodle/login/index.php"

# --- Submission URLs Configuration ---
# Add all the submission URLs you want to process:
# Each URL can be from different quizzes, pages, or filters
# If there are multiple pages, you can add more URLs with different page numbers
SUBMISSION_URLS = [
    # "https://moodlecse.iitkgp.ac.in/moodle/mod/quiz/report.php?id=1470&mode=overview",
    "https://moodlecse.iitkgp.ac.in/moodle/mod/assign/view.php?id=1530&action=grading",
    # Add more URLs as needed:
    # "https://moodlecse.iitkgp.ac.in/moodle/mod/quiz/report.php?id=1509&mode=overview",
    # "https://moodlecse.iitkgp.ac.in/moodle/mod/quiz/report.php?id=1470&mode=overview&page=2",
]

# --- Question Configuration ---
# Specify which questions to process:
# - All questions: QUESTIONS_TO_PROCESS = "all"
# - Specific questions: QUESTIONS_TO_PROCESS = [1, 2]  # Process Q.1 and Q.2 only
# - Single question: QUESTIONS_TO_PROCESS = [1]  # Process only Q.1
QUESTIONS_TO_PROCESS = "all"  # Change this to control which questions to process

if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)


import re

def analyze_table_columns(page, table_selector="#yui_3_18_1_1_1755757807821_328"):
    """
    Analyze table headers to map header names to column indices
    Returns a dictionary: {header_name: column_index}
    """
    column_map = {}
    try:
        table = page.locator(table_selector)
        table_headers = table.locator("thead th").all()

        for i, header in enumerate(table_headers):
            try:
                header_text = header.inner_text().strip()

                # Clean header text (remove extra spaces, line breaks)
                header_text = re.sub(r'\s+', ' ', header_text)

                if header_text:  # only add non-empty headers
                    column_map[header_text] = i
                    print(f"  Mapped '{header_text}' to column {i}")

            except Exception:
                continue

    except Exception as e:
        print(f"Error analyzing table columns: {e}")

    return column_map


def get_questions_to_process(available_questions):
    """
    Determine which questions to process based on configuration
    """
    if QUESTIONS_TO_PROCESS == "all":
        return sorted(available_questions.keys())
    else:
        # Filter to only include available questions
        return [q for q in QUESTIONS_TO_PROCESS if q in available_questions]


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
    page.goto(MOODLE_URL)
    page.get_by_label("Username").fill(USERNAME)
    page.get_by_label("Password").fill(PASSWORD)

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
                    page.goto(MOODLE_URL)
                    page.get_by_label("Username").fill(USERNAME)
                    page.get_by_label("Password").fill(PASSWORD)
                    time.sleep(1)  # Brief pause before retry
        else:
            print(f"Could not extract CAPTCHA text on attempt {attempt + 1}.")
            if attempt < max_retries - 1:
                print("Retrying...")
                # Refresh the page to get a new CAPTCHA
                page.reload()
                page.get_by_label("Username").fill(USERNAME)
                page.get_by_label("Password").fill(PASSWORD)
                time.sleep(1)  # Brief pause before retry

    # If all OCR attempts failed, fall back to manual solving
    if not login_successful:
        print("All OCR attempts failed. Please solve CAPTCHA manually.")
        page.wait_for_url("**/moodle/", timeout=300000)
        print("Login successful!")

    # --- 3. Process Submission URLs ---
    print(f"Processing {len(SUBMISSION_URLS)} submission URLs...")

    if not SUBMISSION_URLS:
        print("No submission URLs configured! Check SUBMISSION_URLS configuration.")
        return

    total_students_processed = 0

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

        submissions_table = page.locator("table.generaltable")
        rows = submissions_table.locator("tbody tr")
        row_count = rows.count()

        logger.info(f"Found {row_count} submissions in table.")

        for i in range(row_count):
            row = rows.nth(i)
            try:
                # Username cell: has "username" in its class list
                username_cell = row.locator("td.username")
                if username_cell.count() == 0:
                    logger.debug(f"Skipping row {i+1}: no username cell")
                    continue

                roll_number = username_cell.inner_text(timeout=2000).strip()
                if not roll_number:
                    logger.debug(f"Skipping row {i+1}: empty roll number text")
                    continue

                logger.info(f"Processing student: {roll_number}")

                # Submission cell: Moodle uses c10 for "File submissions"
                submission_cell = row.locator("td.c10")
                if submission_cell.count() == 0:
                    logger.info(f"No submission cell found for {roll_number}")
                    continue

                file_links = submission_cell.locator("a").all()
                downloaded_any = False

                for link in file_links:
                    file_url = link.get_attribute("href")
                    file_name = link.inner_text().strip()

                    # only download .c files
                    if file_url and file_name.endswith(".c"):
                        student_folder = os.path.join(DOWNLOAD_DIRECTORY, roll_number)
                        os.makedirs(student_folder, exist_ok=True)

                        save_path = os.path.join(student_folder, f"{roll_number}_{file_name}")
                        with page.expect_download() as download_info:
                            link.click()
                        download = download_info.value
                        download.save_as(save_path)
                        logger.info(f"Downloaded: {os.path.basename(save_path)}")
                        downloaded_any = True

                if not downloaded_any:
                    logger.info(f"No .c submissions found for {roll_number}")

            except Exception as e:
                logger.error(f"Skipping row {i+1}: {e}")

        print(f"Completed URL {url_index} - processed {row_count} students")

    print(f"\n--- Automation Complete ---")
    print(f"Total students processed: {total_students_processed}")
    print(f"URLs processed: {len(SUBMISSION_URLS)}")

    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
