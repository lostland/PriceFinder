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
        # 최적화된 Selenium 사용 - Agoda는 JavaScript 실행 필요
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-images')  # 이미지 차단
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-web-security')  # 웹 보안 해제로 속도 향상
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')  # 렌더링 최적화
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-features=NetworkService')  # 네트워크 최적화
        chrome_options.add_argument('--disable-ipc-flooding-protection')  # IPC 최적화
        chrome_options.add_argument('--window-size=1920,1080')  # 데스크탑 크기로 변경  
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--silent')
        chrome_options.add_argument('--no-zygote')  # 프로세스 최적화
        chrome_options.add_argument('--single-process')  # 단일 프로세스
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # 봇 감지 우회
        
        # 봇 탐지 우회 (간단하게)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        print(f"스크래핑 사용 URL: {url}")
        
        start_time = time.time()
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(6)  # 6초로 적당히 단축
        
        # 봇 탐지 우회 스크립트 (빠르게)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # 스크롤을 맨 위로 고정
        driver.execute_script("window.scrollTo(0, 0);")
        
        try:
            # 💡 JavaScript 실행을 위한 단계별 로딩
            print("🌐 페이지 로딩 시작...")
            driver.get(url)
            
            # 1단계: 1초 대기 (JavaScript 실행 시간 확보)
            print("⏳ JavaScript 실행을 위해 1초 대기...")
            time.sleep(1)
            
            # 1초 후 첫 번째 소스 확인
            initial_source = driver.page_source
            initial_text = BeautifulSoup(initial_source, 'html.parser').get_text()
            
            print(f"1초 후 텍스트 크기: {len(initial_text)} 글자")
            print(f"1초 후 텍스트 미리보기: {initial_text[:200]}...")
            
            # "시작가" 또는 "Start Price" 키워드 체크
            price_keyword_found = ('시작가' in initial_text or 'Start Price' in initial_text)
            
            if price_keyword_found:
                print("🎯 1초 후 가격 키워드 발견!")
                page_source = initial_source
            else:
                print("⏰ 가격 키워드 없음 - 추가 대기...")
                
                # 2단계: 최대 5초 더 대기하면서 매 1초마다 체크
                max_additional_wait = 5
                start_additional = time.time()
                
                while time.time() - start_additional < max_additional_wait:
                    time.sleep(1)
                    current_source = driver.page_source
                    current_text = BeautifulSoup(current_source, 'html.parser').get_text()
                    
                    elapsed = int(time.time() - start_additional)
                    print(f"⏰ +{elapsed}초 경과 - 텍스트 크기: {len(current_text)} 글자")
                    
                    # 키워드 체크
                    if '시작가' in current_text or 'Start Price' in current_text:
                        print("🎯 가격 키워드 발견 - 바로 추출 진행")
                        page_source = current_source
                        break
                        
                    # 10KB 넘으면 중단
                    if len(current_text.encode('utf-8')) >= 10 * 1024:
                        print("📏 10KB 도달 - 로딩 중단")
                        page_source = current_source
                        break
                        
                    page_source = current_source
                
                if time.time() - start_additional >= max_additional_wait:
                    print("⏰ 최대 대기 시간 도달")
            
            # 최종 소스 크기 제한 (10KB)
            final_text = BeautifulSoup(page_source, 'html.parser').get_text()
            if len(final_text.encode('utf-8')) > 10 * 1024:
                # HTML 소스 자체를 10KB로 제한
                page_source = page_source.encode('utf-8')[:10*1024].decode('utf-8', errors='ignore')
                print(f"📏 10KB로 소스 잘라내기 완료")
            
        except:
            # 타임아웃되어도 현재까지 로딩된 소스라도 가져오기
            page_source = driver.page_source
        finally:
            driver.quit()
        
        load_time = time.time() - start_time
        print(f"✅ 페이지 로딩 완료: {load_time:.2f}초")
        
        # BeautifulSoup으로 파싱
        parse_start = time.time()
        soup = BeautifulSoup(page_source, 'html.parser')
        parse_time = time.time() - parse_start
        
        # 🔍 디버깅: 전체 텍스트 추출 과정 기록
        debug_info = []
        debug_info.append(f"=== 텍스트 추출 디버그 정보 ===")
        debug_info.append(f"파싱 시간: {parse_time:.3f}초")
        debug_info.append(f"페이지 소스 크기: {len(page_source)} characters")
        debug_info.append(f"추출 시작 시간: {time.strftime('%H:%M:%S')}")
        debug_info.append(f"")
        
        # 📊 방법1: 전체 텍스트 (기본 방식)
        method1_start = time.time()
        all_text_full = soup.get_text()
        method1_time = time.time() - method1_start
        debug_info.append(f"방법1 - soup.get_text() 전체:")
        debug_info.append(f"  시간: {method1_time:.3f}초")
        debug_info.append(f"  크기: {len(all_text_full)} 글자")
        debug_info.append(f"  앞쪽 미리보기: {all_text_full[:200]}...")
        debug_info.append(f"")
        
        # 📊 방법2: body 태그만
        method2_start = time.time()
        body_tag = soup.find('body')
        if body_tag:
            body_text = body_tag.get_text()
            method2_time = time.time() - method2_start
            debug_info.append(f"방법2 - body.get_text():")
            debug_info.append(f"  시간: {method2_time:.3f}초")
            debug_info.append(f"  크기: {len(body_text)} 글자")
            debug_info.append(f"  앞쪽 미리보기: {body_text[:200]}...")
        else:
            body_text = ""
            debug_info.append(f"방법2 - body 태그 없음")
        debug_info.append(f"")
        
        # 📊 방법3: 상위 10개 div만
        method3_start = time.time()
        top_divs = soup.find_all('div')[:10]
        div_text = ""
        for i, div in enumerate(top_divs):
            div_content = div.get_text(strip=True)
            if div_content:
                div_text += f"[DIV{i+1}] {div_content}\n"
        method3_time = time.time() - method3_start
        debug_info.append(f"방법3 - 상위 10개 div:")
        debug_info.append(f"  시간: {method3_time:.3f}초")
        debug_info.append(f"  크기: {len(div_text)} 글자")
        debug_info.append(f"  앞쪽 미리보기: {div_text[:200]}...")
        debug_info.append(f"")
        
        # 📊 방법4: JavaScript로 화면에 보이는 텍스트만 추출 시도
        method4_start = time.time()
        try:
            visible_text = driver.execute_script("""
                // 화면에 보이는 텍스트만 추출
                var walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    {
                        acceptNode: function(node) {
                            var parent = node.parentElement;
                            var style = window.getComputedStyle(parent);
                            
                            // 숨겨진 요소는 제외
                            if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                                return NodeFilter.FILTER_REJECT;
                            }
                            
                            // 화면 영역 밖은 제외 (대략적으로)
                            var rect = parent.getBoundingClientRect();
                            if (rect.bottom < 0 || rect.top > window.innerHeight * 2) {
                                return NodeFilter.FILTER_REJECT;
                            }
                            
                            return NodeFilter.FILTER_ACCEPT;
                        }
                    }
                );
                
                var textNodes = [];
                var node;
                while (node = walker.nextNode()) {
                    if (node.nodeValue.trim()) {
                        textNodes.push(node.nodeValue.trim());
                    }
                }
                return textNodes.join(' ');
            """)
            method4_time = time.time() - method4_start
            debug_info.append(f"방법4 - JavaScript 화면 텍스트:")
            debug_info.append(f"  시간: {method4_time:.3f}초")
            debug_info.append(f"  크기: {len(visible_text)} 글자")
            debug_info.append(f"  앞쪽 미리보기: {visible_text[:200]}...")
        except Exception as js_error:
            visible_text = ""
            debug_info.append(f"방법4 - JavaScript 실패: {js_error}")
        debug_info.append(f"")
        
        # 🎯 최종 선택: 가장 적절한 텍스트 선택
        debug_info.append(f"=== 최종 선택 ===")
        
        if visible_text and len(visible_text) > 100:
            all_text = visible_text
            debug_info.append(f"선택: 방법4 - JavaScript 화면 텍스트")
        elif body_text and len(body_text) > 100:
            all_text = body_text[:10240]  # 첫 10KB만
            debug_info.append(f"선택: 방법2 - body 텍스트 (10KB 제한)")
        else:
            all_text = all_text_full[:10240]  # 첫 10KB만
            debug_info.append(f"선택: 방법1 - 전체 텍스트 (10KB 제한)")
        
        debug_info.append(f"최종 크기: {len(all_text)} 글자, {len(all_text.encode('utf-8'))} bytes")
        debug_info.append(f"=" * 50)
        
        print(f"페이지 크기: {len(all_text)} 글자, {len(all_text.encode('utf-8'))} bytes")
        
        # 🎯 단순화: "시작가" 또는 "Start Price"만 찾기
        patterns = [
            r'시작가\s*₩\s*(\d{1,3}(?:,\d{3})+)',  # 한국어 "시작가 ₩ 63,084"
            r'Start\s+Price\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # 영어 "Start Price $ 123.45"
            r'시작가\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # 한국어 "시작가 $ 123.45"
        ]
        
        found_price = None
        for pattern in patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                price_number = match.group(1)
                currency_symbol = "₩" if "₩" in pattern else "$"
                
                found_price = {
                    'price': f"{currency_symbol}{price_number}",
                    'context': match.group(0),  # 전체 매치된 텍스트
                    'source': 'start_price_simple'
                }
                print(f"✅ 가격 발견: {found_price['price']}")
                break
        
        # 파일 저장 (디버그 정보 포함)
        try:
            import os
            if not os.path.exists('downloads'):
                os.makedirs('downloads')
            
            cid_match = re.search(r'cid=([^&]+)', url)
            cid_value = cid_match.group(1) if cid_match else 'unknown'
            filename = f"page_text_cid_{cid_value}.txt"
            filepath = os.path.join('downloads', filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n")
                f.write(f"CID: {cid_value}\n")
                f.write(f"스크래핑 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"총 소요 시간: {load_time:.2f}초\n")
                f.write(f"파일 크기: {len(all_text.encode('utf-8'))} bytes\n")
                f.write("\n" + "\n".join(debug_info) + "\n\n")
                f.write("=== 실제 추출된 텍스트 ===\n")
                f.write(all_text)
                
            print(f"파일 저장됨: {filepath} (디버그 정보 포함)")
        except Exception as save_error:
            print(f"파일 저장 오류: {save_error}")
        
        # 결과 반환 (찾으면 반환, 못 찾으면 빈 리스트)
        if found_price:
            return [found_price]
        else:
            print("❌ 시작가/Start Price 없음 - 빈 결과 반환")
            return []

    except Exception as e:
        print(f"스크래핑 오류: {e}")
        return []


def process_all_cids_sequential(base_url, cid_list):
    """
    모든 CID를 순차적으로 처리하고 각 결과를 즉시 반환
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
            
            # 스크래핑 실행
            prices = scrape_prices_simple(new_url, 'USD')
            
            # 결과 반환
            yield {
                'type': 'progress',
                'step': i,
                'total_steps': total_cids,
                'cid': new_cid,
                'url': new_url,
                'prices': prices,
                'success': len(prices) > 0
            }
            
        except Exception as e:
            # 에러가 발생해도 진행 계속
            yield {
                'type': 'progress',
                'step': i,
                'total_steps': total_cids,
                'cid': new_cid,
                'url': new_url if 'new_url' in locals() else base_url,
                'prices': [],
                'success': False,
                'error': str(e)
            }
    
    # 완료 신호
    yield {
        'type': 'complete'
    }


def extract_cid_from_url(url):
    """URL에서 CID 파라미터 값을 추출"""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return params.get('cid', [None])[0]
    except:
        return None


def reorder_url_parameters(url):
    """URL의 파라미터들을 일관된 순서로 재정렬"""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        
        # 파라미터들을 알파벳 순서로 정렬
        sorted_params = []
        for key in sorted(params.keys()):
            for value in params[key]:
                sorted_params.append(f"{key}={value}")
        
        # 새로운 URL 구성
        new_query = "&".join(sorted_params)
        new_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
        
        return new_url
    except:
        return url  # 오류 시 원본 URL 반환
