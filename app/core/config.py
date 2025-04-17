from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # 環境設定
    environment: str = "local"  # "local" or "cloud"
    
    # GCP設定
    gcp_project: str = ""
    region: str = "asia-northeast1"
    
    # Cloud Storage設定
    bucket_raw: str = "pdf-raw-bucket"
    bucket_zip: str = "pdf-zip-bucket"
    
    # ローカルストレージ設定
    local_storage_path: str = "local_storage"
    
    # 署名付きURL設定
    sign_url_exp: int = 3600
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_storage_path(self, job_id: str) -> str:
        """ジョブIDに基づいてストレージパスを取得"""
        if self.environment == "local":
            return os.path.join(self.local_storage_path, job_id)
        return f"{job_id}"

@lru_cache()
def get_settings() -> Settings:
    return Settings() 