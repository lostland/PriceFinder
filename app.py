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
        
        # URL 파라미터를 지정된 순서로 재배치하고 CID 교체
        from scraper import extract_cid_from_url, scrape_prices_simple
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        import re
        
        # URL 파싱
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query, keep_blank_values=True)
        
        # 파라미터 값을 단일 값으로 변환 (parse_qs는 리스트를 반환하므로)
        params_dict = {}
        for key, value_list in params.items():
            params_dict[key] = value_list[0] if value_list else ''
        params = params_dict
        
        # 지정된 순서로 파라미터 재배치
        ordered_params = [
            'countryId', 'finalPriceView', 'isShowMobileAppPrice', 'numberOfBedrooms',
            'familyMode', 'adults', 'children', 'rooms', 'maxRooms', 'checkIn',
            'isCalendarCallout', 'childAges', 'numberOfGuest', 'missingChildAges',
            'travellerType', 'showReviewSubmissionEntry', 'currencyCode', 
            'isFreeOccSearch', 'los', 'searchrequestid', 'cid'
        ]
        
        # CID 교체
        params['cid'] = current_cid
        
        # 순서대로 파라미터 문자열 생성
        param_pairs = []
        for param_name in ordered_params:
            if param_name in params:
                value = params[param_name]
                param_pairs.append(f"{param_name}={value}")
        
        # URL 재구성
        new_query = '&'.join(param_pairs)
        new_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment
        ))
        
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
        
        # 텍스트 파일 다운로드 링크 생성
        download_filename = f"page_text_cid_{current_cid}.txt"
        download_link = f"/download/{download_filename}"
        
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
            'next_step': step + 1 if step + 1 < len(cid_values) else None,
            'download_link': download_link,  # 텍스트 파일 다운로드 링크
            'download_filename': download_filename
        }
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error in scraping: {str(e)}")
        return jsonify({
            'error': f'처리 실패: {str(e)}'
        }), 500

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)