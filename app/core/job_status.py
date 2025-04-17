from app.models.schemas import JobStatus
from typing import Dict
from datetime import datetime

class JobStatusManager:
    def __init__(self):
        self._statuses: Dict[str, JobStatus] = {}
    
    def update_status(self, job_id: str, status: JobStatus):
        """ジョブのステータスを更新"""
        self._statuses[job_id] = status
    
    def get_status(self, job_id: str) -> JobStatus:
        """ジョブのステータスを取得"""
        if job_id not in self._statuses:
            return JobStatus(
                job_id=job_id,
                status="not_found",
                progress=0,
                created_at=datetime.now(),
                message="ジョブが見つかりません"
            )
        return self._statuses[job_id]
    
    def delete_status(self, job_id: str):
        """ジョブのステータスを削除"""
        if job_id in self._statuses:
            del self._statuses[job_id]

# シングルトンインスタンスを作成
job_status_manager = JobStatusManager() 