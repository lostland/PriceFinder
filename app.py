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
            """스트리밍으로 결과를 하나씩 전송"""
            import json
            
            # 시작 메시지
            yield f"data: {json.dumps({'type': 'start', 'total_cids': len(all_urls_to_check)})}\n\n"
            
            results = []
            # 순차적으로 하나씩 모든 CID를 검색
            for i, url_info in enumerate(all_urls_to_check):
                app.logger.info(f"Step {i+1}/{len(all_urls_to_check)}: Searching with CID: {url_info['cid']}")
                
                # 진행 상태 전송
                yield f"data: {json.dumps({'type': 'progress', 'step': i+1, 'total': len(all_urls_to_check), 'cid': url_info['cid']})}\n\n"
                
                try:
                    prices = scrape_prices(url_info['url'])
                    
                    result = {
                        'cid': url_info['cid'],
                        'url': url_info['url'],
                        'prices': prices if prices else [],
                        'status': 'success' if prices else 'no_prices'
                    }
                    
                    results.append(result)
                    
                    # 결과 즉시 전송
                    yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
                    
                    if prices:
                        app.logger.info(f"✅ Found {len(prices)} prices with CID: {url_info['cid']}")
                    else:
                        app.logger.info(f"❌ No prices found with CID: {url_info['cid']}")
                        
                except Exception as e:
                    app.logger.error(f"Error with CID {url_info['cid']}: {str(e)}")
                    result = {
                        'cid': url_info['cid'],
                        'url': url_info['url'],
                        'prices': [],
                        'status': 'error',
                        'error': str(e)
                    }
                    results.append(result)
                    
                    # 오류 결과도 즉시 전송
                    yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
            
            # 완료 메시지
            total_prices_found = sum(len(result.get('prices', [])) for result in results)
            yield f"data: {json.dumps({'type': 'complete', 'total_results': len(results), 'total_prices_found': total_prices_found})}\n\n"
        
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
