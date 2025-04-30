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
        self._statuses.get(session_id).image_num += image_cnt
        logger.info(f"画像連番を更新: {self._statuses.get(session_id).image_num:07d}")

    def set_imagenum(self, session_id: str, image_num: int):
        self._statuses.get(session_id).image_num = image_num
        logger.info(f"画像連番を更新: {self._statuses.get(session_id).image_num:07d}")

    def get_imagenum(self, session_id: str) -> int:
        return self._statuses.get(session_id).image_num

# シングルトンインスタンスを作成
session_status_manager = SessionStatusManager() 