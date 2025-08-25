#!/usr/bin/env python3
"""
가상서버용 초간단 파일 디버그 도구
"""
import os
import time

def simple_file_debug():
    """가장 기본적인 파일 생성 테스트"""
    
    print("🔍 가상서버 파일 생성 초간단 테스트")
    print("="*50)
    
    # 1. 현재 위치와 권한 확인
    current_dir = os.getcwd()
    print(f"📍 현재 위치: {current_dir}")
    print(f"✏️  쓰기 권한: {os.access(current_dir, os.W_OK)}")
    
    # 2. downloads 폴더 확인/생성
    downloads_dir = 'downloads'
    print(f"\n📁 downloads 폴더:")
    
    if not os.path.exists(downloads_dir):
        try:
            os.makedirs(downloads_dir)
            print(f"   ✅ 생성 성공")
        except Exception as e:
            print(f"   ❌ 생성 실패: {e}")
            return False
    else:
        print(f"   ✅ 이미 존재")
    
    print(f"   쓰기 권한: {os.access(downloads_dir, os.W_OK)}")
    
    # 3. 초간단 파일 쓰기 테스트
    test_file = os.path.join(downloads_dir, f"simple_test_{int(time.time())}.txt")
    print(f"\n✏️  파일 쓰기 테스트: {test_file}")
    
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("테스트\n")
        
        if os.path.exists(test_file):
            size = os.path.getsize(test_file)
            print(f"   ✅ 성공 ({size} bytes)")
            
            # 파일 읽기 테스트
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"   📖 읽기: '{content.strip()}'")
            
            # 파일 삭제
            os.remove(test_file)
            print(f"   🗑️  삭제 완료")
            return True
        else:
            print(f"   ❌ 파일이 생성되지 않음")
            return False
            
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return False

def test_agoda_file_creation():
    """실제 아고다 파일 생성 방식 테스트"""
    
    print(f"\n🏷️  아고다 방식 파일 생성 테스트")
    print("="*50)
    
    # CID 시뮬레이션
    test_cid = "TEST999"
    filename = f"page_text_cid_{test_cid}.txt"
    filepath = os.path.join('downloads', filename)
    
    print(f"📝 파일명: {filename}")
    print(f"📂 전체 경로: {filepath}")
    
    try:
        # 1단계: 기본 파일 생성
        print(f"\n1️⃣  1단계: 기본 생성")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("🔍 AGODA MAGIC PRICE - 테스트\n")
            f.write("="*80 + "\n")
            f.write(f"⏰ 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        if os.path.exists(filepath):
            print(f"   ✅ 1단계 성공")
        else:
            print(f"   ❌ 1단계 실패")
            return False
        
        # 2단계: 내용 추가
        print(f"\n2️⃣  2단계: 내용 추가")
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(f"📊 테스트 데이터 크기: 1000 글자\n")
            f.write(f"✅ 2단계 완료\n")
        
        # 3단계: 대량 텍스트 추가
        print(f"\n3️⃣  3단계: 대량 텍스트")
        with open(filepath, 'a', encoding='utf-8') as f:
            test_content = "시작가 ₩64,039 한글 테스트 " * 100
            f.write("="*80 + "\n")
            f.write("📄 테스트 내용\n")
            f.write("="*80 + "\n")
            f.write(test_content)
        
        # 최종 확인
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"   ✅ 3단계 성공 ({size:,} bytes)")
            
            # 내용 확인
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"   📄 총 라인 수: {len(lines)}")
                print(f"   📖 첫 줄: {lines[0].strip()}")
            
            return True
        else:
            print(f"   ❌ 3단계 실패")
            return False
            
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 가상서버 파일 시스템 디버그 시작\n")
    
    # 1. 기본 테스트
    basic_ok = simple_file_debug()
    
    # 2. 아고다 방식 테스트
    if basic_ok:
        agoda_ok = test_agoda_file_creation()
        
        if agoda_ok:
            print(f"\n🎉 모든 테스트 성공!")
            print(f"   가상서버에서도 파일 생성이 정상 작동해야 합니다.")
        else:
            print(f"\n⚠️  아고다 방식에서 문제 발생!")
    else:
        print(f"\n❌ 기본 파일 생성부터 실패!")
        print(f"   가상서버 파일 시스템에 문제가 있습니다.")