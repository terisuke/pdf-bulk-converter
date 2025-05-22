from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from app.models.schemas import UploadRequest, SessionRequest, SessionResponse, UploadResponse, SessionStatus, JobStatus, NotifyUploadCompleteRequest
from app.services.storage import (
    generate_session_url,
    generate_upload_url,
    get_next_image_number,
)
import os
from app.core.config import get_settings
from datetime import datetime, timedelta
import json
import asyncio
from fastapi import BackgroundTasks
from urllib.parse import unquote
from app.core.job_status import job_status_manager
from app.core.session_status import session_status_manager
from app.services.converter import convert_pdfs_to_images
import logging
from typing import Optional, List
import uuid
import traceback

# google-cloud-storage is optional in local mode
gcs_client = None
gcs_available = False
try:
    import google.cloud.storage
    gcs_available = True
except ImportError:  # pragma: no cover - optional dependency
    pass

# ロガーの設定
logger = logging.getLogger(__name__)

router = APIRouter()
local_router = APIRouter()
settings = get_settings()

# 複数のファイルを処理するための辞書
pending_files = {}

def get_session_image_num(session_id: str) -> int:
    """
    Retrieves the current image_num from the session status.
    Defaults to 0 if the session status does not exist.
    """
    current_session_status = session_status_manager.get_status(session_id)
    return current_session_status.image_num if current_session_status else 0

