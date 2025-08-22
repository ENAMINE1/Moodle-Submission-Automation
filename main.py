import os
import re
import time
import pytesseract
from PIL import Image
import io
from playwright.sync_api import sync_playwright, expect

import os
import logging

import google.generativeai as genai
import requests
from dotenv import load_dotenv

load_dotenv()

QUESTION_PATH = "./ASSIGN_VAR/question.txt"
EVALUATION_PATH = "./ASSIGN_VAR/evaluation.txt"


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
    # "https://moodlecse.iitkgp.ac.in/moodle/mod/assign/view.php?id=1531&action=grading",
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



def process_page(page):
    """Process all rows of the current page"""
    rows = page.locator("table.generaltable tbody tr")
    row_count = rows.count()

    for i in range(row_count):
        row = rows.nth(i)
        try:
            username_cell = row.locator("td.username")
            if username_cell.count() == 0:
                continue

            roll_number = username_cell.inner_text(timeout=2000).strip()
            if not roll_number:
                continue

            logger.info(f"Processing student: {roll_number}")

            submission_cell = row.locator("td.c10")
            if submission_cell.count() == 0:
                continue

            file_links = submission_cell.locator("a").all()
            for link in file_links:
                file_url = link.get_attribute("href")
                file_name = link.inner_text().strip()
                if file_url and file_name.endswith(".c"):
                    student_folder = os.path.join(DOWNLOAD_DIRECTORY, roll_number)
                    os.makedirs(student_folder, exist_ok=True)

                    save_path = os.path.join(student_folder, f"{file_name}")
                    with page.expect_download() as download_info:
                        link.click()
                    download = download_info.value
                    download.save_as(save_path)
                    logger.info(f"Downloaded: {os.path.basename(save_path)}")
                    # Analyze the code and save comments
                    analyze_code(QUESTION_PATH, EVALUATION_PATH, save_path, student_folder)
                    logger.info(f"Analyzed code for {roll_number} and saved comments.")

        except Exception as e:
            logger.error(f"Error processing row {i+1}: {e}")


def download_all_pages(page):
    page_num = 1
    while True:
        logger.info(f"Processing page {page_num}...")
        process_page(page)

        # Locate next page button (take first match to avoid strict mode error)
        next_page = page.locator("nav.pagination a:has-text('»')").first

        if not next_page.is_visible() or not next_page.is_enabled():
            logger.info("No more pages to process. Scraping finished.")
            break

        logger.info(f"Moving to next page {page_num + 1}...")
        next_page.click()
        page.wait_for_load_state("load")

        page_num += 1


def analyze_code(question_file, evlaution_file, code_file, save_path):

    code = generate_prompt(question_file, evlaution_file, code_file)
    api_key=os.getenv("GEMINI_API_KEY")
    print(api_key)
    model_id = "gemini-1.5-flash"  # or gemini-2.5-pro, depending on your setup

    endpoint = f"https://generativelanguage.googleapis.com/v1/models/{model_id}:generateContent?key={api_key}"

    headers = {
        "Content-Type": "application/json"
    }

    data = {
    "contents": [
        {
            "role": "user",
            "parts": [
                {
                    "text": (
                        "You are a liberal programming examiner. But be little strict for indentation and comments "
                        "Rules: "
                        "1) Output plain text only (no markdown, no code fences). "
                        "2) Response must have exactly two sections:\n"
                        "Comments:\nMarks:\n"
                        "3) Limit response length to 50–60 words. "
                        "4) In Comments: only show <wrong_code_snippet>\s*→\s*<what is wrong>\s*→\s*<what should have been done>\n\n"
                        "5) Do not explain anything else, do not add extra lines. "
                        "6) Marks must follow this structure in Marking Criteria\n"
                        "7) Dont forget to give marks for each criteria\n"
                        f"Question: {code["question"]}\n\n"
                        f"Evaluation Criteria: {code["evaluation_criteria"]["criteria"]}\n\n"
                        "Code:\n"
                        f"{code["code"]}\n\n"
                        "Marking Criteria:\n"
                        f"- Logical Sanity: {code["evaluation_criteria"]["logical_marks"]}\n"
                        f"- Correct Indentation: {code["evaluation_criteria"]["indentation_marks"]}\n"
                        f"- Comments in the code: {code["evaluation_criteria"]["comments_marks"]}\n"
                        f"- Output correctness: {code["evaluation_criteria"]["output_marks"]}"
                        f"- Total Marks: {code["evaluation_criteria"]["total_marks"]}\n"
                    )
                }
            ]
        }
        ],
        "generationConfig": {
            "maxOutputTokens": 150,
            "temperature": 0.2
        }
    }
    response = requests.post(endpoint, headers=headers, json=data)
    resp_json = response.json()
    if "candidates" in resp_json:
        output_text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
        with open (os.path.join(save_path, "comments.txt"), 'w') as f:
            f.write(output_text)
    else:
        print("No text in response:", resp_json)

def generate_prompt(question_file, evlaution_file, code_file):
    with open(question_file, 'r') as f:
        question = f.read().strip()

    marks_dict = {}
    remaining_text = ""

    with open(evlaution_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:   # stop when an empty line is found
                # store the rest of the file into remaining_text
                remaining_text = f.read().strip()
                break
            if "=" in line:
                key, value = line.split("=")
                marks_dict[key.strip()] = int(value.strip())
        with open(code_file, 'r') as f:
            code = f.read().strip()

    evaluation_criteria = {
        "criteria": remaining_text,
        "logical_marks": marks_dict.get("Logic_syntax", 0),
        "indentation_marks": marks_dict.get("Indentation", 0),
        "comments_marks": marks_dict.get("Comment", 0),
        "output_marks": marks_dict.get("Compilation_I/O", 0),
        "total_marks": marks_dict.get("Total", 0)
    }

    return {
        "question": question,
        "evaluation_criteria": evaluation_criteria,
        "code": code
    }

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

        download_all_pages(page)

    print(f"\n--- Automation Complete ---")
    print(f"Total students processed: {total_students_processed}")
    print(f"URLs processed: {len(SUBMISSION_URLS)}")

    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
