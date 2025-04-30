from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class SessionStatus(BaseModel):
    session_id: str
    status: str  # "pending", "processing", "completed", "failed"
    message: str
    progress: float  # 0-100
    image_num: int
    # created_at: datetime
    # total_files: Optional[int] = None
    # processed_files: Optional[int] = None
    # current_file: Optional[str] = None

class SessionStatusManager:
    def __init__(self):
        self.statuses: Dict[str, SessionStatus] = {}
    
    def update_status(self, status: SessionStatus):
        """セッションのステータスを更新"""
        self.statuses = status
        logger.info(f"セッションのステータスを更新: {status.status} ({status.progress:.2f}%)")
    
    def get_status(self) -> Optional[SessionStatus]:
        """セッションのステータスを取得"""
        return self.statuses.get()
    
    def update_progress(self, progress: float, message: Optional[str] = None):
        self.progress = progress
        if message:
            self.message = message
        logger.info(f"セッションの進捗を更新: {progress:.2f}%")

    def add_imagenum(self, image_cnt: int):
        self.image_num += image_cnt
        logger.info(f"画像連番を更新: {self.image_num:07d}")

    def set_imagenum(self, image_num: int):
        self.image_num = image_num
        logger.info(f"画像連番を更新: {self.image_num:07d}")

    def get_imagenum(self) -> int:
        return self.image_num

# シングルトンインスタンスを作成
session_status_manager = SessionStatusManager() 