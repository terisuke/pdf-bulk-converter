import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple
import fitz
from app.core.job_status import JobStatus, job_status_manager
from app.core.session_status import SessionStatus, session_status_manager
from datetime import datetime
import logging
from app.core.config import get_settings
try:  # google-cloud-storage is optional in local mode
    from google.cloud import storage
except ImportError:  # pragma: no cover - optional dependency
    storage = None
import json

# ロガーの設定
logger = logging.getLogger(__name__)

settings = get_settings()

if settings.gcp_region != "local":
    if storage is None:
        raise RuntimeError("google-cloud-storage package is required for cloud mode")
    try:
        with open(settings.gcp_keypath, "r") as f:
            credentials_info = json.load(f)
        gcs_client = storage.Client.from_service_account_info(credentials_info)
        logger.info(f"GCS client initialized for project: {gcs_client.project}")
    except FileNotFoundError as exc:
        logger.error(f"GCP key file not found: {settings.gcp_keypath}")
        raise FileNotFoundError(f"GCP key file not found: {settings.gcp_keypath}") from exc
    except Exception as e:
        logger.error(f"Failed to initialize GCS client: {str(e)}")
        raise RuntimeError(f"Failed to initialize GCS client: {str(e)}")
else:
    gcs_client = None

async def convert_1pdf_to_images(session_id: str, job_id: str, pdf_path: str, dpi: int, format: str, images_dir: str,) -> Tuple[str, List[str]]:
    """
    単一のPDFファイルを画像に変換する
    
    Args:
        session_id: セッションID
        job_id: ジョブID
        pdf_path: PDFファイルのパス
        dpi: 出力画像のDPI
        format: 出力画像のフォーマット
        images_dir: 出力ディレクトリ
        
    Returns:
        Tuple[str, List[str]]: 出力ディレクトリのパスと生成された画像ファイルのパスのリスト
    """
    try:
        logger.info(f"Starting conversion of PDF: {pdf_path} with job_id: {job_id}, session_id: {session_id}")
        
        # PDFファイル名を取得（拡張子なし）
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        logger.info(f"PDF name: {pdf_name}")
        
        # PDFを開く
        if not os.path.exists(pdf_path):
            error_msg = f"PDF file not found: {pdf_path}"
            logger.error(error_msg)
            status = JobStatus(
                session_id=session_id,
                job_id=job_id,
                status="error",
                message=error_msg,
                progress=0,
                created_at=datetime.now()
            )
            job_status_manager.update_status(job_id, status)
            return images_dir, []
            
        logger.info(f"Opening PDF file: {pdf_path}")
        pdf_document = fitz.open(pdf_path)
        total_pages = len(pdf_document)
        image_paths = []

        imagenum_start = session_status_manager.get_imagenum(session_id)
        logger.info(f"Starting image number: {imagenum_start}, total pages: {total_pages}")
        
        # 各ページを画像に変換
        for page_num in range(total_pages):
            page = pdf_document[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
            
            # 画像ファイル名を生成
            imagenum_current = imagenum_start + page_num
            image_filename = f"{imagenum_current:07d}.{format}"
            image_path = os.path.join(images_dir, image_filename)
            
            logger.info(f"Rendering page {page_num+1}/{total_pages} to {image_path}")
            
            # 画像を保存
            pix.save(image_path)
            image_paths.append(image_path)
            
            if settings.gcp_region != "local" and gcs_client is not None:
                try:
                    logger.info(f"Uploading image to GCS_BUCKET_IMAGE: {settings.gcs_bucket_image}/{session_id}/{image_filename}")
                    
                    bucket = gcs_client.bucket(settings.gcs_bucket_image)
                    blob = bucket.blob(f"{session_id}/{image_filename}")
                    
                    blob.upload_from_filename(image_path)
                    logger.info(f"Successfully uploaded image to GCS: {settings.gcs_bucket_image}/{session_id}/{image_filename}")
                except Exception as e:
                    error_msg = f"Failed to upload image to GCS: {str(e)}"
                    logger.error(error_msg)
            
            # 進捗を更新
            progress = (page_num + 1) / total_pages * 100
            status = JobStatus(
                session_id=session_id,
                job_id=job_id,
                status="processing",
                message=f"ページ変換完了: {page_num + 1}/{total_pages}",
                progress=progress,
                created_at=datetime.now()
            )
            job_status_manager.update_status(job_id, status)
        
        # PDFを閉じる
        session_status_manager.add_imagenum(session_id, total_pages)
        pdf_document.close()
        
        logger.info(f"PDF conversion completed: {pdf_path} -> {len(image_paths)} images")
        return images_dir, image_paths
        
    except Exception as e:
        error_msg = f"Error converting PDF to images: {str(e)}"
        logger.error(error_msg)
        status = JobStatus(
            session_id=session_id,
            job_id=job_id,
            status="error",
            message=error_msg,
            progress=0,
            created_at=datetime.now()
        )
        job_status_manager.update_status(job_id, status)
        return images_dir, []

# 複数のPDFファイルを処理する関数を追加
async def convert_pdfs_to_images(session_id: str, job_id: str, pdf_paths: List[str], dpi: int = 300, format: str = "jpeg") -> Tuple[str, List[str]]:
    """
    PDFファイルを画像変換する (複数対応)
    
    Args:
        session_id: セッションID
        job_id: ジョブID
        pdf_paths: PDFファイルのパスリスト
        dpi: 出力画像のDPI
        format: 出力形式（常にjpeg）
        imagenum_start: 
    
    Returns:
        Tuple[画像格納ディレクトリ, 生成された画像ファイルのパスリスト]
    """
    try:
        # 常にJPEGとして処理
        format = "jpeg"
        logger.info(f"複数PDF変換開始: session_id={session_id}, job_id={job_id}, pdf_count={len(pdf_paths)}, dpi={dpi}")
        
        # 出力ディレクトリの作成
        images_dir = os.path.join(settings.get_session_dirpath(session_id), "images")
        os.makedirs(images_dir, exist_ok=True)
        
        # すべての画像ファイルのパスを保持
        all_image_paths = []
        
        # 各PDFファイルを処理
        total_files = len(pdf_paths)
        for i, pdf_path in enumerate(pdf_paths, 1):
            # PDFファイルを処理
            _, image_paths = await convert_1pdf_to_images(session_id, job_id, pdf_path, dpi, format, images_dir)
            all_image_paths.extend(image_paths)
            
            # ジョブの進捗を更新
            job_process = (i / total_files) * 100
            job_status = JobStatus(
                session_id=session_id,
                job_id=job_id,
                status="processing",
                message=f"PDFファイル {i}/{total_files} を処理中",
                progress=job_process,
                created_at=datetime.now()
            )
            job_status_manager.update_status(job_id, job_status)
        
        # 完了ステータスを設定
        job_complete_status = JobStatus(
            session_id=session_id,
            job_id=job_id,
            status="completed",
            message=f"ジョブ {job_id} のファイルの画像変換が完了しました",
            progress=100,
            created_at=datetime.now()
        )
        job_status_manager.update_status(job_id, job_complete_status)
        
        return images_dir, all_image_paths
        
    except Exception as e:
        # エラーが発生した場合、ステータスを更新
        error_message = f"変換中にエラーが発生しました: {str(e)}"
        logger.error(f"エラー発生: job_id={job_id}, error={str(e)}")
        error_status = JobStatus(
            session_id=session_id,
            job_id=job_id,
            status="error",
            message=error_message,
            progress=0,
            created_at=datetime.now()
        )
        job_status_manager.update_status(job_id, error_status)
        raise

# ZIPファイルの作成
def create_zip_file(session_id: str, image_paths: List[str]) -> str:
    """
    画像ファイルをZIPにまとめる
    
    Args:
        session_id: セッションID
        image_paths: 画像ファイルのパスのリスト
        
    Returns:
        str: 作成されたZIPファイルのパス
    """
    try:
        logger.info(f"Creating ZIP file for session: {session_id} with {len(image_paths)} images")
        
        # 最初の画像ファイル名からベース名を取得
        if not image_paths:
            error_msg = "No images to create ZIP file"
            logger.error(error_msg)
            session_status_manager.update_status(
                session_id, 
                SessionStatus(
                    session_id=session_id,
                    status="error",
                    message=error_msg,
                    progress=0,
                    pdf_num=0,
                    image_num=0,
                    created_at=datetime.now()
                )
            )
            return ""
            
        base_name = os.path.splitext(os.path.basename(image_paths[0]))[0].split('_page')[0]
        zip_filename = "all_pdfs_images.zip"
        zip_path = os.path.join(settings.get_session_dirpath(session_id), zip_filename)
        
        logger.info(f"Creating ZIP file at: {zip_path}")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for image_path in image_paths:
                # ファイル名のみを取得（ディレクトリパスを除外）
                arcname = os.path.basename(image_path)
                logger.info(f"Adding file to ZIP: {arcname}")
                # UTF-8でファイル名を保存
                zipf.write(image_path, arcname)
        
        current_status = session_status_manager.get_status(session_id)
        
        # current_statusがNoneの場合のデフォルト値を設定
        pdf_num = 0
        image_num = 0
        if current_status:
            pdf_num = current_status.pdf_num if hasattr(current_status, 'pdf_num') else 0
            image_num = current_status.image_num if hasattr(current_status, 'image_num') else 0
        
        status = SessionStatus(
            session_id=session_id,
            status="completed",
            message="変換が完了しました",
            progress=100,
            pdf_num=pdf_num,
            image_num=image_num,
            created_at=datetime.now()
        )
        
        session_status_manager.update_status(session_id, status)
        
        if settings.gcp_region != "local" and gcs_client is not None:
            try:
                logger.info(f"Uploading ZIP to GCS_BUCKET_WORKS: {settings.gcs_bucket_works}/{session_id}/all_pdfs_images.zip")
                
                bucket = gcs_client.bucket(settings.gcs_bucket_works)
                blob = bucket.blob(f"{session_id}/all_pdfs_images.zip")
                
                blob.upload_from_filename(zip_path)
                logger.info(f"Successfully uploaded ZIP to GCS: {settings.gcs_bucket_works}/{session_id}/all_pdfs_images.zip")
            except Exception as e:
                error_msg = f"Failed to upload ZIP to GCS: {str(e)}"
                logger.error(error_msg)
        
        logger.info(f"ZIP file created: {zip_path}")
        return zip_path
        
    except Exception as e:
        error_msg = f"Error creating ZIP file: {str(e)}"
        logger.error(error_msg)
        session_status_manager.update_status(
            session_id, 
            SessionStatus(
                session_id=session_id,
                status="error",
                message=f"ZIP作成エラー: {error_msg}",
                progress=0,
                pdf_num=0,
                image_num=0,
                created_at=datetime.now()
            )
        )
        return ""
