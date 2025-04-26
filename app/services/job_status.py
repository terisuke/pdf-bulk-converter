from enum import Enum
from typing import Dict, Optional
from datetime import datetime

class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobStatusManager:
    def __init__(self):
        self.jobs: Dict[str, Dict] = {}

    def create_job(self, job_id: str) -> None:
        self.jobs[job_id] = {
            "status": JobStatus.PENDING,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "error": None
        }

    def update_job_status(self, job_id: str, status: JobStatus, error: Optional[str] = None) -> None:
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = status
            self.jobs[job_id]["updated_at"] = datetime.now()
            if error:
                self.jobs[job_id]["error"] = error

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        return self.jobs.get(job_id)

job_status_manager = JobStatusManager() 