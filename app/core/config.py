from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional
import os
import json

class Settings(BaseSettings):
    # GCP設定
    gcp_keypath: str = "./config/service_account.json"
    gcp_region: str
    gcp_project: Optional[str] = None
    
    # Cloud Storage設定
    gcs_bucket_image: Optional[str] = None     # 変換した画像を直接格納
    gcs_bucket_works: Optional[str] = None     # アップロードしたPDF・ZIPや変換圧縮したZIPなど、セッションデータを格納 (local_workspaceに相当)
    
    # 作業用スペース設定
    workspace_path: str = "tmp_workspace"
    
    # 署名付きURL設定
    sign_url_exp: int = 3600
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # サービスアカウントJSONファイルからproject_idを読み込む
        if self.gcp_region != "local" and os.path.exists(self.gcp_keypath):
            with open(self.gcp_keypath, 'r') as f:
                service_account = json.load(f)
                self.gcp_project = service_account.get('project_id')

    def get_session_dirpath(self, session_id: str) -> str:
        """セッションIDに基づいてストレージパスを取得"""
        if self.gcp_region == "local":
            return os.path.join(self.workspace_path, session_id)
        return f"{session_id}"

    def get_storage_path(self, session_id: str, job_id: str = None) -> str:
        """ジョブIDに基づいてストレージパスを取得"""
        if self.gcp_region == "local":
            return os.path.join(self.workspace_path, session_id, job_id)
        return f"{session_id}/{job_id}"

@lru_cache()
def get_settings() -> Settings:
    return Settings() 