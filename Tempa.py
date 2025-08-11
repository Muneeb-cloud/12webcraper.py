from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time

# --- Config ---
MAX_PAGES = 10  # Set page limit
all_data = []

# --- Set up Selenium ---
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# --- Open website ---
url = ""
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
page = 1
while page <= MAX_PAGES:
    time.sleep(2)
    print(f"🔄 Scraping Page {page}...")

    soup = BeautifulSoup(driver.page_source, "html.parser")
    results = driver.find_elements(By.CSS_SELECTOR, "div.ResultItem")

    if not results:
        print("❌ No results found.")
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
        print(all_data)
    # --- Try to go to next page ---
    try:
        next_btn = driver.find_element(By.XPATH, "//a[contains(@href, 'fn_pagination2(true)')]")
        driver.execute_script("arguments[0].click();", next_btn)
        print("➡️ Going to next page...")
        page += 1
        time.sleep(5)
    except Exception as e:
        print("✅ No more pages or pagination failed.")
        break

# --- Save to Excel ---
df = pd.DataFrame(all_data)
df.to_excel("testing1.xlsx", index=False)
print("✅ Data saved to 'florida_realtors_data.xlsx'.")

driver.quit()