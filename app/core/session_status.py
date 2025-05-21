from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel
from app.models.schemas import SessionStatus

import logging
logger = logging.getLogger(__name__)

class SessionStatusManager:
    def __init__(self):
        self._statuses: Dict[str, SessionStatus] = {}
    
    def update_status(self, session_id: str, status: SessionStatus):
        """セッションのステータスを更新"""
        self._statuses[session_id] = status
        logger.info(f"セッションのステータスを更新: {status.status} ({status.progress:.2f}%)")
    
    def get_status(self, session_id: str) -> Optional[SessionStatus]:
        """セッションのステータスを取得"""
        return self._statuses.get(session_id)
    
    def update_progress(self, session_id: str, progress: float, message: Optional[str] = None):
        if session_id in self._statuses:
            status = self._statuses[session_id]
            status.progress = progress
            if message:
                status.message = message
            self._statuses[session_id] = status
            logger.info(f"セッション {session_id} の進捗を更新: {progress:.2f}%")

    def add_imagenum(self, session_id: str, image_cnt: int):
        status = self._statuses.get(session_id)
        if status is None:
            logger.error("Session %s not found when adding image number", session_id)
            return
        status.image_num += image_cnt
        logger.info("画像連番を更新: %07d", status.image_num)

    def set_imagenum(self, session_id: str, image_num: int):
        status = self._statuses.get(session_id)
        if status is None:
            logger.error("Session %s not found when setting image number", session_id)
            return
        status.image_num = image_num
        logger.info("画像連番を更新: %07d", status.image_num)

    def get_imagenum(self, session_id: str) -> int:
        status = self._statuses.get(session_id)
        if status is None:
            logger.error("Session %s not found when getting image number", session_id)
            return 0
        return status.image_num

# シングルトンインスタンスを作成
session_status_manager = SessionStatusManager() 