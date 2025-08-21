# 🎓 Moodle Assignment Automation Tool

An advanced Python automation tool for efficiently downloading student submissions from Moodle quiz reports. This tool automatically handles login, CAPTCHA solving, navigation, and bulk downloading of student assignments with intelligent organization.

## ✨ Features

### 🔐 **Smart Authentication**
- **Automatic CAPTCHA Solving**: Uses OCR (pytesseract) to solve CAPTCHAs automatically
- **Retry Logic**: 3-attempt retry system with fallback to manual solving
- **Session Management**: Maintains login session across multiple operations

### 📊 **Intelligent Processing** 
- **Multi-URL Support**: Process multiple submission URLs in sequence
- **Dynamic Question Detection**: Automatically detects and maps question columns (Q.1, Q.2, etc.)
- **Selective Question Processing**: Choose specific questions or process all available
- **Smart Link Detection**: Handles both "Requires grading" and graded submissions

### 📁 **Advanced File Organization**
- **Student-Specific Folders**: Creates organized folders for each student
- **Question-Specific Files**: Files are tagged with question numbers
- **Dual Content Extraction**: Downloads both text answers and file attachments
- **UTF-8 Support**: Proper encoding for international characters

### 🚀 **Performance & Reliability**
- **Timeout Protection**: 5-second timeouts prevent hanging
- **Error Recovery**: Continues processing even if individual items fail
- **Progress Tracking**: Detailed logging and progress reporting
- **Browser Control**: Visible browser for debugging and monitoring

## 🛠️ Installation

### Prerequisites
- Python 3.7+
- Tesseract OCR engine
- Chrome/Chromium browser

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from: https://github.com/tesseract-ocr/tesseract

### 3. Install Playwright Browsers
```bash
playwright install chromium
```

## ⚙️ Configuration

Edit the configuration section in `main.py`:

### Basic Configuration
```python
# --- Configuration ---
USERNAME = "your_username"
PASSWORD = "your_password"
DOWNLOAD_DIRECTORY = "Moodle_Assignments_Playwright"
```

### Submission URLs
Add all the URLs you want to process:
```python
SUBMISSION_URLS = [
    "https://moodlecse.iitkgp.ac.in/moodle/mod/quiz/report.php?id=1470&mode=overview",
    "https://moodlecse.iitkgp.ac.in/moodle/mod/quiz/report.php?id=1470&mode=overview&page=1",
    # Add more URLs as needed
]
```

### Question Selection
```python
# Process all questions
QUESTIONS_TO_PROCESS = "all"

# Process specific questions only
QUESTIONS_TO_PROCESS = [1, 2]  # Only Q.1 and Q.2

# Process single question
QUESTIONS_TO_PROCESS = [1]  # Only Q.1
```

## 🚀 Usage

### Basic Usage
```bash
python main.py
```

### Expected Output
```
Attempting to solve CAPTCHA automatically...
CAPTCHA attempt 1/3...
OCR extracted CAPTCHA text: 'ABC123'
Login successful with OCR on attempt 1!

Processing 2 submission URLs...

--- Processing Submission URL 1/2 ---
URL: https://moodlecse.iitkgp.ac.in/moodle/mod/quiz/report.php?id=1470&mode=overview

=== QUESTION COLUMN MAPPING ===
  Mapped Q.1 to column 11
  Mapped Q.2 to column 12
Available questions: [1, 2]
Questions to process: [1, 2]
=== END QUESTION MAPPING ===

Found 30 student submissions at URL 1.

Processing student: 22CH30041
  Processing Question 1 (column 11)...
    Found link: 'Requires grading'
    -> Saved text answer to '22CH30041_Q1_answer.txt'
    -> Downloaded 'assignment_Q1.pdf' for Q.1
    
--- Automation Complete ---
Total students processed: 30
URLs processed: 2
```

## 📁 File Structure

The tool creates an organized directory structure:

```
Moodle_Assignments_Playwright/
├── 22CH30041/
│   ├── 22CH30041_Q1_answer.txt     # Text answer for Question 1
│   ├── assignment_Q1.pdf           # File attachment for Question 1
│   ├── 22CH30041_Q2_answer.txt     # Text answer for Question 2
│   └── homework_Q2.zip             # File attachment for Question 2
├── 23MT10017/
│   ├── 23MT10017_Q1_answer.txt
│   ├── code_Q1.cpp
│   └── 23MT10017_Q2_answer.txt
└── 24CH10056/
    ├── 24CH10056_Q1_answer.txt
    └── solution_Q1.py
```

