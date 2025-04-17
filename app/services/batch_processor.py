import os
import zipfile
from pathlib import Path
from typing import List, Set
import asyncio
import logging
from app.core.config import get_settings
from app.services.converter import convert_pdf_to_images

logger = logging.getLogger(__name__)
settings = get_settings()

async def process_directory(
    job_id: str,
    directory_path: str,
    dpi: int = 300
) -> List[str]:
    """
    ディレクトリ内のPDFファイルを再帰的に処理
    
    Args:
        job_id: ジョブID
        directory_path: 処理対象ディレクトリのパス
        dpi: 出力画像のDPI
    
    Returns:
        処理されたPDFファイルのパスリスト
    """
    processed_files = []
    
    # ディレクトリ内のPDFファイルを再帰的に検索
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                try:
                    # 相対パスを取得（ZIP内のパス構造を維持するため）
                    rel_path = os.path.relpath(pdf_path, directory_path)
                    # 出力ディレクトリを作成
                    output_dir = os.path.join(settings.get_storage_path(job_id), "pdfs", os.path.dirname(rel_path))
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # PDFを変換
                    await convert_pdf_to_images(job_id, pdf_path, dpi)
                    processed_files.append(pdf_path)
                    logger.info(f"PDF処理完了: {pdf_path}")
                except Exception as e:
                    logger.error(f"PDF処理エラー: {pdf_path}, error={str(e)}")
    
    return processed_files

async def process_zip(
    job_id: str,
    zip_path: str,
    dpi: int = 300
) -> List[str]:
    """
    ZIPファイル内のPDFファイルを処理
    
    Args:
        job_id: ジョブID
        zip_path: ZIPファイルのパス
        dpi: 出力画像のDPI
    
    Returns:
        処理されたPDFファイルのパスリスト
    """
    processed_files = []
    extract_dir = os.path.join(settings.get_storage_path(job_id), "extracted")
    os.makedirs(extract_dir, exist_ok=True)
    
    try:
        # ZIPファイルを展開
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # 展開したディレクトリを処理
        processed_files = await process_directory(job_id, extract_dir, dpi)
        
    except Exception as e:
        logger.error(f"ZIP処理エラー: {zip_path}, error={str(e)}")
        raise
    finally:
        # 展開したファイルを削除
        if os.path.exists(extract_dir):
            import shutil
            shutil.rmtree(extract_dir)
    
    return processed_files

async def process_input(
    job_id: str,
    input_path: str,
    dpi: int = 300
) -> List[str]:
    """
    入力（ファイル/ディレクトリ/ZIP）を処理
    
    Args:
        job_id: ジョブID
        input_path: 入力パス
        dpi: 出力画像のDPI
    
    Returns:
        処理されたPDFファイルのパスリスト
    """
    if os.path.isfile(input_path):
        if input_path.lower().endswith('.zip'):
            return await process_zip(job_id, input_path, dpi)
        elif input_path.lower().endswith('.pdf'):
            await convert_pdf_to_images(job_id, input_path, dpi)
            return [input_path]
    elif os.path.isdir(input_path):
        return await process_directory(job_id, input_path, dpi)
    
    raise ValueError(f"未対応の入力形式: {input_path}") 