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
        
        # 스마트한 호텔 방값 검색 전략
        # 1단계: 최우선 - 확실한 시작가 키워드
        priority_patterns = [
            r'(?:시작가|from|starting\s+from|starts\s+at|부터)[\s:]*([₩$€£¥]\s*[\d,]+(?:\.\d{2})?)',
            r'([₩$€£¥]\s*[\d,]+(?:\.\d{2})?)\s*(?:부터|~|from|starting)'
        ]
        
        # 2단계: 일반 가격 패턴 (평균 가격 컨텍스트 제외)
        general_patterns = [
            r'(?:1박|per\s+night|nightly)[\s:]*([₩$€£¥]\s*[\d,]+(?:\.\d{2})?)',
            r'([₩$€£¥]\s*[\d,]{3,}(?:\.\d{2})?)',
            r'([\d,]{4,}(?:\.\d{2})?\s*[₩원])'
        ]
        
        prices_found = []
        seen_prices = set()
        
        # 단계별 스마트 검색
        text_content = soup.get_text()
        logging.info(f"Text content length: {len(text_content)}")
        
        def is_average_price_context(context_text):
            """평균 가격 컨텍스트인지 확인 (이제 우선적으로 찾기 위함)"""
            average_keywords = ['average', '평균', 'compared to', 'compare', 'stands at']
            return any(keyword in context_text.lower() for keyword in average_keywords)
        
        # 1단계: 평균 가격 우선 검색 (찾으면 즉시 반환)
        average_found = False
        
        # 간단한 가격 패턴으로 평균값 찾기
        basic_price_pattern = r'([₩$€£¥]\s*[\d,]+(?:\.\d{2})?)'
        matches = re.finditer(basic_price_pattern, text_content, re.IGNORECASE)
        
        for match in matches:
            price_text = match.group(1).strip()
            
            if price_text in seen_prices:
                continue
            
            # 컨텍스트 확인
            start_pos = max(0, match.start() - 100)
            end_pos = min(len(text_content), match.end() + 100)
            context = text_content[start_pos:end_pos].strip()
            context = re.sub(r'\s+', ' ', context)
            
            # 평균 가격 컨텍스트 찾기 (이제 우선적으로 선택)
            if is_average_price_context(context):
                seen_prices.add(price_text)
                clean_price = price_text.rstrip(',').strip()
                
                prices_found.append({
                    'price': clean_price,
                    'context': context,
                    'position': match.start(),
                    'priority': True,
                    'type': 'average_price'  # 평균 가격 타입
                })
                
                average_found = True
                logging.info(f"Found average price: {clean_price} - continuing search for more patterns")
        
        # 평균 가격을 찾았어도 계속 검색 (모든 패턴을 확인)
        
        # 2단계: 평균 가격을 못 찾은 경우에만 빠른 패턴 검색 (최적화됨)
        if not average_found:
            logging.info("No average price found, quick pattern search...")
            
            # 최적화된 핵심 패턴만 사용 (속도 우선)
            key_patterns = [
                r'([₩$€£¥]\s*[\d,]{3,}(?:\.\d{2})?)\s*(?:per\s+night|1박|nightly)',  # 1박 가격 (최우선)
                r'([₩$€£¥]\s*[\d,]{3,}(?:\.\d{2})?)'  # 기본 통화 패턴 (빠른 검색)
            ]
            
            for pattern in key_patterns:
                matches = re.finditer(pattern, text_content[:10000], re.IGNORECASE)  # 첫 10KB만 검색
                
                for match in list(matches)[:5]:  # 패턴당 최대 5개만 처리
                    price_text = match.group(1).strip()
                    
                    if price_text in seen_prices or len(price_text) < 2:
                        continue
                        
                    # 간단한 컨텍스트 확인
                    start_pos = max(0, match.start() - 50)
                    end_pos = min(len(text_content), match.end() + 50)
                    context = text_content[start_pos:end_pos].strip()
                    context = re.sub(r'\s+', ' ', context)[:150]  # 컨텍스트 크기 제한
                    
                    # 이미 처리된 평균 가격 제외
                    if is_average_price_context(context):
                        continue
                    
                    seen_prices.add(price_text)
                    clean_price = price_text.rstrip(',').strip()
                    
                    prices_found.append({
                        'price': clean_price,
                        'context': context,
                        'position': match.start(),
                        'priority': False,
                        'type': 'quick_search'
                    })
                    
                    logging.info(f"✓ Quick find: {clean_price}")
                    
                    # 빠른 검색 - 1개 찾으면 바로 다음 패턴으로
                    if len(prices_found) >= 2:
                        break
                
                if len(prices_found) >= 2:
                    break
        
        # 빠른 CSS 선택자 검색 (평균가 없을 때만, 최소한)
        if not average_found and len(prices_found) == 0:
            logging.info("Quick CSS selector search...")
            
            # 핵심 선택자만 사용 (속도 최적화)
            key_selectors = [
                '[class*="price"]',
                '.price'
            ]
            
            for selector in key_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)[:2]  # 최대 2개만
                    
                    for element in elements:
                        element_text = element.get_attribute('textContent') or element.text
                        if element_text and len(element_text) < 500:  # 너무 긴 텍스트는 제외
                            price_matches = re.findall(r'([₩$€£¥]\s*[\d,]+(?:\.\d{2})?)', element_text)
                            if price_matches:
                                clean_price = price_matches[0].strip()
                                if clean_price not in seen_prices:
                                    seen_prices.add(clean_price)
                                    prices_found.append({
                                        'price': clean_price,
                                        'context': element_text[:100],
                                        'position': 0,
                                        'priority': False,
                                        'type': 'css_quick'
                                    })
                                    logging.info(f"✓ CSS quick find: {clean_price}")
                                    break
                    
                    if len(prices_found) >= 1:
                        break
                        
                except Exception:
                    continue

        # 구식 CSS 선택자 섹션 제거 (성능 최적화)
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
        
        # CSS 선택자로 추가 검색 (부족한 경우에만)
        if len(prices_found) < 2:
            logging.info("Searching with CSS selectors...")
            
            for selector in priority_selectors[:5]:  # 상위 5개 선택자만 사용
                elements = soup.select(selector)
                logging.info(f"Selector '{selector}' found {len(elements)} elements")
                
                for element in elements:
                    element_text = element.get_text().strip()
                    if len(element_text) < 5:  # 너무 짧은 텍스트 제외
                        continue
                    
                    # 간단한 가격 패턴으로 검색
                    simple_patterns = [
                        r'[₩$€£¥]\s*[\d,]{3,}(?:\.\d{2})?',
                        r'[\d,]{4,}\s*[₩원]'
                    ]
                    
                    for pattern in simple_patterns:
                        matches = re.finditer(pattern, element_text, re.IGNORECASE)
                        for match in matches:
                            price_text = match.group().strip()
                            clean_price = price_text.rstrip(',').strip()
                            
                            if clean_price in seen_prices:
                                continue
                            
                            seen_prices.add(clean_price)
                            context = element_text[:200]  # 컨텍스트 제한
                            context = re.sub(r'\s+', ' ', context)
                            
                            prices_found.append({
                                'price': clean_price,
                                'context': context,
                                'position': 0,
                                'priority': False
                            })
                            
                            logging.info(f"Found price via selector: {clean_price}")
                            
                            if len(prices_found) >= 3:
                                break
                        
                        if len(prices_found) >= 3:
                            break
                    
                    if len(prices_found) >= 3:
                        break
                
                if len(prices_found) >= 3:
                    break
        
        # Sort by position to maintain order from the page
        prices_found.sort(key=lambda x: x['position'])
        
        # 간단하고 직접적인 가격 처리 (디버깅용)
        unique_prices = []
        seen_prices = set()
        
        logging.info(f"Processing {len(prices_found)} found prices for final selection...")
        
        for i, price_info in enumerate(prices_found):
            price = price_info['price']
            context = price_info['context']
            
            logging.info(f"Examining price {i+1}: '{price}' from context: {context[:100]}...")
            
            # 기본 검증: 숫자 포함 확인
            if not re.search(r'\d{2,}', price):
                logging.info(f"  -> Skipped: no sufficient numbers")
                continue
                
            # 중복 확인
            if price in seen_prices:
                logging.info(f"  -> Skipped: duplicate price")
                continue
            
            # 평균 가격은 이미 1단계에서 처리했으므로 여기서는 제외하지 않음
            # (평균 가격을 찾지 못한 경우에만 이 단계가 실행됨)
            
            # 성공적으로 추가
            seen_prices.add(price)
            
            # 우선순위 설정
            is_priority = price_info.get('type') in ['starting_price', 'booking_price']
            
            final_price = {
                'price': price,
                'context': context[:150],  # 컨텍스트 길이 제한
                'priority': is_priority,
                'type': price_info.get('type', 'general')
            }
            
            unique_prices.append(final_price)
            logging.info(f"  -> ✅ ADDED: {price} (type: {price_info.get('type', 'general')}, priority: {is_priority})")
            
            # 최대 3개
            if len(unique_prices) >= 3:
                logging.info("Reached maximum price limit (3)")
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
