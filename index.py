#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import cgitb

# CGI 오류 디버깅 활성화
cgitb.enable()

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 환경변수 설정
os.environ['SESSION_SECRET'] = 'cafe24-default-secret-key-change-this'

from app import app

# CGI로 실행
if __name__ == '__main__':
    from wsgiref.handlers import CGIHandler
    CGIHandler().run(app)