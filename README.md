# 🎓 Moodle Submission Downloader

An advanced Python automation tool for efficiently downloading student assignments from Moodle. This tool is specifically tailored for `mod/assign` (Assignment) and `mod/quiz` (Quiz) submissions, handling login, navigation, and bulk downloading with intelligent organization.

## ✨ Features

### 🔐 **Smart Authentication**

  - **Automatic CAPTCHA Solving**: Uses OCR (pytesseract) to automatically solve CAPTCHAs during login.
  - **Retry Logic**: 3-attempt retry system with fallback to manual solving.
  - **Session Management**: Maintains the login session across multiple operations.

### 📊 **Intelligent Processing**

  - **Multi-URL Support**: Processes multiple submission URLs in a sequence, allowing for bulk downloads from different quizzes or pages.
  - **Dynamic File Detection**: Specifically targets and downloads `.c` files for code assignments.
  - **Error Recovery**: Continues processing even if individual items fail.

### 📁 **Advanced File Organization**

  - **Student-Specific Folders**: Creates organized folders for each student using their roll number.
  - **File Naming**: Downloaded files are saved with the student's roll number and original filename to prevent duplicates.
  - **UTF-8 Support**: Ensures proper encoding.

### 🚀 **Performance & Reliability**

  - **Progress Tracking**: Detailed logging to both the console and a `submissions.log` file.
  - **Browser Control**: Visible browser for debugging and monitoring (`headless=False`).
  - **Timeout Protection**: Timeouts prevent the script from hanging on unresponsive elements.

-----

## 🛠️ Installation

### Prerequisites

  - Python 3.7+
  - Tesseract OCR engine
  - Chrome/Chromium browser

### 1\. Install Python Dependencies

```bash
pip install -r requirements.txt
```

The required packages are:

  - `playwright==1.40.0`
  - `pytesseract==0.3.10`
  - `Pillow==10.1.0`

### 2\. Install Tesseract OCR

**macOS:**

```bash
brew install tesseract
```

**Ubuntu/Debian:**

```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from: [https://github.com/tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract)

### 3\. Install Playwright Browsers

```bash
playwright install chromium
```

-----

## ⚙️ Configuration

Edit the configuration section in `main.py`:

### Basic Configuration

```python
# --- Configuration ---
MODULENAME = "your_username"
PASSWORD = "your_password"
DOWNLOAD_DIRECTORY = "Assignments"  # This will be your download folder
```

### Submission URLs

Add all the URLs you want to process. The script is configured to work with Moodle's `mod/assign` (`.../view.php?id=...&action=grading`) pages.

```python
SUBMISSION_URLS = [
    "https://moodle.example.edu/mod/assign/view.php?id=123&action=grading",
    "https://moodle.example.edu/mod/assign/view.php?id=456&action=grading",
    # Add more URLs as needed
]
```

-----

## 🚀 Usage

### Basic Usage

```bash
python main.py
```

### Expected Output

The script logs its progress to both the console and a `submissions.log` file.

```
[2025-08-21 12:53:20] INFO: Attempting to solve CAPTCHA automatically...
[2025-08-21 12:53:20] INFO: CAPTCHA attempt 1/3...
[2025-08-21 12:53:20] INFO: OCR extracted CAPTCHA text: 'ABC123'
[2025-08-21 12:53:22] INFO: Login successful with OCR on attempt 1!

[2025-08-21 12:53:22] INFO: Processing 2 submission URLs...

--- Processing Submission URL 1/2 ---
URL: https://moodle.example.edu/mod/assign/view.php?id=123&action=grading
[2025-08-21 12:53:23] INFO: Successfully navigated to submission URL 1
[2025-08-21 12:53:23] INFO: Processing page 1...
[2025-08-21 12:53:23] INFO: Processing student: 2024CS001
[2025-08-21 12:53:23] INFO: Downloaded: 2024CS001_assignment_1.c
[2025-08-21 12:53:24] INFO: Processing student: 2024CS002
[2025-08-21 12:53:24] INFO: Downloaded: 2024CS002_code_1.c

--- Automation Complete ---
URLs processed: 2
```

-----

## 📁 File Structure

The tool creates an organized directory structure. For each student, a folder is created containing their submissions. The current version is configured to download only `.c` files.

```
Assignments/
├── 2024CS001/
│   └── 2024CS001_assignment_1.c  # Example .c file
├── 2024CS002/
│   └── 2024CS002_code_1.c
└── 2024CS003/
    └── 2024CS003_solution_1.c
```

-----

## 🎯 Use Cases

### 1\. **Batch Downloading Multiple Assignments**

Process multiple different assignment pages by listing them in `SUBMISSION_URLS`.

```python
SUBMISSION_URLS = [
    "https://moodle.example.edu/mod/assign/view.php?id=123&action=grading",  # Assignment 1
    "https://moodle.example.edu/mod/assign/view.php?id=456&action=grading",  # Assignment 2
]
```

### 2\. **Downloading from Paginated Pages**

The script now automatically handles pagination by clicking the "next page" button (`»`) until all pages are processed. You only need to provide the first URL.

### 3\. **Downloading Specific File Types**

The `process_page` function is hardcoded to only download files ending with `.c`. This can be easily modified to download other file types.

-----

## 🐛 Troubleshooting

### Common Issues

**CAPTCHA Recognition Fails:**

  - Ensure Tesseract is properly installed and its executable is in your system's PATH.
  - The script has a retry logic, but if all attempts fail, you'll need to solve it manually in the browser.

**Login Issues:**

  - Verify your `USERNAME` and `PASSWORD` in the `main.py` file are correct.
  - Check for account lockouts or security restrictions on your Moodle account.

**Download Failures:**

  - Ensure you have sufficient disk space in the `DOWNLOAD_DIRECTORY`.
  - Verify the Moodle URLs in `SUBMISSION_URLS` are correct and accessible.

### Debug Mode

The browser runs in visible mode (`headless=False`) for easy debugging. You can:

  - Watch the automation process in real-time.
  - Manually intervene if needed during a login or navigation error.
  - Debug CAPTCHA or navigation issues visually.

-----

## 🤝 Contributing

1.  Fork the repository
2.  Create a feature branch (`git checkout -b feature/amazing-feature`)
3.  Commit your changes (`git commit -m 'Add amazing feature'`)
4.  Push to the branch (`git push origin feature/amazing-feature`)
5.  Open a Pull Request

## ⚠️ Disclaimer

This tool is for educational purposes and legitimate academic use only. Users are responsible for:

  - Complying with their institution's terms of service.
  - Respecting rate limits and server resources.
  - Ensuring proper authorization for data access.
  - Following academic integrity guidelines.

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## 🙏 Acknowledgments

  - **Playwright** - For reliable browser automation.
  - **Tesseract OCR** - For CAPTCHA text recognition.
  - **PIL/Pillow** - For image processing capabilities.