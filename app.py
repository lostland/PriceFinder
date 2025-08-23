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
    """Handle URL scraping request with sequential CID processing"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL을 입력해주세요'}), 400
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        app.logger.info(f"Starting sequential scraping for URL: {url}")
        
        # 7개의 CID 값 리스트 - 모든 CID 처리
        cid_values = [
            '1833981',  # 원본
            '1917614', 
            '1829968',
            '1908612',
            '1922868',
            '1776688',
            '1729890'
        ]
        
        def generate_streaming_results():
            """순차적 처리 결과를 실시간 스트리밍"""
            import json
            
            results = []
            total_prices_found = 0
            
            # 새로운 순차 처리 시스템 사용
            for stream_data in process_all_cids_sequential(url, cid_values):
                
                if stream_data['type'] == 'start':
                    yield f"data: {json.dumps(stream_data)}\n\n"
                
                elif stream_data['type'] == 'progress':
                    yield f"data: {json.dumps(stream_data)}\n\n"
                
                elif stream_data['type'] == 'result':
                    # 결과 데이터 포맷팅
                    result_data = {
                        'cid': stream_data['cid'],
                        'url': stream_data['url'],
                        'prices': stream_data['prices'],
                        'status': 'success' if stream_data['found_count'] > 0 else 'no_prices',
                        'process_time': stream_data.get('process_time', 0)
                    }
                    
                    results.append(result_data)
                    total_prices_found += stream_data['found_count']
                    
                    # 즉시 결과 전송
                    yield f"data: {json.dumps({'type': 'result', 'data': result_data})}\n\n"
                
                elif stream_data['type'] == 'error':
                    error_data = {
                        'cid': stream_data['cid'],
                        'url': url,
                        'prices': [],
                        'status': 'error',
                        'error': stream_data['error']
                    }
                    results.append(error_data)
                    
                    # 오류 결과 전송
                    yield f"data: {json.dumps({'type': 'result', 'data': error_data})}\n\n"
                
                elif stream_data['type'] == 'complete':
                    # 완료 메시지
                    completion_data = {
                        'type': 'complete', 
                        'total_results': len(results), 
                        'total_prices_found': total_prices_found
                    }
                    yield f"data: {json.dumps(completion_data)}\n\n"
        
        # 스트리밍 응답 반환
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
        app.logger.error(f"Error in scraping: {str(e)}")
        return jsonify({
            'error': f'처리 실패: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)