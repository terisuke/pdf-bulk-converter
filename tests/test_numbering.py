#!/usr/bin/env python3
"""
PDF Bulk Converter - 簡単な動作確認スクリプト

このスクリプトは連番ファイル名生成機能が正しく動作するかを確認するためのものです。
"""

import sys
from pathlib import Path

# プロジェクトのパスを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.session_status import SessionStatusManager, SessionStatus
from datetime import datetime

def test_sequential_numbering():
    """連番ファイル名生成のテスト"""
    print("=== 連番ファイル名生成テスト ===")
    
    # セッション状態管理のテスト
    manager = SessionStatusManager()
    test_session_id = "test_session_001"
    
    # テストケース1: 開始番号1
    print("\n1. 開始番号1からのテスト")
    start_number = 1
    status = SessionStatus(
        session_id=test_session_id,
        status="uploading",
        progress=0.0,
        created_at=datetime.now(),
        pdf_num=1,
        image_num=start_number,
        message="テスト用セッション"
    )
    manager.update_status(test_session_id, status)
    
    # 連番取得テスト
    for i in range(5):
        current_num = manager.get_imagenum(test_session_id)
        filename = f"{current_num:07d}.jpeg"
        print(f"  ページ{i+1}: {filename}")
        manager.add_imagenum(test_session_id, 1)
    
    # テストケース2: 開始番号100
    print("\n2. 開始番号100からのテスト")
    test_session_id2 = "test_session_002"
    start_number = 100
    status2 = SessionStatus(
        session_id=test_session_id2,
        status="uploading",
        progress=0.0,
        created_at=datetime.now(),
        pdf_num=1,
        image_num=start_number,
        message="テスト用セッション2"
    )
    manager.update_status(test_session_id2, status2)
    
    for i in range(5):
        current_num = manager.get_imagenum(test_session_id2)
        filename = f"{current_num:07d}.jpeg"
        print(f"  ページ{i+1}: {filename}")
        manager.add_imagenum(test_session_id2, 1)
    
    # テストケース3: 開始番号999995（7桁制限のテスト）
    print("\n3. 開始番号999995からのテスト（7桁制限）")
    test_session_id3 = "test_session_003"
    start_number = 999995
    status3 = SessionStatus(
        session_id=test_session_id3,
        status="uploading",
        progress=0.0,
        created_at=datetime.now(),
        pdf_num=1,
        image_num=start_number,
        message="テスト用セッション3"
    )
    manager.update_status(test_session_id3, status3)
    
    for i in range(5):
        current_num = manager.get_imagenum(test_session_id3)
        filename = f"{current_num:07d}.jpeg"
        print(f"  ページ{i+1}: {filename}")
        manager.add_imagenum(test_session_id3, 1)
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    test_sequential_numbering()
