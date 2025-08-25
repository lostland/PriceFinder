#!/usr/bin/env python3
"""
가상서버 파일 시스템 디버그 도구
"""
import os
import time
import sys
import platform
# import psutil  # 가상서버에 없을 수 있음

def debug_file_system():
    """파일 시스템 문제를 단계별로 진단"""
    
    print("="*60)
    print("🔍 가상서버 파일 시스템 디버그 시작")
    print("="*60)
    
    # 1. 시스템 정보 확인
    print("\n📊 1. 시스템 정보:")
    print(f"   운영체제: {platform.system()} {platform.release()}")
    print(f"   Python: {sys.version}")
    print(f"   현재 경로: {os.getcwd()}")
    print(f"   사용자: {os.getenv('USER', 'unknown')}")
    
    # 2. 기본 시스템 확인 (psutil 없이)
    print("\n💾 2. 기본 시스템 상태:")
    try:
        # 디스크 여유 공간 확인 (statvfs 사용)
        import statvfs
        stat = os.statvfs('/')
        free_space = stat.f_bavail * stat.f_frsize
        print(f"   디스크 여유 공간: {free_space // (1024*1024*1024)} GB")
    except:
        # 간단한 df 명령어로 확인
        import subprocess
        try:
            result = subprocess.run(['df', '-h', '.'], capture_output=True, text=True)
            print(f"   디스크 상태: {result.stdout.strip()}")
        except:
            print(f"   ⚠️ 디스크 상태 확인 불가")
    
    # 3. 현재 디렉토리 권한 확인
    print("\n🔐 3. 파일 권한 테스트:")
    current_dir = os.getcwd()
    print(f"   현재 디렉토리: {current_dir}")
    print(f"   읽기 권한: {os.access(current_dir, os.R_OK)}")
    print(f"   쓰기 권한: {os.access(current_dir, os.W_OK)}")
    print(f"   실행 권한: {os.access(current_dir, os.X_OK)}")
    
    # 4. downloads 디렉토리 테스트
    print("\n📁 4. downloads 디렉토리 테스트:")
    downloads_dir = os.path.join(current_dir, 'downloads')
    
    try:
        if not os.path.exists(downloads_dir):
            print(f"   📂 downloads 디렉토리 생성 시도...")
            os.makedirs(downloads_dir)
            print(f"   ✅ downloads 디렉토리 생성 성공")
        else:
            print(f"   ✅ downloads 디렉토리 이미 존재")
            
        print(f"   읽기 권한: {os.access(downloads_dir, os.R_OK)}")
        print(f"   쓰기 권한: {os.access(downloads_dir, os.W_OK)}")
        
    except Exception as e:
        print(f"   ❌ downloads 디렉토리 생성 실패: {e}")
        return False
    
    # 5. 간단한 파일 쓰기 테스트
    print("\n✏️ 5. 파일 쓰기 테스트:")
    test_files = []
    
    for i in range(3):
        try:
            test_filename = f"test_file_{i}_{int(time.time())}.txt"
            test_filepath = os.path.join(downloads_dir, test_filename)
            
            print(f"   테스트 {i+1}: {test_filename}")
            
            # 파일 쓰기
            with open(test_filepath, 'w', encoding='utf-8') as f:
                f.write(f"테스트 파일 {i+1}\n")
                f.write(f"생성 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("한글 텍스트 테스트 ₩12,345\n")
            
            # 파일 확인
            if os.path.exists(test_filepath):
                file_size = os.path.getsize(test_filepath)
                print(f"      ✅ 생성 성공 ({file_size} bytes)")
                test_files.append(test_filepath)
            else:
                print(f"      ❌ 파일이 생성되지 않음")
                
        except Exception as e:
            print(f"      ❌ 쓰기 실패: {e}")
    
    # 6. 파일 읽기 테스트
    print("\n📖 6. 파일 읽기 테스트:")
    for filepath in test_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"   ✅ {os.path.basename(filepath)}: {len(content)} 글자 읽기 성공")
        except Exception as e:
            print(f"   ❌ {os.path.basename(filepath)} 읽기 실패: {e}")
    
    # 7. 대용량 파일 테스트
    print("\n💾 7. 대용량 파일 테스트:")
    try:
        large_filename = f"large_test_{int(time.time())}.txt"
        large_filepath = os.path.join(downloads_dir, large_filename)
        
        print(f"   50KB 파일 생성 테스트...")
        with open(large_filepath, 'w', encoding='utf-8') as f:
            # 50KB 정도의 텍스트 생성
            test_content = "한글 테스트 텍스트 ₩12,345 " * 1000
            f.write(test_content)
        
        if os.path.exists(large_filepath):
            file_size = os.path.getsize(large_filepath)
            print(f"   ✅ 대용량 파일 생성 성공 ({file_size:,} bytes)")
            test_files.append(large_filepath)
        else:
            print(f"   ❌ 대용량 파일 생성 실패")
            
    except Exception as e:
        print(f"   ❌ 대용량 파일 테스트 실패: {e}")
    
    # 8. 정리
    print("\n🧹 8. 테스트 파일 정리:")
    for filepath in test_files:
        try:
            os.remove(filepath)
            print(f"   🗑️ {os.path.basename(filepath)} 삭제됨")
        except Exception as e:
            print(f"   ❌ {os.path.basename(filepath)} 삭제 실패: {e}")
    
    print("\n" + "="*60)
    print("🎯 디버그 완료!")
    print("="*60)
    
    return True

if __name__ == "__main__":
    debug_file_system()