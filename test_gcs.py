"""
Test script to verify GCS connectivity and bucket access.
"""
import os
import json
import logging
from google.cloud import storage
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

def main():
    """Main function to test GCS connectivity and bucket access."""
    try:
        gcp_region = os.getenv("GCP_REGION")
        gcp_keypath = os.getenv("GCP_KEYPATH")
        gcs_bucket_image = os.getenv("GCS_BUCKET_IMAGE")
        gcs_bucket_works = os.getenv("GCS_BUCKET_WORKS")
        
        logger.info(f"GCP Region: {gcp_region}")
        logger.info(f"GCP Key Path: {gcp_keypath}")
        logger.info(f"GCS Bucket Image: {gcs_bucket_image}")
        logger.info(f"GCS Bucket Works: {gcs_bucket_works}")
        
        try:
            with open(gcp_keypath, "r") as f:
                credentials_info = json.load(f)
            client = storage.Client.from_service_account_info(credentials_info)
            logger.info(f"GCS client initialized for project: {client.project}")
        except FileNotFoundError as exc:
            logger.error(f"GCP key file not found: {gcp_keypath}")
            raise FileNotFoundError(f"GCP key file not found: {gcp_keypath}") from exc
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {str(e)}")
            raise RuntimeError(f"Failed to initialize GCS client: {str(e)}") from e
        
        try:
            bucket_image = client.bucket(gcs_bucket_image)
            exists = bucket_image.exists()
            logger.info(f"Bucket {gcs_bucket_image} exists: {exists}")
            
            bucket_works = client.bucket(gcs_bucket_works)
            exists = bucket_works.exists()
            logger.info(f"Bucket {gcs_bucket_works} exists: {exists}")
        except Exception as e:
            logger.error(f"Failed to check bucket existence: {str(e)}")
            raise
        
        try:
            logger.info(f"Listing contents of bucket: {gcs_bucket_works}")
            blobs = list(client.list_blobs(gcs_bucket_works))
            for blob in blobs:
                logger.info(f"- {blob.name}")
                
            logger.info(f"Listing contents of bucket: {gcs_bucket_image}")
            blobs = list(client.list_blobs(gcs_bucket_image))
            for blob in blobs:
                logger.info(f"- {blob.name}")
        except Exception as e:
            logger.error(f"Failed to list bucket contents: {str(e)}")
            raise
        
        try:
            test_file_path = "test/test.pdf"
            if os.path.exists(test_file_path):
                blob = bucket_works.blob("test_upload/test.pdf")
                blob.upload_from_filename(test_file_path)
                logger.info(f"Successfully uploaded {test_file_path} to {gcs_bucket_works}/test_upload/test.pdf")
            else:
                logger.error(f"Test file not found: {test_file_path}")
        except Exception as e:
            logger.error(f"Failed to upload test file: {str(e)}")
            raise
            
        logger.info("GCS connectivity and bucket access test completed successfully")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
