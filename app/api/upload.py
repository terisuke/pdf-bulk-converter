from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from app.models.schemas import UploadRequest, UploadResponse, JobStatus, DownloadResponse
from app.services.storage import generate_upload_url, generate_download_url
import os
from app.core.config import get_settings
from datetime import datetime, timedelta
import json
import asyncio
from fastapi import BackgroundTasks
from urllib.parse import unquote
from app.core.job_status import job_status_manager
from app.services.converter import convert_pdf_to_images, process_multiple_pdfs
import logging
from typing import Optional, List
import uuid
from app.services.batch_processor import process_input, process_multiple_files

# ロガーの設定
logger = logging.getLogger(__name__)

router = APIRouter()
local_router = APIRouter()
settings = get_settings()

# 複数のファイルを処理するための辞書
pending_files = {}

@router.post("/upload-url", response_model=UploadResponse)
async def get_upload_url(request: UploadRequest):
    """PDFアップロード用の署名付きURLを取得"""
    try:
        upload_url, job_id = generate_upload_url(request.filename, request.content_type)
        # 新しいジョブのステータスを初期化
        initial_status = JobStatus(
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
            job_id=job_id
        )
    except Exception as e:
        logger.error(f"アップロードURL生成エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}")
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

@local_router.post("/local-upload/{job_id}/{filename}")
async def local_upload(
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
        upload_path = os.path.join(settings.get_storage_path(job_id), decoded_filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        
        # ファイルを保存
        with open(upload_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # ジョブステータスを更新
        job_status = JobStatus(
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
            uploaded_files = [f for f in os.listdir(settings.get_storage_path(job_id)) if f.lower().endswith('.pdf')]
            
            # すべてのファイルがアップロードされた場合、変換処理を開始
            if len(uploaded_files) == len(pending_files[job_id]):
                # 保存されたファイルのパスを取得
                pdf_paths = [os.path.join(settings.get_storage_path(job_id), f) for f in uploaded_files]
                
                # バックグラウンドで変換処理を開始
                background_tasks.add_task(
                    process_multiple_pdfs,
                    job_id=job_id,
                    pdf_paths=pdf_paths,
                    dpi=pending_files[job_id][0].get('dpi', 300)
                )
                
                # 処理済みのファイル情報を削除
                del pending_files[job_id]
        
        return {"message": "ファイルのアップロードが完了しました"}
    except Exception as e:
        logger.error(f"アップロードエラー: {str(e)}")
        # エラーが発生した場合、ジョブステータスを更新
        error_status = JobStatus(
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

@local_router.get("/local-download/{job_id}/{filename}")
async def local_download(job_id: str, filename: str):
    """ローカル環境でのファイルダウンロード用エンドポイント"""
    try:
        file_path = os.path.join(settings.get_storage_path(job_id), filename)
        logger.info(f"ダウンロード要求: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"ファイルが見つかりません: {file_path}")
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            file_path,
            filename=filename,
            media_type="application/zip"
        )
    except Exception as e:
        logger.error(f"ダウンロードエラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{job_id}", response_model=DownloadResponse)
async def get_download_url(job_id: str):
    """ダウンロード用のURLを取得"""
    try:
        status = job_status_manager.get_status(job_id)
        
        # ジョブが完了していない場合はエラー
        if status.status != "completed":
            raise HTTPException(status_code=400, detail="Job not completed yet")
        
        # ZIPファイル名を取得
        storage_path = settings.get_storage_path(job_id)
        # _images.zipで終わるファイルまたはall_pdfs_images.zipを検索
        zip_files = [f for f in os.listdir(storage_path) if f.endswith("_images.zip") or f == "all_pdfs_images.zip"]
        if not zip_files:
            raise HTTPException(status_code=404, detail="ZIP file not found")
        
        # ダウンロードURLを生成
        download_url = generate_download_url(job_id)
        expires_at = datetime.now() + timedelta(seconds=settings.sign_url_exp)
        
        return DownloadResponse(
            download_url=download_url,
            expires_at=expires_at
        )
    except Exception as e:
        logger.error(f"ダウンロードURL生成エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_file(
    files: List[UploadFile] = File(...),
    dpi: Optional[int] = 300,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    複数のファイル（PDF/ZIP）をアップロードして処理
    """
    try:
        # ジョブIDを生成
        job_id = str(uuid.uuid4())
        
        # 一時保存用ディレクトリを作成
        temp_dir = os.path.join(settings.get_storage_path(job_id), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 各ファイルを保存
        saved_files = []
        for file in files:
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            saved_files.append(file_path)
        
        # 処理開始ステータスを更新
        status = JobStatus(
            job_id=job_id,
            status="processing",
            message=f"{len(files)}個のファイルを処理中...",
            progress=0,
            created_at=datetime.now()
        )
        job_status_manager.update_status(job_id, status)
        
        # バックグラウンドで処理を開始
        background_tasks.add_task(process_multiple_files, job_id, saved_files, dpi)
        
        return {
            "job_id": job_id,
            "message": "処理を開始しました",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"アップロードエラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 一時ファイルを削除
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)

async def process_multiple_files(job_id: str, file_paths: List[str], dpi: int = 300):
    """
    複数のファイルを処理
    """
    try:
        total_files = len(file_paths)
        processed_files = []
        
        for i, file_path in enumerate(file_paths, 1):
            # 進捗状況を更新
            progress = (i - 1) / total_files * 100
            status = JobStatus(
                job_id=job_id,
                status="processing",
                message=f"ファイル {i}/{total_files} を処理中...",
                progress=progress,
                created_at=datetime.now()
            )
            job_status_manager.update_status(job_id, status)
            
            # ファイルを処理
            if file_path.lower().endswith('.zip'):
                processed = await process_zip(job_id, file_path, dpi)
                processed_files.extend(processed)
            elif file_path.lower().endswith('.pdf'):
                await convert_pdf_to_images(job_id, file_path, dpi)
                processed_files.append(file_path)
        
        # 完了ステータスを更新
        final_status = JobStatus(
            job_id=job_id,
            status="completed",
            message=f"{total_files}個のファイルの処理が完了しました",
            progress=100,
            created_at=datetime.now()
        )
        job_status_manager.update_status(job_id, final_status)
        
    except Exception as e:
        logger.error(f"処理エラー: {str(e)}")
        error_status = JobStatus(
            job_id=job_id,
            status="error",
            message=f"処理中にエラーが発生しました: {str(e)}",
            progress=0,
            created_at=datetime.now()
        )
        job_status_manager.update_status(job_id, error_status)            