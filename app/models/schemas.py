from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UploadRequest(BaseModel):
    session_id: str
    filename: str
    content_type: str
    dpi: Optional[int] = 300
    format: Optional[str] = "jpeg"
    start_number: Optional[int] = 1  # 連番開始番号

class SessionResponse(BaseModel):
    session_id: str

class UploadResponse(BaseModel):
    upload_url: str
    session_id: str
    job_id: str

class SessionStatus(BaseModel):
    session_id: str
    status: str     # "pending", "processing", "converted", "completed", "failed"
    message: str
    progress: float
    pdf_num: int
    image_num: int
    created_at: datetime

class JobStatus(BaseModel):
    session_id: str
    job_id: str
    status: str     # "pending", "processing", "converted", "completed", "failed"
    progress: float
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    message: Optional[str] = None

class DownloadResponse(BaseModel):
    download_url: str
    expires_at: datetime 