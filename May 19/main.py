import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
import os

# Configuration - Replace with your actual Gemini API key
GEMINI_API_KEY = "AIzaSyAKbj_m5q8HQh8PHoEKxfGokT60oQ6BS6o"

# Path to chromedriver executable (make sure this points to the actual .exe file)
CHROMEDRIVER_PATH = r"C:\Users\santh\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"

def setup_driver():
    """Initialize and return a configured Chrome WebDriver instance."""
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    service = Service(CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)

def fetch_web_content(url):
    """Use Selenium to fetch and return visible text from the webpage (max 10,000 characters)."""
    driver = setup_driver()
    try:
        print(f"🌐 Visiting: {url}")
        driver.get(url)

        # Wait until the body tag is loaded, then extract the text
        content = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        ).text

        return content[:10000]
    except Exception as e:
        print(f"❌ Error fetching content: {str(e)}")
        return None
    finally:
        driver.quit()

def summarize_with_gemini(text):
    """Use Gemini API to summarize the given text into 3-5 bullet points."""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('models/gemini-1.5-pro')
        response = model.generate_content(f"Summarize this in 3-5 bullet points: {text}")
        return response.text
    except Exception as e:
        print(f"❌ Gemini error: {str(e)}")
        return None

def summarize_text(text):
    """Validate and summarize the provided text using Gemini."""
    if not text:
        return "No content to summarize"

    print("✍️ Summarizing content...")
    summary = summarize_with_gemini(text)
    return summary if summary else "Error: Could not generate summary"

def research_topic(topic):
    """Perform research by fetching content from Wikipedia and summarizing it using Gemini."""
    print(f"\n🔍 Researching: {topic}")

    url = f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
    content = fetch_web_content(url)

    if not content:
        return "❌ Failed to fetch content"

    summary = summarize_text(content)

    result = f"""
✅ Research Summary for '{topic}':

{summary}

Source: {url}
"""
    return result

# Main program
if __name__ == "__main__":
    print("🌍 Web Research Assistant")
    print("-----------------------")

    while True:
        topic = input("\nEnter a topic to research (or 'quit' to exit): ").strip()

        if topic.lower() == 'quit':
            print("Goodbye!")
            break

        if not topic:
            print("Please enter a topic")
            continue

        result = research_topic(topic)
        print(result)
