import os
import zipfile
from pathlib import Path
from typing import List, Tuple
import asyncio
import fitz
from app.core.job_status import JobStatus, job_status_manager
from datetime import datetime
import logging
from app.core.config import get_settings

# ロガーの設定
logger = logging.getLogger(__name__)

settings = get_settings()

async def convert_pdf_to_images(
    job_id: str,
    pdf_path: str,
    dpi: int = 300,
    format: str = "jpeg"
) -> Tuple[str, List[str]]:
    """
    PDFをJPEG画像に変換し、ZIPファイルにまとめる
    
    Args:
        job_id: ジョブID
        pdf_path: PDFファイルのパス
        dpi: 出力画像のDPI
        format: 出力形式（常にjpeg）
    
    Returns:
        Tuple[ZIPファイルパス, 生成された画像ファイルのパスリスト]
    """
    try:
        # 常にJPEGとして処理
        format = "jpeg"
        logger.info(f"変換開始: job_id={job_id}, pdf_path={pdf_path}, dpi={dpi}")
        
        # 出力ディレクトリの作成
        output_dir = os.path.join(settings.get_storage_path(job_id), "images")
        os.makedirs(output_dir, exist_ok=True)
        
        # PDFを画像に変換
        image_paths = []
        pdf_document = fitz.open(pdf_path)
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            # カラーモードとアルファチャンネルを指定
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72), alpha=False)
            
            # ページ番号を1から始める
            page_number = page_num + 1
            # 元のPDFファイル名を取得（拡張子なし）
            pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]
            # 出力ファイル名を設定（日本語対応）
            output_filename = f"{pdf_filename}_page_{page_number:03d}.jpeg"
            output_path = os.path.join(output_dir, output_filename)
            
            # JPEGとして保存（品質95%）
            pix.save(output_path, jpg_quality=95)
            image_paths.append(output_path)
            
            # 進捗状況を更新
            progress = (page_number / len(pdf_document)) * 100
            job_status = JobStatus(
                job_id=job_id,
                status="processing",
                message=f"ページ {page_number}/{len(pdf_document)} を変換中...",
                progress=progress,
                created_at=datetime.now()
            )
            job_status_manager.update_status(job_id, job_status)
            logger.info(f"ページ変換完了: {page_number}/{len(pdf_document)}")
        
        # ZIPファイルの作成
        zip_filename = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_images.zip"
        zip_path = os.path.join(settings.get_storage_path(job_id), zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for image_path in image_paths:
                arcname = os.path.basename(image_path)
                zipf.write(image_path, arcname)
        
        # 完了ステータスの更新
        completed_status = JobStatus(
            job_id=job_id,
            status="completed",
            message="変換が完了しました",
            progress=100,
            created_at=datetime.now()
        )
        job_status_manager.update_status(job_id, completed_status)
        logger.info(f"変換完了: job_id={job_id}")
        
        return zip_path, image_paths
        
    except Exception as e:
        # エラーが発生した場合、ステータスを更新
        error_message = f"変換中にエラーが発生しました: {str(e)}"
        logger.error(f"エラー発生: job_id={job_id}, error={str(e)}")
        error_status = JobStatus(
            job_id=job_id,
            status="error",
            message=error_message,
            progress=0,
            created_at=datetime.now()
        )
        job_status_manager.update_status(job_id, error_status)
        raise        