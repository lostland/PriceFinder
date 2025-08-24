#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# CGI 헤더 출력
print("Content-Type: text/html; charset=utf-8")
print()

try:
    # 현재 디렉터리를 Python 경로에 추가
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # 환경변수 설정
    os.environ.setdefault('SESSION_SECRET', 'cafe24-flask-secret-key')
    
    # Flask 앱 임포트
    from app import app
    
    # WSGI를 CGI로 실행
    from wsgiref.handlers import CGIHandler
    handler = CGIHandler()
    handler.run(app)

except ImportError as e:
    print(f"""
    <html><head><title>Import Error</title></head><body>
    <h2>모듈 Import 오류</h2>
    <p>오류: {str(e)}</p>
    <p>Python 경로: {sys.path}</p>
    <p>필요한 패키지가 설치되지 않았을 수 있습니다.</p>
    <p>Cafe24 제어판에서 다음 패키지들을 설치해주세요:</p>
    <ul><li>flask</li><li>beautifulsoup4</li><li>requests</li></ul>
    </body></html>
    """)
except Exception as e:
    print(f"""
    <html><head><title>Runtime Error</title></head><body>
    <h2>실행 오류</h2>
    <p>오류: {str(e)}</p>
    <p>파일 경로: {current_dir}</p>
    <p>Python 버전: {sys.version}</p>
    </body></html>
    """)