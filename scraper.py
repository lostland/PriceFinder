import re
from bs4 import BeautifulSoup
import logging
import requests
import time

def scrape_prices_simple(url):
    """
    단순하고 빠른 가격 스크래핑 - 이미지 처리 없음
    Returns a list of dictionaries containing price and context information
    """
    try:
        logging.info(f"Processing URL: {url}")
        
        # Selenium 사용 - 간단한 설정
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
        chrome_options.add_argument('--window-size=1024,768')
        
        driver = webdriver.Chrome(options=chrome_options)
        
        start_time = time.time()
        try:
            driver.get(url)
            
            # 초고속 대기 전략 (최적화)
            time.sleep(2)  # 2초로 단축
            
            # 빠른 페이지 로딩 확인
            try:
                WebDriverWait(driver, 3).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except:
                pass
            
            page_source = driver.page_source
            load_time = time.time() - start_time
            logging.info(f"Page loaded in {load_time:.1f}s")
            
        finally:
            driver.quit()
        
        # BeautifulSoup으로 파싱
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # script와 style 태그 제거
        for element in soup(["script", "style"]):
            element.decompose()
        
        # 텍스트 추출
        text_content = soup.get_text()
        logging.info(f"Text content length: {len(text_content)}")
        
        # 가격 패턴 검색
        prices_found = []
        seen_prices = set()
        
        # 다양한 가격 패턴
        price_patterns = [
            r'(\$[1-9]\d{2,4}(?:\.\d{2})?)',  # $100-99999.99
            r'([1-9]\d{2,4}(?:\.\d{2})?\s*USD)',  # 123.45 USD
            r'(\$[1-9]\d{1,2})',  # $10-999
            r'([₩]\s*[1-9][\d,]{3,})',  # 원화
            r'([€£¥]\s*[1-9]\d{2,})',  # 다른 통화
        ]
        
        for pattern in price_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            
            for match in matches:
                price_text = match.group(1).strip()
                
                if price_text in seen_prices:
                    continue
                
                # 컨텍스트 추출
                start_pos = max(0, match.start() - 50)
                end_pos = min(len(text_content), match.end() + 50)
                context = text_content[start_pos:end_pos].strip()
                context = re.sub(r'\s+', ' ', context)[:150]
                
                seen_prices.add(price_text)
                prices_found.append({
                    'price': price_text,
                    'context': context
                })
                
                logging.info(f"Found price: {price_text}")
                
                # 최대 5개로 제한
                if len(prices_found) >= 5:
                    break
            
            if len(prices_found) >= 5:
                break
        
        logging.info(f"Total prices found: {len(prices_found)}")
        return prices_found
        
    except Exception as e:
        logging.error(f"Scraping error: {e}")
        return []

def process_all_cids_sequential(base_url, cid_list):
    """
    모든 CID를 순차적으로 처리하고 각 결과를 즉시 반환
    Generator that yields results immediately as they become available
    """
    original_cid = extract_cid_from_url(base_url)
    total_cids = len(cid_list)
    
    logging.info(f"Starting sequential processing of {total_cids} CIDs")
    
    # 시작 신호
    yield {
        'type': 'start',
        'total_cids': total_cids
    }
    
    # 각 CID를 순차적으로 처리
    for i, new_cid in enumerate(cid_list, 1):
        try:
            # URL 생성
            if original_cid:
                new_url = base_url.replace(f"cid={original_cid}", f"cid={new_cid}")
            else:
                separator = "&" if "?" in base_url else "?"
                new_url = f"{base_url}{separator}cid={new_cid}"
            
            # CID 라벨 생성
            if i == 1:
                cid_label = f"원본({new_cid})"
            else:
                cid_label = str(new_cid)
            
            # 진행률 정보
            yield {
                'type': 'progress',
                'step': i,
                'total': total_cids,
                'cid': cid_label
            }
            
            logging.info(f"Step {i}/{total_cids}: Processing CID {cid_label}")
            
            # 스크래핑 실행
            start_time = time.time()
            prices = scrape_prices_simple(new_url)
            process_time = time.time() - start_time
            
            # 즉시 결과 반환
            result = {
                'type': 'result',
                'step': i,
                'total': total_cids,
                'cid': cid_label,
                'url': new_url,
                'prices': prices,
                'found_count': len(prices),
                'process_time': round(process_time, 1)
            }
            
            if len(prices) > 0:
                logging.info(f"✅ Found {len(prices)} prices for CID: {cid_label}")
            else:
                logging.info(f"❌ No prices found for CID: {cid_label}")
            
            yield result
            
        except Exception as e:
            logging.error(f"Error processing CID {new_cid}: {e}")
            yield {
                'type': 'error',
                'step': i,
                'total': total_cids,
                'cid': new_cid,
                'error': str(e)
            }
    
    # 완료 신호
    yield {
        'type': 'complete',
        'total_results': total_cids
    }

def extract_cid_from_url(url):
    """URL에서 CID 값 추출"""
    match = re.search(r'cid=([^&]+)', url)
    return match.group(1) if match else None

def replace_cid_and_scrape(base_url, cid_list):
    """기존 함수명 호환성을 위한 래퍼"""
    return process_all_cids_sequential(base_url, cid_list)