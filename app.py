import os
import logging
from urllib.parse import urlparse, parse_qs
from flask import Flask, render_template, request, jsonify, Response, send_file
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
        
        # [검색창리스트] CID 값들
        search_cids = [
            ('-1', '시크릿창'),
            ('1829968', '구글지도A'),
            ('1917614', '구글지도B'),
            ('1833981', '구글지도C'),
            ('1776688', '구글 검색A'),
            ('1922868', '구글 검색B'),
            ('1908612', '구글 검색C'),
            ('1729890', '네이버 검색'),
            ('1587497', 'TripAdvisor')
        ]
        
        # [카드리스트] CID 값들
        card_cids = [
            ('1942636', '카카오페이'),
            ('1895693', '현대카드'),
            ('1563295', '국민카드'),
            ('1654104', '우리카드'),
            ('1748498', 'BC카드'),
            ('1760133', '신한카드'),
            ('1729471', '하나카드'),
            ('1917334', '토스')
        ]
        
        # 모든 CID를 합친 리스트
        all_cids = search_cids + card_cids
        
        # 유효한 단계인지 확인
        if step >= len(all_cids):
            return jsonify({'error': '모든 CID 처리가 완료되었습니다'}), 400
        
        current_cid, current_name = all_cids[step]
        
        # URL에서 CID 교체하고 currencyCode 유지
        from scraper import extract_cid_from_url, scrape_prices_simple, reorder_url_parameters
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        import re
        
        # 원본 URL에서 currencyCode 추출
        original_currency = None
        currency_match = re.search(r'currencyCode=([^&]+)', url)
        if currency_match:
            original_currency = currency_match.group(1)
        
        original_cid = extract_cid_from_url(url)
        if original_cid:
            new_url = url.replace(f"cid={original_cid}", f"cid={current_cid}")
        else:
            separator = "&" if "?" in url else "?"
            new_url = f"{url}{separator}cid={current_cid}"
        
        # currencyCode가 바뀌었다면 원본으로 복원
        if original_currency:
            # 현재 URL의 currencyCode 찾아서 교체
            current_currency_match = re.search(r'currencyCode=([^&]+)', new_url)
            if current_currency_match:
                current_currency = current_currency_match.group(1)
                if current_currency != original_currency:
                    new_url = new_url.replace(f"currencyCode={current_currency}", f"currencyCode={original_currency}")
                    app.logger.info(f"CurrencyCode 복원: {current_currency} → {original_currency}")
            else:
                # currencyCode가 없으면 추가
                separator = "&" if "?" in new_url else "?"
                new_url = f"{new_url}{separator}currencyCode={original_currency}"
                app.logger.info(f"CurrencyCode 추가: {original_currency}")
        
        # URL 파라메터를 지정된 순서로 재정렬
        app.logger.info(f"재정렬 전 URL: {new_url}")
        new_url = reorder_url_parameters(new_url)
        app.logger.info(f"재정렬 후 URL: {new_url}")
        
        # 진행 단계 정보
        is_search_phase = step < len(search_cids)
        phase_name = "검색창리스트" if is_search_phase else "카드리스트"
        
        app.logger.info(f"Processing step {step+1}/{len(all_cids)}: CID {current_name}({current_cid})")
        
        # 스크래핑 실행 (원본 currencyCode 전달)
        import time
        start_time = time.time()
        prices = scrape_prices_simple(new_url, original_currency_code=original_currency)
        process_time = time.time() - start_time
        
        # 첫번째 CID에서 가격을 찾지 못한 경우 - 잘못된 링크로 판단
        if step == 0 and len(prices) == 0:
            app.logger.warning(f"First CID parsing failed - no prices found: {new_url}")
            return jsonify({
                'error': '잘못된 링크를 입력한 것 같습니다\n사용법을 확인해 주세요',
                'error_type': 'invalid_link',
                'step': step
            }), 400
        
        # 텍스트 파일 다운로드 링크 생성
        download_filename = f"page_text_cid_{current_cid}.txt"
        download_link = f"/download/{download_filename}"
        
        # 결과 반환
        result = {
            'step': step + 1,
            'total_steps': len(all_cids),
            'cid': current_cid,
            'cid_name': current_name,
            'url': new_url,
            'prices': prices,
            'found_count': len(prices),
            'process_time': round(process_time, 1),
            'has_next': step + 1 < len(all_cids),
            'next_step': step + 1 if step + 1 < len(all_cids) else None,
            'is_search_phase': is_search_phase,
            'phase_name': phase_name,
            'search_phase_completed': step + 1 == len(search_cids),
            'download_link': download_link,
            'download_filename': download_filename
        }
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error in scraping: {str(e)}")
        return jsonify({
            'error': f'처리 실패: {str(e)}'
        }), 500

