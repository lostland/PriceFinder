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
        
        # 7개의 cid 값 리스트 (전체 활성화)
        cid_values = [
            '1833981',
            '1917614', 
            '1829968',
            '1908612',
            '1922868',
            '1776688',
            '1729890'
        ]
        
        # URL 파싱하여 cid 파라미터 교체
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        # 원본 URL의 cid 값도 확인
        original_cid = query_params.get('cid', ['원본'])[0]
        
        results = []
        
        # 순차적 검색 시작: 원본 URL + 7개 CID를 모두 처리
        all_urls_to_check = [
            {'cid': f"원본({original_cid})", 'url': url}
        ]
        
        # 각 CID별 URL 생성
        for cid_value in cid_values:
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
            all_urls_to_check.append({'cid': cid_value, 'url': new_url})
        
        def generate_streaming_results():
            """스트리밍으로 결과를 하나씩 전송 - 배치 처리 방식"""
            import json
            from scraper import scrape_all_urls_batch
            
            # 시작 메시지
            yield f"data: {json.dumps({'type': 'start', 'total_cids': len(all_urls_to_check)})}\n\n"
            
            try:
                # 모든 URL을 한 번에 배치 처리 (Selenium 1번만 사용)
                for result in scrape_all_urls_batch(all_urls_to_check):
                    yield f"data: {json.dumps(result)}\n\n"
                    
            except Exception as e:
                app.logger.error(f"Batch processing error: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        # 스트리밍 응답 반환
        from flask import Response
        return Response(
            generate_streaming_results(),
            mimetype='text/plain',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Content-Type': 'text/plain; charset=utf-8'
            }
        )
        
    except Exception as e:
        app.logger.error(f"Error scraping URL: {str(e)}")
        return jsonify({
            'error': f'웹사이트 분석 실패: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
