import os
import zipfile
from pathlib import Path
from typing import List, Set
import asyncio
import logging
from app.core.config import get_settings
from app.services.converter import convert_pdf_to_images
from datetime import datetime
from app.services.job_status import JobStatus, job_status_manager

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
    
    # 除外するパターン
    exclude_patterns = [
        '__MACOSX',
        '._',
        '.DS_Store'
    ]
    
    # ディレクトリ内のPDFファイルを再帰的に検索
    for root, dirs, files in os.walk(directory_path):
        # 除外パターンに一致するディレクトリをスキップ
        dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
        
        for file in files:
            # 除外パターンに一致するファイルをスキップ
            if any(pattern in file for pattern in exclude_patterns):
                continue
                
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

async def process_multiple_files(job_id: str, file_paths: List[str], dpi: int = 300) -> List[str]:
    """
    複数のファイルを処理
    
    Args:
        job_id: ジョブID
        file_paths: 処理するファイルのパスリスト
        dpi: 出力画像のDPI
    
    Returns:
        処理されたPDFファイルのパスリスト
    """
    processed_files = []
    total_files = len(file_paths)
    
    for i, file_path in enumerate(file_paths, 1):
        try:
            if file_path.lower().endswith('.zip'):
                processed = await process_zip(job_id, file_path, dpi)
                processed_files.extend(processed)
            elif file_path.lower().endswith('.pdf'):
                await convert_pdf_to_images(job_id, file_path, dpi)
                processed_files.append(file_path)
            else:
                logger.warning(f"未対応のファイル形式: {file_path}")
                continue
                
            # 進捗状況を更新
            progress = (i / total_files) * 100
            status = JobStatus(
                job_id=job_id,
                status="processing",
                message=f"ファイル {i}/{total_files} を処理中...",
                progress=progress,
                created_at=datetime.now()
            )
            job_status_manager.update_status(job_id, status)
            
        except Exception as e:
            logger.error(f"ファイル処理エラー: {file_path} - {str(e)}")
            continue
    
    return processed_files 