import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path('/opt/inbox-webhook')
load_dotenv(BASE_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/inbox-webhook/logs/worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Directories
QUEUE_DIR = BASE_DIR / 'queue'
PROCESSING_DIR = BASE_DIR / 'processing'
DONE_DIR = BASE_DIR / 'done'
FAILED_DIR = BASE_DIR / 'failed'

POLL_INTERVAL = 2  # seconds
PROCESS_TIMEOUT = 600  # 10 minutes (increased for Claude API calls)

def get_oldest_event():
    """Get the oldest event from queue directory"""
    json_files = list(QUEUE_DIR.glob('*.json'))
    if not json_files:
        return None

    # Sort by modification time (oldest first)
    oldest = min(json_files, key=lambda p: p.stat().st_mtime)
    return oldest

def move_to_processing(event_path: Path) -> Path:
    """Move event from queue to processing"""
    dest = PROCESSING_DIR / event_path.name
    event_path.rename(dest)
    logger.info(f"Moved {event_path.name} to processing/")
    return dest

def move_to_done(event_path: Path, result: dict):
    """Move event to done and save result"""
    # Move event JSON
    dest = DONE_DIR / event_path.name
    event_path.rename(dest)

    # Save result
    result_path = DONE_DIR / event_path.name.replace('.json', '.result.json')
    with open(result_path, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    logger.info(f"Moved {event_path.name} to done/")

def move_to_failed(event_path: Path, error: str):
    """Move event to failed and save error"""
    # Move event JSON
    dest = FAILED_DIR / event_path.name
    event_path.rename(dest)

    # Save error
    error_path = FAILED_DIR / event_path.name.replace('.json', '.error.txt')
    with open(error_path, 'w') as f:
        f.write(f"Error at: {datetime.now().isoformat()}\n")
        f.write(f"Error: {error}\n")

    logger.error(f"Moved {event_path.name} to failed/: {error}")

def process_event(event_path: Path):
    """Process a single event by calling process_event.py"""
    try:
        logger.info(f"Processing event: {event_path.name}")

        # Call process_event.py with event path as argument
        venv_python = BASE_DIR / 'venv' / 'bin' / 'python3'
        process_script = BASE_DIR / 'process_event.py'

        # Pass environment variables to subprocess
        env = os.environ.copy()

        result = subprocess.run(
            [str(venv_python), str(process_script), str(event_path)],
            capture_output=True,
            text=True,
            timeout=PROCESS_TIMEOUT,
            env=env
        )

        if result.returncode == 0:
            # Success - parse result from stdout
            try:
                result_data = json.loads(result.stdout)
            except json.JSONDecodeError:
                result_data = {
                    "status": "success",
                    "output": result.stdout,
                    "processed_at": datetime.now().isoformat()
                }

            move_to_done(event_path, result_data)
        else:
            # Failed
            error_msg = result.stderr or result.stdout or "Unknown error"
            move_to_failed(event_path, error_msg)

    except subprocess.TimeoutExpired:
        move_to_failed(event_path, f"Processing timeout ({PROCESS_TIMEOUT} seconds)")
    except Exception as e:
        logger.exception(f"Error processing {event_path.name}")
        move_to_failed(event_path, str(e))

def main():
    logger.info(f"Worker started, polling queue every {POLL_INTERVAL} seconds (timeout: {PROCESS_TIMEOUT}s)...")

    while True:
        try:
            # Check for events in queue
            event_path = get_oldest_event()

            if event_path:
                # Move to processing
                processing_path = move_to_processing(event_path)

                # Process the event
                process_event(processing_path)
            else:
                # No events, sleep
                time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
            sys.exit(0)
        except Exception as e:
            logger.exception("Unexpected error in worker loop")
            time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    main()
