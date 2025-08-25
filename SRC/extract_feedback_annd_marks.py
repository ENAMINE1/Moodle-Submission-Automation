import os
import logging
logger = logging.getLogger()


def extract_feedback_and_marks(filepath: str):
    total_marks = "0"
    feedback = ""
    file = os.path.join(filepath, "comments.txt")

    with open(file, "r", encoding="utf-8") as f:
        feedback = f.read().strip()

    # Try to extract "Total Marks"
    for line in feedback.splitlines():
        if line.strip().lower().startswith("total marks:"):
            total_marks = line.split(":", 1)[1].strip()
            break

    if total_marks == "0":
        logger.warning(f"Warning: Total Marks missing value")

    return total_marks, feedback
