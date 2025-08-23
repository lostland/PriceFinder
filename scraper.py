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
        chrome_options.add_argument('--window-size=1920,1080')  # 더 큰 화면
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')
        
        # 실제 브라우저처럼 보이게 하는 옵션들
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--accept-language=en-US,en;q=0.9')
        chrome_options.add_argument('--accept-encoding=gzip, deflate, br')
        chrome_options.add_argument('--accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # 봇 탐지 우회
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        start_time = time.time()
        try:
            driver.get(url)
            
            # 간단하고 빠른 로딩 전략
            time.sleep(3)  # 기본 로딩 대기
            
            # 스크롤로 콘텐츠 로딩
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            page_source = driver.page_source
            
        finally:
            driver.quit()
        
        # BeautifulSoup으로 파싱
        soup = BeautifulSoup(page_source, 'html.parser')
        
        prices_found = []
        seen_prices = set()
        
        # 1단계: 특정 가격 요소들부터 우선 찾기 (실제 예약 가격)
        price_selectors = [
            # 일반적인 호텔 예약 사이트 가격 클래스들
            '[class*="price"]',
            '[class*="cost"]', 
            '[class*="rate"]',
            '[class*="amount"]',
            '[class*="total"]',
            '[class*="nightly"]',
            '[data-testid*="price"]',
            '[data-price]',
            # 더 구체적인 셀렉터들
            '.room-price',
            '.hotel-price',
            '.booking-price',
            '.final-price'
        ]
        
        for selector in price_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    
                    # 가격 패턴 찾기
                    price_patterns = [
                        r'(\$[1-9]\d{2,4}(?:\.\d{2})?)',  # $100-99999.99
                        r'([1-9]\d{2,4}(?:\.\d{2})?\s*USD)',  # 123.45 USD
                        r'(\$[1-9]\d{1,2})',  # $10-999
                    ]
                    
                    for pattern in price_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        for price_text in matches:
                            if price_text not in seen_prices:
                                # 평균가격 제외
                                parent_text = element.parent.get_text(strip=True).lower() if element.parent else text.lower()
                                
                                is_average_price = (
                                    'average' in parent_text or
                                    'avg' in parent_text or
                                    'stands at' in parent_text or
                                    'typical' in parent_text
                                )
                                
                                if not is_average_price:
                                    seen_prices.add(price_text)
                                    prices_found.append({
                                        'price': price_text,
                                        'context': f"Found in {selector}: {text[:100]}",
                                        'source': 'targeted_element'
                                    })
                                    
                                    if len(prices_found) >= 3:
                                        break
                        
                        if len(prices_found) >= 3:
                            break
                    
                    if len(prices_found) >= 3:
                        break
            except Exception:
                continue
            
            if len(prices_found) >= 3:
                break
        
        # 2단계: 특정 요소에서 못 찾으면 전체 텍스트 검색
        if len(prices_found) < 2:
            # script와 style 태그 제거
            for element in soup(["script", "style"]):
                element.decompose()
            
            # 텍스트 추출
            text_content = soup.get_text()
            
            # 더 적극적인 가격 패턴 검색
            price_patterns = [
                # 실제 예약 가격이 나올 가능성이 높은 패턴들
                r'(\$[1-9]\d{2,4}(?:\.\d{2})?)\s*(?:per night|night|/night)',  # $123 per night
                r'(\$[1-9]\d{2,4}(?:\.\d{2})?)\s*(?:total|Total)',  # $123 total
                r'(?:from|From)\s*(\$[1-9]\d{2,4}(?:\.\d{2})?)',  # from $123
                r'(\$[1-9]\d{2,4}(?:\.\d{2})?)',  # 일반 $123
                r'([1-9]\d{2,4}(?:\.\d{2})?\s*USD)',  # 123 USD
            ]
            
            for pattern in price_patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                
                for match in matches:
                    price_text = match.group(1).strip()
                    
                    if price_text in seen_prices:
                        continue
                    
                    # 컨텍스트 추출
                    start_pos = max(0, match.start() - 80)
                    end_pos = min(len(text_content), match.end() + 80)
                    context = text_content[start_pos:end_pos].strip()
                    context_lower = context.lower()
                    
                    # 평균가격 및 기타 불필요한 가격 제외
                    skip_keywords = [
                        'with an average room price of',
                        'which stands at',
                        'average room price',
                        'typical price',
                        'generally costs',
                        'usually costs'
                    ]
                    
                    should_skip = any(keyword in context_lower for keyword in skip_keywords)
                    
                    if should_skip:
                        continue
                    
                    context = re.sub(r'\s+', ' ', context)[:150]
                    
                    seen_prices.add(price_text)
                    prices_found.append({
                        'price': price_text,
                        'context': context,
                        'source': 'text_search'
                    })
                    
                    # 최대 5개로 제한
                    if len(prices_found) >= 5:
                        break
                
                if len(prices_found) >= 5:
                    break
        
        # 디버그: 실제 페이지에 어떤 가격 정보가 있는지 확인
        # (실제 배포시에는 제거)
        debug_patterns = [
            r'(\$\d+)',  # 모든 $ 가격
            r'(\d+\.\d+)',  # 소수점 숫자
            r'(USD)',  # USD 텍스트
            r'(price|Price|PRICE)',  # price 텍스트
            r'(total|Total)',  # total 텍스트
            r'(night|Night)',  # night 텍스트
        ]
        
        debug_info = {}
        all_text = soup.get_text()
        
        for pattern in debug_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            if matches:
                debug_info[pattern] = matches[:10]  # 처음 10개만
        
        # 모든 가격 패턴 검색 (범위 제한 없음)
        all_price_patterns = [
            r'(\$[1-9]\d{2,4}(?:\.\d{2})?)',  # $100-99999.99
            r'([1-9]\d{2,4}(?:\.\d{2})?\s*USD)',  # 100-9999.99 USD
            r'USD\s*([1-9]\d{2,4}(?:\.\d{2})?)',  # USD 100-9999.99
            r'(\$[1-9]\d{1,2})',  # $10-999
        ]
        
        all_prices = []
        
        for pattern in all_price_patterns:
            matches = re.finditer(pattern, all_text, re.IGNORECASE)
            for match in matches:
                price_text = match.group(1).strip()
                
                if price_text not in seen_prices:
                    context_start = max(0, match.start() - 60)
                    context_end = min(len(all_text), match.end() + 60)
                    context = all_text[context_start:context_end].strip()
                    context_lower = context.lower()
                    context = re.sub(r'\s+', ' ', context)[:150]
                    
                    # 평균가격만 제외 (핵심)
                    is_average_price = (
                        'with an average room price of' in context_lower or
                        'which stands at' in context_lower
                    )
                    
                    # 부대 서비스 더 강화된 필터링
                    service_keywords = [
                        'attraction tickets', 'hop on hop off', 'esim', 'sim card',
                        'skywalk', 'flow house', 'king power', 'bts skytrain',
                        'transportation', 'transport', 'skytrain', 'ticket',
                        'attraction', 'wifi', 'internet', 'mobile'
                    ]
                    is_service_price = any(service in context_lower for service in service_keywords)
                    
                    # 날짜, ID, 매우 큰 숫자 제외
                    is_not_price = (
                        any(year in context for year in ['2024', '2025', '2026']) or
                        (price_text.isdigit() and len(price_text) > 4) or  # 긴 ID 제외
                        (price_text.isdigit() and int(price_text) > 1000)  # $1000 이상은 보통 부대 서비스
                    )
                    
                    if not is_average_price and not is_service_price and not is_not_price:
                        seen_prices.add(price_text)
                        all_prices.append({
                            'price': f"${price_text}" if not price_text.startswith('$') else price_text,
                            'context': context,
                            'source': 'all_price_search'
                        })
                        
                        # 충분히 수집
                        if len(all_prices) >= 10:
                            break
            
            if len(all_prices) >= 10:
                break
        
        # 두 번째 가격만 반환 (사용자 요구사항)
        if len(all_prices) >= 2:
            prices_found = [all_prices[1]]  # 두 번째 가격만
        elif len(all_prices) >= 1:
            prices_found = [all_prices[0]]  # 첫 번째라도 반환
        else:
            prices_found = all_prices  # 없으면 빈 리스트
        
        return prices_found
        
    except Exception as e:
        return []

def process_all_cids_sequential(base_url, cid_list):
    """
    모든 CID를 순차적으로 처리하고 각 결과를 즉시 반환
    Generator that yields results immediately as they become available
    """
    original_cid = extract_cid_from_url(base_url)
    total_cids = len(cid_list)
    
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
            
            yield result
            
        except Exception as e:
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