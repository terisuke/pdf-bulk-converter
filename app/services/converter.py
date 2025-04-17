import pypdfium2 as pdfium
from app.core.config import get_settings
import os
import zipfile
from pathlib import Path
from typing import List, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor

settings = get_settings()

async def convert_pdf_to_images(
    job_id: str,
    pdf_path: str,
    dpi: int = 300,
    format: str = "png"
) -> Tuple[str, List[str]]:
    """
    PDFを画像に変換し、ZIPファイルにまとめる
    
    Args:
        job_id: ジョブID
        pdf_path: PDFファイルのパス
        dpi: 出力画像のDPI
        format: 出力形式（"png" or "jpeg"）
    
    Returns:
        Tuple[ZIPファイルパス, 生成された画像ファイルのパスリスト]
    """
    # 出力ディレクトリの準備
    output_dir = os.path.join(settings.get_storage_path(job_id), "images")
    os.makedirs(output_dir, exist_ok=True)
    
    # PDFを読み込み
    pdf = pdfium.PdfDocument(pdf_path)
    page_count = len(pdf)
    
    # 画像変換用のスレッドプール
    with ThreadPoolExecutor() as executor:
        # 各ページを並列で変換
        futures = []
        for page_idx in range(page_count):
            page = pdf[page_idx]
            future = executor.submit(
                _convert_page,
                page,
                output_dir,
                page_idx,
                dpi,
                format
            )
            futures.append(future)
        
        # 変換結果を待機
        image_paths = []
        for future in futures:
            image_path = future.result()
            image_paths.append(image_path)
    
    # ZIPファイルの作成
    zip_path = os.path.join(settings.get_storage_path(job_id), "output.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for image_path in image_paths:
            zipf.write(image_path, os.path.basename(image_path))
    
    return zip_path, image_paths

def _convert_page(
    page: pdfium.PdfPage,
    output_dir: str,
    page_idx: int,
    dpi: int,
    format: str
) -> str:
    """
    単一ページを画像に変換
    
    Args:
        page: PDFページオブジェクト
        output_dir: 出力ディレクトリ
        page_idx: ページ番号
        dpi: 出力画像のDPI
        format: 出力形式
    
    Returns:
        生成された画像ファイルのパス
    """
    # ページをレンダリング
    bitmap = page.render(
        scale=dpi/72,  # PDFiumは72 DPIを基準とする
        format=pdfium.BitmapConv.pil_image
    )
    
    # 画像を保存
    output_path = os.path.join(
        output_dir,
        f"page_{page_idx + 1:04d}.{format}"
    )
    bitmap.save(output_path, format=format.upper())
    
    return output_path 