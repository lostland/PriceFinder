import os
import logging
from urllib.parse import urlparse, parse_qs
from flask import Flask, render_template, request, jsonify, Response
from werkzeug.middleware.proxy_fix import ProxyFix
from scraper import process_all_cids_sequential

logging.basicConfig(level=logging.INFO)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

@app.route('/')
def index():
    """Main page with URL input form"""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """Handle single CID scraping request"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        step = data.get('step', 0)  # 현재 단계 (0부터 시작)
        
        if not url:
            return jsonify({'error': 'URL을 입력해주세요'}), 400
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # 7개의 CID 값 리스트
        cid_values = [
            '1833981',  # 원본
            '1917614', 
            '1829968',
            '1908612',
            '1922868',
            '1776688',
            '1729890'
        ]
        
        # 유효한 단계인지 확인
        if step >= len(cid_values):
            return jsonify({'error': '모든 CID 처리가 완료되었습니다'}), 400
        
        current_cid = cid_values[step]
        
        # URL에서 CID 교체
        from scraper import extract_cid_from_url, scrape_prices_simple
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        original_cid = extract_cid_from_url(url)
        if original_cid:
            new_url = url.replace(f"cid={original_cid}", f"cid={current_cid}")
        else:
            separator = "&" if "?" in url else "?"
            new_url = f"{url}{separator}cid={current_cid}"
        
        # CID 라벨 생성
        if step == 0:
            cid_label = f"원본({current_cid})"
        else:
            cid_label = str(current_cid)
        
        app.logger.info(f"Processing step {step+1}/{len(cid_values)}: CID {cid_label}")
        
        # 스크래핑 실행
        import time
        start_time = time.time()
        prices = scrape_prices_simple(new_url)
        process_time = time.time() - start_time
        
        # 결과 반환
        result = {
            'step': step + 1,
            'total_steps': len(cid_values),
            'cid': cid_label,
            'url': new_url,
            'prices': prices,
            'found_count': len(prices),
            'process_time': round(process_time, 1),
            'has_next': step + 1 < len(cid_values),  # 다음 단계가 있는지
            'next_step': step + 1 if step + 1 < len(cid_values) else None
        }
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error in scraping: {str(e)}")
        return jsonify({
            'error': f'처리 실패: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)