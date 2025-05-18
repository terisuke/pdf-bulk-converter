import os
import pytest
import uuid
import json
from datetime import datetime
from google.cloud import storage
from google.cloud.exceptions import NotFound
from app.core.config import get_settings

def test_upload_to_gcs():
    settings = get_settings()
    bucket_works = settings.gcs_bucket_works
    # テスト用の設定
    source_file = "./test.pdf"
    # 現在日時からセッションIDを生成（YYYYMMDD_HHMMSS形式）
    session_id = "test-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    job_id = str(uuid.uuid4())
    destination_blob_name = f"{session_id}/{job_id}/test.pdf"

    # サービスアカウントの認証情報を読み込む
    with open(settings.gcp_keypath, 'r') as f:
        credentials_info = json.load(f)

    # Google Cloud Storageクライアントの初期化（認証情報を直接渡す）
    storage_client = storage.Client.from_service_account_info(credentials_info)
    
    try:
        # バケットの存在確認
        bucket = storage_client.bucket(bucket_works)
        if not bucket.exists():
            pytest.skip(f"バケット {bucket_works} が存在しません。テストをスキップします。")

        # ファイルの存在確認
        if not os.path.exists(source_file):
            pytest.skip(f"ファイル {source_file} が存在しません。テストをスキップします。")

        # アップロード処理
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file)

        # アップロードの確認
        assert blob.exists(), "ファイルが正常にアップロードされませんでした。"

        # # テスト後のクリーンアップ
        blob.delete()
        assert not blob.exists(), "テストファイルの削除に失敗しました。"

    except Exception as e:
        pytest.fail(f"テスト中にエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    pytest.main([__file__]) 