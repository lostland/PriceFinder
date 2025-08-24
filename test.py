#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 간단한 테스트용 CGI 스크립트
print("Content-Type: text/html; charset=utf-8")
print()

import sys
import os

print("""
<html>
<head>
    <title>Cafe24 Python 테스트</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .info { background: #f0f0f0; padding: 10px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>🐍 Cafe24 Python CGI 테스트</h1>
""")

print(f"<div class='info'><strong>Python 버전:</strong> {sys.version}</div>")
print(f"<div class='info'><strong>Python 경로:</strong> {sys.executable}</div>")
print(f"<div class='info'><strong>현재 디렉터리:</strong> {os.getcwd()}</div>")
print(f"<div class='info'><strong>스크립트 경로:</strong> {os.path.abspath(__file__)}</div>")

# 모듈 가용성 체크
modules_to_check = ['flask', 'requests', 'bs4']
print("<h2>📦 설치된 모듈 확인</h2>")

for module in modules_to_check:
    try:
        __import__(module)
        print(f"<div class='info' style='color: green;'>✅ {module} - 설치됨</div>")
    except ImportError:
        print(f"<div class='info' style='color: red;'>❌ {module} - 설치 필요</div>")

# 환경변수 확인
print("<h2>🔧 환경변수</h2>")
env_vars = ['REQUEST_METHOD', 'QUERY_STRING', 'CONTENT_TYPE', 'SERVER_SOFTWARE']
for var in env_vars:
    value = os.environ.get(var, '(없음)')
    print(f"<div class='info'><strong>{var}:</strong> {value}</div>")

print("""
    <h2>✅ 테스트 완료</h2>
    <p>이 페이지가 보인다면 Python CGI가 정상 작동합니다!</p>
</body>
</html>
""")