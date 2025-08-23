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
        
        # Wait for page to load and JavaScript to execute
        time.sleep(5)
        
        # Try to wait for common price elements to load
        try:
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Try to wait for specific price elements
            common_price_selectors = [
                '[class*="price"]', '[class*="가격"]', '[data-price]', 
                '.price', '[class*="amount"]', '[class*="cost"]',
                '[class*="PropertyCardPrice"]', '[class*="rate"]'
            ]
            
            for selector in common_price_selectors:
                try:
                    WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logging.info(f"Found price elements with selector: {selector}")
                    break
                except:
                    continue
                    
        except Exception as e:
            logging.warning(f"Timeout waiting for page elements: {e}")
            
        # Additional wait for dynamic content to fully render
        time.sleep(3)
        
        # Try to scroll down to trigger lazy loading (if any)
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
        except Exception as e:
            logging.warning(f"Error during scrolling: {e}")
        
        # Get the page source after JavaScript execution
        page_source = driver.page_source
        
        # Parse the HTML
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Enhanced price patterns for different currencies and formats
        price_patterns = [
            # Korean Won - comprehensive patterns
            r'₩\s*[\d,]+(?:\.\d{2})?',
            r'[₩]\s*[\d,]+',
            r'[\d,]+\s*원',
            r'KRW\s*[\d,]+(?:\.\d{2})?',
            r'[\d,]+\s*KRW',
            
            # US Dollar - various formats
            r'\$\s*[\d,]+(?:\.\d{2})?',
            r'USD\s*[\d,]+(?:\.\d{2})?',
            r'[\d,]+(?:\.\d{2})?\s*USD',
            r'US\$\s*[\d,]+(?:\.\d{2})?',
            
            # Euro
            r'€\s*[\d,]+(?:\.\d{2})?',
            r'EUR\s*[\d,]+(?:\.\d{2})?',
            r'[\d,]+(?:\.\d{2})?\s*EUR',
            r'[\d,]+(?:\.\d{2})?\s*€',
            
            # British Pound
            r'£\s*[\d,]+(?:\.\d{2})?',
            r'GBP\s*[\d,]+(?:\.\d{2})?',
            r'[\d,]+(?:\.\d{2})?\s*GBP',
            
            # Japanese Yen
            r'¥\s*[\d,]+',
            r'JPY\s*[\d,]+',
            r'[\d,]+\s*JPY',
            r'[\d,]+\s*¥',
            
            # Common price indicators with numbers
            r'(?:가격|price|cost|amount|총액|합계|Price|Cost|Amount|Total)[\s:]*[₩$€£¥]?\s*[\d,]+(?:\.\d{2})?',
            r'[₩$€£¥]\s*[\d,]+(?:\.\d{2})?(?:\s*(?:USD|EUR|GBP|KRW|JPY|원|won|dollars?|euros?|pounds?))?',
            
            # Numbers followed by currency words
            r'[\d,]+(?:\.\d{2})?\s*(?:USD|EUR|GBP|KRW|JPY|원|won|dollars?|euros?|pounds?)',
            
            # Decimal prices (common in e-commerce)
            r'[\d,]+\.\d{2}\s*[₩$€£¥]?',
            
            # Large numbers with commas (likely prices)
            r'[₩$€£¥]\s*[\d]{1,3}(?:,\d{3})+(?:\.\d{2})?',
            
            # Korean specific patterns
            r'[\d,]+\s*천원',
            r'[\d,]+\s*만원',
            
            # Common price range patterns
            r'[₩$€£¥]?\s*[\d,]+(?:\.\d{2})?\s*[-~]\s*[₩$€£¥]?\s*[\d,]+(?:\.\d{2})?'
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
        
        # Enhanced selectors for price elements on modern e-commerce sites
        price_selectors = [
            # Generic price-related selectors
            '[class*="price"]',
            '[class*="cost"]',
            '[class*="amount"]',
            '[class*="total"]',
            '[id*="price"]',
            '[id*="cost"]',
            '[data-testid*="price"]',
            '[data-price]',
            
            # Common class patterns
            '.price',
            '.cost',
            '.amount',
            '.total-price',
            '.final-price',
            '.current-price',
            '.sale-price',
            '.regular-price',
            '.list-price',
            
            # Element type with price-related classes
            'span[class*="price"]',
            'div[class*="price"]',
            'p[class*="price"]',
            'strong[class*="price"]',
            'b[class*="price"]',
            'em[class*="price"]',
            'h1[class*="price"]',
            'h2[class*="price"]',
            'h3[class*="price"]',
            
            # Korean e-commerce specific patterns
            '[class*="가격"]',
            '[class*="금액"]',
            '[class*="원"]',
            
            # Common data attributes
            '[data-price-value]',
            '[data-original-price]',
            '[data-sale-price]',
            '[data-current-price]',
            
            # Agoda and hotel booking specific
            '[class*="PropertyCardPrice"]',
            '[class*="price-display"]',
            '[class*="rate"]',
            '[class*="booking-price"]',
            '[data-selenium*="price"]',
            
            # Amazon and marketplace specific
            '[class*="a-price"]',
            '[class*="price-current"]',
            '[class*="price-now"]',
            '[class*="price-range"]'
        ]
        
        for selector in price_selectors:
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
        
        # Remove duplicates while preserving order
        unique_prices = []
        seen_contexts = set()
        
        for price_info in prices_found:
            # Create a key based on price and simplified context
            key = (price_info['price'], price_info['context'][:100])
            if key not in seen_contexts:
                seen_contexts.add(key)
                unique_prices.append(price_info)
        
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
