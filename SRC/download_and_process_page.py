import os
import logging
from SRC.generate_prompt import analyze_code

logger = logging.getLogger()


QUESTION_PATH = "./ASSIGN_VAR/question.txt"
EVALUATION_PATH = "./ASSIGN_VAR/evaluation.txt"
DOWNLOAD_DIRECTORY = "PDS_SEC_2"

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
            if not file_links:
                logger.warning(f"No submission links found for {roll_number}")
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
                    # analyze_code(QUESTION_PATH, EVALUATION_PATH, save_path, student_folder)
                    # logger.info(f"Analyzed code for {roll_number} and saved comments.")

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