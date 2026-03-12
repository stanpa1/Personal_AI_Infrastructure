#!/usr/bin/env python3
"""
Telegram message sender module.
Sends responses back to users via Telegram Bot API.
"""

import os
import logging
import requests
from typing import List, Optional

logger = logging.getLogger(__name__)

# Telegram message limit
MAX_MESSAGE_LENGTH = 4096

def get_bot_token() -> str:
    """Get Telegram bot token from environment"""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")
    return token

def send_typing_action(chat_id: int) -> bool:
    """Send 'typing...' indicator to user"""
    try:
        token = get_bot_token()
        url = f"https://api.telegram.org/bot{token}/sendChatAction"

        response = requests.post(url, json={
            'chat_id': chat_id,
            'action': 'typing'
        }, timeout=10)

        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Failed to send typing action: {e}")
        return False

def split_long_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> List[str]:
    """
    Split long message into chunks that fit Telegram's limit.
    Tries to split at paragraph boundaries, then sentence boundaries, then word boundaries.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break

        # Try to find a good split point
        chunk = remaining[:max_length]

        # Try paragraph break first
        split_at = chunk.rfind('\n\n')
        if split_at == -1 or split_at < max_length // 2:
            # Try single newline
            split_at = chunk.rfind('\n')
        if split_at == -1 or split_at < max_length // 2:
            # Try sentence end
            for sep in ['. ', '! ', '? ']:
                idx = chunk.rfind(sep)
                if idx > max_length // 2:
                    split_at = idx + 1
                    break
        if split_at == -1 or split_at < max_length // 2:
            # Try space
            split_at = chunk.rfind(' ')
        if split_at == -1 or split_at < max_length // 2:
            # Hard split
            split_at = max_length

        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()

    return chunks

def send_message(chat_id: int, text: str, parse_mode: Optional[str] = None) -> dict:
    """
    Send message to Telegram chat.
    Automatically splits long messages.

    Args:
        chat_id: Telegram chat ID
        text: Message text
        parse_mode: Optional parse mode ('Markdown', 'HTML', or None)

    Returns:
        dict with 'success', 'message_ids', and optional 'error'
    """
    try:
        token = get_bot_token()
        url = f"https://api.telegram.org/bot{token}/sendMessage"

        # Split message if needed
        chunks = split_long_message(text)
        message_ids = []

        for i, chunk in enumerate(chunks):
            payload = {
                'chat_id': chat_id,
                'text': chunk
            }

            if parse_mode:
                payload['parse_mode'] = parse_mode

            response = requests.post(url, json=payload, timeout=30)
            result = response.json()

            if result.get('ok'):
                msg_id = result.get('result', {}).get('message_id')
                if msg_id:
                    message_ids.append(msg_id)
                logger.info(f"Sent message chunk {i+1}/{len(chunks)} to chat {chat_id}")
            else:
                error_desc = result.get('description', 'Unknown error')
                logger.error(f"Failed to send message: {error_desc}")

                # If Markdown parsing failed, retry without parse_mode
                if parse_mode and 'parse' in error_desc.lower():
                    logger.info("Retrying without parse_mode...")
                    payload.pop('parse_mode', None)
                    response = requests.post(url, json=payload, timeout=30)
                    result = response.json()
                    if result.get('ok'):
                        msg_id = result.get('result', {}).get('message_id')
                        if msg_id:
                            message_ids.append(msg_id)
                    else:
                        return {
                            'success': False,
                            'error': result.get('description', 'Unknown error'),
                            'message_ids': message_ids
                        }
                else:
                    return {
                        'success': False,
                        'error': error_desc,
                        'message_ids': message_ids
                    }

        return {
            'success': True,
            'message_ids': message_ids,
            'chunks_sent': len(chunks)
        }

    except requests.Timeout:
        logger.error("Telegram API timeout")
        return {'success': False, 'error': 'Telegram API timeout'}
    except Exception as e:
        logger.exception(f"Failed to send Telegram message: {e}")
        return {'success': False, 'error': str(e)}

def send_audio_file(chat_id: int, file_path: str, caption: str = None) -> dict:
    """
    Send audio file to Telegram chat.

    Args:
        chat_id: Telegram chat ID
        file_path: Path to audio file (MP3, MP4, OGG, etc.)
        caption: Optional caption for the audio

    Returns:
        dict with 'success' and optional 'error'
    """
    try:
        token = get_bot_token()
        url = f"https://api.telegram.org/bot{token}/sendAudio"

        with open(file_path, 'rb') as f:
            files = {'audio': f}
            data = {'chat_id': chat_id}
            if caption:
                data['caption'] = caption[:1024]  # Telegram caption limit

            response = requests.post(url, files=files, data=data, timeout=120)
            result = response.json()

        if result.get('ok'):
            logger.info(f"Audio sent to chat {chat_id}: {file_path}")
            return {'success': True, 'message_id': result['result']['message_id']}
        else:
            error = result.get('description', 'Unknown error')
            logger.error(f"Failed to send audio: {error}")

            # If file too large for sendAudio (50MB), try sendDocument
            if 'too big' in error.lower() or 'file is too big' in error.lower():
                return send_document(chat_id, file_path, caption)

            return {'success': False, 'error': error}

    except Exception as e:
        logger.exception(f"Failed to send audio file: {e}")
        return {'success': False, 'error': str(e)}


def send_document(chat_id: int, file_path: str, caption: str = None) -> dict:
    """
    Send file as document to Telegram chat.
    Fallback for files too large for sendAudio.
    """
    try:
        token = get_bot_token()
        url = f"https://api.telegram.org/bot{token}/sendDocument"

        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': chat_id}
            if caption:
                data['caption'] = caption[:1024]

            response = requests.post(url, files=files, data=data, timeout=120)
            result = response.json()

        if result.get('ok'):
            logger.info(f"Document sent to chat {chat_id}: {file_path}")
            return {'success': True, 'message_id': result['result']['message_id']}
        else:
            error = result.get('description', 'Unknown error')
            logger.error(f"Failed to send document: {error}")
            return {'success': False, 'error': error}

    except Exception as e:
        logger.exception(f"Failed to send document: {e}")
        return {'success': False, 'error': str(e)}


def send_error_message(chat_id: int, error_type: str = "generic") -> dict:
    """Send user-friendly error message"""
    error_messages = {
        'timeout': "Przepraszam, przetwarzanie trwa zbyt długo. Spróbuj ponownie za chwilę.",
        'api_error': "Wystąpił błąd podczas przetwarzania. Spróbuj ponownie.",
        'generic': "Coś poszło nie tak. Spróbuj ponownie później."
    }

    message = error_messages.get(error_type, error_messages['generic'])
    return send_message(chat_id, message)
