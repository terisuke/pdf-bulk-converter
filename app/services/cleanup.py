import os
import shutil
from pathlib import Path
from app.core.config import get_settings

def cleanup_temp_files(job_id: str) -> None:
    """
    ジョブの一時ファイルを削除する
    
    Args:
        job_id: ジョブID
    """
    settings = get_settings()
    job_dir = os.path.join(settings.local_storage_path, job_id)
    
    # ジョブディレクトリが存在する場合は削除
    if os.path.exists(job_dir):
        shutil.rmtree(job_dir) 