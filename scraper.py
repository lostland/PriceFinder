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
                logging.info(f"Found average price: {clean_price} - stopping search immediately")
                break  # 평균 가격 찾으면 즉시 중단
        
        # 평균 가격을 찾았으면 여기서 검색 완전 중단
        if average_found:
            logging.info("Average price found, skipping all other searches")
            return prices_found[:1]  # 평균 가격만 반환
        
        # 2단계: 평균 가격을 못 찾은 경우에만 일반 패턴 검색
        if not average_found:
            logging.info("No starting price found, searching general patterns...")
            
            # 개선된 호텔 방값 패턴 (실제 예약 가격 위주)
            improved_patterns = [
                r'(?:from|starting)\s+(?:USD|usd)\s+([₩$€£¥]?\s*[\d,]+(?:\.\d{2})?)',  # "from USD 322" 패턴
                r'(?:USD|usd)\s+([₩$€£¥]?\s*[\d,]+(?:\.\d{2})?)(?:\s*(?:VIEW|DEAL|Book))',  # 예약 관련 USD 가격
                r'([₩$€£¥]\s*[\d,]{3,}(?:\.\d{2})?)\s*(?:per\s+night|1박|nightly)',  # 1박 가격
                r'([₩$€£¥]\s*[\d,]{3,}(?:\.\d{2})?)'  # 기본 통화 패턴
            ]
            
            for i, pattern in enumerate(improved_patterns):
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                match_count = 0
                for match in matches:
                    match_count += 1
                    
                    # 가격 텍스트 추출
                    if match.groups():
                        price_text = match.group(1).strip()
                    else:
                        price_text = match.group().strip()
                        
                    # 잘못된 패턴 필터링 (Updated, Stars 등)
                    if any(word in price_text for word in ['Updated', 'U', 'S', 'out', 'of']):
                        continue
                    
                    # 컨텍스트 확인
                    start_pos = max(0, match.start() - 100)
                    end_pos = min(len(text_content), match.end() + 100)
                    context = text_content[start_pos:end_pos].strip()
                    context = re.sub(r'\s+', ' ', context)
                    
                    logging.info(f"Pattern {i+1} match: {price_text} | Context: {context[:120]}...")
                    
                    # 평균 가격 컨텍스트는 이미 1단계에서 처리했으므로 여기서는 제외
                    if is_average_price_context(context):
                        logging.info(f"Skipped (already processed average price): {price_text}")
                        continue
                    
                    # 제목이나 메타데이터에서 나오는 가격 제외
                    if any(word in context.lower() for word in ['updated', 'deals', 'booking.com', 'agoda']):
                        logging.info(f"Excluded (metadata context): {price_text}")
                        continue
                    
                    if price_text not in seen_prices and len(price_text) >= 2:
                        seen_prices.add(price_text)
                        clean_price = price_text.rstrip(',').strip()
                        
                        prices_found.append({
                            'price': clean_price,
                            'context': context,
                            'position': match.start(),
                            'priority': i < 2,  # 처음 2개 패턴이 우선순위
                            'type': 'booking_price'
                        })
                        
                        logging.info(f"✓ Added hotel price: {clean_price}")
                        
                        # 우선순위 패턴에서 가격을 찾으면 2개까지, 일반은 1개 추가
                        max_prices = 2 if i < 2 else 3
                        if len(prices_found) >= max_prices:
                            break
                
                logging.info(f"Pattern '{pattern[:50]}...' found {match_count} total matches")
                
                if len(prices_found) >= 3:
                    break
        
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
