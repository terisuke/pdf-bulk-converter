from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from app.models.schemas import UploadRequest, SessionResponse, UploadResponse, SessionStatus, JobStatus, DownloadResponse
from app.services.storage import generate_session_url, generate_upload_url, generate_download_url
import os
from app.core.config import get_settings
from datetime import datetime, timedelta
import json
import asyncio
from fastapi import BackgroundTasks
from urllib.parse import unquote
from app.core.job_status import job_status_manager
from app.core.session_status import session_status_manager
from app.services.converter import process_multiple_pdfs, create_zip_file
import logging
from typing import Optional, List
import uuid

# ロガーの設定
logger = logging.getLogger(__name__)

router = APIRouter()
local_router = APIRouter()
settings = get_settings()

# 複数のファイルを処理するための辞書
pending_files = {}

@router.get("/session", response_model=SessionResponse)
def get_session_id():
    try:
        session_url, session_id = generate_session_url()
        # TODO: 正式にはフロントから開始番号を取得
        initial_session = SessionStatus(
            session_id=session_id,
            status="uploading",
            progress=0.0,
            created_at=datetime.now(),
            pdf_num=1,
            image_num=1,
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
                            # if f.lower().endswith(('.pdf', '.zip'))]
            
            # すべてのファイルがアップロードされた場合、変換処理を開始
            if len(uploaded_files) == len(pending_files[job_id]):
                # 保存されたファイルのパスを取得
                file_paths = [os.path.join(settings.get_storage_path(session_id, job_id), f) for f in uploaded_files]
                
                # ZIPファイルとPDFファイルを分離
                zip_files = [f for f in file_paths if f.lower().endswith('.zip')]
                pdf_files = [f for f in file_paths if f.lower().endswith('.pdf')]
                
                if pdf_files:
                    background_tasks.add_task(
                        process_multiple_pdfs,
                        session_id=session_id,
                        job_id=job_id,
                        pdf_paths=pdf_files,
                        dpi=pending_files[job_id][0].get('dpi', 300)
                    )

                # TODO: 個数に依らずzip自体を一旦保留
                # # バックグラウンドで変換処理を開始
                # if zip_files:
                #     if len(zip_files) == 1:
                #         background_tasks.add_task(
                #             process_zip,
                #             job_id=job_id,
                #             zip_path=zip_files[0],
                #             dpi=pending_files[job_id][0].get('dpi', 300)
                #         )
                #     # TODO: zipが複数時の対応 (process_zipが複数zipファイル未対応)
                #     # else: 
                #     #     background_tasks.add_task(
                #     #         process_zips,
                #     #         job_id=job_id,
                #     #         zip_paths=zip_files,
                #     #         dpi=pending_files[job_id][0].get('dpi', 300)
                #     #     )
                
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
    
@local_router.post("/create-zip/{session_id}")
async def create_zip(session_id: str):
    try:
        session_dirpath = settings.get_session_dirpath(session_id)
        images_dirpath = os.path.join(session_dirpath, "images")
        if not os.path.exists(images_dirpath):
            logger.error(f"画像ディレクトリがありません: {images_dirpath}")
            raise HTTPException(status_code=404, detail="File not found")
        
        image_paths = [f for f in os.listdir(images_dirpath)]
        create_zip_file(session_id, image_paths)
        
    except Exception as e:
        logger.error(f"ZIP作成エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@local_router.get("/local-download/{session_id}/{filename}")
async def local_download(session_id: str, job_id: str, filename: str):
    """ローカル環境でのファイルダウンロード用エンドポイント"""
    try:
        file_path = os.path.join(settings.get_session_dirpath(session_id), filename)
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

@router.get("/download/{session_id}", response_model=DownloadResponse)
async def get_download_url(session_id: str):
    """ダウンロード用のURLを取得"""
    try:
        status = session_status_manager.get_status(session_id)
        
        # # ジョブが完了していない場合はエラー
        # if status.status != "completed":
        #     raise HTTPException(status_code=400, detail="Job not completed yet")
        
        # ZIPファイル名を取得
        session_dirpath = settings.get_session_dirpath(session_id)
        # _images.zipで終わるファイルまたはall_pdfs_images.zipを検索
        zip_files = [f for f in os.listdir(session_dirpath) if f.endswith("_images.zip") or f == "all_pdfs_images.zip"]
        if not zip_files:
            raise HTTPException(status_code=404, detail="ZIP file not found")
        
        # ダウンロードURLを生成
        download_url = generate_download_url(session_id)
        expires_at = datetime.now() + timedelta(seconds=settings.sign_url_exp)
        
        return DownloadResponse(
            download_url=download_url,
            expires_at=expires_at
        )
    except Exception as e:
        logger.error(f"ダウンロードURL生成エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
        raise HTTPException(status_code=500, detail=str(e))            