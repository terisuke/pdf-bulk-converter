import asyncio
import os
import shutil
from app.services.converter import convert_pdf_to_images
from app.core.config import get_settings

async def test_conversion():
    settings = get_settings()
    job_id = "test-job"
    
    job_dir = os.path.join(settings.local_storage_path, job_id)
    os.makedirs(job_dir, exist_ok=True)
    print(f"Created job directory: {job_dir}")
    
    source_pdf = "./test.pdf"
    
    pdf_path = os.path.join(job_dir, "test.pdf")
    
    if os.path.exists(source_pdf):
        shutil.copy(source_pdf, pdf_path)
        print(f"Copied test PDF from {source_pdf} to {pdf_path}")
    else:
        print(f"Source PDF not found at {source_pdf}")
        return False
    
    print(f"Starting conversion of {pdf_path}")
    try:
        zip_path, image_paths = await convert_pdf_to_images(
            job_id=job_id, 
            pdf_path=pdf_path,
            dpi=300,
            format="png"
        )
        
        print(f"Conversion successful!")
        print(f"ZIP file created at: {zip_path}")
        print(f"Generated {len(image_paths)} images")
        
        for i, img_path in enumerate(image_paths):
            print(f"Image {i+1}: {img_path}")
            
        return True
    except Exception as e:
        import traceback
        print(f"Conversion failed with error: {str(e)}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = asyncio.run(test_conversion())
    print(f"Test {'succeeded' if success else 'failed'}")
