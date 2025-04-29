from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UploadRequest(BaseModel):
    filename: str
    content_type: str
    dpi: Optional[int] = 300
    format: Optional[str] = "jpeg"
    start_number: Optional[int] = 1  # 連番開始番号

class UploadResponse(BaseModel):
    upload_url: str
    job_id: str

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    message: Optional[str] = None

class DownloadResponse(BaseModel):
    download_url: str
    expires_at: datetime 