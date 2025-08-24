#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 첫 번째로 헤더 출력 (CGI 필수)
print("Content-Type: text/html; charset=utf-8")
print()

# 프로젝트 경로 미리 설정
current_dir = os.path.dirname(os.path.abspath(__file__))

try:
    # 프로젝트 경로 추가
    sys.path.insert(0, current_dir)
    
    # 환경변수 설정
    os.environ['SESSION_SECRET'] = 'cafe24-secret-key-change-this'
    
    # Flask 앱 import 및 실행
    from app import app
    
    # CGI 환경에서 실행
    from wsgiref.handlers import CGIHandler
    CGIHandler().run(app)
    
except Exception as e:
    # 에러 발생시 HTML로 출력
    print(f"""
    <html>
    <head><title>에러</title></head>
    <body>
    <h2>실행 오류</h2>
    <p><strong>오류 내용:</strong> {str(e)}</p>
    <p><strong>Python 경로:</strong> {sys.executable}</p>
    <p><strong>현재 디렉터리:</strong> {current_dir}</p>
    <p><strong>Python 버전:</strong> {sys.version}</p>
    <hr>
    <p>Cafe24 호스팅에서 Python CGI 실행 중 문제가 발생했습니다.</p>
    </body>
    </html>
    """)