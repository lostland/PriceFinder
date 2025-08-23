import os
import logging
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from flask import Flask, render_template, request, jsonify, flash
from werkzeug.middleware.proxy_fix import ProxyFix
from scraper import scrape_prices

logging.basicConfig(level=logging.DEBUG)

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
    """Handle URL scraping request with multiple CID values"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL을 입력해주세요'}), 400
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        app.logger.info(f"Scraping URL: {url}")
        
        # 7개의 cid 값 리스트 (테스트를 위해 처음 3개만 사용)
        cid_values = [
            '1833981',
            '1917614', 
            '1829968'
            # '1908612',
            # '1922868',
            # '1776688',
            # '1729890'
        ]
        
        # URL 파싱하여 cid 파라미터 교체
        
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        # 원본 URL의 cid 값도 확인
        original_cid = query_params.get('cid', ['원본'])[0]
        
        results = []
        
        # 1. 먼저 원본 URL로 검색
        app.logger.info(f"Searching with original CID: {original_cid}")
        try:
            prices = scrape_prices(url)
            results.append({
                'cid': f"원본({original_cid})",
                'url': url,
                'prices': prices if prices else [],
                'status': 'success' if prices else 'no_prices'
            })
        except Exception as e:
            results.append({
                'cid': f"원본({original_cid})",
                'url': url,
                'prices': [],
                'status': 'error',
                'error': str(e)
            })
        
        # 2. 각 cid 값으로 URL 생성하고 검색
        for cid_value in cid_values:
            app.logger.info(f"Searching with CID: {cid_value}")
            
            # cid 파라미터 교체
            query_params_copy = query_params.copy()
            query_params_copy['cid'] = [cid_value]
            new_query = urlencode(query_params_copy, doseq=True)
            new_url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))
            
            try:
                prices = scrape_prices(new_url)
                results.append({
                    'cid': cid_value,
                    'url': new_url,
                    'prices': prices if prices else [],
                    'status': 'success' if prices else 'no_prices'
                })
            except Exception as e:
                results.append({
                    'cid': cid_value,
                    'url': new_url,
                    'prices': [],
                    'status': 'error',
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'total_results': len(results),
            'original_url': url
        })
        
    except Exception as e:
        app.logger.error(f"Error scraping URL: {str(e)}")
        return jsonify({
            'error': f'웹사이트 분석 실패: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