@app.route('/guide')
def guide():
    """사용방법 가이드 페이지"""
    lang = request.args.get('lang', 'ko')  # 기본값은 한국어
    return render_template('guide.html', lang=lang)

@app.route('/download/<filename>')
def download_file(filename):
    """텍스트 파일 다운로드 엔드포인트"""
    try:
        import os
        file_path = os.path.join('downloads', filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': '파일을 찾을 수 없습니다'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain; charset=utf-8'
        )
        
    except Exception as e:
        app.logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': f'다운로드 실패: {str(e)}'}), 500

@app.route('/test')
def test_page():
    """테스트 페이지 라우트"""
    return send_file('static/pages/test.html')

@app.route('/info')
def info_page():
    """정보 페이지 라우트"""
    return send_file('static/pages/info.html')

@app.route('/split')
def split_view_page():
    """분할 뷰 페이지 라우트"""
    return send_file('static/pages/split_view.html')

@app.route('/status')
def status_page():
    """시스템 상태 페이지"""
    import platform
    import sys
    import os
    
    status_info = {
        'app_status': 'Running',
        'python_version': sys.version,
        'platform': platform.platform(),
        'server_port': '8000 (프록시 연결)',
        'domain': 'https://agodamagic.cafe24.com',
        'static_pages': [
            '/test - 테스트 페이지',
            '/info - 정보 페이지',
            '/split - 분할 뷰 페이지', 
            '/status - 상태 페이지',
            '/static/pages/test.html - 직접 접근',
            '/static/pages/info.html - 직접 접근',
            '/static/pages/split_view.html - 직접 접근'
        ]
    }
    
    # 간단한 HTML 응답
    html = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>시스템 상태 - agoda-magic-price</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%); min-height: 100vh; color: white; }}
            .card {{ background: rgba(255,255,255,0.1); border: none; border-radius: 15px; }}
            .btn-custom {{ background: linear-gradient(45deg, #4299e1, #3182ce); border: none; color: white; }}
        </style>
    </head>
    <body>
        <div class="container py-5">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-body p-5">
                            <h1 class="text-center mb-4">⚙️ 시스템 상태</h1>
                            <div class="row">
                                <div class="col-md-6">
                                    <h5>📊 앱 상태</h5>
                                    <p>✅ {status_info['app_status']}</p>
                                    <h5>🌐 접속 정보</h5>
                                    <p>도메인: {status_info['domain']}</p>
                                    <p>포트: {status_info['server_port']}</p>
                                </div>
                                <div class="col-md-6">
                                    <h5>🖥️ 시스템 정보</h5>
                                    <p>Python: {status_info['python_version'].split()[0]}</p>
                                    <p>OS: {status_info['platform']}</p>
                                </div>
                            </div>
                            <div class="mt-4">
                                <h5>📄 사용 가능한 페이지</h5>
                                <ul class="list-unstyled">
                                    {''.join(f'<li>• {page}</li>' for page in status_info['static_pages'])}
                                </ul>
                            </div>
                            <div class="text-center mt-4">
                                <a href="/" class="btn btn-custom me-2">메인 페이지</a>
                                <a href="/test" class="btn btn-custom me-2">테스트 페이지</a>
                                <a href="/info" class="btn btn-custom me-2">정보 페이지</a>
                                <a href="/split" class="btn btn-custom">분할 뷰</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)