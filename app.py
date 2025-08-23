import os
import logging
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
    """Handle URL scraping request"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL을 입력해주세요'}), 400
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        app.logger.info(f"Scraping URL: {url}")
        
        # Scrape prices from the URL
        prices = scrape_prices(url)
        
        if not prices:
            return jsonify({
                'error': '이 페이지에서 호텔 방값 정보를 찾을 수 없습니다',
                'prices': []
            }), 404
        
        # Return top 5 prices
        top_prices = prices[:5]
        
        return jsonify({
            'success': True,
            'url': url,
            'prices': top_prices,
            'total_found': len(prices)
        })
        
    except Exception as e:
        app.logger.error(f"Error scraping URL: {str(e)}")
        return jsonify({
            'error': f'웹사이트 분석 실패: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