async def convert_and_notify(session_id: str, job_ids: List[str], dpi: int = 300, format: str = "jpeg", max_retries: int = 3):
    """
    PDFファイルを変換し、進捗状況を通知する
    
    Args:
        session_id: セッションID
        job_ids: ジョブIDのリスト（各ファイルに対応）
        dpi: 出力画像のDPI
        format: 出力画像のフォーマット
        max_retries: リトライ回数の最大値
    """
    try:
        logger.info(f"Starting PDF conversion for session: {session_id}, job_ids: {job_ids}")
        
        local_pdf_paths = []
        
        # Check if we're in cloud mode or local mode
        logger.info(f"Current GCP region: {settings.gcp_region}")
        
        if settings.gcp_region != "local":
            logger.info("Running in cloud mode, attempting to download files from GCS")
            if not gcs_available:
                logger.warning("Google Cloud Storage module is not available, cannot access GCS")
            else:
                
                for job_id in job_ids:
                    retry_count = 0
                    success = False
                    
                    while not success and retry_count <= max_retries:
                        try:
                            with open(settings.gcp_keypath, "r") as f:
                                credentials_info = json.load(f)
                            if not gcs_available:
                                logger.error("Google Cloud Storage module is not available, cannot initialize client")
                                raise RuntimeError("Google Cloud Storage module is not available, cannot initialize client")
                                
                            client = google.cloud.storage.Client.from_service_account_info(credentials_info)
                            logger.info(f"GCS client initialized for project: {client.project}")
                            
                            bucket = client.bucket(settings.gcs_bucket_works)
                            blobs = list(bucket.list_blobs(prefix=f"{session_id}/{job_id}/"))
                            
                            if not blobs:
                                logger.warning(f"No files found in GCS at {session_id}/{job_id}/")
                                all_blobs = list(bucket.list_blobs())
                                logger.info(f"Total blobs in bucket: {len(all_blobs)}")
                                for b in all_blobs[:10]:  # Show first 10 blobs
                                    logger.info(f"Found blob: {b.name}")
                                    
                                retry_count += 1
                                if retry_count <= max_retries:
                                    logger.info(f"Retrying ({retry_count}/{max_retries})...")
                                    await asyncio.sleep(2 ** retry_count)  # 指数バックオフ
                                    continue
                                else:
                                    logger.error(f"Max retries reached for {job_id}, skipping")
                                    break
                            
                            for blob in blobs:
                                filename = blob.name.split("/")[-1]
                                local_dir = os.path.join(settings.get_session_dirpath(session_id), "pdfs")
                                os.makedirs(local_dir, exist_ok=True)
                                local_path = os.path.join(local_dir, filename)
                                
                                logger.info(f"Downloading {blob.name} from GCS to {local_path}")
                                blob.download_to_filename(local_path)
                                local_pdf_paths.append(local_path)
                            
                            success = True
                            
                        except FileNotFoundError as exc:
                            logger.error(f"GCP key file not found: {settings.gcp_keypath}")
                            raise FileNotFoundError(f"GCP key file not found: {settings.gcp_keypath}") from exc
                        except Exception as e:
                            logger.error(f"Error downloading file from GCS: {str(e)}")
                            retry_count += 1
                            if retry_count <= max_retries:
                                logger.info(f"Retrying ({retry_count}/{max_retries})...")
                                await asyncio.sleep(2 ** retry_count)  # 指数バックオフ
                            else:
                                logger.error(f"Max retries reached for {job_id}, skipping")
        else:
            local_dir = os.path.join(settings.get_session_dirpath(session_id), "pdfs")
            if not os.path.exists(local_dir):
                logger.info(f"Creating local directory: {local_dir}")
                os.makedirs(local_dir, exist_ok=True)
                
            logger.info(f"Checking for PDF files in local directory: {local_dir}")
            if os.path.exists(local_dir) and os.listdir(local_dir):
                for job_id in job_ids:
                    for filename in os.listdir(local_dir):
                        local_path = os.path.join(local_dir, filename)
                        if os.path.isfile(local_path) and filename.lower().endswith('.pdf'):
                            logger.info(f"Found PDF file: {local_path}")
                            local_pdf_paths.append(local_path)
            else:
                logger.warning(f"Local directory {local_dir} does not exist or is empty")
        
        if not local_pdf_paths:
            error_message = "変換するPDFファイルが見つかりませんでした"
            logger.error(error_message)
            
            # 現在のセッション状態を取得して開始番号を保持
            start_image_num = get_session_image_num(session_id)
            
            session_status_manager.update_status(
                session_id,
                SessionStatus(
                    session_id=session_id,
                    status="error",
                    message=error_message,
                    progress=0,
                    pdf_num=0,
                    image_num=start_image_num,  # 開始番号を保持
                    created_at=datetime.now()
                )
            )
            return
        
        conversion_job_id = str(uuid.uuid4())
        await convert_pdfs_to_images(session_id, conversion_job_id, local_pdf_paths, dpi)
        
        logger.info(f"PDF conversion completed for session: {session_id}")
    except Exception as e:
        error_message = f"PDF変換中にエラーが発生しました: {str(e)}"
        logger.error(error_message)
        
        # 現在のセッション状態を取得して開始番号を保持
        start_image_num = get_session_image_num(session_id)
        
        session_status_manager.update_status(
            session_id,
            SessionStatus(
                session_id=session_id,
                status="error",
                message=error_message,
                progress=0,
                pdf_num=0,
                image_num=start_image_num,  # 開始番号を保持
                created_at=datetime.now()
            )
        )

async def convert_and_notify_single(session_id: str, job_id: str, pdf_paths: List[str], dpi: int, format: str = "jpg"):
    """PDFを変換し、進捗を通知するバックグラウンドタスク（エラーハンドリング付き）"""
    try:
        logger.info(f"Starting background task to convert PDFs for session_id: {session_id}, job_id: {job_id}")
        job_status_manager.update_status(
            job_id, 
            JobStatus(
                session_id=session_id,
                job_id=job_id,
                status="processing",
                message="PDF変換処理を開始します",
                progress=0,
                created_at=datetime.now()
            )
        )
        
        logger.info(f"Converting {len(pdf_paths)} PDFs to images with dpi={dpi}, format={format}")
        await convert_pdfs_to_images(
            session_id=session_id,
            job_id=job_id,
            pdf_paths=pdf_paths,
            dpi=dpi,
            format=format
        )
        
        logger.info(f"PDF conversion completed for job_id: {job_id}")
        job_status_manager.update_status(
            job_id, 
            JobStatus(
                session_id=session_id,
                job_id=job_id,
                status="completed",
                message="PDF変換が完了しました",
                progress=100,
                created_at=datetime.now()
            )
        )
    except Exception as e:
        error_msg = f"Error in PDF conversion background task: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())  # スタックトレースを出力
        
        job_status_manager.update_status(
            job_id, 
            JobStatus(
                session_id=session_id,
                job_id=job_id,
                status="error",
                message=f"PDF変換中にエラーが発生しました: {str(e)}",
                progress=0,
                created_at=datetime.now()
            )
        )
        
        # 現在のセッション状態を取得して開始番号を保持
        start_image_num = get_session_image_num(session_id)
        
        session_status_manager.update_status(
            session_id, 
            SessionStatus(
                session_id=session_id,
                status="error",
                message=f"PDF変換中にエラーが発生しました: {str(e)}",
                progress=0,
                pdf_num=0,
                image_num=start_image_num,  # 開始番号を保持
                created_at=datetime.now()
            )
        )

