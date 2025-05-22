import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logging.getLogger('app.api.upload').setLevel(logging.DEBUG)
logging.getLogger('app.services.converter').setLevel(logging.DEBUG)
logging.getLogger('app.core.session_status').setLevel(logging.DEBUG)
logging.getLogger('app.core.job_status').setLevel(logging.DEBUG)

print("Logging configuration loaded. Debug level enabled for all modules.")
