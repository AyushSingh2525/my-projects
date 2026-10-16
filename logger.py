import traceback
import logging
from database import get_db

logging.basicConfig(
    filename='app_errors.log',
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s: %(message)s'
)

def log_exception(endpoint: str, error: Exception):
    stack = traceback.format_exc()
    logging.error(f"Error in {endpoint}: {str(error)}\n{stack}")
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO error_logs (endpoint, error_message, stack_trace) VALUES (%s, %s, %s)",
            (endpoint, str(error), stack)
        )
        conn.close()
    except Exception as db_err:
        logging.critical(f"Failed to write error log to DB: {str(db_err)}")
        