## 🎯 Use Cases

### 1. **Multiple Quiz Pages**
Process different pages of the same quiz:
```python
SUBMISSION_URLS = [
    "https://moodlecse.iitkgp.ac.in/moodle/mod/quiz/report.php?id=1470&mode=overview&page=0",
    "https://moodlecse.iitkgp.ac.in/moodle/mod/quiz/report.php?id=1470&mode=overview&page=1",
    "https://moodlecse.iitkgp.ac.in/moodle/mod/quiz/report.php?id=1470&mode=overview&page=2",
]
```

### 2. **Different Quizzes**
Process multiple different quizzes:
```python
SUBMISSION_URLS = [
    "https://moodlecse.iitkgp.ac.in/moodle/mod/quiz/report.php?id=1470&mode=overview",  # Quiz 1
    "https://moodlecse.iitkgp.ac.in/moodle/mod/quiz/report.php?id=1509&mode=overview",  # Quiz 2
    "https://moodlecse.iitkgp.ac.in/moodle/mod/quiz/report.php?id=1520&mode=overview",  # Quiz 3
]
```

### 3. **Filtered Results**
Process with specific filters (graded only, specific attempts, etc.):
```python
SUBMISSION_URLS = [
    "https://moodlecse.iitkgp.ac.in/moodle/mod/quiz/report.php?id=1470&mode=overview&attempts=enrolled_with&onlygraded&onlyregraded",
]
```

### 4. **Selective Question Processing**
Process only specific questions for grading efficiency:
```python
# Only process Questions 1 and 3 (skip Q.2)
QUESTIONS_TO_PROCESS = [1, 3]
```

## 🔧 Advanced Features

### CAPTCHA Handling
- **Automatic OCR**: Uses Tesseract with optimized settings for CAPTCHA recognition
- **Character Whitelisting**: Restricts to alphanumeric characters for better accuracy
- **Retry Logic**: 3 attempts with page refresh between failures
- **Manual Fallback**: Falls back to manual solving if OCR fails

### Question Detection
- **Dynamic Mapping**: Automatically detects question columns using regex pattern `Q.\s*(\d+)`
- **Flexible Layout**: Adapts to different Moodle table structures
- **Column Indexing**: Maps question numbers to actual column positions

### File Handling
- **Smart Naming**: Automatically adds question numbers to filenames
- **Duplicate Prevention**: Handles multiple files for the same question
- **Extension Preservation**: Maintains original file extensions
- **UTF-8 Encoding**: Proper text file encoding for international content

## 🐛 Troubleshooting

### Common Issues

**CAPTCHA Recognition Fails:**
- Ensure Tesseract is properly installed
- Check image quality and contrast
- Use manual fallback when OCR fails consistently

**Login Issues:**
- Verify username and password are correct
- Check for account lockouts or security restrictions
- Ensure network connectivity to Moodle server

**Download Failures:**
- Check Moodle URL accessibility
- Verify question URLs are valid
- Ensure sufficient disk space

**Navigation Errors:**
- Update submission URLs if Moodle structure changes
- Check for pagination or filter changes
- Verify table structure hasn't changed

### Debug Mode
The browser runs in visible mode (`headless=False`) for easy debugging. You can:
- Watch the automation process in real-time
- Manually intervene if needed
- Debug CAPTCHA or navigation issues

## 📋 Requirements

```txt
playwright==1.40.0
pytesseract==0.3.10
Pillow==10.1.0
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## ⚠️ Disclaimer

This tool is for educational purposes and legitimate academic use only. Users are responsible for:
- Complying with their institution's terms of service
- Respecting rate limits and server resources
- Ensuring proper authorization for data access
- Following academic integrity guidelines

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Playwright** - For reliable browser automation
- **Tesseract OCR** - For CAPTCHA text recognition
- **PIL/Pillow** - For image processing capabilities

---

**Note**: Always test with a small subset of data first and ensure you have proper permissions before running bulk operations on institutional systems.
