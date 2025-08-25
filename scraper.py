import re
from bs4 import BeautifulSoup
import logging
import requests
import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def scrape_prices_simple(url, original_currency_code=None, debug_filepath=None, step_info=None):
    """
    단순하고 빠른 가격 스크래핑 - 이미지 처리 없음
    Returns a list of dictionaries containing price and context information
    original_currency_code: 원본 URL의 통화 코드 (예: USD, KRW, THB)
    debug_filepath: 디버그 로그를 저장할 파일 경로 (첫 번째 단계에서만 전달됨)
    step_info: (step_num, total_steps, cid_name, cid_value) 튜플
    """
    
    def write_debug_log(message):
        """디버그 파일에 로그 기록"""
        if debug_filepath:
            try:
                with open(debug_filepath, 'a', encoding='utf-8') as f:
                    timestamp = time.strftime('%H:%M:%S')
                    f.write(f"[{timestamp}] {message}\n")
            except:
                pass
        print(message)  # 콘솔에도 출력
    
    try:
        # 단계 정보 기록
        if step_info:
            step_num, total_steps, cid_name, cid_value = step_info
            write_debug_log(f"\n{'='*60}")
            write_debug_log(f"📍 단계 {step_num}/{total_steps}: {cid_name} (CID: {cid_value})")
            write_debug_log(f"🌐 접속 URL: {url}")
            write_debug_log(f"{'='*60}")
        
        # 최적화된 Selenium 사용 - Agoda는 JavaScript 실행 필요
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        write_debug_log("🔧 Chrome 브라우저 옵션 설정 중...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-images')  # 이미지 차단으로 속도 향상
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--window-size=1200,800')  # 창 크기 늘림
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-component-extensions-with-background-pages')
        
        # 봇 탐지 우회 강화
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 2
        })
        
        write_debug_log("✅ Chrome 옵션 설정 완료")
        write_debug_log(f"🚀 웹페이지 접속 시작...")
        
        start_time = time.time()
        
        write_debug_log("⚡ Chrome 드라이버 실행 중...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)  # 30초로 타임아웃 연장
        driver.implicitly_wait(10)  # 요소 대기 시간 추가
        
        write_debug_log("🔐 봇 탐지 우회 스크립트 실행...")
        # 봇 탐지 우회 스크립트
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            write_debug_log(f"🌐 페이지 로딩 시작...")
            
            # 페이지 로딩 전략 변경 - none으로 설정해서 기본 HTML 로딩 후 즉시 진행
            driver.execute_cdp_cmd('Page.setLoadEventFired', {})
            
            try:
                driver.get(url)
                write_debug_log("✅ 초기 페이지 로딩 완료")
                
                # JavaScript 로딩 대기 (최대 10초)
                write_debug_log("⏳ JavaScript 처리 대기 중...")
                time.sleep(5)  # 5초 기본 대기
                
                # 추가 JavaScript 완료 확인
                for i in range(5):  # 최대 5번 시도
                    try:
                        ready_state = driver.execute_script("return document.readyState")
                        write_debug_log(f"📊 페이지 상태 확인 #{i+1}: {ready_state}")
                        if ready_state == 'complete':
                            break
                        time.sleep(1)
                    except:
                        break
                        
            except Exception as load_error:
                write_debug_log(f"⚠️ 페이지 로딩 중 오류: {load_error}")
                write_debug_log("🔄 오류에도 불구하고 소스 추출 시도...")
            
            write_debug_log("📄 페이지 소스 추출 중...")
            page_source = driver.page_source
            write_debug_log(f"✅ 페이지 소스 추출 완료 ({len(page_source)} 문자)")
            
        finally:
            write_debug_log("🔚 Chrome 드라이버 종료...")
            driver.quit()
        
        load_time = time.time() - start_time
        write_debug_log(f"⏱️ 총 페이지 로딩 시간: {load_time:.2f}초")
        
        # BeautifulSoup으로 파싱
        write_debug_log("🔍 HTML 파싱 시작...")
        soup = BeautifulSoup(page_source, 'html.parser')
        all_text = soup.get_text()
        
        text_size = len(all_text)
        byte_size = len(all_text.encode('utf-8'))
        write_debug_log(f"📊 추출된 텍스트: {text_size} 글자, {byte_size} bytes")
        
        # 페이지 텍스트 샘플 기록 (처음 500자)
        text_sample = all_text[:500].replace('\n', ' ').replace('\r', ' ')
        write_debug_log(f"📝 페이지 텍스트 샘플: {text_sample}...")
        
        # 가격 추출 시작
        write_debug_log("💰 가격 추출 시작...")
        
        # 다중 통화 및 지역별 가격 패턴
        patterns = []
        
        # 원화 (KRW) 패턴들
        if original_currency_code in ['KRW', None]:
            patterns.extend([
                r'₩\s*(\d{1,3}(?:,\d{3})+)',
                r'(\d{1,3}(?:,\d{3})+)\s*원',
                r'시작가\s*₩\s*(\d{1,3}(?:,\d{3})+)',
                r'(\d{1,3}(?:,\d{3})+)\s*KRW'
            ])
            write_debug_log("🔍 KRW(원화) 패턴 검색 중...")
        
        # 달러 (USD) 패턴들
        if original_currency_code in ['USD', None]:
            patterns.extend([
                r'\$\s*(\d{1,3}(?:,\d{3})*\.?\d*)',
                r'(\d{1,3}(?:,\d{3})*\.?\d*)\s*USD'
            ])
            write_debug_log("🔍 USD(달러) 패턴 검색 중...")
        
        # 태국 바트 (THB) 패턴들
        if original_currency_code in ['THB', None]:
            patterns.extend([
                r'฿\s*(\d{1,3}(?:,\d{3})*\.?\d*)',
                r'(\d{1,3}(?:,\d{3})*\.?\d*)\s*THB'
            ])
            write_debug_log("🔍 THB(바트) 패턴 검색 중...")
        
        # 유로 (EUR) 패턴들
        if original_currency_code in ['EUR', None]:
            patterns.extend([
                r'€\s*(\d{1,3}(?:,\d{3})*\.?\d*)',
                r'(\d{1,3}(?:,\d{3})*\.?\d*)\s*EUR'
            ])
            write_debug_log("🔍 EUR(유로) 패턴 검색 중...")
        
        # 엔 (JPY) 패턴들
        if original_currency_code in ['JPY', None]:
            patterns.extend([
                r'¥\s*(\d{1,3}(?:,\d{3})*)',
                r'(\d{1,3}(?:,\d{3})*)\s*엔',
                r'(\d{1,3}(?:,\d{3})*)\s*JPY'
            ])
            write_debug_log("🔍 JPY(엔) 패턴 검색 중...")
        
        # 파운드 (GBP) 패턴들
        if original_currency_code in ['GBP', None]:
            patterns.extend([
                r'£\s*(\d{1,3}(?:,\d{3})*\.?\d*)',
                r'(\d{1,3}(?:,\d{3})*\.?\d*)\s*GBP'
            ])
            write_debug_log("🔍 GBP(파운드) 패턴 검색 중...")
        
        # 패턴 매칭 및 가격 추출
        found_prices = []
        
        for i, pattern in enumerate(patterns):
            matches = re.finditer(pattern, all_text)
            for match in matches:
                price_text = match.group(1)
                context_start = max(0, match.start() - 30)
                context_end = min(len(all_text), match.end() + 30)
                context = all_text[context_start:context_end].strip()
                
                found_prices.append({
                    'price': price_text,
                    'context': context,
                    'position': match.start(),
                    'pattern_index': i
                })
        
        write_debug_log(f"💰 발견된 가격 패턴: {len(found_prices)}개")
        
        # 가격별로 디버그 로그 기록
        for i, price_info in enumerate(found_prices[:5]):  # 상위 5개만 기록
            write_debug_log(f"  💵 #{i+1}: {price_info['price']} (위치: {price_info['position']})")
            write_debug_log(f"      📝 컨텍스트: {price_info['context'][:100]}...")
        
        # 중복 제거 및 정렬
        unique_prices = []
        seen_prices = set()
        
        for price_info in sorted(found_prices, key=lambda x: x['position']):
            price_key = price_info['price']
            if price_key not in seen_prices:
                seen_prices.add(price_key)
                unique_prices.append(price_info)
        
        write_debug_log(f"🔧 중복 제거 후 유니크 가격: {len(unique_prices)}개")
        
        # 상위 5개만 반환
        final_prices = unique_prices[:5]
        write_debug_log(f"✅ 최종 반환할 가격: {len(final_prices)}개")
        
        if final_prices:
            write_debug_log("🎉 가격 추출 성공!")
            for i, price in enumerate(final_prices):
                write_debug_log(f"  🏆 최종 #{i+1}: {price['price']}")
        else:
            write_debug_log("😔 가격을 찾을 수 없음")
            # 디버그: 페이지에서 숫자 패턴 확인
            number_patterns = re.findall(r'\d{1,3}(?:,\d{3})+', all_text)
            write_debug_log(f"🔍 페이지의 큰 숫자 패턴: {len(number_patterns)}개 발견")
            if number_patterns:
                write_debug_log(f"    예시: {number_patterns[:10]}")
        
        write_debug_log(f"✅ 스크래핑 완료 - 처리 시간: {load_time:.2f}초")
        
        return final_prices
        
    except Exception as e:
        error_msg = f"❌ 스크래핑 중 오류 발생: {str(e)}"
        write_debug_log(error_msg)
        import traceback
        write_debug_log(f"📋 상세 오류:\n{traceback.format_exc()}")
        return []

def extract_cid_from_url(url):
    """URL에서 CID 값을 추출"""
    cid_match = re.search(r'cid=([^&]+)', url)
    return cid_match.group(1) if cid_match else None

def reorder_url_parameters(url):
    """URL 파라미터를 지정된 순서로 재정렬"""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        
        # 파라미터 순서 정의
        param_order = [
            'countryId', 'finalPriceView', 'isShowMobileAppPrice', 'familyMode',
            'adults', 'children', 'maxRooms', 'rooms', 'checkIn', 'isCalendarCallout',
            'childAges', 'numberOfGuest', 'missingChildAges', 'travellerType',
            'showReviewSubmissionEntry', 'currencyCode', 'currency', 'isFreeOccSearch',
            'los', 'searchrequestid', 'cid'
        ]
        
        # 순서대로 정리된 파라미터
        ordered_params = []
        for param in param_order:
            if param in params:
                for value in params[param]:
                    ordered_params.append(f"{param}={value}")
                del params[param]
        
        # 남은 파라미터들 추가
        for param, values in params.items():
            for value in values:
                ordered_params.append(f"{param}={value}")
        
        new_query = '&'.join(ordered_params)
        new_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
        
        return new_url
    except:
        return url

def process_all_cids_sequential(url):
    """모든 CID를 순차적으로 처리 (기존 함수 유지)"""
    # 이 함수는 기존 코드 호환성을 위해 유지
    return []