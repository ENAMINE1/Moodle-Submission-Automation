import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

def analyze_code(question_file, evlaution_file, code_file, save_path):

    code = generate_prompt(question_file, evlaution_file, code_file)
    api_key=os.getenv("GEMINI_API_KEY")
    model_id = "gemini-2.0-flash"  # or gemini-2.5-pro, depending on your setup

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
                        "4) In Comments: only show <wrong_code_snippet> → <what is wrong> → <what should have been done>\n\n"
                        "5) Do not explain anything else, do not add extra lines. "
                        "6) Marks must follow this structure in Marking Criteria\n"
                        "7) Dont forget to give marks for each criteria\n"
                        "8) Add another line for Total Marks where you dont write any other text than the total marks\n\n"
                        f"Question: {code["question"]}\n\n"
                        f"Evaluation Criteria: {code["evaluation_criteria"]["criteria"]}\n\n"
                        "Code:\n"
                        f"{code["code"]}\n\n"
                        "Marking Criteria:\n"
                        f"Logical Sanity: {code["evaluation_criteria"]["logical_marks"]}\n"
                        f"Correct Indentation: {code["evaluation_criteria"]["indentation_marks"]}\n"
                        f"Comments in the code: {code["evaluation_criteria"]["comments_marks"]}\n"
                        f"Output correctness: {code["evaluation_criteria"]["output_marks"]}"
                        f"Total Marks: {code["evaluation_criteria"]["total_marks"]}\n"
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
