import re
from bs4 import BeautifulSoup
import logging
import requests
import time  
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def scrape_prices_simple(url, original_currency_code=None):
    """
    단순하고 빠른 가격 스크래핑 - 이미지 처리 없음
    Returns a list of dictionaries containing price and context information
    original_currency_code: 원본 URL의 통화 코드 (예: USD, KRW, THB)
    """
    try:
        # Selenium 사용 - 간단한 설정
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        chrome_options = Options()
        #chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        #chrome_options.add_argument('--disable-javascript')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1028,720')  # 더 큰 화면
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')
        #chrome_options.add_argument('--blink-setting=imagesEnable=false')
        #chrome_options.page_load_strategy = 'eager' # 또는 'none'으로 변경 가능
        #chrome_options.add_argument('--disable-extensions')
        # 실제 브라우저처럼 보이게 하는 옵션들
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        #chrome_options.add_argument('--accept-language=en-US,en;q=0.9')
        chrome_options.add_argument('--accept-encoding=gzip, deflate, br')
        chrome_options.add_argument('--accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        #chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # 봇 탐지 우회
        #driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # URL은 app.py에서 이미 올바르게 처리되었으므로 추가 수정하지 않음
        #print(f"스크래핑 사용 URL: {url}")

#        try:
        import os
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        # CID 정보 추출
        cid_match = re.search(r'cid=([^&]+)', url)
        cid_value = cid_match.group(1) if cid_match else 'unknown'

        # 파일명 생성
        #filename = f"page_text_cid_{cid_value}.txt"
        #filepath = os.path.join('downloads', filename)

        # 전체 텍스트 저장
        #f = open(filepath, 'w', encoding='utf-8')
        #f.write(f"start-------------------------------------\n")
        #f.write(f"스크래핑 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        #f.flush()
#        except Exception as save_error:
#            print(f"텍스트 파일 저장 오류: {save_error}")


        #print(f"driver.get() start\n")
        start_time = time.time()
        try:
            print(f"start driver.get(): {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            #f.flush()

            #driver.set_script_timeout(5)
            driver.set_page_load_timeout(4)
            driver.get(url)
            #f.write(f"finish driver.get(): {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            #f.flush()
            print(f"driver.get() end\n")

        
            # 빠른 로딩 전략 (timeout 방지)
            #time.sleep(1.5)  # 로딩 대기 시간 단축
            
            # 스크롤로 콘텐츠 로딩
            #driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
            #page_source = driver.page_source
            
        except:
           print(f"driver.get() fail\n")
            #f.write(f"driver.get fail: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            #f.flush()

        #f.write(f"start parsing: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        #f.flush()

        #driver.execute_script("window.scrollTo(0, 0);")
        page_source = driver.page_source
        # BeautifulSoup으로 파싱
        #f.write( page_source )

        soup = BeautifulSoup(page_source, 'html.parser')
        #f.write( '---------------------------------------\n')
        #f.write( soup.get_text() )
        #f.flush()

        driver.quit()

        print(f"start parsing: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        #f.flush()
        
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
        
        # 5KB 제한: 텍스트가 5KB를 넘으면 5KB까지만 자르고 즉시 종료
        text_size_bytes = len(all_text.encode('utf-8'))
        if text_size_bytes > 5 * 1024:  # 5KB = 5 * 1024 bytes
            # UTF-8 기준 5KB까지만 자르기 (안전하게)
            truncated_text = all_text
            while len(truncated_text.encode('utf-8')) > 5 * 1024:
                truncated_text = truncated_text[:-100]  # 100글자씩 줄이기
            all_text = truncated_text + "... [5KB 제한으로 텍스트 일부만 수집됨]"
            
            # 즉시 파일 저장하고 가격 분석 건너뛰기
            #try:
                #import os
                #if not os.path.exists('downloads'):
                #    os.makedirs('downloads')
                
                # CID 정보 추출
                #cid_match = re.search(r'cid=([^&]+)', url)
                #cid_value = cid_match.group(1) if cid_match else 'unknown'
                
                # 파일명 생성
                #filename = f"page_text_cid_{cid_value}.txt"
                #filepath = os.path.join('downloads', filename)
                
                # 전체 텍스트 저장
                #with open(filepath, 'w', encoding='utf-8') as f:
                #f.write(f"2----------------------------------\n")
                #f.write(f"URL: {url}\n")
                ##f.write(f"CID: {cid_value}\n")
                #f.write(f"스크래핑 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                #f.write(f"파일 크기: 5KB 제한 적용\n")
                #f.write("="*50 + "\n\n")
                #f.write(all_text)
                
                #print(f"5KB 제한 - 텍스트 파일 저장됨: {filepath}")
                
            #except Exception as save_error:
                #print(f"텍스트 파일 저장 오류: {save_error}")
            
            # txt 파일에서 "시작가" 뒤의 가격 찾기
            starting_price = None
            try:
                # "시작가" 뒤의 가격 패턴 검색 (다양한 통화 단위 지원)
                starting_price_patterns = [
                    r'시작가\s*(USD\s+[\d,]+(?:\.\d+)?)',         # USD 46 형태
                    r'시작가\s*(KRW\s+[\d,]+(?:\.\d+)?)',         # KRW 46000 형태  
                    r'시작가\s*(THB\s+[\d,]+(?:\.\d+)?)',         # THB 1500 형태
                    r'시작가\s*([₩]\s*[\d,]+(?:\.\d+)?)',         # ₩ 33,458 형태 (공백 포함)
                    r'시작가\s*([₩][\d,]+(?:\.\d+)?)',           # ₩46000 형태
                    r'시작가\s*([฿]\s*[\d,]+(?:\.\d+)?)',         # ฿ 1,500 형태 (공백 포함)
                    r'시작가\s*([฿][\d,]+(?:\.\d+)?)',           # ฿1500 형태
                    r'시작가\s*(\$\s*[\d,]+(?:\.\d+)?)',         # $ 46 형태 (공백 포함)
                    r'시작가\s*(\$[\d,]+(?:\.\d+)?)',            # $46 형태
                    r'시작가[^\d]*([\d,]+(?:\.\d+)?\s*USD)',      # 46 USD 형태
                    r'시작가[^\d]*([\d,]+(?:\.\d+)?\s*THB)',      # 46 THB 형태
                    r'시작가[^\d]*([\d,]+(?:\.\d+)?\s*KRW)',      # 46 KRW 형태
                ]
                
                match = None
                for pattern in starting_price_patterns:
                    match = re.search(pattern, all_text, re.IGNORECASE)
                    if match:
                        break
                
                if match:
                    price_text = match.group(1).strip()
                    # 원본 가격 텍스트를 그대로 사용 (통화 단위 포함)
                    if price_text:
                        starting_price = {
                            'price': price_text,  # 원본 형태 그대로 (₩, THB, $ 등 포함)
                            'context': f"시작가 {price_text}",
                            'source': 'starting_price_from_file'
                        }
                        print(f"시작가 발견: {starting_price['price']}")
                
            except Exception as e:
                print(f"시작가 검색 오류: {e}")
            
            # 시작가를 찾았으면 반환, 못 찾았으면 빈 결과
            if starting_price:
                return [starting_price]
            else:
                return []
        
        for pattern in debug_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            if matches:
                debug_info[pattern] = matches[:10]  # 처음 10개만
        
        # 더 광범위한 가격 패턴 검색
        all_price_patterns = [
            # 달러 패턴
            r'(\$[1-9]\d{2,4}(?:\.\d{2})?)',  # $100-99999.99
            r'(\$[1-9]\d{1,2})',  # $10-999
            # USD 패턴
            r'([1-9]\d{2,4}(?:\.\d{2})?\s*USD)',  # 100-9999.99 USD
            r'USD\s*([1-9]\d{2,4}(?:\.\d{2})?)',  # USD 100-9999.99
            r'USD\s*([1-9]\d{1,2})',  # USD 10-999
            # 순수 숫자 패턴 (가격일 가능성)
            r'\b([2-9]\d{2})\b',  # 200-999 (3자리)
            r'\b([1-9]\d{3})\b',  # 1000-9999 (4자리)
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
                    
                    # 평균가격 강화 필터링 
                    is_average_price = (
                        'with an average room price of' in context_lower or
                        'which stands at' in context_lower or
                        '평균 객실 가격은' in context_lower or
                        'average room price' in context_lower or
                        '평균 가격' in context_lower or
                        '평균 객실' in context_lower or
                        '방콕의 평균' in context_lower
                    )
                    
                    # 명백한 ID나 날짜만 제외
                    is_not_price = (
                        any(year in context for year in ['2024', '2025', '2026']) or
                        (price_text.isdigit() and len(price_text) > 4)  # 긴 ID만 제외
                    )
                    
                    if not is_average_price and not is_not_price:
                        seen_prices.add(price_text)
                        all_prices.append({
                            'price': f"${price_text}" if not price_text.startswith('$') else price_text,
                            'context': context,
                            'source': 'all_price_search'
                        })
                        
                        # 더 많이 수집 (두 번째 가격을 찾기 위해)
                        if len(all_prices) >= 20:
                            break
            
            if len(all_prices) >= 20:
                print("20개 이상의 가격 발견 - 수집 중지")
                break
        
        # 가격 분석 전에 먼저 전체 텍스트를 파일로 저장 (다운로드용)
        #try:
            #import os
            #if not os.path.exists('downloads'):
            #    os.makedirs('downloads')
            
            # CID 정보 추출
            #cid_match = re.search(r'cid=([^&]+)', url)
            #cid_value = cid_match.group(1) if cid_match else 'unknown'
            
            # 파일명 생성
            #filename = f"page_text_cid_{cid_value}.txt"
            #filepath = os.path.join('downloads', filename)
            
            # 전체 텍스트 저장
            #with open(filepath, 'w', encoding='utf-8') as f:
            #f.write(f"3------------------------\n")
            #f.write(f"URL: {url}\n")
            #f.write(f"CID: {cid_value}\n")
            #f.write(f"스크래핑 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            #f.write("="*50 + "\n\n")
            #f.write(all_text)
            
            #print(f"텍스트 파일 저장됨: {filepath}")
            
        #except Exception as save_error:
            #print(f"텍스트 파일 저장 오류: {save_error}")
        
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

def reorder_url_parameters(url):
    """
    URL의 파라메터를 지정된 순서로 재정렬하고 필요한 파라메터만 유지
    """
    # 지정된 파라메터 순서 (필요한 모든 파라미터 포함)
    desired_order = [
        'countryId',
        'finalPriceView', 
        'isShowMobileAppPrice',
        'familyMode',
        'adults',
        'children',
        'childs',  # children의 다른 표현
        'maxRooms',
        'rooms',
        'checkIn',    # 체크인 날짜 (camelCase)
        'checkin',    # 체크인 날짜 (lowercase)
        'checkOut',   # 체크아웃 날짜 (camelCase)
        'checkout',   # 체크아웃 날짜 (lowercase)
        'isCalendarCallout',
        'childAges',
        'numberOfGuest',
        'missingChildAges',
        'travellerType',
        'showReviewSubmissionEntry',
        'currencyCode',
        'currency',
        'isFreeOccSearch',
        'los',
        'textToSearch',  # 검색 텍스트 추가
        'productType',   # 상품 타입 추가
        'searchrequestid',
        'ds',           # ds 파라미터 추가
        'cid'
    ]
    
    try:
        # URL 파싱
        parsed_url = urlparse(url)
        query_string = parsed_url.query
        
        # 정규표현식으로 파라메터 추출 (디코딩 없이)
        params_dict = {}
        
        # 쿼리 스트링을 &로 분리하여 파라메터 추출
        if query_string:
            param_pairs = query_string.split('&')
            for pair in param_pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    params_dict[key] = value
        
        # 체크인 관련 파라미터 확인 (간소화)
        checkin_found = [f"{k}={v}" for k, v in params_dict.items() if 'checkin' in k.lower()]
        if checkin_found:
            print(f"체크인 관련 파라미터 발견: {', '.join(checkin_found)}")
        
        # currency 파라미터가 없으면 기본값 KRW 추가
        if 'currency' not in params_dict:
            params_dict['currency'] = 'KRW'
            print("currency 파라미터가 없어서 currency=KRW로 기본값 추가")
        
        # 새로운 파라메터 딕셔너리 (지정된 순서대로)
        reordered_params = {}
        
        # 지정된 순서대로 파라메터 추가 (존재하는 경우만)
        for param in desired_order:
            if param in params_dict:
                reordered_params[param] = params_dict[param]
        
        # 새로운 쿼리 스트링 생성
        query_parts = []
        for key, value in reordered_params.items():
            query_parts.append(f"{key}={value}")
        new_query = "&".join(query_parts)
        
        # 새로운 URL 구성
        new_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment
        ))
        
        return new_url
        
    except Exception as e:
        print(f"URL 파라메터 재정렬 오류: {e}")
        return url  # 오류 시 원본 URL 반환

def replace_cid_and_scrape(base_url, cid_list):
    """기존 함수명 호환성을 위한 래퍼"""
    return process_all_cids_sequential(base_url, cid_list)