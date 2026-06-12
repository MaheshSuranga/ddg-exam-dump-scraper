import asyncio
import os
import sys
import random
import urllib.parse
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
OUTPUT_DIR = "output"

async def main(exam_name):
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    async with async_playwright() as p:
        # Launch with a realistic user-agent and standard bot-evasion practices
        # headless=False can sometimes help avoid instant bot detection by Google, 
        # Using channel="chrome" uses your system's actual Google Chrome installation, 
        # which easily bypasses Cloudflare Turnstile and Google CAPTCHAs.
        browser = await p.chromium.launch(headless=False, channel="chrome", args=["--disable-blink-features=AutomationControlled"])
        
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.2; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        ]
        
        context = await browser.new_context(
            user_agent=random.choice(user_agents),
            viewport={"width": 1920, "height": 1080},
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            }
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        topic_num = 1
        missing_topics_count = 0
        
        while True:
            # Inner loop: question_num starting from 1
            question_num = 1
            missing_questions_count = 0
            
            found_any_question_in_topic = False
            
            while True:
                print(f"--- Processing Topic {topic_num}, Question {question_num} ---")
                
                # Check if file already exists to skip scraping
                topic_dir = os.path.join(OUTPUT_DIR, f"Topic_{topic_num}")
                expected_filename = f"{exam_name}_Topic_{topic_num}_Question_{question_num}.png"
                expected_filepath = os.path.join(topic_dir, expected_filename)
                
                if os.path.exists(expected_filepath):
                    print(f"File {expected_filename} already exists. Skipping search.")
                    missing_questions_count = 0
                    found_any_question_in_topic = True
                    question_num += 1
                    continue
                
                # Construct the exact query
                query = f"Exam {exam_name} topic {topic_num} question {question_num} discussion site:examtopics.com"
                search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                
                try:
                    # Navigate to search results (Using DuckDuckGo HTML to avoid Google CAPTCHA)
                    await page.goto(search_url, wait_until="domcontentloaded")
                    
                    question_found = False
                    
                    # Wait for search results to appear
                    try:
                        while True:
                            try:
                                await page.wait_for_selector(".result__a", timeout=5000)
                                break
                            except Exception:
                                content = await page.content()
                                if "Unfortunately, bots use DuckDuckGo too." in content or "Please complete the following challenge" in content:
                                    print("\n[ACTION REQUIRED] CAPTCHA detected! Please solve it in the open browser window.")
                                    print("Waiting for human interaction...")
                                    await asyncio.sleep(10)
                                else:
                                    raise Exception("No search results and no CAPTCHA detected.")
                        
                        # Get the href of the first organic search result
                        first_result_element = page.locator(".result__a").first
                        first_result_url = await first_result_element.get_attribute("href")
                        
                        if not first_result_url:
                            print("First result URL is empty.")
                        else:
                            # DuckDuckGo HTML uses redirect links (e.g. //duckduckgo.com/l/?uddg=...)
                            # We need to extract the clean ExamTopics URL from the 'uddg' parameter.
                            if first_result_url.startswith("//"):
                                first_result_url = "https:" + first_result_url
                                
                            if "uddg=" in first_result_url:
                                parsed_url = urllib.parse.urlparse(first_result_url)
                                query_params = urllib.parse.parse_qs(parsed_url.query)
                                if "uddg" in query_params:
                                    first_result_url = query_params["uddg"][0]

                            # ----------------------------------------------------------------
                            # GOOGLE INDEXING LOGIC & VALIDATION
                            # ----------------------------------------------------------------
                            expected_pattern = f"topic-{topic_num}-question-{question_num}"
                            
                            if expected_pattern not in first_result_url.lower():
                                print(f"First result URL: {first_result_url}")
                                print(f"Does NOT match expected pattern: '{expected_pattern}'")
                            else:
                                print(f"Valid match found: {first_result_url}. Navigating...")
                                
                                # Navigate to the target ExamTopics page
                                await page.goto(first_result_url, wait_until="networkidle", timeout=60000)
                                
                                # ----------------------------------------------------------------
                                # DOM MANIPULATION STEP
                                # ExamTopics uses an aggressive anti-scraping technique: they have a 
                                # setInterval loop running every 200ms that clones and recreates the 
                                # popup if it detects it was removed from the DOM.
                                # To defeat this, we inject a global CSS rule to forcefully hide it,
                                # rather than removing it. This bypasses the recreation script entirely.
                                # ----------------------------------------------------------------
                                await page.add_style_tag(content="""
                                    #notRemoverPopup, .popup-overlay, .popup-wrapper, .modal, .modal-backdrop, #exam-modal, .fc-ab-root {
                                        display: none !important;
                                        visibility: hidden !important;
                                        opacity: 0 !important;
                                        pointer-events: none !important;
                                        z-index: -9999 !important;
                                    }
                                    body, html {
                                        overflow: auto !important;
                                    }
                                """)
                                
                                await page.evaluate("""() => {
                                    document.body.classList.remove('modal-open');
                                    document.body.style.overflow = 'auto';
                                }""")
                                
                                print("Successfully removed overlays and fixed scrolling.")
                                
                                # Give it a brief moment to settle rendering
                                await asyncio.sleep(1)
                                
                                # Create topic-specific directory if it doesn't exist
                                topic_dir = os.path.join(OUTPUT_DIR, f"Topic_{topic_num}")
                                if not os.path.exists(topic_dir):
                                    os.makedirs(topic_dir)
                                
                                # Generate Screenshot
                                filename = f"{exam_name}_Topic_{topic_num}_Question_{question_num}.png"
                                filepath = os.path.join(topic_dir, filename)
                                
                                await page.screenshot(path=filepath, full_page=True)
                                print(f"Screenshot saved successfully: {filepath}")
                                
                                question_found = True

                    except Exception as inner_e:
                        print("Could not find search results or parse URL.")

                    if question_found:
                        missing_questions_count = 0
                        found_any_question_in_topic = True
                    else:
                        missing_questions_count += 1
                        print(f"Question not found. Missing count: {missing_questions_count}/5")
                        if missing_questions_count >= 5:
                            print(f"Topic {topic_num} exhausted (5 consecutive missing questions). Moving to next topic.")
                            break
                            
                except Exception as e:
                    # Resilience: catch timeouts, network issues, or DOM errors
                    print(f"An error occurred while processing Topic {topic_num} Question {question_num}: {e}")
                    missing_questions_count += 1
                    print(f"Missing count: {missing_questions_count}/5 due to error")
                    if missing_questions_count >= 5:
                        print(f"Topic {topic_num} exhausted due to consecutive errors. Moving to next topic.")
                        break

                # Increment for the next question in the current topic
                question_num += 1
                
                # Sleep to prevent rapid-fire requests (Human-Like Request Delays)
                delay = random.uniform(4.5, 8.5)
                await asyncio.sleep(delay)

            # Check if we should stop scraping entirely
            if not found_any_question_in_topic:
                missing_topics_count += 1
                print(f"No questions found in Topic {topic_num}. Missing topics count: {missing_topics_count}/10")
                if missing_topics_count >= 10:
                    print("10 consecutive topics had no questions. Assuming scraping is completed.")
                    break
            else:
                missing_topics_count = 0
                
            topic_num += 1

        await browser.close()
        print("Scraping completed.")

if __name__ == "__main__":
    exam_name = input("Enter your exam code (e.g., AZ-400): ").strip()
    if not exam_name:
        print("Exam code cannot be empty. Exiting.")
        sys.exit(1)
        
    asyncio.run(main(exam_name))
