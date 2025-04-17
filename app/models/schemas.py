from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UploadRequest(BaseModel):
    filename: str
    content_type: str

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

class DownloadResponse(BaseModel):
    download_url: str
    expires_at: datetime 