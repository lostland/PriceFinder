#!/usr/bin/env python3
"""
Agoda 스크래퍼 파일 생성 디버그 도구
"""
import os
import time
import re

def debug_scraper_file_creation():
    """스크래퍼에서 파일 생성 문제를 직접 테스트"""
    
    print("="*60)
    print("🔍 Agoda 스크래퍼 파일 생성 디버그")
    print("="*60)
    
    # 가상의 스크래핑 데이터로 테스트
    test_url = "https://www.agoda.com/ko-kr/test?cid=DEBUG999"
    test_page_source = "가상 페이지 소스" * 1000  # 큰 페이지 시뮬레이션
    test_all_text = "시작가 ₩64,039 한글 텍스트 테스트 " * 500  # 큰 텍스트 시뮬레이션
    test_load_time = 15.5
    
    print(f"📊 테스트 데이터:")
    print(f"   URL: {test_url}")
    print(f"   페이지 크기: {len(test_page_source):,} 글자")
    print(f"   텍스트 크기: {len(test_all_text):,} 글자")
    print(f"   로딩 시간: {test_load_time}초")
    
    # 실제 스크래퍼 코드와 동일한 로직으로 테스트
    debug_filepath = None
    
    try:
        print(f"\n📝 1단계: 디렉토리 및 파일명 설정")
        
        # downloads 디렉토리 생성
        if not os.path.exists('downloads'):
            os.makedirs('downloads')
            print(f"   ✅ downloads 디렉토리 생성됨")
        else:
            print(f"   ✅ downloads 디렉토리 이미 존재")
        
        # CID 정보 추출
        cid_match = re.search(r'cid=([^&]+)', test_url)
        cid_value = cid_match.group(1) if cid_match else 'unknown'
        print(f"   🎯 CID 값: {cid_value}")
        
        # 파일명 생성
        filename = f"page_text_cid_{cid_value}.txt"
        debug_filepath = os.path.join('downloads', filename)
        print(f"   📁 파일 경로: {debug_filepath}")
        
        print(f"\n📝 2단계: 기본 파일 생성")
        
        # 1단계: 기본 헤더 파일 생성
        with open(debug_filepath, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("🔍 AGODA MAGIC PRICE - 상세 디버그 정보\n")
            f.write("="*80 + "\n")
            f.write(f"📅 스크래핑 일시: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"🌐 요청 URL: {test_url}\n")
            f.write(f"🎯 CID 값: {cid_value}\n")
            f.write("✅ 1단계 완료: 기본 파일 생성됨\n")
        
        # 파일 생성 확인
        if os.path.exists(debug_filepath):
            print(f"   ✅ 기본 파일 생성 성공")
        else:
            print(f"   ❌ 기본 파일 생성 실패")
            return False
        
        print(f"\n📝 3단계: 성능 정보 추가")
        
        # 2단계: 성능 정보 추가
        with open(debug_filepath, 'a', encoding='utf-8') as f:
            f.write(f"📊 원본 페이지 크기: {len(test_page_source):,} 글자\n")
            f.write(f"📝 텍스트 크기: {len(test_all_text):,} 글자\n")
            f.write(f"💾 파일 크기: {len(test_all_text.encode('utf-8')):,} bytes\n")
            f.write(f"⚡ 로딩 시간: {test_load_time:.2f}초\n")
            f.write("✅ 2단계 완료: 성능 정보 추가됨\n")
        
        print(f"   ✅ 성능 정보 추가 성공")
        
        print(f"\n📝 4단계: 가격 분석 정보 추가")
        
        # 3단계: 가격 분석 정보 추가
        with open(debug_filepath, 'a', encoding='utf-8') as f:
            # 시작가 검색 결과
            pattern = r'시작가\s*₩\s*(\d{1,3}(?:,\d{3})+)'
            match = re.search(pattern, test_all_text)
            if match:
                f.write(f"✅ 시작가 발견: ₩{match.group(1)}\n")
            else:
                f.write("❌ 시작가 패턴 실패\n")
            
            # 통화 정보 분석
            krw_count = len(re.findall(r'₩', test_all_text))
            usd_count = len(re.findall(r'\$', test_all_text))
            thb_count = len(re.findall(r'฿', test_all_text))
            f.write(f"💱 통화 기호 개수: ₩({krw_count}), $({usd_count}), ฿({thb_count})\n")
            
            # 숫자 패턴 분석
            price_numbers = re.findall(r'\d{1,3}(?:,\d{3})+', test_all_text)
            f.write(f"🔢 큰 숫자 패턴: {len(price_numbers)}개 발견\n")
            if price_numbers:
                f.write(f"    예시: {', '.join(price_numbers[:5])}\n")
            
            f.write("✅ 3단계 완료: 가격 분석 정보 추가됨\n")
        
        print(f"   ✅ 가격 분석 정보 추가 성공")
        
        print(f"\n📝 5단계: 전체 텍스트 내용 추가")
        
        # 4-5단계: 기술 정보 및 텍스트 내용 추가
        with open(debug_filepath, 'a', encoding='utf-8') as f:
            # 브라우저 정보
            f.write(f"🌐 Chrome 옵션: headless, no-images, 800x600\n")
            f.write(f"🚀 최적화: 이미지 차단, 플러그인 차단\n")
            f.write("✅ 4단계 완료: 기술 정보 추가됨\n")
            
            f.write("="*80 + "\n")
            f.write("📄 실제 페이지 텍스트 내용\n")
            f.write("="*80 + "\n\n")
            f.write(test_all_text)
            f.write("\n\n✅ 5단계 완료: 전체 텍스트 내용 추가됨")
        
        print(f"   ✅ 전체 텍스트 내용 추가 성공")
        
        # 최종 파일 확인
        if os.path.exists(debug_filepath):
            file_size = os.path.getsize(debug_filepath)
            print(f"\n🎉 최종 결과:")
            print(f"   ✅ 파일 생성 완료: {debug_filepath}")
            print(f"   📊 파일 크기: {file_size:,} bytes")
            
            # 파일 내용 미리보기
            with open(debug_filepath, 'r', encoding='utf-8') as f:
                preview = f.read(500)
                print(f"   📖 파일 내용 미리보기:")
                print(f"      {preview[:200]}...")
            
            return True
        else:
            print(f"\n❌ 최종 파일 확인 실패")
            return False
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_scraper_file_creation()