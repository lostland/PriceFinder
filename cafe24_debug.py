#!/usr/bin/env python3
"""
Cafe24 가상서버용 독립 디버그 스크립트
- 이 파일을 가상서버에 업로드하고 python3 cafe24_debug.py 실행
"""
import os
import time
import sys
import platform

def main():
    print("🚀 Cafe24 가상서버 파일 시스템 진단")
    print("="*60)
    
    # 1. 환경 정보
    print("📊 1. 환경 정보:")
    print(f"   운영체제: {platform.system()} {platform.release()}")
    print(f"   Python: {sys.version}")
    print(f"   현재 경로: {os.getcwd()}")
    print(f"   실행 사용자: {os.getenv('USER', 'unknown')}")
    
    # 2. 권한 확인
    print("\n🔐 2. 권한 확인:")
    current_dir = os.getcwd()
    print(f"   읽기 권한: {os.access(current_dir, os.R_OK)}")
    print(f"   쓰기 권한: {os.access(current_dir, os.W_OK)}")
    print(f"   실행 권한: {os.access(current_dir, os.X_OK)}")
    
    # 3. downloads 디렉토리
    print("\n📁 3. downloads 디렉토리:")
    downloads_dir = 'downloads'
    
    if not os.path.exists(downloads_dir):
        try:
            os.makedirs(downloads_dir)
            print(f"   ✅ downloads 디렉토리 생성 성공")
        except Exception as e:
            print(f"   ❌ downloads 디렉토리 생성 실패: {e}")
            return False
    else:
        print(f"   ✅ downloads 디렉토리 이미 존재")
    
    print(f"   쓰기 권한: {os.access(downloads_dir, os.W_OK)}")
    
    # 4. 기본 파일 테스트
    print("\n✏️ 4. 기본 파일 생성 테스트:")
    test_results = []
    
    for i in range(3):
        try:
            test_file = os.path.join(downloads_dir, f"cafe24_test_{i}_{int(time.time())}.txt")
            test_content = f"Cafe24 테스트 파일 {i+1}\\n생성 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n"
            
            print(f"   테스트 {i+1}: {os.path.basename(test_file)}")
            
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            if os.path.exists(test_file):
                size = os.path.getsize(test_file)
                print(f"      ✅ 성공 ({size} bytes)")
                test_results.append(test_file)
            else:
                print(f"      ❌ 파일이 생성되지 않음")
                
        except Exception as e:
            print(f"      ❌ 오류: {e}")
    
    # 5. 아고다 스타일 파일 테스트
    print("\n🏷️ 5. 아고다 스타일 파일 테스트:")
    
    try:
        agoda_file = os.path.join(downloads_dir, f"page_text_cid_CAFE24TEST.txt")
        
        # 1단계: 헤더 생성
        print(f"   1단계: 헤더 생성")
        with open(agoda_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\\n")
            f.write("🔍 AGODA MAGIC PRICE - Cafe24 테스트\\n")
            f.write("="*80 + "\\n")
            f.write(f"📅 생성 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"🌐 테스트 URL: https://www.agoda.com/test?cid=CAFE24TEST\\n")
        
        if os.path.exists(agoda_file):
            print(f"      ✅ 1단계 성공")
        else:
            print(f"      ❌ 1단계 실패")
            return False
        
        # 2단계: 성능 정보 추가
        print(f"   2단계: 성능 정보 추가")
        with open(agoda_file, 'a', encoding='utf-8') as f:
            f.write(f"📊 원본 페이지 크기: 25,000 글자\\n")
            f.write(f"📝 텍스트 크기: 5,000 글자\\n")
            f.write(f"⚡ 로딩 시간: 15.5초\\n")
            f.write("✅ 2단계 완료\\n")
        
        print(f"      ✅ 2단계 성공")
        
        # 3단계: 가격 분석
        print(f"   3단계: 가격 분석 정보")
        with open(agoda_file, 'a', encoding='utf-8') as f:
            f.write(f"✅ 시작가 발견: ₩64,039\\n")
            f.write(f"💱 통화 기호 개수: ₩(25), $(2), ฿(0)\\n")
            f.write(f"🔢 큰 숫자 패턴: 15개 발견\\n")
            f.write("✅ 3단계 완료\\n")
        
        print(f"      ✅ 3단계 성공")
        
        # 4단계: 대량 텍스트
        print(f"   4단계: 대량 텍스트 추가")
        with open(agoda_file, 'a', encoding='utf-8') as f:
            f.write("="*80 + "\\n")
            f.write("📄 페이지 텍스트 내용\\n")
            f.write("="*80 + "\\n")
            
            # 대량 텍스트 시뮬레이션 (약 50KB)
            large_content = "시작가 ₩64,039 갤러리아 10 수쿰윗 바이 콤파스 호스피탈리티 Galleria 10 Sukhumvit by Compass Hospitality 한글 텍스트 테스트 " * 200
            f.write(large_content)
            f.write("\\n\\n✅ 4단계 완료: 대량 텍스트 추가됨")
        
        if os.path.exists(agoda_file):
            size = os.path.getsize(agoda_file)
            print(f"      ✅ 4단계 성공 ({size:,} bytes)")
            test_results.append(agoda_file)
        else:
            print(f"      ❌ 4단계 실패")
            
    except Exception as e:
        print(f"   ❌ 아고다 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. 파일 읽기 테스트
    print("\n📖 6. 파일 읽기 테스트:")
    for test_file in test_results:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"   ✅ {os.path.basename(test_file)}: {len(content)} 글자 읽기 성공")
        except Exception as e:
            print(f"   ❌ {os.path.basename(test_file)} 읽기 실패: {e}")
    
    # 7. 파일 목록 확인
    print("\n📂 7. downloads 폴더 내용:")
    try:
        files = os.listdir(downloads_dir)
        if files:
            print(f"   총 {len(files)}개 파일:")
            for i, filename in enumerate(files):
                file_path = os.path.join(downloads_dir, filename)
                file_size = os.path.getsize(file_path)
                print(f"   {i+1}. {filename} ({file_size:,} bytes)")
        else:
            print(f"   (파일 없음)")
    except Exception as e:
        print(f"   ❌ 목록 확인 실패: {e}")
    
    # 8. 정리
    print("\n🧹 8. 테스트 파일 정리:")
    for test_file in test_results:
        try:
            os.remove(test_file)
            print(f"   🗑️ {os.path.basename(test_file)} 삭제됨")
        except Exception as e:
            print(f"   ❌ {os.path.basename(test_file)} 삭제 실패: {e}")
    
    print("\n" + "="*60)
    print("🎯 진단 결과:")
    print("="*60)
    
    if len(test_results) > 0:
        print("✅ 파일 시스템 정상 작동")
        print("   → 스크래퍼 코드에서 문제를 찾아야 합니다")
        print("   → 더 자세한 로그를 위해 스크래퍼 디버그 모드를 켜세요")
    else:
        print("❌ 파일 시스템 문제 발견")
        print("   → Cafe24 서버 환경에 문제가 있습니다")
        print("   → 권한 설정이나 디스크 공간을 확인하세요")
    
    print("\n🔧 다음 단계:")
    print("1. 이 결과를 개발자에게 보고하세요")
    print("2. 웹에서 /debug-files 페이지도 확인해보세요")
    print("3. 스크래퍼에 더 자세한 로그를 추가하겠습니다")
    
    return True

if __name__ == "__main__":
    main()