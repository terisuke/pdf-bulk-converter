from app.core.config import get_settings
import os
import logging
import shutil
import uuid
from typing import Optional

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
        raise RuntimeError(f"Failed to initialize GCS client: {str(e)}")

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
                method="PUT",
                content_type=content_type
            )
            logger.info(f"Generated signed URL for upload: {session_id}/{job_id}/{safe_filename}")
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {str(e)}")
            raise
        
        return url, job_id

def cleanup_job(session_id: str, job_id: str) -> None:
    """Remove job related files for the given session."""
    if settings.gcp_region == "local":
        job_path = settings.get_storage_path(session_id, job_id)
        if os.path.exists(job_path):
            shutil.rmtree(job_path)
    else:
        # クラウドモードのクリーンアップはCloud Storageのライフサイクルポリシーに任せる
        pass

def _max_number_in_path(path: str) -> int:
    """Return the maximum numeric filename in the given directory tree."""
    max_number = 0
    for _, _, files in os.walk(path):
        for filename in files:
            if filename.lower().endswith((".jpeg", ".jpg")):
                name, _ = os.path.splitext(filename)
                if name.isdigit():
                    num = int(name)
                    if num > max_number:
                        max_number = num
    return max_number

def get_next_image_number(path: Optional[str] = None) -> int:
    """Calculate the next available image number.

    Args:
        path: Optional path for local mode. Defaults to workspace path.

    Returns:
        int: next available number (current max + 1)
    """
    try:
        if settings.gcp_region != "local":
            if client is None:
                logger.warning("GCS client is None, defaulting to 1")
                return 1
            bucket = client.bucket(settings.gcs_bucket_image)
            max_number = 0
            for blob in bucket.list_blobs():
                base = os.path.basename(blob.name)
                if base.lower().endswith((".jpeg", ".jpg")):
                    name, _ = os.path.splitext(base)
                    if name.isdigit():
                        num = int(name)
                        if num > max_number:
                            max_number = num
            return max_number + 1

        local_path = path or settings.workspace_path
        return _max_number_in_path(local_path) + 1
    except Exception as exc:
        logger.error("Failed to get next image number: %s", exc)
        return 1