@router.post("/session", response_model=SessionResponse)
def get_session_id(request: SessionRequest):
    try:
        session_url, session_id = generate_session_url()
        logger.info("session_id: %s", session_id)

        start_number = request.start_number
        if start_number is None:
            start_number = get_next_image_number()

        initial_session = SessionStatus(
            session_id=session_id,
            status="uploading",
            progress=0.0,
            created_at=datetime.now(),
            pdf_num=1,  # NOTE: PDF格納先を連番にする場合に使用を想定
            image_num=start_number,
            message="セッションを初期化しました"
        )
        session_status_manager.update_status(session_id, initial_session)
        return SessionResponse(
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"セッションID取得エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-url", response_model=UploadResponse)
async def get_upload_url(request: UploadRequest):
    """PDFアップロード用の署名付きURLを取得"""
    try:
        session_id = request.session_id
        upload_url, job_id = generate_upload_url(request.filename, session_id, request.content_type)
        # 新しいジョブのステータスを初期化
        initial_status = JobStatus(
            session_id=session_id,
            job_id=job_id,
            status="pending",
            progress=0.0,
            created_at=datetime.now(),
            message="ジョブを初期化しました"
        )
        job_status_manager.update_status(job_id, initial_status)
        
        # ファイル情報を保存
        if job_id not in pending_files:
            pending_files[job_id] = []
        pending_files[job_id].append({
            "filename": request.filename,
            "content_type": request.content_type,
            "dpi": request.dpi,
            "format": request.format
        })
        
        return UploadResponse(
            upload_url=upload_url,
            session_id=session_id,
            job_id=job_id
        )
    except Exception as e:
        logger.error(f"アップロードURL生成エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session-status/{session_id}")
async def get_session_status(session_id: str):
    """セッションのステータスを取得（SSE）"""
    async def event_generator():
        while True:
            status = session_status_manager.get_status(session_id)
            if status is None:
                break
            status_dict = {
                "status": status.status,
                "message": status.message,
                "progress": status.progress,
                "created_at": status.created_at.isoformat() if status.created_at else None
            }
            yield f"data: {json.dumps(status_dict)}\n\n"
            if status.status in ["completed", "error"]:
                break
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )    

