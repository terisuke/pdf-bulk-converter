from app.core.config import get_settings
import uuid
import os
import shutil
from pathlib import Path
# from google.cloud import storage  # GCP環境で使用する場合はコメントを外す

settings = get_settings()

# ローカルストレージの初期化
if settings.environment == "local":
    os.makedirs(settings.local_storage_path, exist_ok=True)
    client = None
# else:
#     client = storage.Client()

def generate_session_url() -> tuple[str, str]:
    session_id = str(uuid.uuid4())
    if settings.environment == "local":
        session_dirpath = settings.get_session_dirpath(session_id)
        os.makedirs(session_dirpath, exist_ok=True)
        return f"/local-upload/{session_id}", session_id

def generate_upload_url(filename: str, session_id: str, content_type: str = "") -> tuple[str, str]:
    """署名付きアップロードURLを生成（ローカルモードでは一時的なアップロードパスを返す）"""
    job_id = str(uuid.uuid4())
    
    if settings.environment == "local":
        # ローカルモード: 一時的なアップロードパスを返す
        # ファイル名をURLエンコード
        from urllib.parse import quote
        encoded_filename = quote(filename)
        upload_path = os.path.join(settings.get_storage_path(session_id, job_id), filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        return f"/local-upload/{session_id}/{job_id}/{encoded_filename}", job_id
    # else:
    #     # クラウドモード: 署名付きURLを生成
    #     if not content_type:
    #         content_type = "application/pdf"  # デフォルトのcontent_type
    #     
    #     bucket = client.bucket(settings.bucket_raw)
    #     blob = bucket.blob(f"{job_id}/{filename}")
    #     
    #     url = blob.generate_signed_url(
    #         version="v4",
    #         expiration=settings.sign_url_exp,
    #         method="PUT",
    #         content_type=content_type
    #     )
    #     
    #     return url, job_id
    # 開発中はローカルモードのみ対応
    return f"/local-upload/{session_id}/{job_id}/{encoded_filename}", job_id

def generate_download_url(session_id: str) -> str:
    """署名付きダウンロードURLを生成（ローカルモードでは一時的なダウンロードパスを返す）"""
    if settings.environment == "local":
        # ローカルモード: 一時的なダウンロードパスを返す
        session_dirpath = settings.get_session_dirpath(session_id)
        zip_filename = f"{session_id}_images.zip"
        zip_path = os.path.join(session_dirpath, zip_filename)
        
        if not os.path.exists(zip_path):
            raise ValueError("ZIP file not found")
        
        # URLエンコードされたファイル名を使用
        from urllib.parse import quote
        encoded_filename = quote(zip_filename)
        return f"/local-download/{session_id}/{encoded_filename}"
    # else:
    #     # クラウドモード: 署名付きURLを生成
    #     bucket = client.bucket(settings.bucket_zip)
    #     blob = bucket.blob(f"{session_id}/output.zip")
    #     
    #     url = blob.generate_signed_url(
    #         version="v4",
    #         expiration=settings.sign_url_exp,
    #         method="GET"
    #     )
    #     
    #     return url
    # 開発中はローカルモードのみ対応

def cleanup_job(job_id: str):
    """ジョブ関連のファイルをクリーンアップ"""
    if settings.environment == "local":
        job_path = settings.get_storage_path(job_id)
        if os.path.exists(job_path):
            shutil.rmtree(job_path)
    # else:
    #     # クラウドモードのクリーンアップはCloud Storageのライフサイクルポリシーに任せる
    #     pass    