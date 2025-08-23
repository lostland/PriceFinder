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
        
        # 호텔 방값 패턴 (균형잡힌 접근)
        price_patterns = [
            # 기본 통화 패턴 (가장 흔한 형태)
            r'[₩$€£¥]\s*[\d,]{2,}(?:\.\d{2})?',
            r'[\d,]{3,}(?:\.\d{2})?\s*[₩원KRW]',
            
            # 호텔 특화 패턴 (한글)
            r'[\d,]+\s*원\s*(?:부터|~|에서|시작)',
            r'[\d,]+\s*만원',
            r'(?:1박|박당|per\s+night)[\s:]*[₩$€£¥]?\s*[\d,]+(?:\.\d{2})?',
            
            # 호텔 특화 패턴 (영어)
            r'(?:from|starting)[\s:]*[₩$€£¥]\s*[\d,]+(?:\.\d{2})?',
            r'(?:room|rate|price)[\s:]*[₩$€£¥]?\s*[\d,]+(?:\.\d{2})?',
            
            # 예약 사이트 패턴
            r'(?:total|final)[\s:]*[₩$€£¥]\s*[\d,]+(?:\.\d{2})?'
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
                
                # 가격 포맷 정리
                clean_price = price_text.rstrip(',').strip()
                
                prices_found.append({
                    'price': clean_price,
                    'context': context,
                    'position': match.start()
                })
        
        # 호텔 방값에 특화된 CSS 선택자 (우선순위별)
        priority_selectors = [
            # 최우선 - 호텔 예약 사이트 특화
            '[class*="PropertyCardPrice"]',      # Agoda 
            '[class*="price-display"]',          # 일반적인 가격 표시
            '[class*="room-price"]',             # 룸 가격
            '[class*="rate"]',                   # 요금
            '[class*="nightly"]',                # 1박 요금
            
            # 높은 우선순위 - 확실한 가격 요소
            '[data-price]',
            '[data-price-value]',
            '[data-room-price]',
            '.price',
            '.final-price',
            '.room-rate',
            
            # 중간 우선순위 - 한글 지원
            '[class*="가격"]',
            '[class*="요금"]',
            '[class*="원"]',
            '[class*="할인"]',
            
            # 일반적인 패턴
            'span[class*="price"]',
            'div[class*="price"]',
            'strong[class*="price"]',
            'b[class*="price"]',
            
            # 예약 사이트별 특화
            '[class*="booking-price"]',
            '[class*="hotel-price"]',
            '[class*="accommodation-price"]'
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
                        
                        # 가격 포맷 정리
                        clean_price = price_text.rstrip(',').strip()
                        
                        prices_found.append({
                            'price': clean_price,
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
            
            # 간단한 방값 필터링
            price_numbers = re.findall(r'[\d,]+', price)
            if price_numbers:
                num_str = price_numbers[0].replace(',', '')
                # 합리적인 방값 범위만 허용
                if len(num_str) < 2 or len(num_str) > 8:
                    continue
                    
            # 리뷰 관련 더 정확하게 제외
            if price.lower().endswith(' r') or price.lower().endswith('r'):
                continue
            if 'review' in context.lower() and re.search(r'\b\d+\s*r\b', price.lower()):
                continue
            if 'out of' in context.lower():
                continue
                
            # 가격 포맷 정리 (쉼표가 끝에 있는 경우 제거)
            price = price.rstrip(',').strip()
                
            # Create unique key
            key = (price, context)
            if key not in seen_contexts and price not in seen_prices:
                seen_contexts.add(key)
                seen_prices.add(price)
                unique_prices.append(price_info)
                
                # 호텔 방값은 2-3개만 찾기
                if len(unique_prices) >= 5:  # 최대 5개까지만 수집
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
