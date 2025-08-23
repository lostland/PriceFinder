import re
from bs4 import BeautifulSoup
import logging
import requests
import time

def scrape_prices(url):
    """
    Real Agoda price scraper using optimized Selenium
    """
    driver = None
    try:
        logging.info(f"Real Agoda scraping: {url}")
        start_time = time.time()
        
        # 초고속 Selenium 설정
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
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-javascript')  # JS 비활성화로 속도 향상
        chrome_options.add_argument('--window-size=800,600')  # 더 작은 창
        chrome_options.add_argument('--disable-web-security')  # 보안 체크 비활성화
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # 최소 대기 + 빠른 가격 확인
        time.sleep(0.8)  # 더 짧은 대기
        try:
            WebDriverWait(driver, 1.5).until(  # 더 짧은 타임아웃
                EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="price"]'))
            )
        except:
            pass
        
        page_source = driver.page_source
        load_time = time.time() - start_time
        logging.info(f"Selenium loaded in {load_time:.1f}s")
        
        # BeautifulSoup로 파싱
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 실제 가격 검색
        prices_found = []
        seen_prices = set()
        
        # 1. 텍스트에서 가격 패턴 검색
        text_content = soup.get_text()
        price_patterns = [
            r'([₩]\s*[\d,]{3,})',  # 원화 (한국 사이트)
            r'([\d,]{3,}\s*[원₩])',  # 원화 변형
            r'(\$[\d,]{2,}(?:\.\d{2})?)',  # 달러
            r'(USD\s*[\d,]+(?:\.\d{2})?)',  # USD
            r'([\d,]{3,}(?:\.\d{2})?\s*USD)',  # 숫자 USD
        ]
        
        for pattern in price_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in list(matches)[:10]:  # 최대 10개
                price_text = match.group(1).strip()
                
                if price_text in seen_prices or len(price_text) < 3:
                    continue
                
                # 컨텍스트 추출
                start_pos = max(0, match.start() - 50)
                end_pos = min(len(text_content), match.end() + 50)
                context = text_content[start_pos:end_pos].strip()
                context = re.sub(r'\s+', ' ', context)[:200]
                
                seen_prices.add(price_text)
                prices_found.append({
                    'price': price_text,
                    'context': context
                })
                
                if len(prices_found) >= 5:
                    break
        
        # 2. CSS 선택자로 가격 요소 직접 검색
        if len(prices_found) < 3:
            price_selectors = [
                '[class*="PropertyCardPrice"]',
                '[class*="price"]',
                '[data-price]',
                '.price',
                '[class*="rate"]',
                '[class*="cost"]'
            ]
            
            for selector in price_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements[:5]:
                        element_text = element.text or element.get_attribute('textContent') or ""
                        if element_text and len(element_text) < 100:
                            # 가격 패턴 찾기
                            for pattern in price_patterns:
                                price_match = re.search(pattern, element_text, re.IGNORECASE)
                                if price_match:
                                    price_text = price_match.group(1).strip()
                                    if price_text not in seen_prices and len(price_text) >= 3:
                                        seen_prices.add(price_text)
                                        prices_found.append({
                                            'price': price_text,
                                            'context': f"Price element: {element_text[:100]}"
                                        })
                                        break
                        
                        if len(prices_found) >= 5:
                            break
                except:
                    continue
                
                if len(prices_found) >= 5:
                    break
        
        load_time = time.time() - start_time
        logging.info(f"Found {len(prices_found)} real prices in {load_time:.1f}s: {[p['price'] for p in prices_found]}")
        
        return prices_found[:5]  # 최대 5개 반환
        
    except Exception as e:
        logging.error(f"Real scraping error: {e}")
        return []
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

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