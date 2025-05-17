import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple
import fitz
from app.core.job_status import JobStatus, job_status_manager
from app.core.session_status import SessionStatus, session_status_manager
from datetime import datetime
import logging
from app.core.config import get_settings

# ロガーの設定
logger = logging.getLogger(__name__)

settings = get_settings()

async def convert_1pdf_to_images(session_id: str, job_id: str, pdf_path: str, dpi: int, format: str, images_dir: str,) -> Tuple[str, List[str]]:
    """
    単一のPDFファイルを画像に変換する
    
    Args:
        session_id: セッションID
        job_id: ジョブID
        pdf_path: PDFファイルのパス
        dpi: 出力画像のDPI
        format: 出力画像のフォーマット
        images_dir: 出力ディレクトリ
        
    Returns:
        Tuple[str, List[str]]: 出力ディレクトリのパスと生成された画像ファイルのパスのリスト
    """
    # PDFファイル名を取得（拡張子なし）
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # PDFを開く
    pdf_document = fitz.open(pdf_path)
    total_pages = len(pdf_document)
    image_paths = []

    imagenum_start = session_status_manager.get_imagenum(session_id)
    
    # 各ページを画像に変換
    for page_num in range(total_pages):
        page = pdf_document[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
        
        # 画像ファイル名を生成
        imagenum_current = imagenum_start + page_num
        image_filename = f"{imagenum_current:07d}.{format}"
        image_path = os.path.join(images_dir, image_filename)
        
        # 画像を保存
        pix.save(image_path)
        image_paths.append(image_path)
        
        # 進捗を更新
        progress = (page_num + 1) / total_pages * 100
        status = JobStatus(
            session_id=session_id,
            job_id=job_id,
            status="processing",
            message=f"ページ変換完了: {page_num + 1}/{total_pages}",
            progress=progress,
            created_at=datetime.now()
        )
        job_status_manager.update_status(job_id, status)
    
    # PDFを閉じる
    session_status_manager.add_imagenum(session_id, total_pages)
    pdf_document.close()
    
    return images_dir, image_paths

# 複数のPDFファイルを処理する関数を追加
async def convert_pdfs_to_images(session_id: str, job_id: str, pdf_paths: List[str], dpi: int = 300, format: str = "jpeg") -> Tuple[str, List[str]]:
    """
    PDFファイルを画像変換する (複数対応)
    
    Args:
        session_id: セッションID
        job_id: ジョブID
        pdf_paths: PDFファイルのパスリスト
        dpi: 出力画像のDPI
        format: 出力形式（常にjpeg）
        imagenum_start: 
    
    Returns:
        Tuple[画像格納ディレクトリ, 生成された画像ファイルのパスリスト]
    """
    try:
        # 常にJPEGとして処理
        format = "jpeg"
        logger.info(f"複数PDF変換開始: session_id={session_id}, job_id={job_id}, pdf_count={len(pdf_paths)}, dpi={dpi}")
        
        # 出力ディレクトリの作成
        images_dir = os.path.join(settings.get_session_dirpath(session_id), "images")
        os.makedirs(images_dir, exist_ok=True)
        
        # すべての画像ファイルのパスを保持
        all_image_paths = []
        
        # 各PDFファイルを処理
        total_files = len(pdf_paths)
        for i, pdf_path in enumerate(pdf_paths, 1):
            # PDFファイルを処理
            _, image_paths = await convert_1pdf_to_images(session_id, job_id, pdf_path, dpi, format, images_dir)
            all_image_paths.extend(image_paths)
            
            # 全体の進捗を更新
            total_progress = (i / total_files) * 100
            status = JobStatus(
                session_id=session_id,
                job_id=job_id,
                status="processing",
                message=f"PDFファイル {i}/{total_files} を処理中",
                progress=total_progress,
                created_at=datetime.now()
            )
            job_status_manager.update_status(job_id, status)
        
        # 完了ステータスを設定
        complete_status = JobStatus(
            session_id=session_id,
            job_id=job_id,
            status="converted",
            message=f"ジョブ {job_id} のファイルの画像変換が完了しました",
            progress=100,
            created_at=datetime.now()
        )
        job_status_manager.update_status(job_id, complete_status)
        
        return images_dir, all_image_paths
        
    except Exception as e:
        # エラーが発生した場合、ステータスを更新
        error_message = f"変換中にエラーが発生しました: {str(e)}"
        logger.error(f"エラー発生: job_id={job_id}, error={str(e)}")
        error_status = JobStatus(
            session_id=session_id,
            job_id=job_id,
            status="error",
            message=error_message,
            progress=0,
            created_at=datetime.now()
        )
        job_status_manager.update_status(job_id, error_status)
        raise

# ZIPファイルの作成
def create_zip_file(session_id: str, image_paths: List[str]) -> str:
    """
    画像ファイルをZIPにまとめる
    
    Args:
        session_id: セッションID
        image_paths: 画像ファイルのパスのリスト
        
    Returns:
        str: 作成されたZIPファイルのパス
    """
    # 最初の画像ファイル名からベース名を取得
    base_name = os.path.splitext(os.path.basename(image_paths[0]))[0].split('_page')[0]
    zip_filename = "all_pdfs_images.zip"
    zip_path = os.path.join(settings.get_session_dirpath(session_id), zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for image_path in image_paths:
            # ファイル名のみを取得（ディレクトリパスを除外）
            arcname = os.path.basename(image_path)
            # UTF-8でファイル名を保存
            zipf.write(image_path, arcname)
    
    current_status: SessionStatus = session_status_manager.get_status(session_id)
    status = SessionStatus(
        session_id=session_id,
        status="completed",
        message="変換が完了しました",
        progress=100,
        pdf_num=current_status.pdf_num,
        image_num=current_status.image_num,
        created_at=datetime.now()
    )

    session_status_manager.update_status(session_id, status)

    return zip_path