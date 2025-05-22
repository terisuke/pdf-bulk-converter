"""
Test script to verify PDF conversion through the API.
"""
import os
import json
import time
import logging
import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

API_BASE_URL = "http://localhost:8000"

def main():
    """Main function to test PDF conversion through the API."""
    try:
        test_file_path = "../test/test.pdf"
        if not os.path.exists(test_file_path):
            logger.error(f"Test file not found: {test_file_path}")
            return
            
        logger.info(f"Testing PDF conversion with file: {test_file_path}")
        
        logger.info("Creating a new session...")
        response = requests.post(f"{API_BASE_URL}/api/session", json={"dpi": 300})
        if response.status_code != 200:
            logger.error(f"Failed to create session: {response.text}")
            return
            
        session_data = response.json()
        session_id = session_data.get("session_id")
        logger.info(f"Session created with ID: {session_id}")
        
        logger.info("Getting upload URL...")
        response = requests.post(
            f"{API_BASE_URL}/api/upload-url",
            json={
                "filename": "test.pdf",
                "session_id": session_id,
                "content_type": "application/pdf",
                "dpi": 300
            }
        )
        if response.status_code != 200:
            logger.error(f"Failed to get upload URL: {response.text}")
            return
            
        upload_data = response.json()
        upload_url = upload_data.get("upload_url")
        job_id = upload_data.get("job_id")
        logger.info(f"Upload URL received for job ID: {job_id}")
        
        logger.info("Uploading the file...")
        with open(test_file_path, "rb") as f:
            file_content = f.read()
            
        headers = {"Content-Type": "application/pdf"}
        response = requests.put(upload_url, data=file_content, headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to upload file: {response.text}")
            return
            
        logger.info("File uploaded successfully")
        
        logger.info("Checking job status...")
        max_retries = 30
        retry_count = 0
        job_completed = False
        
        while retry_count < max_retries and not job_completed:
            response = requests.get(f"{API_BASE_URL}/api/job-status/{job_id}")
            if response.status_code != 200:
                logger.error(f"Failed to get job status: {response.text}")
                break
                
            lines = response.text.strip().split("\n")
            for line in lines:
                if line.startswith("data:"):
                    try:
                        data = json.loads(line[5:])
                        status = data.get("status")
                        progress = data.get("progress")
                        message = data.get("message")
                        logger.info(f"Job status: {status}, progress: {progress}%, message: {message}")
                        
                        if status == "completed":
                            job_completed = True
                            break
                        elif status == "error":
                            logger.error(f"Job failed: {message}")
                            return
                    except json.JSONDecodeError:
                        pass
            
            if not job_completed:
                logger.info("Waiting for job to complete...")
                time.sleep(2)
                retry_count += 1
        
        if not job_completed:
            logger.error("Job did not complete within the expected time")
            return
            
        logger.info("Job completed successfully")
        
        logger.info("PDF conversion test completed successfully")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
