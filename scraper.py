import re
from bs4 import BeautifulSoup
import logging
import requests
import time

def scrape_prices(url):
    """
    완전 독립적인 가격 스크래핑 - 매번 새로운 Selenium 인스턴스 사용
    """
    driver = None
    try:
        logging.info(f"Independent scraping: {url}")
        start_time = time.time()
        
        # 매번 새로운 Selenium 인스턴스 (완전 독립)
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox') 
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-images')  # 이미지 완전 차단
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--window-size=800,600')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # 이미지 로딩 완전 차단
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        
        # 프리페치 설정으로 이미지/미디어 차단
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.media_stream": 2,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 새로운 드라이버 인스턴스 생성
        driver = webdriver.Chrome(options=chrome_options)
        
        # URL 로드 (대기 없음)
        driver.get(url)
        # 대기 완전 제거 (최대 속도 달성)
        
        # 페이지 소스 가져오기
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 고속 가격 검색 (최대 속도)
        prices_found = []
        seen_prices = set()
        text_content = soup.get_text()[:8000]  # 텍스트 크기 제한
        
        # 가장 빠른 패턴만 사용
        price_patterns = [
            r'(USD\s*[\d,]+)',  # USD 가격만 우선
        ]
        
        for pattern in price_patterns:
            if len(prices_found) >= 2:  # 2개만 찾으면 충분
                break
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in list(matches)[:2]:  # 최대 2개
                price_text = match.group(1).strip()
                if price_text not in seen_prices and len(price_text) >= 4:
                    context = f"CID price: {price_text}"  # 간단한 컨텍스트
                    seen_prices.add(price_text)
                    prices_found.append({
                        'price': price_text,
                        'context': context
                    })
                    if len(prices_found) >= 2:
                        break
        
        processing_time = time.time() - start_time
        logging.info(f"✅ Independent processing completed in {processing_time:.1f}s: Found {len(prices_found)} prices")
        
        return prices_found
        
    except Exception as e:
        logging.error(f"Independent scraping error: {e}")
        return []
    finally:
        # 완전히 종료 (누적 방지)
        if driver:
            try:
                driver.quit()
                logging.info("Driver closed independently")
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