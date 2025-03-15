import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import gspread
from google.oauth2.service_account import Credentials

# GOOGLE SHEETS SETUP
SERVICE_ACCOUNT_FILE = "google_sheets_credentials.json"  # Update this with your credentials file
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(credentials)

# Replace with your actual Google Sheet ID
SHEET_ID = "1yBlp-RZHAAx3clfkCu-LQWEaHKmCtqrO6DzOVv_pKDE"
sheet = client.open_by_key(SHEET_ID).sheet1  # Open the first sheet


def fetch_maxpreps_stats(player_url):
    """Fetch player statistics from MaxPreps (Game Stats + Shooting Stats)."""
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)

    stats = {}

    try:
        driver.get(player_url)
        time.sleep(5)  # Allow time for the page to load

        # **Extract Player Name**
        try:
            player_name = driver.find_element(By.XPATH, '//a[@class="sc-e36b58d4-0 eJUgpV athlete-name"]').text.strip()
        except:
            player_name = "Unknown"

        stats["Player Name"] = player_name

        # **Extract Game Stats**
        rows = driver.find_elements(By.XPATH, '//tbody/tr')
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if len(cells) > 8:  # Ensure correct row
                stats.update({
                    'GP': cells[3].text.strip(),
                    'PPG': cells[5].text.strip(),
                    'RPG': cells[8].text.strip(),
                    'APG': cells[9].text.strip(),
                    'SPG': cells[10].text.strip(),
                    'BPG': cells[11].text.strip(),
                })
                break  # Extract first row only

        # **Click on the "Shooting" tab**
        shooting_tab = driver.find_element(By.XPATH, '//button[@title="Shooting"]')
        shooting_tab.click()
        time.sleep(3)

        # **Extract Shooting (1) Stats**
        shooting_rows_1 = driver.find_elements(By.XPATH, '//h2[text()="Shooting (1)"]/following-sibling::div//tbody/tr')
        for row in shooting_rows_1:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if len(cells) > 8:
                stats.update({
                    'PTS': cells[5].text.strip(),
                    'FG%': cells[8].text.strip(),
                })
                break

        # **Extract Shooting (2) Stats for 3P%**
        shooting_rows_2 = driver.find_elements(By.XPATH, '//h2[text()="Shooting (2)"]/following-sibling::div//tbody/tr')
        for row in shooting_rows_2:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if len(cells) > 8:
                stats.update({
                    '3P%': cells[8].text.strip(),
                })
                break

        return stats if stats else None

    except Exception as e:
        print(f"Error: {e}")
        return None

    finally:
        driver.quit()


def save_to_google_sheets(data):
    """Save extracted stats to Google Sheets."""
    if not data:
        print("No data to save!")
        return

    headers = ["Player Name", "GP", "PPG", "RPG", "APG", "SPG", "BPG", "PTS", "FG%", "3P%"]

    # Check if headers exist, if not, insert them
    existing_headers = sheet.row_values(1)
    if not existing_headers:
        sheet.insert_row(headers, 1)

    # Insert the player stats as a new row
    new_row = [data.get(col, "N/A") for col in headers]
    sheet.append_row(new_row)
    print("✅ Data saved to Google Sheets!")


# **MAIN EXECUTION**
if __name__ == "__main__":
    player_url = input("Enter MaxPreps Player Stats URL: ").strip()
    if player_url:
        print("⏳ Fetching stats...")
        player_stats = fetch_maxpreps_stats(player_url)
        if player_stats:
            print("✅ Stats Retrieved:", player_stats)
            save_to_google_sheets(player_stats)
        else:
            print("⚠️ Could not fetch player stats.")
    else:
        print("❌ No URL entered. Exiting script.")
