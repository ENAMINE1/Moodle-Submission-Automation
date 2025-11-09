import os
import re
import requests
import logging
from dotenv import load_dotenv

logger = logging.getLogger()

load_dotenv()

def analyze_code(question_file, evlaution_file, code_file, save_path):
    prompt = generate_prompt(question_file, evlaution_file, code_file)
    api_key=os.getenv("GEMINI_API_KEY")
    model_id = "gemini-2.0-flash"  # or gemini-2.5-pro, depending on your setup
    logger.info(f"Using model: {model_id}")

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
                        f"You are a liberal programming examiner and give marks above {0.75 * int(prompt["evaluation_criteria"]["total_marks"])} if you find the code in correct direction and penalise for wrong answer."
                        "Rules: "
                        "1) Output plain text only (no markdown, no code fences). "
                        "2) Response must have exactly two sections:\n"
                        "Comments:\nMarks:\n"
                        "3) Limit response length to 50–60 words. "
                        "4) In Comments: if necessary only show the wrong code block followed by what is wrong in it and what should have been done, also\n\n"
                        "5) Do not explain anything else, do not add extra lines. "
                        "6) Marks must follow this structure in Marking Criteria\n"
                        "7) Dont forget to give marks for each criteria\n"
                        "8) Give extra marks than expected but less than total marks.\n"
                        "9) Point out maximum 3 mistakes."
                        f"Question: {prompt["question"]}\n\n"
                        f"Evaluation Criteria: {prompt["evaluation_criteria"]["criteria"]}\n\n"
                        "Code:\n"
                        f"{prompt["code"]}\n\n"
                        "Marking Criteria:\n"
                        f"Logical Sanity: {prompt["evaluation_criteria"]["logical_marks"]}\n"
                        f"Correct Indentation: {prompt["evaluation_criteria"]["indentation_marks"]}\n"
                        f"Comments in the code: {prompt["evaluation_criteria"]["comments_marks"]}\n"
                        f"Output correctness: {prompt["evaluation_criteria"]["output_marks"]}"
                        f"Total Marks: {prompt["evaluation_criteria"]["total_marks"]}\n"
                    )
                }
            ]
        }
        ],
        "generationConfig": {
            "maxOutputTokens": 200,
            "temperature": 0.2
        }
    }
    response = requests.post(endpoint, headers=headers, json=data)
    resp_json = response.json()
    logger.warning(f"Response: {resp_json}")
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
        "output_marks": marks_dict.get("Compilation_and_I/O", 0),
        "total_marks": marks_dict.get("Total", 0)
    }

    return {
        "question": question,
        "evaluation_criteria": evaluation_criteria,
        "code": code
    }
