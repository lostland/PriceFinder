import os
import logging
from urllib.parse import urlparse, parse_qs
from flask import Flask, render_template, request, jsonify, Response, send_file
from werkzeug.middleware.proxy_fix import ProxyFix
from scraper import process_all_cids_sequential, start_progress_ticker
from flask import Flask
from scraper import print_file

logging.basicConfig(level=logging.INFO)

# 기준 가격을 저장하기 위한 전역 변수
global_base_price = None
global_base_price_cid_name = ''
global_page_title = ''
is_cancelled = False  # 분석 중단 플래그

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

logging.getLogger("werkzeug").setLevel(logging.WARNING)  # INFO 로그 숨김

def _start_ticker_once():
    # 개발 서버(reloader) 중복 실행 회피는 필요 시 추가
    start_progress_ticker(logger=app.logger)

@app.route('/')
def index():
    """Main page with URL input form"""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """Handle single CID scraping request"""
    try:
        # 중단 플래그 확인
        global is_cancelled

        app.logger.info(f"is_cancelled: {is_cancelled}")

        data = request.get_json()
        url = data.get('url', '').strip()
        step = data.get('step', 0)

        # 새 시작은 언제나 취소 플래그 무시하고 초기화
        if step == 0:
            is_cancelled = False
            app.logger.info("새로운 분석 시작 - 중단 플래그 초기화")
        else:
            # 진행 중 단계에서만 취소 반영
            if is_cancelled:
                is_cancelled = False
                return jsonify({'status': 'cancelled', 'message': '분석이 중단되었습니다.'}), 200

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
            ('1807747', 'VIO'),
            ('1838029', '호텔스컴바인'),
            ('1928503', 'BluePillow'),
            ('1729890', '네이버'),
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
            ('1917334', '토스'),
            ('1783115', '삼성카드'),
            ('1827579', '농협카드'),
            ('1917349', '트레블월렛'),
            ('1845157', '페이코'),
            ('1889319', '비자'),
            ('1889572', '마스터카드'),
            ('1801110', '유니온페이')
        ]

        # 모든 CID를 합친 리스트
        all_cids = search_cids + card_cids

        # 유효한 단계인지 확인 (step 0는 기준가격만 설정)
        if step >= len(all_cids) + 1:
            return jsonify({'error': '모든 CID 처리가 완료되었습니다'}), 400

        # step이 0이면 기준가격만 설정, 1 이상이면 실제 CID 처리
        if step == 0:
            current_cid, current_name = None, "기준가격 설정"
        else:
            current_cid, current_name = all_cids[step - 1]  # step 1: all_cids[0], step 2: all_cids[1] ...

        # URL에서 CID 교체하고 currencyCode 유지
        from scraper import extract_cid_from_url, scrape_prices_simple, reorder_url_parameters, set_progress, get_progress_state
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        import re

        # 원본 URL에서 currencyCode 추출
        original_currency = None
        currency_match = re.search(r'currencyCode=([^&]+)', url)
        if currency_match:
            original_currency = currency_match.group(1)

        original_cid = extract_cid_from_url(url)

        # step이 0이면 원본 URL 사용, 1 이상이면 CID 교체
        if step == 0:
            new_url = url  # 원본 URL 그대로 사용
        else:
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
        #app.logger.info(f"재정렬 전 URL: {new_url}")
        new_url = reorder_url_parameters(new_url)
        #app.logger.info(f"재정렬 후 URL: {new_url}")

        # 진행 단계 정보
        if step == 0:
            is_search_phase = False  # 기준가격은 검색창 리스트에 표시하지 않음
            phase_name = "기준가격 설정"
        else:
            is_search_phase = step <= len(search_cids)  # step 1부터 search_cids 처리
            phase_name = "검색창리스트" if is_search_phase else "카드리스트"

        app.logger.info(f"Processing 스텝 {step+1}/{len(all_cids) + 1}: CID {current_name}({current_cid})")

        # 기준 가격 계산 (첫 번째 스텝에서 원본 URL의 CID 가격을 기준으로 설정)
        global global_base_price, global_base_price_cid_name, global_page_title

        print_file(f"Processing 스텝 {step+1}/{len(all_cids) + 1}: CID {current_name}({current_cid})")

        if step == 0:
            # 첫 번째 스텝에서는 전역 변수 초기화
            global_base_price = None
            global_base_price_cid_name = ''
            # 원본 URL의 CID로 기준 가격 추출
            if original_cid:
                # 원본 URL에 CID가 있으면 그것으로 기준 가격 추출
                base_url = url  # 원본 URL 사용
                # 원본 CID의 이름 찾기
                for cid_value, cid_name in all_cids:
                    if cid_value == original_cid:
                        global_base_price_cid_name = cid_name
                        break
                if not global_base_price_cid_name:
                    global_base_price_cid_name = f'원본 CID({original_cid})'
            else:
                # CID가 없으면 첫 번째 CID(시크릿창)로 기준 설정
                base_url = new_url
                global_base_price_cid_name = current_name

            base_url_new = reorder_url_parameters(base_url)

            from scraper import set_progress
            set_progress(0, f"{current_name} 시작")

            # 기준 가격 스크래핑
            import time
            start_time = time.time()
            #time.sleep(1)

            print_file(f"기준 가격 스크래핑 시작: {base_url_new}")
            
            base_resp = scrape_prices_simple(
                base_url_new,
                original_currency_code=original_currency,
                progress_cb=lambda pct, msg=None: set_progress(pct, f"기준가 {msg or ''}".strip())
            )

            global_page_title = base_resp.get('page_title', '')
            app.logger.info(f"page title : {global_page_title}")
            print_file(f"page title : {global_page_title}")

            
            base_prices = base_resp.get('prices', [])
            
            if base_prices:
                base_price_str = base_prices[0]['price']
                # 숫자만 추출하여 기준 가격 설정
                import re
                base_price_match = re.search(r'[\d,]+', base_price_str)
                if base_price_match:
                    global_base_price = int(base_price_match.group().replace(',', ''))
                    app.logger.info(f"기준 가격 설정: {base_price_str} ({global_base_price}) - {global_base_price_cid_name}")
                    print_file(f"기준 가격 설정: {base_price_str} ({global_base_price}) - {global_base_price_cid_name}")

        # step이 0이면 기준가격만 설정하고 바로 리턴
        if step == 0:
            progress = get_progress_state()
            result = {
                'step': step + 1,
                'total_steps': len(all_cids) + 1,  # step 0도 포함
                'cid': None,
                'cid_name': current_name,
                'url': new_url,
                'prices': [],
                'found_count': 0,
                'process_time': 0,
                'has_next': True,
                'next_step': 1,
                'is_search_phase': is_search_phase,
                'phase_name': phase_name,
                'search_phase_completed': False,
                'download_link': None,
                'download_filename': None,
                'base_price': global_base_price,
                'base_price_cid_name': global_base_price_cid_name,
                'current_price': None,
                'discount_percentage': None,
                'subprogress_pct': progress.get('pct', 100),
                'subprogress_msg': progress.get('msg', '기준가격 설정 완료'),
                'page_title': global_page_title
            }
            return jsonify(result)

        # 현재 CID 스크래핑 실행 (step 1 이상에서만)
        import time
        start_time = time.time()
        #time.sleep(1)
        print_file(f"현재 CID 스크래핑 시작: {new_url}")
        resp = scrape_prices_simple(
            new_url,
            original_currency_code=original_currency,
            progress_cb=lambda pct, msg=None: set_progress(pct, f"{current_name} {msg or ''}".strip())
        )
        # 실패 시 1회 재시도 그대로 유지
        if len(resp.get('prices', [])) == 0:
            resp = scrape_prices_simple(
                new_url,
                original_currency_code=original_currency,
                progress_cb=lambda pct, msg=None: set_progress(pct, f"{current_name} {msg or ''}".strip())
            )

        prices = resp.get('prices', [])
        global_page_title = resp.get('page_title', '')

        process_time = time.time() - start_time

        # 텍스트 파일 다운로드 링크 생성
        download_filename = f"page_text_cid_{current_cid}.txt"
        download_link = f"/download/{download_filename}"

        # 할인율 계산
        discount_percentage = None
        current_price = None

        print(f"global_base_price: {global_base_price}")
        print(f"prices: {prices}")
        if prices and global_base_price:
            current_price_str = prices[0]['price']
            # 숫자만 추출
            import re
            current_price_match = re.search(r'[\d,]+', current_price_str)
            print(f"current_price_match: {current_price_match}")
            if current_price_match:
                current_price = int(current_price_match.group().replace(',', ''))
                if current_price < global_base_price:
                    discount_percentage = round(((global_base_price - current_price) / global_base_price) * 100, 1)
                    app.logger.info(f"할인율: {discount_percentage}% (기준: {global_base_price}, 현재: {current_price})")
                elif current_price > global_base_price:
                    # 더 비싼 경우 음수로 표시 (예: -5%)
                    discount_percentage = round(((global_base_price - current_price) / global_base_price) * 100, 1)
                    app.logger.info(f"가격 상승: {discount_percentage}% (기준: {global_base_price}, 현재: {current_price})")
                else:
                    discount_percentage = 0

                print(f"discount_percentage: {discount_percentage}")

        progress = get_progress_state()

        print(f"progress: {progress}")
        print(f"step: {step}")
        print(f"len(all_cids): {len(all_cids)}")
                
        # 결과 반환
        result = {
            'step': step + 1,
            'total_steps': len(all_cids) + 1,  # step 0도 포함
            'cid': current_cid,
            'cid_name': current_name,
            'url': new_url,
            'prices': prices,
            'found_count': len(prices),
            'process_time': round(process_time, 1),
            'has_next': step + 1 <= len(all_cids),  # step이 len(all_cids)까지 가능
            'next_step': step + 1 if step + 1 <= len(all_cids) else None,
            'is_search_phase': is_search_phase,
            'phase_name': phase_name,
            'search_phase_completed': step == len(search_cids),  # step이 search_cids 길이와 같을 때 완료
            'download_link': download_link,
            'download_filename': download_filename,
            'base_price': global_base_price,
            'base_price_cid_name': global_base_price_cid_name,
            'current_price': current_price,
            'discount_percentage': discount_percentage,
            'subprogress_pct': progress.get('pct', 0),
            'subprogress_msg': progress.get('msg', ''),
            'page_title': global_page_title
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

@app.route('/progress', methods=['GET'])
def progress_state():
    from scraper import get_progress_state
    return jsonify(get_progress_state())

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

@app.route('/cancel', methods=['POST'])
def cancel_analysis():
    """분석 중단 요청 처리"""
    global is_cancelled
    is_cancelled = True
    app.logger.info("분석 중단 요청 받음")
    return jsonify({'status': 'cancelled', 'message': '분석이 중단되었습니다.'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)