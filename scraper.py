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
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')
        
        # 데스크톱 사이트 접속용 설정
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--window-size=1920,1080')  # 데스크톱 해상도
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.media_stream_mic": 2,
            "profile.default_content_setting_values.media_stream_camera": 2,
            "profile.default_content_setting_values.geolocation": 2
        })
        
        # 데스크톱 브라우저 설정 (모바일 에뮬레이션 제거)
        
        write_debug_log("✅ Chrome 옵션 설정 완료")
        write_debug_log(f"🚀 웹페이지 접속 시작...")
        
        start_time = time.time()
        
        # 환경 진단 추가
        import subprocess
        import sys
        import os
        
        write_debug_log("🔍 환경 진단 시작...")
        
        # Chrome 버전 확인
        try:
            chrome_version = subprocess.check_output(['google-chrome', '--version']).decode().strip()
            write_debug_log(f"🌐 Chrome 버전: {chrome_version}")
        except:
            try:
                chrome_version = subprocess.check_output(['chromium-browser', '--version']).decode().strip()
                write_debug_log(f"🌐 Chromium 버전: {chrome_version}")
            except:
                write_debug_log("❌ Chrome/Chromium 버전 확인 실패")
        
        # ChromeDriver 버전 확인
        try:
            driver_version = subprocess.check_output(['chromedriver', '--version']).decode().strip()
            write_debug_log(f"🚗 ChromeDriver 버전: {driver_version}")
        except:
            write_debug_log("❌ ChromeDriver 버전 확인 실패")
        
        # 시스템 정보
        write_debug_log(f"🐍 Python 버전: {sys.version}")
        write_debug_log(f"💻 작업 디렉토리: {os.getcwd()}")
        write_debug_log(f"🔒 실행 사용자: {os.getenv('USER', 'unknown')}")
        
        # 메모리 정보
        try:
            memory_info = subprocess.check_output(['free', '-h']).decode()
            write_debug_log(f"💾 메모리 상태:\n{memory_info}")
        except:
            write_debug_log("❌ 메모리 정보 확인 실패")
        
        # 실행 중인 Chrome 프로세스 정리
        try:
            chrome_processes = subprocess.check_output(['pgrep', '-f', 'chrome']).decode().strip().split('\n')
            chrome_count = len([p for p in chrome_processes if p.strip()])
            write_debug_log(f"🔄 실행 중인 Chrome 프로세스: {chrome_count}개")
            
            # Chrome 프로세스가 5개 이상이면 정리
            if chrome_count > 5:
                write_debug_log("🧹 과도한 Chrome 프로세스 정리 시작...")
                try:
                    subprocess.run(['pkill', '-f', 'chrome'], check=False)
                    time.sleep(2)  # 프로세스 종료 대기
                    
                    # 정리 후 다시 확인
                    chrome_processes_after = subprocess.check_output(['pgrep', '-f', 'chrome']).decode().strip().split('\n')
                    chrome_count_after = len([p for p in chrome_processes_after if p.strip()])
                    write_debug_log(f"✅ Chrome 프로세스 정리 완료: {chrome_count}개 → {chrome_count_after}개")
                except:
                    write_debug_log("⚠️ Chrome 프로세스 정리 중 일부 오류 발생 (정상)")
        except:
            write_debug_log("ℹ️ 실행 중인 Chrome 프로세스 없음")
        
        write_debug_log("⚡ Chrome 드라이버 실행 중...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(5)  # 5초로 적정 복원
        
        write_debug_log("🖥️ 데스크톱 사이트 접속용 스크립트 실행...")
        
        # 데스크톱 전용 봇 탐지 우회 스크립트들
        desktop_stealth_scripts = [
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
            "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})",  # 데스크톱 플러그인 시뮬레이션
            "Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']})",
            "Object.defineProperty(navigator, 'platform', {get: () => 'Win32'})",
            "Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 0})",  # 터치 지원 없음
            "window.chrome = { runtime: {} }",
            "delete navigator.__proto__.webdriver"
        ]
        
        for script in desktop_stealth_scripts:
            try:
                driver.execute_script(script)
            except:
                pass  # 스크립트 실행 실패해도 계속 진행
        
        # 간단한 페이지 테스트
        write_debug_log("🧪 Chrome 작동 테스트 (Google 접속)...")
        try:
            driver.get("https://www.google.com")
            google_title = driver.title
            write_debug_log(f"✅ Google 테스트 성공: {google_title}")
        except Exception as google_error:
            write_debug_log(f"❌ Google 테스트 실패: {google_error}")
            write_debug_log("🚨 Chrome 자체에 문제가 있습니다!")
        
        try:
            # 데스크톱 사이트 직접 접속
            write_debug_log(f"🖥️ 데스크톱 아고다 페이지 로딩 시작...")
            write_debug_log(f"🌐 데스크톱 URL: {url[:100]}...")
            
            try:
                driver.get(url)
            except:
                # 페이지 로딩이 완료되지 않아도 계속 진행
                pass
            
            write_debug_log("🔍 실시간 페이지 모니터링 시작...")
            
            # 실시간 모니터링 시스템
            previous_source = ""
            page_source = ""
            max_attempts = 20  # 최대 20번 시도 (10초)
            found_prices = []
            
            for attempt in range(max_attempts):
                try:
                    # 현재 페이지 소스 가져오기
                    current_source = driver.page_source
                    
                    # 페이지가 변화했으면 처리
                    if len(current_source) > len(previous_source) + 1000:  # 1KB 이상 변화
                        write_debug_log(f"📄 페이지 변화 감지 #{attempt+1}: {len(current_source)} 문자")
                        
                        # 즉시 파일 저장
                        text_filename = f"downloads/page_text_cid_-1_attempt_{attempt+1}.txt"
                        try:
                            with open(text_filename, 'w', encoding='utf-8') as f:
                                f.write(current_source)
                            write_debug_log(f"💾 페이지 내용 저장: {text_filename}")
                        except:
                            pass
                        
                        # 즉시 가격 추출 시도 - 간단한 패턴 매칭
                        import re
                        krw_patterns = [
                            r'₩\s*([0-9,]+)',
                            r'KRW\s*([0-9,]+)', 
                            r'([0-9,]+)\s*원',
                            r'([0-9,]+)\s*KRW'
                        ]
                        temp_prices = []
                        for pattern in krw_patterns:
                            matches = re.findall(pattern, current_source)
                            for match in matches:
                                try:
                                    price_num = int(match.replace(',', ''))
                                    if 10000 <= price_num <= 1000000:  # 1만원~100만원 범위
                                        temp_prices.append({'price': price_num, 'currency': 'KRW'})
                                except:
                                    pass
                        if temp_prices:
                            write_debug_log(f"💰 가격 발견! {len(temp_prices)}개 (시도 #{attempt+1})")
                            found_prices = temp_prices
                            page_source = current_source
                            break
                        
                        previous_source = current_source
                        page_source = current_source  # 최신 소스 유지
                    
                    time.sleep(0.5)  # 0.5초마다 체크
                    
                except Exception as monitor_error:
                    write_debug_log(f"⚠️ 모니터링 중 오류 #{attempt+1}: {monitor_error}")
                    continue
            
            # 최종 결과 (모든 CID 테스트를 위해 바로 반환하지 않음)
            if found_prices:
                write_debug_log(f"✅ 실시간 모니터링 성공! {len(found_prices)}개 가격 발견")
                write_debug_log(f"📄 최종 페이지 소스: {len(page_source)} 문자")
                # 모든 CID를 테스트하기 위해 계속 진행
            else:
                write_debug_log(f"📄 최종 페이지 소스: {len(page_source)} 문자")
                write_debug_log("⚠️ 실시간 모니터링에서 가격을 찾지 못함")
            
        except Exception as agoda_error:
            write_debug_log(f"❌ 데스크톱 아고다 페이지 로딩 실패: {agoda_error}")
            
            # 네이버로 한국 사이트 테스트
            write_debug_log("🧪 네이버 테스트 시도...")
            try:
                driver.get("https://www.naver.com")
                naver_title = driver.title
                write_debug_log(f"✅ 네이버 테스트 성공: {naver_title}")
                write_debug_log("🔍 결론: 아고다만 접속 차단당하고 있습니다!")
            except Exception as naver_error:
                write_debug_log(f"❌ 네이버 테스트도 실패: {naver_error}")
                write_debug_log("🚨 모든 사이트 접속 불가 - Chrome 환경 문제!")
            
            # 빈 페이지 소스로 설정하여 다음 단계로 진행
            page_source = "<html><body>페이지 로딩 실패</body></html>"
            
        finally:
            write_debug_log("🔚 Chrome 드라이버 종료...")
            try:
                driver.quit()
                write_debug_log("✅ Chrome 드라이버 정상 종료")
                
                # 종료 후 프로세스 정리 확인
                time.sleep(1)
                try:
                    remaining_processes = subprocess.check_output(['pgrep', '-f', 'chrome']).decode().strip().split('\n')
                    remaining_count = len([p for p in remaining_processes if p.strip()])
                    write_debug_log(f"🔍 종료 후 남은 Chrome 프로세스: {remaining_count}개")
                    
                    # 프로세스가 남아있으면 강제 종료
                    if remaining_count > 10:
                        write_debug_log("🚨 과도한 프로세스 발견 - 추가 정리 실행")
                        subprocess.run(['pkill', '-9', '-f', 'chrome'], check=False)
                        time.sleep(1)
                except:
                    pass
                    
            except Exception as quit_error:
                write_debug_log(f"⚠️ Chrome 드라이버 종료 중 오류: {quit_error}")
                # 강제 종료
                try:
                    subprocess.run(['pkill', '-9', '-f', 'chrome'], check=False)
                    write_debug_log("🔨 Chrome 프로세스 강제 종료 완료")
                except:
                    pass
        
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