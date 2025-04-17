from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from app.models.schemas import UploadRequest, UploadResponse, JobStatus, DownloadResponse
from app.services.storage import generate_upload_url, generate_download_url
import os
from app.core.config import get_settings
from datetime import datetime, timedelta
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
    
    def datetime_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    async def event_generator():
        while True:
            status = job_statuses[job_id]
            job_status = JobStatus(job_id=job_id, **status)
            
            status_dict = job_status.dict()
            
            if status["status"] in ["completed", "error"]:
                # 完了またはエラーの場合は最後のステータスを送信して終了
                yield f"data: {json.dumps(status_dict, default=datetime_serializer)}\n\n"
                break
            
            # 現在のステータスを送信
            yield f"data: {json.dumps(status_dict, default=datetime_serializer)}\n\n"
            await asyncio.sleep(1)  # 1秒待機
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@local_router.post("/local-upload/{job_id}/{filename}")
async def local_upload(job_id: str, filename: str, file: UploadFile = File(...), dpi: int = 300, format: str = "png"):
    """ローカル環境でのファイルアップロード用エンドポイント"""
    print(f"Received upload request for job_id: {job_id}, filename: {filename}")
    print(f"File details: {file.filename}, content_type: {file.content_type}, size: {file.size if hasattr(file, 'size') else 'unknown'}")
    print(f"Parameters: dpi={dpi}, format={format}")
    
    try:
        # アップロード先のパスを取得（ファイル名を固定して日本語文字化けを回避）
        upload_path = os.path.join(settings.get_storage_path(job_id), "input.pdf")
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        print(f"Created directory: {os.path.dirname(upload_path)}")
        
        # ファイルを保存
        content = await file.read()
        print(f"Read file content, size: {len(content)} bytes")
        
        with open(upload_path, "wb") as f:
            f.write(content)
        print(f"Saved file to: {upload_path}")
        
        # ジョブステータスを更新
        if job_id in job_statuses:
            job_statuses[job_id]["status"] = "processing"
            job_statuses[job_id]["progress"] = 50.0
            print(f"Updated job status to processing: {job_statuses[job_id]}")
        else:
            # ジョブステータスが存在しない場合は作成
            job_statuses[job_id] = {
                "status": "processing",
                "progress": 50.0,
                "created_at": datetime.now(),
                "completed_at": None,
                "error": None
            }
            print(f"Created new job status: {job_statuses[job_id]}")
        
        # PDFからZIPへの変換処理を実行
        from app.services.converter import convert_pdf_to_images
        
        try:
            print(f"Starting PDF conversion for job {job_id}, file: {upload_path}")
            print(f"Using DPI: {dpi}, Format: {format}")
            
            # 変換処理を実行
            zip_path, image_paths = await convert_pdf_to_images(
                job_id=job_id, 
                pdf_path=upload_path,
                dpi=int(dpi),
                format=format.lower()
            )
            
            print(f"PDF conversion completed successfully, zip file: {zip_path}")
            print(f"Generated {len(image_paths)} images")
            
            # ジョブステータスを更新
            if job_id in job_statuses:
                job_statuses[job_id]["status"] = "completed"
                job_statuses[job_id]["progress"] = 100.0
                job_statuses[job_id]["completed_at"] = datetime.now()
                print(f"Updated job status to completed: {job_statuses[job_id]}")
            
            return JSONResponse(content={"message": "File uploaded and converted successfully", "job_id": job_id})
        except Exception as conversion_error:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in PDF conversion: {str(conversion_error)}\n{error_details}")
            
            if job_id in job_statuses:
                job_statuses[job_id]["status"] = "error"
                job_statuses[job_id]["error"] = str(conversion_error)
                print(f"Updated job status to error: {job_statuses[job_id]}")
            
            raise HTTPException(status_code=500, detail=f"PDF conversion error: {str(conversion_error)}")
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in local_upload: {str(e)}\n{error_details}")
        
        if job_id in job_statuses:
            job_statuses[job_id]["status"] = "error"
            job_statuses[job_id]["error"] = str(e)
            print(f"Updated job status to error: {job_statuses[job_id]}")
        
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

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

@router.get("/download/{job_id}", response_model=DownloadResponse)
async def get_download_url(job_id: str):
    """ダウンロード用のURLを取得"""
    try:
        if job_id not in job_statuses:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # ジョブが完了していない場合はエラー
        if job_statuses[job_id]["status"] != "completed":
            raise HTTPException(status_code=400, detail="Job not completed yet")
            
        # ダウンロードURLを生成
        download_url = generate_download_url(job_id)
        expires_at = datetime.now() + timedelta(seconds=settings.sign_url_exp)
        
        return DownloadResponse(
            download_url=download_url,
            expires_at=expires_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))            