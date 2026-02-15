#!/usr/bin/env python3
"""
AI handler module.
Processes user queries through DeepSeek API with PAI context.
"""

import os
import logging
from typing import Optional, Tuple
from pathlib import Path
from datetime import datetime

import openai

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_TRIGGER_PREFIX = '@pai'
DEFAULT_TIMEOUT = 120
DEFAULT_MODEL = 'deepseek-chat'
MAX_TOKENS = 4096

# PAI context directory (synced from local machine)
PAI_CONTEXT_DIR = Path('/opt/inbox-webhook/pai-context')


def get_trigger_prefix() -> str:
    """Get trigger prefix from environment"""
    return os.environ.get('CLAUDE_TRIGGER_PREFIX', DEFAULT_TRIGGER_PREFIX)


def get_timeout() -> int:
    """Get timeout from environment"""
    try:
        return int(os.environ.get('CLAUDE_TIMEOUT_SECONDS', DEFAULT_TIMEOUT))
    except ValueError:
        return DEFAULT_TIMEOUT


def should_process_with_claude(text: str) -> bool:
    """
    Check if message should be processed by AI.
    Returns True if message starts with trigger prefix (case-insensitive).
    """
    if not text:
        return False

    prefix = get_trigger_prefix().lower()
    text_lower = text.strip().lower()

    return text_lower.startswith(prefix)


def extract_query(text: str) -> str:
    """
    Extract query from message by removing trigger prefix.
    """
    prefix = get_trigger_prefix()
    text_stripped = text.strip()

    # Case-insensitive prefix removal
    if text_stripped.lower().startswith(prefix.lower()):
        query = text_stripped[len(prefix):].strip()
        return query

    return text_stripped


def load_pai_context() -> str:
    """
    Load PAI context from synced files.
    Includes: telos (mission, beliefs), projects, recent notes.
    """
    context_parts = []

    # Base system prompt
    context_parts.append("""Jesteś PAI (Personal AI Infrastructure) - osobistym asystentem AI użytkownika Pawła.

Kontekst:
- Użytkownik komunikuje się z tobą przez Telegram
- Masz dostęp do jego notatek, projektów i celów (poniżej)
- Odpowiadaj zwięźle, ale pomocnie
- Używaj polskiego języka, chyba że użytkownik pisze po angielsku
- Formatuj odpowiedzi czytelnie (limit 4096 znaków Telegram)

Zasady:
- Bądź pomocny i rzeczowy
- Odwołuj się do kontekstu użytkownika gdy to istotne
- Jeśli nie znasz odpowiedzi, powiedz o tym
- Unikaj zbędnych frazesów
""")

    # Load telos files (mission, beliefs, strategies)
    telos_files = ['mission.md', 'beliefs.md', 'strategies.md']
    telos_content = []
    for filename in telos_files:
        filepath = PAI_CONTEXT_DIR / filename
        if filepath.exists():
            try:
                content = filepath.read_text(encoding='utf-8').strip()
                if content:
                    telos_content.append(f"### {filename}\n{content}")
            except Exception as e:
                logger.warning(f"Failed to read {filepath}: {e}")

    if telos_content:
        context_parts.append("\n## TELOS (Cele i misja użytkownika)\n" + "\n\n".join(telos_content))

    # Load active projects
    projects_dir = PAI_CONTEXT_DIR / 'projects'
    if projects_dir.exists():
        project_files = list(projects_dir.glob('*.md'))
        if project_files:
            projects_content = []
            for pf in project_files[:5]:  # Max 5 projects
                try:
                    content = pf.read_text(encoding='utf-8').strip()
                    # Take first 2000 chars of each project
                    if len(content) > 2000:
                        content = content[:2000] + "\n... (skrócono)"
                    projects_content.append(f"### {pf.stem}\n{content}")
                except Exception as e:
                    logger.warning(f"Failed to read {pf}: {e}")

            if projects_content:
                context_parts.append("\n## AKTYWNE PROJEKTY\n" + "\n\n".join(projects_content))

    # Load recent short-term notes (last 7 days)
    short_term_dir = PAI_CONTEXT_DIR / 'short-term'
    if short_term_dir.exists():
        note_files = sorted(short_term_dir.glob('*.md'), reverse=True)[:10]  # Last 10 notes
        if note_files:
            notes_content = []
            for nf in note_files:
                try:
                    content = nf.read_text(encoding='utf-8').strip()
                    # Take first 500 chars of each note
                    if len(content) > 500:
                        content = content[:500] + "\n... (skrócono)"
                    notes_content.append(f"### {nf.stem}\n{content}")
                except Exception as e:
                    logger.warning(f"Failed to read {nf}: {e}")

            if notes_content:
                context_parts.append("\n## OSTATNIE NOTATKI\n" + "\n\n".join(notes_content))

    # Add current date/time
    now = datetime.now()
    context_parts.append(f"\n## AKTUALNY CZAS\n{now.strftime('%Y-%m-%d %H:%M')} (czas serwera)")

    full_context = "\n".join(context_parts)
    logger.info(f"Loaded PAI context: {len(full_context)} chars")

    return full_context


def process_with_claude(query: str, context: Optional[str] = None) -> Tuple[bool, str]:
    """
    Process query using DeepSeek API.

    Args:
        query: User's question/request
        context: Optional additional context

    Returns:
        Tuple of (success: bool, response: str)
    """
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        logger.error("DEEPSEEK_API_KEY not set")
        return False, "Błąd konfiguracji: brak klucza API"

    try:
        # DeepSeek uses OpenAI-compatible API
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        # Build system prompt with PAI context
        system_prompt = load_pai_context()
        if context:
            system_prompt += f"\n\n## DODATKOWY KONTEKST\n{context}"

        logger.info(f"Sending query to DeepSeek: {query[:100]}...")

        # Make API call
        timeout = get_timeout()
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            timeout=timeout
        )

        # Extract response text
        response_text = response.choices[0].message.content

        if not response_text:
            return False, "DeepSeek nie zwrócił odpowiedzi"

        logger.info(f"DeepSeek response received: {len(response_text)} chars")
        return True, response_text

    except openai.APITimeoutError:
        logger.error("DeepSeek API timeout")
        return False, "Przekroczono limit czasu odpowiedzi. Spróbuj ponownie."
    except openai.RateLimitError:
        logger.error("DeepSeek API rate limit")
        return False, "Zbyt wiele zapytań. Spróbuj za chwilę."
    except openai.APIError as e:
        logger.error(f"DeepSeek API error: {e}")
        return False, "Błąd API. Spróbuj ponownie później."
    except Exception as e:
        logger.exception(f"Unexpected error processing with DeepSeek: {e}")
        return False, f"Wystąpił nieoczekiwany błąd: {str(e)}"


def handle_claude_query(text: str, transcription: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Main entry point for AI query handling.
    Checks for trigger and processes if found.

    Args:
        text: Original message text
        transcription: Optional transcription (for voice messages)

    Returns:
        Tuple of (should_respond: bool, response: Optional[str])
    """
    # Check text first, then transcription
    message_to_check = text or transcription or ""

    if not should_process_with_claude(message_to_check):
        return False, None

    query = extract_query(message_to_check)
    if not query:
        return True, "Nie podałeś żadnego pytania. Napisz: @pai <twoje pytanie>"

    # Build context from transcription if voice message
    context = None
    if transcription and text != transcription:
        context = f"Wiadomość głosowa, transkrypcja: {transcription}"

    success, response = process_with_claude(query, context)
    return True, response
