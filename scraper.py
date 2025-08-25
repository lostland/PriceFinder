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
        chrome_options.add_argument('--window-size=320,240')  # 더더욱 작은 창  
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
        
        try:
            # 페이지 로딩 시작
            driver.get(url)
            
            # 💡 10KB 제한: 페이지 소스가 10KB 넘으면 바로 중단
            max_wait = 10  # 최대 10초 대기
            start_wait = time.time()
            
            while time.time() - start_wait < max_wait:
                current_source = driver.page_source
                if len(current_source.encode('utf-8')) >= 10 * 1024:  # 10KB
                    print("📏 10KB 도달 - 로딩 중단")
                    break
                time.sleep(0.2)  # 0.2초마다 체크
            
            page_source = driver.page_source
            
        except:
            # 타임아웃되어도 현재까지 로딩된 소스라도 가져오기
            page_source = driver.page_source
        finally:
            driver.quit()
        
        load_time = time.time() - start_time
        print(f"✅ 페이지 로딩 완료: {load_time:.2f}초")
        
        # BeautifulSoup으로 파싱
        soup = BeautifulSoup(page_source, 'html.parser')
        all_text = soup.get_text()
        
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
        
        # 파일 저장 (항상 저장)
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
                f.write(f"파일 크기: {len(all_text.encode('utf-8'))} bytes\n")
                f.write("="*50 + "\n\n")
                f.write(all_text)
                
            print(f"파일 저장됨: {filepath}")
        except:
            pass
        
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
