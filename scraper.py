import re
from bs4 import BeautifulSoup
import logging
import requests
import time

def scrape_all_urls_batch(url_list):
    """
    배치 처리: Selenium 한 번만 시작해서 모든 URL 처리 (8개 CID 모두 완료)
    """
    driver = None
    try:
        logging.info(f"Starting batch processing for {len(url_list)} URLs")
        
        # 초고속 Selenium 설정 (한 번만)
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox') 
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--window-size=800,600')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        
        for i, url_info in enumerate(url_list):
            start_time = time.time()
            cid = url_info['cid']
            url = url_info['url']
            
            logging.info(f"Batch step {i+1}/{len(url_list)}: Processing CID {cid}")
            
            # 진행 상태 전송
            yield {'type': 'progress', 'step': i+1, 'total': len(url_list), 'cid': cid}
            
            try:
                # URL 로드 
                driver.get(url)
                time.sleep(0.4)  # 최소 대기 (가격 로딩 위함)
                
                # 페이지 소스 가져오기
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # 안정적인 가격 검색 (실제 가격 확보)
                prices_found = []
                seen_prices = set()
                text_content = soup.get_text()[:15000]  # 충분한 텍스트
                
                price_patterns = [
                    r'(USD\s*[\d,]+)',  # USD 가격
                    r'(\$[\d,]{2,})',   # 달러 가격  
                    r'([₩]\s*[\d,]{3,})', # 원화
                ]
                
                for pattern in price_patterns:
                    if len(prices_found) >= 3:
                        break
                    matches = re.finditer(pattern, text_content, re.IGNORECASE)
                    for match in list(matches)[:3]:
                        price_text = match.group(1).strip()
                        if price_text not in seen_prices and len(price_text) >= 4:
                            context = text_content[max(0, match.start()-40):match.end()+40][:100]
                            seen_prices.add(price_text)
                            prices_found.append({
                                'price': price_text,
                                'context': context.strip()
                            })
                            if len(prices_found) >= 3:
                                break
                
                processing_time = time.time() - start_time
                logging.info(f"✅ CID {cid}: Found {len(prices_found)} prices in {processing_time:.1f}s")
                
                # 결과 즉시 전송
                result = {
                    'cid': cid,
                    'url': url, 
                    'prices': prices_found,
                    'status': 'success' if prices_found else 'no_prices'
                }
                yield {'type': 'result', 'data': result}
                
            except Exception as e:
                logging.error(f"Error processing CID {cid}: {str(e)}")
                result = {
                    'cid': cid,
                    'url': url,
                    'prices': [],
                    'status': 'error',
                    'error': str(e)
                }
                yield {'type': 'result', 'data': result}
        
        # 완료 메시지
        total_processed = len(url_list)
        yield {'type': 'complete', 'total_results': total_processed, 'message': f'All {total_processed} CIDs processed'}
        
    except Exception as e:
        logging.error(f"Batch processing failed: {e}")
        yield {'type': 'error', 'message': str(e)}
    finally:
        if driver:
            try:
                driver.quit()
                logging.info("Driver closed successfully")
            except:
                pass

def scrape_prices(url):
    """
    Legacy function - kept for compatibility
    """
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