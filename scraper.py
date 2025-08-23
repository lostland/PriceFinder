import re
from bs4 import BeautifulSoup
import logging
import requests
import time

def scrape_prices(url):
    """
    Hybrid ultra-fast scraping: requests for speed + minimal Selenium for JS content
    Returns a list of dictionaries containing price and context information
    """
    try:
        logging.info(f"Hybrid ultra-fast scraping: {url}")
        
        # 1단계: 초고속 requests로 기본 체크
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=2)
        static_content = response.text
        
        # 2단계: 실제 가격 정보 확인 후 동적 콘텐츠 로딩
        price_pattern = r'([₩$€£¥]\s*[\d,]+(?:\.\d{2})?)'
        static_prices = re.findall(price_pattern, static_content)
        
        # 디버깅: Agoda는 항상 동적 로딩이 필요하므로 강제 Selenium 실행
        if True:  # 항상 Selenium 사용 (Agoda 전용)
            logging.info("Dynamic content detected - using minimal Selenium...")
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-images')  # 이미지 로딩 제거
            chrome_options.add_argument('--disable-extensions')  # 확장 프로그램 제거
            chrome_options.add_argument('--window-size=800,600')  # 작은 창
            chrome_options.add_argument('--disable-plugins')  # 플러그인 제거
            
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                driver.get(url)
                # 매우 짧은 대기 후 가격 요소 확인
                time.sleep(1)  # 최소 대기
                
                # 빠른 가격 요소 체크
                try:
                    WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="price"], [data-price]'))
                    )
                except:
                    pass  # 실패해도 계속 진행
                
                page_source = driver.page_source
                load_time = time.time() - start_time
                logging.info(f"Selenium loaded in {load_time:.1f}s (ultra-fast mode)")
            finally:
                driver.quit()
        else:
            page_source = static_content
            load_time = time.time() - start_time
            logging.info(f"Static content loaded in {load_time:.1f}s")
        
        # Parse the HTML
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # 초고속 가격 검색 전략 (속도 최우선)
        text_content = soup.get_text()[:15000]  # 텍스트 크기 제한 (속도)
        logging.info(f"Text content length: {len(text_content)}")
        
        prices_found = []
        seen_prices = set()
        
        def is_average_price_context(context_text):
            """평균 가격 컨텍스트 빠른 확인"""
            return 'average' in context_text.lower() or '평균' in context_text
        
        # 초고속 평균 가격 검색
        average_found = False
        basic_price_pattern = r'([₩$€£¥]\s*[\d,]+(?:\.\d{2})?)'
        
        # 첫 50개 매치만 확인 (속도 최우선)
        matches = list(re.finditer(basic_price_pattern, text_content, re.IGNORECASE))[:50]
        
        for match in matches:
            if len(prices_found) >= 3:  # 최대 3개로 제한
                break
                
            price_text = match.group(1).strip()
            if price_text in seen_prices or len(price_text) < 3:
                continue
            
            # 빠른 컨텍스트 확인 (최소한만)
            start_pos = max(0, match.start() - 40)
            end_pos = min(len(text_content), match.end() + 40)
            context = text_content[start_pos:end_pos].strip()[:150]
            
            # 평균 가격 우선 처리
            if is_average_price_context(context):
                seen_prices.add(price_text)
                prices_found.append({
                    'price': price_text,
                    'context': context,
                    'position': match.start(),
                    'priority': True,
                    'type': 'average_price'
                })
                average_found = True
                logging.info(f"Found average price: {price_text}")
            else:
                # 일반 가격도 수집
                seen_prices.add(price_text)
                prices_found.append({
                    'price': price_text,
                    'context': context,
                    'position': match.start(),
                    'priority': False,
                    'type': 'general_price'
                })
                logging.info(f"Found general price: {price_text}")
        
        # 매우 빠른 HTML 기반 추가 검색 (가격 부족시)
        if len(prices_found) < 2:
            logging.info("Quick HTML pattern search...")
            # 호텔 가격에 맞는 패턴들 (더 정확)
            extra_patterns = [
                r'(\$[1-9]\d{2,3}(?:\.\d{2})?)',  # $100-9999.99 (호텔 범위)
                r'([1-9]\d{2,3}(?:\.\d{2})?\s*USD)',  # 123.45 USD
                r'(\$[1-9]\d{1,2})',  # $50-999 (1박 요금 범위)
            ]
            
            for pattern in extra_patterns:
                extra_matches = re.finditer(pattern, page_source[:10000], re.IGNORECASE)
                for match in list(extra_matches)[:5]:
                    price_text = match.group(1).strip()
                    if len(price_text) >= 3 and price_text not in seen_prices:
                        seen_prices.add(price_text)
                        prices_found.append({
                            'price': price_text,
                            'context': f"HTML pattern: {price_text}",
                            'position': match.start(),
                            'priority': False,
                            'type': 'html_pattern'
                        })
                        logging.info(f"✓ HTML pattern find: {price_text}")
                        
                        if len(prices_found) >= 3:
                            break
                
                if len(prices_found) >= 3:
                    break
        
        # Sort by position to maintain order from the page
        prices_found.sort(key=lambda x: x['position'])
        
        # 간단하고 직접적인 가격 처리 (디버깅용)
        unique_prices = []
        seen_final = set()
        
        logging.info(f"Processing {len(prices_found)} found prices for final selection...")
        
        for i, price_info in enumerate(prices_found):
            price = price_info['price']
            context = price_info['context']
            
            logging.info(f"Examining price {i+1}: '{price}' from context: {context[:80]}...")
            
            # Skip duplicates
            if price in seen_final:
                logging.info(f"  -> ❌ SKIPPED: {price} (already added)")
                continue
            
            # Basic validation
            if len(price) < 2:
                logging.info(f"  -> ❌ SKIPPED: {price} (too short)")
                continue
            
            # Add to final list
            seen_final.add(price)
            unique_prices.append({
                'price': price,
                'context': context
            })
            logging.info(f"  -> ✅ ADDED: {price} (type: {price_info.get('type', 'unknown')}, priority: {price_info.get('priority', False)})")
            
            # Limit to top 5 prices
            if len(unique_prices) >= 5:
                break
        
        logging.info(f"Found {len(unique_prices)} unique prices")
        return unique_prices
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")
        return []
    except Exception as e:
        logging.error(f"Scraping error: {e}")
        return []

