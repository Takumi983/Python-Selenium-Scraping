from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import re

# =========================================================
# CONFIG（※ 公開用：ユーザーが自分で設定する）
# =========================================================
TARGET_URL = ""                 # 対象URLを設定
PREF_SELECT_IDS = []            # 例: ["select_id_1", "select_id_2"]
PREF_VALUES = []                # 例: ["", ""]
JOB_CHECKBOX_ID = ""            # 職種チェックボックスID
RESULT_TABLE_SELECTOR = ""      # 検索結果テーブルCSS
DETAIL_LINK_SELECTOR = ""       # 詳細リンクCSS
NEXT_BUTTON_NAME = ""           # 次へボタンname
MAX_PAGES = 3                   # 取得ページ上限

CSV_FILENAME = "job_scraping_result.csv"

# =========================================================
# WebDriver
# =========================================================
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)
driver.get(TARGET_URL)
time.sleep(1)

# =========================================================
# 1. 条件選択（例：勤務地）
# =========================================================
for select_id, value in zip(PREF_SELECT_IDS, PREF_VALUES):
    if not value:
        continue
    select_box = Select(wait.until(
        EC.presence_of_element_located((By.ID, select_id))
    ))
    select_box.select_by_value(value)

# =========================================================
# 2. 職種選択（任意）
# =========================================================
if JOB_CHECKBOX_ID:
    checkbox = wait.until(
        EC.presence_of_element_located((By.ID, JOB_CHECKBOX_ID))
    )
    driver.execute_script("arguments[0].click();", checkbox)

# =========================================================
# 3. 検索実行
# =========================================================
search_btn = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
)
search_btn.click()
time.sleep(1)

# =========================================================
# 4. 詳細ページリンク収集
# =========================================================
detail_links = []
page_count = 0

while page_count < MAX_PAGES:
    tables = driver.find_elements(By.CSS_SELECTOR, RESULT_TABLE_SELECTOR)

    for table in tables:
        try:
            link = table.find_element(By.CSS_SELECTOR, DETAIL_LINK_SELECTOR)
            href = link.get_attribute("href")
            if href:
                detail_links.append(href)
        except:
            continue

    try:
        next_btn = driver.find_element(By.NAME, NEXT_BUTTON_NAME)
        if next_btn.get_attribute("disabled"):
            break
        next_btn.click()
        time.sleep(1)
        page_count += 1
    except:
        break

print(f"Collected detail links: {len(detail_links)}")

# =========================================================
# 5. 詳細ページ情報取得
# =========================================================
def get_text(xpath: str) -> str:
    try:
        return driver.find_element(By.XPATH, xpath).text.strip()
    except:
        return ""

with open(CSV_FILENAME, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "job_id", "company_name", "location",
        "employment_type", "salary",
        "working_hours", "description", "notes"
    ])

    for href in detail_links:
        driver.get(href)
        time.sleep(1)

        job_id = get_text("//th[contains(text(),'ID')]/following-sibling::td")
        company = get_text("//th[contains(text(),'Company')]/following-sibling::td")
        location = get_text("//th[contains(text(),'Location')]/following-sibling::td")
        employment = get_text("//th[contains(text(),'Employment')]/following-sibling::td")
        salary = get_text("//th[contains(text(),'Salary')]/following-sibling::td")
        hours = get_text("//th[contains(text(),'Hours')]/following-sibling::td")
        description = get_text("//th[contains(text(),'Description')]/following-sibling::td")
        notes = get_text("//th[contains(text(),'Notes')]/following-sibling::td")

        writer.writerow([
            job_id, company, location,
            employment, salary, hours,
            description, notes
        ])

        driver.back()
        time.sleep(1)

print(f"CSV output completed: {CSV_FILENAME}")
driver.quit()