@router.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    """ジョブのステータスを取得（SSE）"""
    async def event_generator():
        while True:
            status = job_status_manager.get_status(job_id)
            if status is None:
                break
            status_dict = {
                "status": status.status,
                "message": status.message,
                "progress": status.progress,
                "created_at": status.created_at.isoformat() if status.created_at else None
            }
            yield f"data: {json.dumps(status_dict)}\n\n"
            if status.status in ["completed", "error"]:
                break
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@local_router.post("/local-upload/{session_id}/{job_id}/{filename}")
async def local_upload(
    session_id: str,
    job_id: str,
    filename: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """ローカルファイルアップロードエンドポイント"""
    try:
        # URLデコードされたファイル名を取得
        decoded_filename = unquote(filename)
        logger.info(f"ファイルアップロード開始: {decoded_filename}")
        
        # ファイルの保存先パスを設定
        upload_path = os.path.join(settings.get_storage_path(session_id, job_id), decoded_filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        
        # ファイルを保存
        with open(upload_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # ジョブステータスを更新
        job_status = JobStatus(
            session_id=session_id,
            job_id=job_id,
            status="processing",
            message="ファイルをアップロードしました。変換を開始します。",
            progress=0,
            created_at=datetime.now()
        )
        job_status_manager.update_status(job_id, job_status)
        
        # このジョブのすべてのファイルがアップロードされたかチェック
        if job_id in pending_files:
            # アップロード済みのファイル数をカウント
            uploaded_files = [f for f in os.listdir(settings.get_storage_path(session_id, job_id)) 
                            if f.lower().endswith('.pdf')]
            
            # すべてのファイルがアップロードされた場合、変換処理を開始
            if len(uploaded_files) == len(pending_files[job_id]):
                # 保存されたファイルのパスを取得
                file_paths = [os.path.join(settings.get_storage_path(session_id, job_id), f) for f in uploaded_files]
                
                # PDFファイルを処理
                pdf_files = [f for f in file_paths if f.lower().endswith('.pdf')]
                
                if pdf_files:
                    background_tasks.add_task(
                        convert_and_notify_single,
                        session_id=session_id,
                        job_id=job_id,
                        pdf_paths=pdf_files,
                        dpi=pending_files[job_id][0].get('dpi', 300),
                        format=pending_files[job_id][0].get('format', 'jpg')
                    )
                
                # 処理済みのファイル情報を削除
                del pending_files[job_id]
        
        return {"message": "ファイルのアップロードが完了しました"}
    except Exception as e:
        logger.error(f"アップロードエラー: {str(e)}")
        # エラーが発生した場合、ジョブステータスを更新
        error_status = JobStatus(
            session_id=session_id,
            job_id=job_id,
            status="error",
            message=f"アップロード中にエラーが発生しました: {str(e)}",
            progress=0,
            created_at=datetime.now()
        )
        job_status_manager.update_status(job_id, error_status)
        raise HTTPException(
            status_code=500,
            detail=f"ファイルのアップロード中にエラーが発生しました: {str(e)}"
        )

@router.post("/notify-upload-complete/{session_id}")
async def notify_upload_complete(
    session_id: str,
    background_tasks: BackgroundTasks,
    request: NotifyUploadCompleteRequest
):
    """
    クラウドモードでのファイルアップロード完了を通知し、変換処理を開始するエンドポイント
    
    Args:
        session_id: セッションID
        request: アップロード完了通知リクエスト（ジョブIDのリスト、DPI設定など）
    """
    try:
        logger.info(f"Upload complete notification received for session: {session_id}")
        
        # 現在のセッション状態を取得して開始番号を保持
        start_image_num = get_session_image_num(session_id)
        
        session_status_manager.update_status(
            session_id,
            SessionStatus(
                session_id=session_id,
                status="processing",
                message="PDFファイルの変換を開始します",
                progress=20.0,
                pdf_num=len(request.job_ids),
                image_num=start_image_num,  # 開始番号を保持
                created_at=datetime.now()
            )
        )
        
        background_tasks.add_task(
            convert_and_notify,
            session_id=session_id,
            job_ids=request.job_ids,
            dpi=request.dpi,
            format=request.format,
            max_retries=request.max_retries
        )
        
        return {"status": "processing", "message": "PDFファイルの変換を開始します"}
    except Exception as e:
        error_message = f"アップロード完了通知の処理中にエラーが発生しました: {str(e)}"
        logger.error(error_message)
        raise HTTPException(status_code=500, detail=error_message)

@router.put("/session-update/{session_id}")
async def update_session_status(session_id: str, status_update: dict):
    """セッションのステータスを更新"""
    try:
        current_status = session_status_manager.get_status(session_id)
        if current_status is None:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # 現在のステータスを保持しながら、新しいステータスで更新
        updated_status = SessionStatus(
            session_id=session_id,
            status=status_update.get("status", current_status.status),
            message=status_update.get("message", current_status.message),
            progress=status_update.get("progress", current_status.progress),
            pdf_num=current_status.pdf_num,
            image_num=current_status.image_num,
            created_at=datetime.now()
        )
        
        session_status_manager.update_status(session_id, updated_status)
        return {"message": "Session status updated successfully"}
    except Exception as e:
        logger.error(f"セッションステータス更新エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e
