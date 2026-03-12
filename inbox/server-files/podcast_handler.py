#!/usr/bin/env python3
"""
NotebookLM Podcast Generator handler.
Generates audio podcasts from URLs, text, or YouTube videos using NotebookLM API.
Also supports YouTube transcript extraction.

Triggers:
  @pai podcast: <URL or text>
  @pai podcast debate: <URL>
  @pai podcast brief: <URL>
  @pai podcast critique: <URL>
  @pai transcript: <YouTube URL>
"""

import os
import re
import json
import asyncio
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict

logger = logging.getLogger(__name__)

# Directories
BASE_DIR = Path("/opt/inbox-webhook")
PODCAST_DIR = BASE_DIR / "podcasts"
NOTEBOOKLM_HOME = BASE_DIR / ".notebooklm"

# Trigger patterns
PODCAST_PATTERNS = [
    r'^@pai\s+podcast\s+debate:?\s+(.+)$',
    r'^@pai\s+podcast\s+brief:?\s+(.+)$',
    r'^@pai\s+podcast\s+critique:?\s+(.+)$',
    r'^@pai\s+podcast\s+krótki:?\s+(.+)$',
    r'^@pai\s+podcast:?\s+(.+)$',
    r'^@pai\s+zrób\s+podcast:?\s+(.+)$',
    r'^@pai\s+nagraj\s+podcast:?\s+(.+)$',
]

TRANSCRIPT_PATTERNS = [
    r'^@pai\s+transcript:?\s+(.+)$',
    r'^@pai\s+transkrypcja:?\s+(.+)$',
    r'^@pai\s+transkrypcja\s+yt:?\s+(.+)$',
]

# URL detection
URL_REGEX = re.compile(r'https?://\S+')
YOUTUBE_REGEX = re.compile(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)[\w-]+')


