from app.core.config import get_settings
import uuid
import os
import shutil
import logging
from pathlib import Path

try:  # google-cloud-storage is optional in local mode
    from google.cloud import storage
except ImportError:  # pragma: no cover - optional dependency
    storage = None
import json

settings = get_settings()

logger = logging.getLogger(__name__)

# ローカルストレージの初期化
if settings.gcp_region == "local":
    os.makedirs(settings.workspace_path, exist_ok=True)
    client = None
else:
    if storage is None:
        raise RuntimeError("google-cloud-storage package is required for cloud mode")
    try:
        with open(settings.gcp_keypath, "r") as f:
            credentials_info = json.load(f)
        client = storage.Client.from_service_account_info(credentials_info)
        logging.info(f"GCS client initialized for project: {client.project}")
    except FileNotFoundError as exc:
        logging.error(f"GCP key file not found: {settings.gcp_keypath}")
        raise FileNotFoundError(f"GCP key file not found: {settings.gcp_keypath}") from exc
    except Exception as e:
        logging.error(f"Failed to initialize GCS client: {str(e)}")
        raise RuntimeError(f"Failed to initialize GCS client: {str(e)}") from e

def generate_session_url() -> tuple[str, str]:
    session_id = str(uuid.uuid4())
    if settings.gcp_region == "local":
        session_dirpath = settings.get_session_dirpath(session_id)
        os.makedirs(session_dirpath, exist_ok=True)
        return f"/local-upload/{session_id}", session_id
    else:
        return f"/upload/{session_id}", session_id

def generate_upload_url(filename: str, session_id: str, content_type: str = "") -> tuple[str, str]:
    """署名付きアップロードURLを生成（ローカルモードでは一時的なアップロードパスを返す）"""
    job_id = str(uuid.uuid4())

    # sanitize filename to prevent path traversal
    if os.path.sep in filename or (os.path.altsep and os.path.altsep in filename):
        raise ValueError("Invalid filename")
    safe_filename = os.path.basename(filename)

    if settings.gcp_region == "local":
        # ローカルモード: 一時的なアップロードパスを返す
        # ファイル名をURLエンコード
        from urllib.parse import quote
        encoded_filename = quote(safe_filename)
        upload_path = os.path.join(settings.get_storage_path(session_id, job_id), safe_filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        return f"/local-upload/{session_id}/{job_id}/{encoded_filename}", job_id
    else:
        # クラウドモード: 署名付きURLを生成
        if not content_type:
            content_type = "application/pdf"  # デフォルトのcontent_type
        
        if client is None:
            logger.error("GCS client is None, cannot generate upload URL")
            raise RuntimeError("GCS client is None, cannot generate upload URL")
            
        try:
            bucket = client.bucket(settings.gcs_bucket_works)
            blob = bucket.blob(f"{session_id}/{job_id}/{safe_filename}")
            
            url = blob.generate_signed_url(
                version="v4",
                expiration=settings.sign_url_exp,
                method="POST",
                content_type=content_type
            )
            logger.info(f"Generated signed URL for upload: {session_id}/{job_id}/{safe_filename}")
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {str(e)}")
            raise
        
        return url, job_id

def generate_download_url(session_id: str) -> str:
    """署名付きダウンロードURLを生成（ローカルモードでは一時的なダウンロードパスを返す）"""
    if settings.gcp_region == "local":
        # ローカルモード: 一時的なダウンロードパスを返す
        session_dirpath = settings.get_session_dirpath(session_id)
        
        # 両方のファイル名パターンをチェック
        zip_filename = None
        for filename in ["all_pdfs_images.zip", f"{session_id}_images.zip"]:
            safe_name = os.path.basename(filename)
            if os.path.exists(os.path.join(session_dirpath, safe_name)):
                zip_filename = safe_name
                break
        
        if not zip_filename:
            raise ValueError("ZIP file not found")
        
        # URLエンコードされたファイル名を使用
        from urllib.parse import quote
        encoded_filename = quote(os.path.basename(zip_filename))
        return f"/local-download/{session_id}/{encoded_filename}"
    else:
        # クラウドモード: 署名付きURLを生成
        if client is None:
            logger.error("GCS client is None, cannot generate download URL")
            raise RuntimeError("GCS client is None, cannot generate download URL")
            
        try:
            bucket = client.bucket(settings.gcs_bucket_works)
            blob = bucket.blob(f"{session_id}/all_pdfs_images.zip")
            
            url = blob.generate_signed_url(
                version="v4",
                expiration=settings.sign_url_exp,
                method="GET"
            )
            logger.info(f"Generated signed URL for download: {session_id}/all_pdfs_images.zip")
            return url
        except Exception as e:
            logger.error(f"Failed to generate signed URL for download: {str(e)}")
            raise
    # 開発中はローカルモードのみ対応

def cleanup_job(session_id: str, job_id: str) -> None:
    """Remove job related files for the given session."""
    if settings.gcp_region == "local":
        job_path = settings.get_storage_path(session_id, job_id)
        if os.path.exists(job_path):
            shutil.rmtree(job_path)
    else:
        # クラウドモードのクリーンアップはCloud Storageのライフサイクルポリシーに任せる
        pass
