from httpcore import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import json
import logging
import csv
import time

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Chrome driver setup
driver_path = r"C:\Windows\chromedriver.exe"
service = Service(driver_path)
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--ignore-certificate-errors")  # Ignore SSL errors
driver = webdriver.Chrome(service=service, options=chrome_options)

def amazon_login(email, password):
    """Login to Amazon account."""
    time.sleep(20)
    logging.info("Attempting to login to Amazon...")
    driver.get("https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F%3Fref_%3Dnav_ya_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0")
    try:
        # Email field
        email_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "ap_email"))
        )
        email_field.send_keys(email)
        logging.info("Entered email.")
        driver.find_element(By.ID, "continue").click()

        # Password field
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ap_password"))
        )
        password_field.send_keys(password)
        logging.info("Entered password.")
        driver.find_element(By.ID, "signInSubmit").click()

       
            
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "nav-link-accountList"))
        )
        logging.info("Login successful.")
        driver.get("https://www.amazon.in/gp/bestsellers/shoes/ref=zg_bs_nav_shoes_0")  # Navigate to Best Seller page
        return True
    except Exception as e:
        logging.error(f"Error during login: {e}")
        return False

def go_to_category(category_url):
    """Navigate to the specified category."""
    logging.info(f"Navigating to category: {category_url}")
    driver.get(category_url)
    try:
        # Wait for category page to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#zg-right-col"))
        )
        logging.info("Category page loaded.")

        # Capture screenshot and save page source for debugging
        # driver.save_screenshot("bestsellers_page.png")
        # with open("page_source.html", "w", encoding="utf-8") as f:
        #     f.write(driver.page_source)

        # Scroll to the bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)

    except Exception as e:
        logging.error(f"Error loading category page: {e}")
        driver.save_screenshot("error_screenshot.png")  # Capture a screenshot for debugging
        raise



def extract_product_links():
    """Extract product links from the category page."""
    logging.info("Extracting product links...")
    product_links = []
    try:
        # Locate product items and extract their links
        products_elements= driver.find_elements(By.CSS_SELECTOR, "a.a-link-normal.aok-block ")
        product_links = [product.get_attribute("href") for product in products_elements if product.get_attribute("href")]
        logging.info(f"Found {len(product_links)} product links.")
        return product_links
    except Exception as e:
        logging.error(f"Error extracting product links: {e}")
        return []
    



def extract_product_details_from_page(product_url):
    """Extract detailed product information from the product page."""
    logging.info(f"Extracting details for product: {product_url}")
    driver.get(product_url)
    time.sleep(3)  # Allow the page to load
    product_details = {}
    try:
        # Extract product details
        product_details['Product URL'] = product_url

        # Product Name
        try:
            product_name = driver.find_element(By.CSS_SELECTOR, "#title_feature_div").text
            product_details['Product Name'] = product_name
        except Exception:
            product_details['Product Name'] = "N/A"

        try:
            rating = driver.find_element(By.CSS_SELECTOR, "span.a-size-base.a-color-base").text.strip()
            product_details['Rating'] = rating
        except Exception:
            product_details['Rating'] = "N/A"

        # Price
        try:
            product_price = driver.find_element(By.CSS_SELECTOR, ".a-price-whole").text.strip()
            product_details['Price'] = "₹"+ product_price
        except Exception:
            product_details['Price'] = "N/A"

        # Sale Discount
        try:
            sale_discount = driver.find_element(By.CSS_SELECTOR, ".savingsPercentage").text.strip()
            product_details['Sale Discount'] = sale_discount
        except Exception:
            product_details['Sale Discount'] = "N/A"

        # Ship From
        try:
            ship_from = driver.find_element(By.CSS_SELECTOR, "div[tabular-attribute-name='Ships from'] .tabular-buybox-text-message").text.strip()
            product_details['Ship From'] = ship_from
        except Exception:
            product_details['Ship From'] = "N/A"

        # Sold By
        try:
            sold_by = driver.find_element(By.ID, "sellerProfileTriggerId").text.strip()
            product_details['Sold By'] = sold_by
        except Exception:
            product_details['Sold By'] = "N/A"

        # Product Description
        try:
            descriptions=[]
            product_desc = driver.find_elements(By.CSS_SELECTOR, "ul.a-unordered-list.a-vertical.a-spacing-small li span.a-list-item.a-size-base.a-color-base")
            for desc in product_desc:
                descriptions.append(desc.text.strip())
            product_details['Product Description'] = descriptions
        except Exception:
            product_details['Product Description'] = "N/A"

        # Number Bought in Past Month
        try:
            bought_count = driver.find_element(By.CSS_SELECTOR, "span.a-size-small.social-proofing-faceout-title-text").text
            product_details['Bought Count'] = bought_count
        except Exception:
            product_details['Bought Count'] = "N/A"

        # Images
        try:
            images = [img.get_attribute("src") for img in driver.find_elements(By.CSS_SELECTOR, "img.a-dynamic-image")]
            product_details['Images'] = images
        except Exception:
            product_details['Images'] = []

        logging.info(f"Details extracted: {product_details}")
    except Exception as e:
        logging.error(f"Error extracting product details from page: {e}")
    return product_details



