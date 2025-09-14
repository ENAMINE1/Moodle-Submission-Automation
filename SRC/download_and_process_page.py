import os
import logging
from SRC.generate_prompt import analyze_code
from SRC.extract_feedback_annd_marks import extract_feedback_and_marks
import google.generativeai as genai

logger = logging.getLogger()

OFFSET_FILE = "student.txt"
PAGE_LIMIT = 5

pages_processed = 0
# Read last offset
if os.path.exists(OFFSET_FILE):
    with open(OFFSET_FILE, "r") as f:
        content = f.read().strip()
        if content:   # only convert if not empty
            pages_processed = int(content)
        else:
            pages_processed = 0   # default if file is empty
# models = genai.list_models()
# for m in models:
#     print(m.name, "=>", m.supported_generation_methods)


QUESTION_PATH = "./ASSIGN_VAR/question.txt"
EVALUATION_PATH = "./ASSIGN_VAR/evaluation.txt"
DOWNLOAD_DIRECTORY = "PDS_SEC_2"

def update_grade_and_feedback(page, roll_number, grade, feedback):
    page.locator("input#id_grade").fill(grade)
    logger.info(f"Graded Student {roll_number}: {grade}")
    # Extract feedback comment
    # Target the TinyMCE iframe
    editor_iframe = page.frame_locator("iframe#id_assignfeedbackcomments_editor_ifr")

    # Clear existing content by pressing Ctrl+A and Backspace, then type
    editor_body = editor_iframe.locator("body#tinymce")

    editor_body.click()  # focus the editor
    editor_body.press("Control+A")
    editor_body.press("Backspace")
    editor_body.type(f"{feedback}")
    editor_text = editor_body.inner_text().strip()

    # Locate the checkbox
    checkbox = page.locator("input[type='checkbox'][name='sendstudentnotifications']")

    # Make sure it is unchecked
    # checkbox.check()
    checkbox.uncheck()
    # page.wait_for_timeout(2000)  # 2000 ms = 2 seconds

    if editor_text:
        # Click save
        save_button = page.locator("form[data-region='grading-actions-form'] button[name='savechanges']")

        with page.expect_response(lambda response: "mod_assign_submit_grading_form" in response.url) as resp_info:
            save_button.click()

        response = resp_info.value
        logger.info(f"Save request completed with status {response.status}")
    else:
        logger.warning("Editor body empty, skipping 'Save changes'.")

    logger.info("Feedback text updated successfully inside TinyMCE editor.")

    # Wait for 5 seconds before going back
    # page.wait_for_timeout(2000)  # 2000 ms = 2 seconds

    # Go back to the previous page (submissions table)
    page.go_back()
    if("page=" in page.url):
        logger.info(f"Returned to submissions page: {page.url}")
    else:
        page.go_back()
        logger.warning(f"Returned to submissions page: {page.url}")

    # Wait for table to reappear
    page.wait_for_selector("table.generaltable")
    # page.wait_for_timeout(5000)  # 2000 ms = 2 seconds
    logger.info("Returned to submissions table.")

def process_page(page, page_num):
    """Process all rows of the current page"""
    global student, cnt
    global OFFSET_FILE
    global QUESTION_PATH, EVALUATION_PATH, DOWNLOAD_DIRECTORY
    global logger
    rows = page.locator("table.generaltable tbody tr")
    row_count = rows.count()
    print(f"Rows found: {row_count} on page {page_num}")
    for i in range(row_count):
        row = rows.nth(i)
        try:
            username_cell = row.locator("td.username")
            if username_cell.count() == 0:
                continue

            roll_number = username_cell.inner_text(timeout=2000).strip()
            if not roll_number:
                continue
            logger.info("----------------------------------------------------------------------------------------")
            logger.info(f"Processing student: {roll_number} in {page_num}")

            submission_cell = row.locator("td.c10")
            if submission_cell.count() == 0:
                continue

            file_links = submission_cell.locator("a").all()
            if not file_links:
                logger.warning(f"No submission links found for {roll_number}")
                # Click grade button to open grade page
                row.locator("a.btn.btn-primary", has_text="Grade").click()

                # Wait until grade panel loads
                page.wait_for_selector("div[data-region='grade-panel']")
                update_grade_and_feedback(page, roll_number, "0", "No submission found.")
                continue

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
                    grade, feedback = extract_feedback_and_marks(student_folder)
                    logger.info(f"Feedback - {feedback}\nGrade - {grade}")
                    row.locator("a.btn.btn-primary", has_text="Grade").click()
                    # Wait until grade panel loads
                    page.wait_for_selector("div[data-region='grade-panel']")
                    update_grade_and_feedback(page, roll_number, grade, feedback)


        except Exception as e:
            logger.error(f"Error processing row {i+1}: {e}")


def download_all_pages(page):
    global pages_processed
    model_ids = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.5-pro"]

    while True:
        # Read current page number from the active <li>
        active_page = page.locator("li.page-item.active[data-page-number]").first
        page_num = int(active_page.get_attribute("data-page-number"))

        logger.info(f"Processing page {page_num}...")

        if page_num > pages_processed:
            if (page_num - pages_processed) <= PAGE_LIMIT:
                process_page(page, page_num)
            else:
                break

        # Locate next page button (»)
        next_page = page.locator("nav.pagination a:has-text('»')").first

        if not next_page.is_visible() or not next_page.is_enabled():
            logger.info("No more pages to process. Scraping finished.")
            break

        logger.info(f"Moving to next page {page_num + 1}...")
        next_page.click()
        page.wait_for_load_state("load")

    # Save current offset
    with open(OFFSET_FILE, "w") as f:
        f.write(str(page_num - 1))
