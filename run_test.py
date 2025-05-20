import asyncio
import os
import shutil
import uuid
from pathlib import Path
from app.core.config import get_settings
from app.core.process import process_input
from app.core.job_status import job_status_manager

async def test_conversion():
    settings = get_settings()
    job_id = f"test-job-{uuid.uuid4().hex[:8]}"
    
    job_dir = os.path.join(settings.workspace_path, job_id)
    os.makedirs(job_dir, exist_ok=True)
    print(f"Created job directory: {job_dir}")
    
    # テスト用のPDFファイルパス
    source_pdf = "./test.pdf"
    
    # テスト用のPDFファイルが存在しない場合は、テスト用のディレクトリを作成
    if not os.path.exists(source_pdf):
        print(f"Source PDF not found at {source_pdf}")
        print("Creating a test directory with sample PDFs...")
        
        # テスト用のディレクトリを作成
        test_dir = Path("./test_files")
        test_dir.mkdir(exist_ok=True)
        
        # テスト用のZIPファイルを作成
        import zipfile
        zip_path = test_dir / "test_pdfs.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # サンプルPDFファイルを作成（実際のPDFファイルがない場合は、空のファイルを作成）
            sample_pdf = test_dir / "sample.pdf"
            with open(sample_pdf, 'wb') as f:
                f.write(b"%PDF-1.4\n%EOF\n")  # 最小限のPDFファイル
            zipf.write(sample_pdf, "sample.pdf")
        
        print(f"Created test ZIP file at: {zip_path}")
        input_path = str(zip_path)
    else:
        input_path = source_pdf
    
    print(f"Starting conversion of {input_path}")
    try:
        # process_input関数を使用して変換を実行
        output_dir = process_input(job_id, input_path, dpi=300)
        
        print(f"Conversion successful!")
        print(f"Output directory: {output_dir}")
        
        # 出力ディレクトリ内のファイルを表示
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            print(f"Generated {len(files)} files in output directory:")
            for file in files:
                print(f"- {file}")
        else:
            print("Output directory not found!")
        
        return True
    except Exception as e:
        import traceback
        print(f"Conversion failed with error: {str(e)}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = asyncio.run(test_conversion())
    print(f"Test {'succeeded' if success else 'failed'}")
