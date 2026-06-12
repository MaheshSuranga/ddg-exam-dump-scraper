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
Run the script using Python:
```bash
python scrape_exam.py
```
You will be prompted to enter the exam code:
```
Enter your exam code (e.g., AZ-400): AZ-400
```
The script will launch a visible Chromium browser (helpful for solving any unexpected CAPTCHAs) and begin scraping.

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
