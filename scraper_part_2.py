from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
import sys
import time

def get_brave_path():
    """
    Attempts to locate the Brave browser executable on Windows.
    Returns the path if found, otherwise None.
    """
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
    print("Setting up Brave Browser Scraper - Part 2...")
    
    brave_path = get_brave_path()
    if not brave_path:
        print("Error: Brave browser executable not found.")
        sys.exit(1)

    print(f"Brave executable found at: {brave_path}")

    # Target URL (can be passed as parameter or from database later)
    target_url = "https://links.modpro.blog/archives/147034"

    # Configure ChromeOptions for Brave
    options = Options()
    options.binary_location = brave_path
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    
    try:
        print("Installing/Updating ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        
        print(f"Launching Brave and navigating to {target_url}...")
        driver = webdriver.Chrome(service=service, options=options)
        
        # Navigate to target URL
        driver.get(target_url)
        
        print("Successfully opened the page.")
        driver.refresh()
        time.sleep(3)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        
        # Find the download link anchor tag
        download_link_xpath = "/html/body/div[1]/div/div/div/div/div/main/div/div/article/div/div[2]/div[2]/p[3]/a"
        
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, download_link_xpath)))
            anchor = driver.find_element(By.XPATH, download_link_xpath)
            
            # Get the href from the anchor tag
            href = anchor.get_attribute("href")
            print(f"\nFound download link: {href}")
            
            # Open the href link
            print(f"Opening the link...")
            driver.get(href)
            time.sleep(3)
            
            print("Successfully navigated to the download link!")
            
            # Step 1: Click on the first element
            print("\nStep 1: Clicking on form link...")
            step1_xpath = "/html/body/section/main/div/form/span/a"
            wait.until(EC.element_to_be_clickable((By.XPATH, step1_xpath)))
            driver.find_element(By.XPATH, step1_xpath).click()
            time.sleep(2)
            
            # Step 2: Click on span[2]
            print("Step 2: Clicking on span[2]...")
            step2_xpath = "/html/body/section/article/span[2]"
            wait.until(EC.element_to_be_clickable((By.XPATH, step2_xpath)))
            driver.find_element(By.XPATH, step2_xpath).click()
            time.sleep(2)
            
            # Step 3: Click on span[1]
            print("Step 3: Clicking on span[1]...")
            step3_xpath = "/html/body/section/article/span[1]"
            wait.until(EC.element_to_be_clickable((By.XPATH, step3_xpath)))
            driver.find_element(By.XPATH, step3_xpath).click()
            time.sleep(2)
            
            # Step 4: Get href from final anchor and open it
            print("Step 4: Getting final download link...")
            step4_xpath = "/html/body/section/article/center[2]/a"
            wait.until(EC.presence_of_element_located((By.XPATH, step4_xpath)))
            final_anchor = driver.find_element(By.XPATH, step4_xpath)
            final_href = final_anchor.get_attribute("href")
            print(f"Final download link: {final_href}")
            
            # Open the final link
            print("Opening final download link...")
            driver.get(final_href)
            
            print("\nSuccessfully reached the final download page!")
            
        except Exception as e:
            print(f"An error occurred during navigation: {e}")
        
        print("\nThe browser will remain open. Press Enter to close it.")
        input()
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'driver' in locals():
            print("Closing browser...")
            driver.quit()

if __name__ == "__main__":
    main()
