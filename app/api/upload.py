from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from app.models.schemas import UploadRequest, UploadResponse, JobStatus
from app.services.storage import generate_upload_url
import os
from app.core.config import get_settings
from datetime import datetime
import json
import asyncio

router = APIRouter()
local_router = APIRouter()
settings = get_settings()

# ジョブステータスを一時的に保存するディクショナリ（開発用）
job_statuses = {}

@router.post("/upload-url", response_model=UploadResponse)
async def get_upload_url(request: UploadRequest):
    """PDFアップロード用の署名付きURLを取得"""
    try:
        upload_url, job_id = generate_upload_url(request.filename, request.content_type)
        # 新しいジョブのステータスを初期化
        job_statuses[job_id] = {
            "status": "pending",
            "progress": 0.0,
            "created_at": datetime.now(),
            "completed_at": None,
            "error": None
        }
        return UploadResponse(
            upload_url=upload_url,
            job_id=job_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """ジョブのステータスを取得（SSE）"""
    if job_id not in job_statuses:
        raise HTTPException(status_code=404, detail="Job not found")
    
    async def event_generator():
        while True:
            status = job_statuses[job_id]
            if status["status"] in ["completed", "error"]:
                # 完了またはエラーの場合は最後のステータスを送信して終了
                yield f"data: {json.dumps(JobStatus(job_id=job_id, **status).dict())}\n\n"
                break
            
            # 現在のステータスを送信
            yield f"data: {json.dumps(JobStatus(job_id=job_id, **status).dict())}\n\n"
            await asyncio.sleep(1)  # 1秒待機
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@local_router.put("/local-upload/{job_id}/{filename}")
async def local_upload(job_id: str, filename: str, file: UploadFile = File(...)):
    """ローカル環境でのファイルアップロード用エンドポイント"""
    try:
        # アップロード先のパスを取得
        upload_path = os.path.join(settings.get_storage_path(job_id), filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        
        # ファイルを保存
        with open(upload_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # ジョブステータスを更新
        if job_id in job_statuses:
            job_statuses[job_id]["status"] = "processing"
            job_statuses[job_id]["progress"] = 50.0
        
        return {"message": "File uploaded successfully"}
    except Exception as e:
        if job_id in job_statuses:
            job_statuses[job_id]["status"] = "error"
            job_statuses[job_id]["error"] = str(e)
        raise HTTPException(status_code=500, detail=str(e))

@local_router.get("/local-download/{job_id}/{filename}")
async def local_download(job_id: str, filename: str):
    """ローカル環境でのファイルダウンロード用エンドポイント"""
    try:
        file_path = os.path.join(settings.get_storage_path(job_id), filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # ジョブステータスを更新
        if job_id in job_statuses:
            job_statuses[job_id]["status"] = "completed"
            job_statuses[job_id]["progress"] = 100.0
            job_statuses[job_id]["completed_at"] = datetime.now()
        
        return FileResponse(file_path)
    except Exception as e:
        if job_id in job_statuses:
            job_statuses[job_id]["status"] = "error"
            job_statuses[job_id]["error"] = str(e)
        raise HTTPException(status_code=500, detail=str(e)) 