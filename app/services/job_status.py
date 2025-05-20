from enum import Enum
from typing import Dict, Optional
from datetime import datetime

class JobStatus(Enum):
    """Enumeration of possible states for a conversion job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobStatusManager:
    """Manage lifecycle and state of conversion jobs."""

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
        """Update status and timestamps for the specified job."""

        if job_id in self.jobs:
            self.jobs[job_id]["status"] = status
            self.jobs[job_id]["updated_at"] = datetime.now()
            if error:
                self.jobs[job_id]["error"] = error

    def get_status(self, job_id: str) -> Optional[Dict]:
        """Return status information for the given job if it exists."""

        return self.jobs.get(job_id)

    def cleanup_completed_jobs(self) -> None:
        """Remove completed or failed jobs from the internal store."""

        for job_id in list(self.jobs.keys()):
            status = self.jobs[job_id]["status"]
            if status in (JobStatus.COMPLETED, JobStatus.FAILED):
                del self.jobs[job_id]

job_status_manager = JobStatusManager() 