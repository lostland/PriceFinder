import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def scrape_prices(url):
    """
    Scrape price information from a given URL using Selenium for JavaScript execution
    Returns a list of dictionaries containing price and context information
    """
    driver = None
    try:
        # Setup Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logging.info(f"Loading URL with Selenium: {url}")
        
        # Load the page
        driver.get(url)
        
        # Optimized waiting strategy
        try:
            # Wait for page to load completely
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Wait for price elements to appear (much faster)
            price_selectors_priority = [
                '[class*="PropertyCardPrice"]',  # Agoda specific
                '[class*="price"]',
                '[data-price]',
                '.price'
            ]
            
            price_found = False
            for selector in price_selectors_priority:
                try:
                    WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logging.info(f"Price elements loaded: {selector}")
                    price_found = True
                    break
                except:
                    continue
            
            # Short additional wait only if prices found
            if price_found:
                time.sleep(2)
            else:
                # Fallback wait
                time.sleep(3)
                
        except Exception as e:
            logging.warning(f"Wait timeout, proceeding: {e}")
            time.sleep(3)  # Minimal fallback wait
        
        # Get the page source after JavaScript execution
        page_source = driver.page_source
        
        # Parse the HTML
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Optimized price patterns - focused on most common formats
        price_patterns = [
            # Primary currency patterns (most likely to be prices)
            r'[₩$€£¥]\s*[\d,]{3,}(?:\.\d{2})?',  # Currency symbols with 3+ digits
            r'[\d,]{4,}(?:\.\d{2})?\s*[₩원]',     # Korean Won
            r'[\d,]{2,}(?:\.\d{2})?\s*(?:USD|EUR|GBP|JPY|KRW)\b',  # Currency codes
            
            # High precision patterns (most reliable)
            r'(?:price|가격|cost|amount)[\s:]+[₩$€£¥]?\s*[\d,]+(?:\.\d{2})?',
            r'[₩$€£¥]\s*[\d]{1,3}(?:,\d{3})+(?:\.\d{2})?',  # Properly formatted numbers
            
            # Hotel/booking specific patterns
            r'[\d,]+\s*원\s*부터',
            r'[\d,]+\s*만원',
            
            # Fallback patterns for edge cases
            r'[\d,]{3,}\s*(?:원|won)\b',
            r'(?:총|합계|total)[\s:]*[₩$€£¥]?\s*[\d,]+(?:\.\d{2})?'
        ]
        
        prices_found = []
        seen_prices = set()
        
        # Search for prices in the text
        text_content = soup.get_text()
        
        for pattern in price_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                price_text = match.group().strip()
                
                # Skip if we've already found this exact price
                if price_text in seen_prices:
                    continue
                
                seen_prices.add(price_text)
                
                # Get context around the price
                start_pos = max(0, match.start() - 50)
                end_pos = min(len(text_content), match.end() + 50)
                context = text_content[start_pos:end_pos].strip()
                
                # Clean up context
                context = re.sub(r'\s+', ' ', context)
                context = context.replace('\n', ' ').replace('\t', ' ')
                
                prices_found.append({
                    'price': price_text,
                    'context': context,
                    'position': match.start()
                })
        
        # Optimized selectors - focus on most effective ones
        priority_selectors = [
            # High priority - most reliable
            '[class*="PropertyCardPrice"]',  # Agoda specific
            '[class*="price-display"]',
            '[data-price]',
            '[data-price-value]',
            
            # Medium priority - common patterns
            '[class*="price"]',
            '.price',
            '.final-price',
            '.current-price',
            
            # Korean specific
            '[class*="가격"]',
            '[class*="원"]',
            
            # Generic but effective
            'span[class*="price"]',
            'div[class*="price"]',
            'strong[class*="price"]',
            
            # Fallback selectors
            '[class*="amount"]',
            '[class*="cost"]'
        ]
        
        for selector in priority_selectors:
            elements = soup.select(selector)
            for element in elements:
                element_text = element.get_text().strip()
                
                for pattern in price_patterns:
                    matches = re.finditer(pattern, element_text, re.IGNORECASE)
                    for match in matches:
                        price_text = match.group().strip()
                        
                        if price_text in seen_prices:
                            continue
                        
                        seen_prices.add(price_text)
                        
                        # Use the entire element text as context
                        context = element_text
                        context = re.sub(r'\s+', ' ', context)
                        
                        prices_found.append({
                            'price': price_text,
                            'context': context,
                            'position': 0  # HTML element based, no specific position
                        })
        
        # Sort by position to maintain order from the page
        prices_found.sort(key=lambda x: x['position'])
        
        # Improved duplicate removal and filtering
        unique_prices = []
        seen_prices = set()
        seen_contexts = set()
        
        for price_info in prices_found:
            price = price_info['price']
            context = price_info['context'][:200]  # More context for better deduplication
            
            # Skip if price is too small (likely not real prices)
            price_numbers = re.findall(r'[\d,]+', price)
            if price_numbers and len(price_numbers[0].replace(',', '')) < 3:
                continue
                
            # Create unique key
            key = (price, context)
            if key not in seen_contexts and price not in seen_prices:
                seen_contexts.add(key)
                seen_prices.add(price)
                unique_prices.append(price_info)
                
                # Limit early to improve performance
                if len(unique_prices) >= 20:  # Stop after finding 20 good prices
                    break
        
        logging.info(f"Found {len(unique_prices)} unique prices")
        return unique_prices
        
    except Exception as e:
        logging.error(f"Scraping error: {e}")
        raise Exception(f"Error loading or parsing the webpage: {str(e)}")
    finally:
        # Make sure to close the driver
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logging.error(f"Error closing driver: {e}")
