# ExamTopics Scraper

A robust, asynchronous web scraper built with Python and Playwright designed to automatically fetch and archive certification exam discussion questions from ExamTopics.

## Overview
This project solves the problem of navigating heavily rate-limited and bot-protected websites by utilizing DuckDuckGo's HTML-only search engine as a gateway. It takes high-quality, full-page screenshots of exam questions while gracefully bypassing CAPTCHAs, popups, and aggressive anti-bot countermeasures.

## Features
* **Resume-Capable**: Automatically detects existing screenshots in the `output` directory. If a file exists, it skips the network request and continues, allowing you to stop and resume the script at any time without wasting time or bandwidth.
* **Smart Lookahead**: Tolerates gaps in question or topic numbering. It will scan ahead for missing questions (up to 5 misses) and missing topics (up to 10 misses) before assuming an exam is fully exhausted.
* **Interactive CLI**: Prompts the user to input the desired exam code (e.g., `AZ-400`, `AWS-Certified-Solutions-Architect-Associate`) at runtime.
* **DOM Manipulation**: Injects global CSS to forcefully disable ExamTopics' aggressive pop-ups and overlays, neutralizing their 200ms anti-scraping recreation loop.

## Anti-Bot Architecture
As a senior architectural decision, this scraper relies on a multi-layered evasion strategy:
1. **DuckDuckGo "HTML-Only" Gateway**: Relies on `https://html.duckduckgo.com/html/` to locate the exact URL of the question, successfully sidestepping the Google Search CAPTCHA walls entirely.
2. **Playwright Stealth**: Implements `playwright-stealth` to mask automated browser signatures (e.g., hiding `navigator.webdriver`).
3. **User-Agent Rotation**: Randomly selects from a curated list of the latest, most common browser User-Agents (Chrome, Firefox, Safari, Edge) for every new execution.
4. **Human-like Request Delays**: Uses `random.uniform(4.5, 8.5)` to introduce natural, unpredictable delays between page loads.
5. **Interactive CAPTCHA Halts**: If DuckDuckGo *does* throw a CAPTCHA, the script does not crash or skip the question. It pauses execution, alerts the user in the terminal, and waits in a background loop until a human solves the visual puzzle in the spawned browser window.

## Prerequisites
* Python 3.8+
* [Playwright for Python](https://playwright.dev/python/)

## Installation
1. Clone this repository or download the script.
2. Install the required Python packages:
   ```bash
   pip install playwright playwright-stealth
   ```
3. Install the Playwright chromium browser binary:
   ```bash
   playwright install chromium
   ```

## Usage

### Command Line Interface (CLI)
Run the script using Python:
```bash
python scrape_exam.py
```
You will be prompted to enter the exam code:
```
Enter your exam code (e.g., AZ-400): AZ-400
```
The script will launch a visible Chromium browser (helpful for solving any unexpected CAPTCHAs) and begin scraping.

### Graphical User Interface (GUI)
You can also run the application using the included GUI:
```bash
python gui_app.py
```
The GUI provides a pleasant interface to select your exam code (e.g., AZ-900, AZ-204, AZ-400), choose a custom output directory, and start or stop the scraping process. Real-time logs are displayed directly in the application window.

### Standalone Executable (.exe)
For users who do not wish to use the command line or have Python installed, a standalone executable (`ExamTopics_Scraper.exe`) is available in the `dist/` directory.

Simply double-click **`ExamTopics_Scraper.exe`** to launch the GUI. 
* **Zero Dependency Setup**: Python or library installations are **not required**.
* **Smart Browser Fallback**: The scraper automatically detects your installed browsers at runtime:
  1. It attempts to launch **Google Chrome** first (which offers the best evasion against CAPTCHAs).
  2. If Chrome is not found, it automatically falls back to **Microsoft Edge** (pre-installed on all Windows 10 & 11 PCs).
  3. If Edge is also missing, it will attempt to launch default **Playwright Chromium**.
  This design ensures the application runs out-of-the-box on virtually any Windows computer.

## Building the Executable
To package the application into a standalone `.exe` yourself, make sure PyInstaller is installed and build it using the provided `.spec` configuration file (which handles the collection of Playwright driver binaries and Stealth package assets automatically):

```bash
pip install pyinstaller
python -m PyInstaller ExamTopics_Scraper.spec --clean --noconfirm
```
The newly compiled executable will be located in the `dist/` folder.
## Output Structure
The scraper automatically organizes screenshots by Topic inside the `output` directory:
```
output/
├── Topic_1/
│   ├── AZ-400_Topic_1_Question_1.png
│   ├── AZ-400_Topic_1_Question_2.png
│   └── ...
├── Topic_2/
│   ├── AZ-400_Topic_2_Question_1.png
│   └── ...
```
Directories are only created if a valid question is found and successfully screenshotted.
