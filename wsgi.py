#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

# Cafe24에서 필요한 환경변수 설정
if not os.environ.get('SESSION_SECRET'):
    os.environ['SESSION_SECRET'] = 'cafe24-default-secret-key-change-this'

# CGI에서 실행할 수 있도록 application 객체 생성
application = app

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5000)