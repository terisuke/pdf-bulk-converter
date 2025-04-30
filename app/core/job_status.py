from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class JobStatus(BaseModel):
    session_id: str
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    message: str
    progress: float  # 0-100
    created_at: datetime
    total_files: Optional[int] = None
    processed_files: Optional[int] = None
    current_file: Optional[str] = None

class JobStatusManager:
    def __init__(self):
        self._statuses: Dict[str, JobStatus] = {}
    
    def update_status(self, job_id: str, status: JobStatus):
        """ジョブのステータスを更新"""
        self._statuses[job_id] = status
        logger.info(f"ジョブ {job_id} のステータスを更新: {status.status} ({status.progress:.2f}%)")
    
    def get_status(self, job_id: str) -> Optional[JobStatus]:
        """ジョブのステータスを取得"""
        return self._statuses.get(job_id)
    
    def delete_status(self, job_id: str):
        """ジョブのステータスを削除"""
        if job_id in self._statuses:
            del self._statuses[job_id]
    
    def update_progress(self, job_id: str, progress: float, message: Optional[str] = None):
        if job_id in self._statuses:
            status = self._statuses[job_id]
            status.progress = progress
            if message:
                status.message = message
            self._statuses[job_id] = status
            logger.info(f"ジョブ {job_id} の進捗を更新: {progress:.2f}%")

# シングルトンインスタンスを作成
job_status_manager = JobStatusManager() 