def detect_podcast_request(text: str) -> Optional[Dict]:
    """
    Detect if text is a podcast or transcript request.

    Returns:
        Dict with keys: type ('podcast'|'transcript'), content, format, or None.
    """
    if not text:
        return None

    text_stripped = text.strip()

    # Check transcript patterns first
    for pattern in TRANSCRIPT_PATTERNS:
        match = re.match(pattern, text_stripped, re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            if content:
                return {
                    'type': 'transcript',
                    'content': content,
                    'format': None,
                }

    # Check podcast patterns
    for pattern in PODCAST_PATTERNS:
        match = re.match(pattern, text_stripped, re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            if not content:
                continue

            # Determine format from pattern
            audio_format = 'deep-dive'  # default
            pattern_lower = pattern.lower()
            if 'debate' in pattern_lower:
                audio_format = 'debate'
            elif 'brief' in pattern_lower or 'krótki' in pattern_lower:
                audio_format = 'brief'
            elif 'critique' in pattern_lower:
                audio_format = 'critique'

            return {
                'type': 'podcast',
                'content': content,
                'format': audio_format,
            }

    return None


def _detect_source_type(content: str) -> str:
    """Detect if content is a URL, YouTube URL, or plain text."""
    if YOUTUBE_REGEX.search(content):
        return 'youtube'
    elif URL_REGEX.match(content.split()[0]):
        return 'url'
    else:
        return 'text'


async def generate_podcast(content: str, audio_format: str = 'deep-dive') -> Dict:
    """
    Generate a podcast using NotebookLM API.

    Args:
        content: URL, YouTube URL, or text to create podcast from
        audio_format: deep-dive, brief, critique, or debate

    Returns:
        Dict with status, file_path, notebook_id, etc.
    """
    # Import here to avoid issues if notebooklm not installed
    from notebooklm import NotebookLMClient, AudioFormat, AudioLength

    FORMAT_MAP = {
        'deep-dive': AudioFormat.DEEP_DIVE,
        'brief': AudioFormat.BRIEF,
        'critique': AudioFormat.CRITIQUE,
        'debate': AudioFormat.DEBATE,
    }

    source_type = _detect_source_type(content)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    PODCAST_DIR.mkdir(parents=True, exist_ok=True)

    # Set NotebookLM home to server location
    os.environ['NOTEBOOKLM_HOME'] = str(NOTEBOOKLM_HOME)

    try:
        async with await NotebookLMClient.from_storage() as client:
            # 1. Create notebook
            title = f"PAI Podcast {timestamp}"
            if source_type == 'url' or source_type == 'youtube':
                # Use domain/video as title hint
                title = f"Podcast: {content[:60]}"

            logger.info(f"Creating notebook: {title}")
            nb = await client.notebooks.create(title)
            nb_id = nb.id
            logger.info(f"Notebook created: {nb_id}")

            # 2. Add source
            logger.info(f"Adding {source_type} source: {content[:100]}")
            if source_type == 'youtube':
                source = await client.sources.add_youtube(nb_id, content.split()[0])
            elif source_type == 'url':
                source = await client.sources.add_url(nb_id, content.split()[0])
            else:
                # Plain text
                source = await client.sources.add_text(nb_id, "User Content", content)

            logger.info(f"Source added: {source.id}")

            # 3. Generate audio
            nlm_format = FORMAT_MAP.get(audio_format, AudioFormat.DEEP_DIVE)
            logger.info(f"Generating audio (format={audio_format})...")

            status = await client.artifacts.generate_audio(
                nb_id,
                audio_format=nlm_format,
                audio_length=AudioLength.DEFAULT,
                language="en",
            )

            # 4. Wait for completion (up to 30 minutes)
            logger.info(f"Waiting for audio generation (task_id={status.task_id})...")
            final = await client.artifacts.wait_for_completion(
                nb_id,
                status.task_id,
                timeout=1800,
                poll_interval=15,
            )

            if not final.is_complete:
                return {
                    'status': 'failed',
                    'error': f'Audio generation did not complete: {final.status}',
                    'notebook_id': nb_id,
                }

            # 5. Download audio
            output_path = str(PODCAST_DIR / f"podcast_{timestamp}.mp4")
            downloaded = await client.artifacts.download_audio(nb_id, output_path)
            logger.info(f"Audio downloaded: {downloaded}")

            return {
                'status': 'success',
                'file_path': downloaded,
                'notebook_id': nb_id,
                'notebook_title': title,
                'format': audio_format,
                'source_type': source_type,
            }

    except Exception as e:
        logger.exception(f"Podcast generation failed: {e}")
        return {
            'status': 'failed',
            'error': str(e),
        }


async def extract_youtube_transcript(url: str) -> Dict:
    """
    Extract transcript from YouTube video using NotebookLM.

    Returns:
        Dict with status, transcript text, etc.
    """
    from notebooklm import NotebookLMClient

    os.environ['NOTEBOOKLM_HOME'] = str(NOTEBOOKLM_HOME)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        async with await NotebookLMClient.from_storage() as client:
            # Create notebook
            title = f"YT Transcript {timestamp}"
            nb = await client.notebooks.create(title)
            nb_id = nb.id

            # Add YouTube source
            youtube_url = url.split()[0]
            source = await client.sources.add_youtube(nb_id, youtube_url)
            logger.info(f"YouTube source added: {source.id}")

            # Wait a moment for indexing
            await asyncio.sleep(5)

            # Get full text content
            fulltext = await client.sources.get_fulltext(nb_id, source.id)

            return {
                'status': 'success',
                'transcript': fulltext.content,
                'char_count': fulltext.char_count,
                'source_title': source.title,
                'notebook_id': nb_id,
            }

    except Exception as e:
        logger.exception(f"YouTube transcript extraction failed: {e}")
        return {
            'status': 'failed',
            'error': str(e),
        }


def handle_podcast_request(text: str, chat_id: int) -> Tuple[bool, Optional[str]]:
    """
    Main entry point called from process_event.py.
    Detects podcast/transcript intent and processes asynchronously.

    Returns:
        Tuple of (handled: bool, immediate_response: Optional[str])
    """
    request = detect_podcast_request(text)
    if not request:
        return False, None

    from telegram_sender import send_message, send_audio_file

    if request['type'] == 'transcript':
        # YouTube transcript - relatively quick
        send_message(chat_id, "📝 Extracting YouTube transcript...")

        result = asyncio.run(extract_youtube_transcript(request['content']))

        if result['status'] == 'success':
            transcript = result['transcript']
            title = result.get('source_title', 'YouTube Video')
            header = f"📝 Transcript: {title}\n({result['char_count']} chars)\n\n"
            send_message(chat_id, header + transcript)
        else:
            send_message(chat_id, f"❌ Transcript extraction failed: {result.get('error', 'Unknown error')}")

        return True, None

    elif request['type'] == 'podcast':
        # Podcast generation - long running
        source_type = _detect_source_type(request['content'])
        format_name = request['format']

        format_emoji = {
            'deep-dive': '🎙️ Deep Dive',
            'brief': '⚡ Brief',
            'critique': '🔍 Critique',
            'debate': '⚔️ Debate',
        }

        source_emoji = {
            'youtube': '🎬 YouTube',
            'url': '🔗 URL',
            'text': '📝 Text',
        }

        msg = (
            f"🎙️ Podcast generation started!\n\n"
            f"📄 Source: {source_emoji.get(source_type, source_type)}\n"
            f"🎧 Format: {format_emoji.get(format_name, format_name)}\n"
            f"⏱️ This takes 5-30 minutes. I'll send the audio when ready."
        )
        send_message(chat_id, msg)

        # Run async generation
        result = asyncio.run(generate_podcast(request['content'], format_name))

        if result['status'] == 'success':
            file_path = result['file_path']
            caption = (
                f"🎙️ Podcast ready!\n"
                f"Format: {format_emoji.get(format_name, format_name)}\n"
                f"Source: {source_emoji.get(source_type, source_type)}"
            )
            send_result = send_audio_file(chat_id, file_path, caption=caption)
            if not send_result.get('success'):
                send_message(chat_id, f"⚠️ Audio generated but sending failed: {send_result.get('error')}")
        else:
            send_message(chat_id, f"❌ Podcast generation failed: {result.get('error', 'Unknown error')}")

        return True, None

    return False, None