def replace_cid_and_scrape(base_url, cid_list):
    """
    Replace the CID parameter in the URL and scrape each variation
    Returns a generator that yields results as they become available
    """
    original_cid = extract_cid_from_url(base_url)
    
    for i, new_cid in enumerate(cid_list, 1):
        try:
            # Replace CID in URL
            if original_cid:
                new_url = base_url.replace(f"cid={original_cid}", f"cid={new_cid}")
            else:
                # Add CID if not present
                separator = "&" if "?" in base_url else "?"
                new_url = f"{base_url}{separator}cid={new_cid}"
            
            # 진행률 정보 생성
            if i == 1:
                cid_label = f"원본({new_cid})"
            else:
                cid_label = str(new_cid)
            
            yield {
                'type': 'progress',
                'step': i,
                'total': len(cid_list),
                'cid': cid_label
            }
            
            # 스크래핑 수행
            prices = scrape_prices(new_url)
            
            yield {
                'type': 'result',
                'step': i,
                'total': len(cid_list),
                'cid': cid_label,
                'url': new_url,
                'prices': prices,
                'found_count': len(prices)
            }
            
        except Exception as e:
            logging.error(f"Error processing CID {new_cid}: {e}")
            yield {
                'type': 'error',
                'step': i,
                'total': len(cid_list),
                'cid': new_cid,
                'error': str(e)
            }

def extract_cid_from_url(url):
    """Extract CID value from URL"""
    import re
    match = re.search(r'cid=([^&]+)', url)
    return match.group(1) if match else None