def process_all_categories(category_urls):
    """Process all categories and extract product details."""
    all_products = []
    for idx, category_url in enumerate(category_urls, start=1):
        logging.info(f"Processing category {idx}/{len(category_urls)}: {category_url}")
        try:
            go_to_category(category_url)
            product_links=extract_product_links()
            if not product_links:
                logging.warning(f"No product links found for category:{category_url}")
                continue
            for product_link in product_links:
                product_details=extract_product_details_from_page(product_link)
                product_details['Category']=category_url.split("/")[-2]

                discount_text = product_details.get('Sale Discount', 'N/A')
                if discount_text != "N/A":
                    try:
                        discount_percentage = int(discount_text.replace('-','').replace('%','').strip())  # Extract discount as an integer
                        if discount_percentage > 50:
                            all_products.append(product_details)
                    except ValueError:
                        logging.warning(f"Invalid discount format: {discount_text}")
            logging.info(f"Completed processing category {idx}.Found {len(product_links)} products.")
        except Exception as e:
            logging.error(f"Failed to process category {category_url}: {e}")
    return all_products



def save_to_csv(products):
    """Save products to a CSV file."""
    logging.info("Saving products to CSV file...")
    try:
        keys = products[0].keys() if products else ['Product Name', 'Price', 'Rating','Category']
        with open('amazon_products.csv', 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=keys)
            writer.writeheader()
            writer.writerows(products)
        logging.info("Data saved to amazon_products.csv.")
    except Exception as e:
        logging.error(f"Error saving to CSV: {e}")


def save_to_json(products):
    """Save products to a JSON file."""
    logging.info("Saving products to JSON file...")
    try:
        with open('amazon_products.json', 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=4)
        logging.info("Data saved to amazon_products.json.")
    except Exception as e:
        logging.error(f"Error saving to JSON: {e}")


# Main flow
try:
    if amazon_login("singh.sandhya1979s@gmail.com", "sandhya123"):
        category_urls = [
            "https://www.amazon.in/gp/bestsellers/shoes/ref=zg_bs_nav_shoes_0",
            "https://www.amazon.in/gp/bestsellers/electronics/ref=zg_bs_nav_electronics_0",
            "https://www.amazon.in/gp/bestsellers/computers/ref=zg_bs_nav_computers_0",
            "https://www.amazon.in/gp/bestsellers/kitchen/ref=zg_bs_nav_kitchen_0", #working
            "https://www.amazon.in/gp/bestsellers/apparel/ref=zg_bs_apparel_sm", #working
            "https://www.amazon.in/gp/bestsellers/luggage/ref=zg_bs_luggage_sm",
            "https://www.amazon.in/gp/bestsellers/boost/ref=zg_bs_boost_sm",
            "https://www.amazon.in/gp/bestsellers/home-improvement/ref=zg_bs_home-improvement_sm",
            "https://www.amazon.in/gp/bestsellers/beauty/ref=zg_bs_nav_beauty_0",
            "https://www.amazon.in/gp/bestsellers/automotive/ref=zg_bs_nav_automotive_0",
            "https://www.amazon.in/gp/bestsellers/sports/ref=zg_bs_nav_sports_0"
            
        ]
        
        all_products = process_all_categories(category_urls)
        save_to_csv(all_products)
        save_to_json(all_products)
    else:
        logging.error("Login Failed! Exiting Program")
        print("Login Failed. Exiting Program")
except Exception as e:
    logging.error(f"An error occurred: {e}")
finally:
    driver.quit()
