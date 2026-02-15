#!/usr/bin/env python3
"""
Process incoming Telegram events.
Downloads files from GDrive, transcribes audio, analyzes images,
and handles Claude queries for @pai triggers.
"""

import os
import sys
import json
import logging
import base64
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import openai

# Load environment variables
BASE_DIR = Path('/opt/inbox-webhook')
load_dotenv(BASE_DIR / '.env')

# Import local modules
from claude_handler import handle_claude_query, should_process_with_claude
from telegram_sender import send_message, send_typing_action, send_error_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DOWNLOADS_DIR = BASE_DIR / 'downloads'
CREDENTIALS_PATH = BASE_DIR / 'credentials.json'

# File extension mapping based on MIME types
MIME_TO_EXT = {
    'audio/ogg': '.ogg',
    'audio/mpeg': '.mp3',
    'audio/mp4': '.m4a',
    'audio/wav': '.wav',
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp',
    'text/plain': '.txt',
    'application/pdf': '.pdf',
    'video/mp4': '.mp4',
}

# Audio extensions for transcription
AUDIO_EXTENSIONS = {'.ogg', '.mp3', '.m4a', '.wav', '.webm', '.mp4', '.mpeg', '.mpga'}

# Image extensions for vision analysis
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


def get_openai_client():
    """Get OpenAI client"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return None
    return openai.OpenAI(api_key=api_key)


def get_drive_service():
    """Initialize Google Drive API service"""
    if not CREDENTIALS_PATH.exists():
        logger.warning("No credentials.json found - skipping GDrive download")
        return None

    try:
        creds = service_account.Credentials.from_service_account_file(
            str(CREDENTIALS_PATH),
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        logger.error(f"Failed to initialize Drive service: {e}")
        return None


def download_file_from_drive(service, file_id: str, event_dir: Path, event_type: str) -> dict:
    """Download file from Google Drive"""
    try:
        # Get file metadata first
        file_meta = service.files().get(fileId=file_id, fields='name,mimeType,size').execute()
        mime_type = file_meta.get('mimeType', '')
        original_name = file_meta.get('name', 'unknown')
        file_size = file_meta.get('size', 0)

        logger.info(f"Downloading: {original_name} ({mime_type}, {file_size} bytes)")

        # Determine file extension
        ext = MIME_TO_EXT.get(mime_type, '')
        if not ext and '.' in original_name:
            ext = '.' + original_name.rsplit('.', 1)[-1]

        # Create filename based on event type
        filename = f"{event_type}{ext}"
        file_path = event_dir / filename

        # Download file
        request = service.files().get_media(fileId=file_id)
        with open(file_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.info(f"Download progress: {int(status.progress() * 100)}%")

        logger.info(f"Downloaded to: {file_path}")

        return {
            'downloaded': True,
            'local_path': str(file_path),
            'filename': filename,
            'mime_type': mime_type,
            'original_name': original_name,
            'size_bytes': int(file_size) if file_size else os.path.getsize(file_path)
        }

    except Exception as e:
        logger.error(f"Failed to download file {file_id}: {e}")
        return {
            'downloaded': False,
            'error': str(e)
        }


def transcribe_audio(file_path: Path) -> dict:
    """Transcribe audio file using OpenAI Whisper API"""
    client = get_openai_client()
    if not client:
        return {'transcribed': False, 'error': 'No OpenAI API key configured'}

    try:
        logger.info(f"Transcribing audio: {file_path}")

        with open(file_path, 'rb') as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pl"  # Polish, can be auto-detected
            )

        transcription = response.text
        logger.info(f"Transcription complete: {len(transcription)} chars")

        return {
            'transcribed': True,
            'text': transcription,
            'language': 'pl'
        }

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return {'transcribed': False, 'error': str(e)}


def analyze_image(file_path: Path, caption: str = None) -> dict:
    """Analyze image using GPT-4 Vision"""
    client = get_openai_client()
    if not client:
        return {'analyzed': False, 'error': 'No OpenAI API key configured'}

    try:
        logger.info(f"Analyzing image: {file_path}")

        # Read and encode image
        with open(file_path, 'rb') as img_file:
            image_data = base64.b64encode(img_file.read()).decode('utf-8')

        # Determine mime type
        ext = file_path.suffix.lower()
        mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
                    '.gif': 'image/gif', '.webp': 'image/webp'}
        mime_type = mime_map.get(ext, 'image/jpeg')

        # Build prompt
        prompt = "Opisz szczegółowo co widzisz na tym obrazku. Jeśli jest tekst, przepisz go (OCR)."
        if caption:
            prompt += f"\n\nPodpis użytkownika: {caption}"

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )

        description = response.choices[0].message.content
        logger.info(f"Image analysis complete: {len(description)} chars")

        return {
            'analyzed': True,
            'description': description,
            'model': 'gpt-4o'
        }

    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        return {'analyzed': False, 'error': str(e)}


def load_event(event_path: Path) -> dict:
    """Load event JSON"""
    with open(event_path, 'r') as f:
        return json.load(f)


def get_chat_id(event: dict) -> int:
    """Extract chat_id from event metadata"""
    metadata = event.get('metadata', {})

    # Try different possible locations
    if 'chat_id' in metadata:
        return int(metadata['chat_id'])
    if 'from_id' in metadata:
        return int(metadata['from_id'])
    if 'user_id' in metadata:
        return int(metadata['user_id'])

    # Check nested structure
    if 'message' in metadata:
        msg = metadata['message']
        if 'chat' in msg:
            return int(msg['chat'].get('id', 0))
        if 'from' in msg:
            return int(msg['from'].get('id', 0))

    return 0


def get_message_text(event: dict, local_file: str = None) -> str:
    """Extract text from event"""
    metadata = event.get('metadata', {})

    # Direct text field
    if 'text' in metadata:
        return metadata['text']

    # Text preview (from n8n)
    if 'text_preview' in metadata:
        return metadata['text_preview']

    # Caption for media
    if 'caption' in metadata:
        return metadata['caption']

    # Nested message structure
    if 'message' in metadata:
        msg = metadata['message']
        return msg.get('text', '') or msg.get('caption', '')

    # Read from downloaded text file if available
    if local_file and local_file.endswith('.txt'):
        try:
            with open(local_file, 'r') as f:
                return f.read().strip()
        except:
            pass

    return ''


def process_event(event_path: Path):
    """Main processing function"""
    try:
        # Load event
        event = load_event(event_path)
        event_id = event['event_id']
        event_type = event['type']
        drive_file_id = event.get('drive_file_id')

        logger.info(f"Processing {event_type.upper()} event: {event_id}")

        # Get chat_id for potential response
        chat_id = get_chat_id(event)
        message_text = get_message_text(event)

        # Create event directory
        event_dir = DOWNLOADS_DIR / event_id
        event_dir.mkdir(parents=True, exist_ok=True)

        # Initialize result
        result = {
            'event_id': event_id,
            'type': event_type,
            'drive_path': event.get('drive_path', ''),
            'processed_at': datetime.now().isoformat(),
            'status': 'success'
        }

        transcription = None
        image_description = None

        # Download file from Google Drive if file_id exists
        if drive_file_id:
            service = get_drive_service()
            if service:
                download_result = download_file_from_drive(service, drive_file_id, event_dir, event_type)
                result['download'] = download_result

                if download_result.get('downloaded'):
                    local_path = Path(download_result['local_path'])
                    result['local_file'] = str(local_path)
                    logger.info(f"File downloaded: {local_path}")

                    # Transcribe audio if applicable
                    if local_path.suffix.lower() in AUDIO_EXTENSIONS:
                        transcription_result = transcribe_audio(local_path)
                        result['transcription'] = transcription_result
                        if transcription_result.get('transcribed'):
                            transcription = transcription_result['text']

                    # Analyze image if applicable
                    elif local_path.suffix.lower() in IMAGE_EXTENSIONS:
                        image_result = analyze_image(local_path, message_text)
                        result['image_analysis'] = image_result
                        if image_result.get('analyzed'):
                            image_description = image_result['description']

                else:
                    result['status'] = 'partial'
                    result['warning'] = 'File download failed'
            else:
                result['warning'] = 'No GDrive credentials - metadata only'
        else:
            result['note'] = 'No drive_file_id - metadata only'

        # Add metadata from original event
        if 'metadata' in event:
            result['source_metadata'] = event['metadata']

        # === CLAUDE HANDLER INTEGRATION ===
        # Check for @pai trigger in text or transcription
        text_to_check = message_text or transcription or ''

        # For voice messages, also check transcription
        if event_type == 'voice' and transcription:
            text_to_check = transcription

        if should_process_with_claude(text_to_check) and chat_id:
            logger.info(f"@pai trigger detected, processing with Claude...")

            # Send typing indicator
            send_typing_action(chat_id)

            # Process with Claude
            should_respond, claude_response = handle_claude_query(
                text_to_check,
                transcription=transcription if event_type == 'voice' else None
            )

            if should_respond and claude_response:
                result['claude_response'] = {
                    'triggered': True,
                    'query': text_to_check,
                    'response_length': len(claude_response)
                }

                # Send response to Telegram
                send_result = send_message(chat_id, claude_response)
                result['telegram_response'] = send_result

                if send_result.get('success'):
                    logger.info(f"Response sent to Telegram chat {chat_id}")
                else:
                    logger.error(f"Failed to send Telegram response: {send_result.get('error')}")

        # Save complete metadata to event directory
        metadata_path = event_dir / 'metadata.json'
        full_metadata = {**event, 'processing_result': result}
        with open(metadata_path, 'w') as f:
            json.dump(full_metadata, f, indent=2, ensure_ascii=False)

        result['event_dir'] = str(event_dir)

        # Return result as JSON to stdout
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    except Exception as e:
        logger.exception(f"Error processing event: {e}")

        # Try to send error message if we have chat_id
        try:
            if chat_id:
                send_error_message(chat_id, 'generic')
        except:
            pass

        error_result = {
            'status': 'error',
            'error': str(e),
            'processed_at': datetime.now().isoformat()
        }
        print(json.dumps(error_result, indent=2), file=sys.stderr)
        return 1


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: process_event.py <event_json_path>", file=sys.stderr)
        sys.exit(1)

    event_path = Path(sys.argv[1])
    if not event_path.exists():
        print(f"Event file not found: {event_path}", file=sys.stderr)
        sys.exit(1)

    sys.exit(process_event(event_path))
