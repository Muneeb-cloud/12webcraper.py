from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import logging

# --- Setup logging ---
logging.basicConfig(filename="scrape_log-Miami.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

# --- Config ---
START_PAGE = 1   # Change this to resume from a specific page
MAX_PAGES = 1000  # Total pages to scrape
FILENAME = "finalfile-Miami.xlsx"
all_data = []

# --- Save progress function ---
def save_to_excel(data):
    df = pd.DataFrame(data)
    if os.path.exists(FILENAME):
        existing = pd.read_excel(FILENAME)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_excel(FILENAME, index=False)
    logging.info(f"✅ Saved {len(data)} records to {FILENAME}")

# --- Set up Selenium ---
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# --- Open website ---
url = "https://www.floridarealtors.org/consumers-realtor-search"
driver.get(url)

# --- Manual form fill ---
input("👉 Fill the form and press Search. When results load, press ENTER to continue...")

# --- Switch to results iframe ---
try:
    iframe = driver.find_element(By.TAG_NAME, "iframe")
    driver.switch_to.frame(iframe)
    print("✅ Switched to iframe.")
except Exception as e:
    print("❌ Iframe not found:", e)
    driver.quit()
    exit()

# --- Pagination loop ---
page = START_PAGE
while page <= MAX_PAGES:
    try:
        print(f"🔄 Scraping Page {page}...")
        logging.info(f"Scraping page {page}")
        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        results = driver.find_elements(By.CSS_SELECTOR, "div.ResultItem")

        if not results:
            print("❌ No results found.")
            logging.warning(f"No results found on page {page}")
            break

        for item in results:
            try:
                name = item.find_element(By.CSS_SELECTOR, "div.ResultInfo div.ContactInfo h2 a").text.strip()
            except:
                name = None
            try:
                company = item.find_element(By.CSS_SELECTOR, "div.ResultInfo div.ContactInfo strong a").text.strip()
            except:
                company = None
            phone = None
            address = None
            try:
                p_elem = item.find_element(By.CSS_SELECTOR, "div.ResultInfo div.ContactInfo p")
                texts = p_elem.get_attribute("innerHTML").split("<br>")
                if len(texts) >= 2:
                    phone = texts[0].strip().strip('"')
                    address_html = texts[1].strip()
                    address = BeautifulSoup(address_html, "html.parser").get_text(separator=" ").strip()
                else:
                    full_text = p_elem.text.split("\n")
                    if len(full_text) >= 2:
                        phone = full_text[0].strip().strip('"')
                        address = full_text[1].strip()
                    else:
                        phone = p_elem.text.strip().strip('"')
            except:
                pass

            all_data.append({
                "Name": name,
                "Company": company,
                "Phone": phone,
                "Address": address
            })

        # Save after each page
        save_to_excel(all_data)
        all_data.clear()  # Clear buffer to prevent duplicates

        time.sleep(4)  # ⏱️ Wait 3 seconds before navigating to the next page

        # Try to go to next page
        try:
            next_btn = driver.find_element(By.XPATH, "//a[contains(@href, 'fn_pagination2(true)')]")
            driver.execute_script("arguments[0].click();", next_btn)
            print("➡️ Going to next page...")
            page += 1
            time.sleep(3)
        except Exception as e:
            print("✅ No more pages or pagination failed.")
            logging.info("No more pages or pagination failed.")
            break
    except Exception as e:
        print(f"❌ Error on page {page}:", e)
        logging.error(f"Error on page {page}: {e}")
        break

driver.quit()
print("✅ Scraping completed.")
logging.info("Scraping completed and driver closed.")
