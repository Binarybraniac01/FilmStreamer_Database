from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import quote
import os
import sys
import time
from supabase_db import init_database, insert_movie, get_movie_count, close_database

def get_brave_path():
    """
    Attempts to locate the Brave browser executable on Windows.
    Returns the path if found, otherwise None.
    """
    # Common paths for Brave on Windows
    paths = [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe")
    ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def main():
    print("Setting up Brave Browser Scraper...")
    
    brave_path = get_brave_path()
    if not brave_path:
        print("Error: Brave browser executable not found in common locations.")
        print("Please ensure Brave is installed, or modify the script to point to your installation.")
        sys.exit(1)

    print(f"Brave executable found at: {brave_path}")

    # Get year and month from user input BEFORE launching browser
    year = input("Enter the year (e.g., 2026): ").strip()
    month = input("Enter the month (01-12): ").strip()
    
    # Validate inputs
    if not year.isdigit() or len(year) != 4:
        print("Error: Please enter a valid 4-digit year.")
        sys.exit(1)
    
    if not month.isdigit() or not (1 <= int(month) <= 12):
        print("Error: Please enter a valid month (01-12).")
        sys.exit(1)
    
    # Ensure month is zero-padded (e.g., "1" becomes "01")
    month = month.zfill(2)
    
    # Construct URL dynamically
    url = f"https://links.modpro.blog/archives/date/{year}/{month}"

    # Configure ChromeOptions for Brave
    options = Options()
    options.binary_location = brave_path
    
    # Run in headless mode
    options.add_argument("--headless=new")  # New headless mode (more compatible)
    
    # Run in incognito mode
    options.add_argument("--incognito")
    
    # Ensure Brave Shields (ad blocker) is enabled
    # These settings keep Brave's built-in ad blocking active
    options.add_argument("--enable-features=BraveAdblockDefault")
    
    # Additional headless optimizations
    options.add_argument("--disable-gpu")  # Required for headless on Windows
    options.add_argument("--window-size=1920,1080")  # Set viewport size for headless
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Disable automation detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Disable infobars
    options.add_argument("--disable-infobars")
    
    print("Running in HEADLESS + INCOGNITO mode with Brave Shields enabled")
    
    try:
        # Initialize WebDriver
        # Brave is Chromium-based, so we use the Chrome driver.
        # webdriver_manager automatically downloads the correct driver.
        print("Installing/Updating ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        
        print(f"Launching Brave and navigating to {url}...")
        driver = webdriver.Chrome(service=service, options=options)
        
        # Navigate directly to the target URL
        driver.get(url)
        
        print("Successfully opened the search results page.")

        driver.refresh()
        time.sleep(3)
        
        # Wait for the main container to load
        print("Waiting for content to load...")
        wait = WebDriverWait(driver, 10)
        main_container_xpath = "/html/body/div[1]/div/div[2]/div/div/div/main/div"
        wait.until(EC.presence_of_element_located((By.XPATH, main_container_xpath)))
        
        # Step 1: Get the last page number from pagination
        # Try multiple xpaths in case the structure varies
        last_page_xpaths = [
            "/html/body/div[1]/div/div[2]/div/div/div/main/nav/div/a[2]",
            "/html/body/div[1]/div/div[2]/div/div/div/main/nav/div/a[4]"
        ]
        last_page_num = 1  # Default to 1 if not found
        
        for last_page_xpath in last_page_xpaths:
            try:
                # Wait for the pagination element to be present
                wait.until(EC.presence_of_element_located((By.XPATH, last_page_xpath)))
                last_page_element = driver.find_element(By.XPATH, last_page_xpath)
                last_page_text = last_page_element.text.strip()
                
                # Filter text to extract only the number (text format is "PAGE\n50")
                # Split by newline and get the numeric part
                for part in last_page_text.split('\n'):
                    if part.strip().isdigit():
                        last_page_num = int(part.strip())
                        break
                
                if last_page_num > 1:
                    print(f"\nTotal pages found: {last_page_num}")
                    break  # Found valid page number, exit loop
                    
            except Exception as e:
                print(f"Xpath {last_page_xpath} not found, trying next...")
                continue
        
        if last_page_num == 1:
            print("Could not find pagination, assuming single page")
        
        # Initialize database
        db_conn = init_database()
        
        # Function to scrape data from current page
        def scrape_current_page(page_num):
            print(f"\n{'='*80}")
            print(f"SCRAPING PAGE {page_num}")
            print(f"{'='*80}")
            
            # Find all child divs in the main container
            divs = driver.find_elements(By.XPATH, f"{main_container_xpath}/div")
            print(f"Found {len(divs)} items on this page.\n")
            
            for index, div in enumerate(divs, 1):
                try:
                    # Find the anchor tag within each div
                    anchor_xpath = ".//article/div/div/div[1]/header/h1/a"
                    anchor = div.find_element(By.XPATH, anchor_xpath)
                    
                    # Extract href and text
                    href = anchor.get_attribute("href")
                    text = anchor.text.strip()
                    
                    # Save to database
                    inserted = insert_movie(db_conn, text, href)
                    status = "[NEW]" if inserted else "[EXISTS]"
                    
                    print(f"{status} [{index}] Title: {text}")
                    print(f"    Link: {href}")
                    print("-" * 80)
                    
                except Exception as e:
                    print(f"[{index}] Could not extract data from this div: {e}")
                    print("-" * 80)
        
        # Scrape page 1 (current page)
        scrape_current_page(1)
        
        # Step 2: Loop through remaining pages (2 to last_page_num)
        for page_no in range(2, last_page_num + 1):
            page_url = f"{url}/page/{page_no}"
            print(f"\nNavigating to page {page_no}: {page_url}")
            driver.get(page_url)
            
            # Refresh and wait for content to load
            driver.refresh()
            time.sleep(3)
            wait.until(EC.presence_of_element_located((By.XPATH, main_container_xpath)))
            
            # Scrape this page
            scrape_current_page(page_no)
        
        print("\n" + "=" * 80)
        print("SCRAPING COMPLETED FOR ALL PAGES!")
        print("=" * 80)
        
        # Show database summary
        total_movies = get_movie_count(db_conn)
        print(f"\nTotal movies in database: {total_movies}")
        
        print("The browser will remain open. Press Enter in this terminal to close it.")
        input()
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close database connection
        if 'db_conn' in locals():
            close_database(db_conn)
        if 'driver' in locals():
            print("Closing browser...")
            driver.quit()

if __name__ == "__main__":
    main()
