#!/usr/bin/env python3
"""
PAI Planner - Check-in System
- Morning check-in: 6:30
- Evening check-in: 19:00
- Weekly review: Sunday 19:00
Uses Notion API + DeepSeek for messages.
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

# Add inbox-webhook to path for telegram_sender
sys.path.insert(0, '/opt/inbox-webhook')
from telegram_sender import send_message, send_typing_action

# Configuration
CHAT_ID = -1003590663382  # Pawel's Telegram
PAI_DIR = Path.home() / '.pai'
LOG_FILE = PAI_DIR / 'logs' / 'checkin.log'
NOTION_DATABASE_ID = "f357240c-2d5b-4694-87f8-2f10a174a46e"

# Ensure log directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_env():
    """Load environment variables from .env file"""
    env_file = Path('/opt/inbox-webhook/.env')
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value


def get_notion_headers() -> Dict:
    """Get Notion API headers"""
    token = os.environ.get('NOTION_API_TOKEN')
    if not token:
        raise ValueError("NOTION_API_TOKEN not set")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }


def get_notion_projects(status_filter: str = "🔵 Active") -> List[Dict]:
    """Fetch projects from Notion database"""
    token = os.environ.get('NOTION_API_TOKEN')
    if not token:
        logger.error("NOTION_API_TOKEN not set")
        return []

    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = get_notion_headers()

    # Query for specified status
    payload = {
        "filter": {
            "property": "Status",
            "select": {
                "equals": status_filter
            }
        },
        "sorts": [
            {"property": "Priority", "direction": "ascending"},
            {"property": "Action Deadline", "direction": "ascending"}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        projects = []
        for page in data.get('results', []):
            props = page.get('properties', {})

            # Extract title
            name_prop = props.get('Name', {}).get('title', [])
            name = name_prop[0].get('plain_text', 'Unnamed') if name_prop else 'Unnamed'

            # Extract other properties
            area = props.get('Area', {}).get('select', {})
            area_name = area.get('name', '') if area else ''

            priority = props.get('Priority', {}).get('select', {})
            priority_name = priority.get('name', '') if priority else ''

            status = props.get('Status', {}).get('select', {})
            status_name = status.get('name', '') if status else ''

            next_action_prop = props.get('Next Action', {}).get('rich_text', [])
            next_action = next_action_prop[0].get('plain_text', '') if next_action_prop else ''

            deadline_prop = props.get('Action Deadline', {}).get('date', {})
            deadline = deadline_prop.get('start', '') if deadline_prop else ''

            risk_prop = props.get('Risk', {}).get('rich_text', [])
            risk = risk_prop[0].get('plain_text', '') if risk_prop else ''

            last_review_prop = props.get('Last Review', {}).get('date', {})
            last_review = last_review_prop.get('start', '') if last_review_prop else ''

            projects.append({
                'id': page['id'],
                'name': name,
                'area': area_name,
                'priority': priority_name,
                'status': status_name,
                'next_action': next_action,
                'deadline': deadline,
                'risk': risk,
                'last_review': last_review
            })

        logger.info(f"Fetched {len(projects)} projects with status '{status_filter}'")
        return projects

    except Exception as e:
        logger.exception(f"Error fetching Notion projects: {e}")
        return []


def get_recently_completed_projects(days: int = 7) -> List[Dict]:
    """Fetch projects completed in the last N days"""
    token = os.environ.get('NOTION_API_TOKEN')
    if not token:
        logger.error("NOTION_API_TOKEN not set")
        return []

    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = get_notion_headers()

    # Calculate date range
    week_ago = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # Query for Done projects with recent Last Review
    payload = {
        "filter": {
            "and": [
                {
                    "property": "Status",
                    "select": {"equals": "✅ Done"}
                },
                {
                    "property": "Last Review",
                    "date": {"on_or_after": week_ago}
                }
            ]
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        projects = []
        for page in data.get('results', []):
            props = page.get('properties', {})
            name_prop = props.get('Name', {}).get('title', [])
            name = name_prop[0].get('plain_text', 'Unnamed') if name_prop else 'Unnamed'

            area = props.get('Area', {}).get('select', {})
            area_name = area.get('name', '') if area else ''

            projects.append({
                'name': name,
                'area': area_name
            })

        logger.info(f"Fetched {len(projects)} completed projects from last {days} days")
        return projects

    except Exception as e:
        logger.exception(f"Error fetching completed projects: {e}")
        return []


def get_stale_projects(days: int = 7) -> List[Dict]:
    """Find active projects not reviewed in the last N days"""
    projects = get_notion_projects("🔵 Active")
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    stale = []
    for p in projects:
        last_review = p.get('last_review', '')
        if not last_review or last_review < cutoff:
            stale.append(p)

    return stale


def generate_checkin_with_deepseek(projects: List[Dict], checkin_type: str,
                                    completed: List[Dict] = None,
                                    stale: List[Dict] = None) -> Optional[str]:
    """Generate check-in message using DeepSeek API"""
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        logger.error("DEEPSEEK_API_KEY not set")
        return None

    today = datetime.now().strftime("%d.%m.%Y")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    # Format projects for prompt
    projects_text = ""
    high_priority = []
    upcoming_deadlines = []
    next_week_deadlines = []

    for p in projects:
        projects_text += f"- {p['name']} ({p['area']}, {p['priority']})\n"
        projects_text += f"  Next action: {p['next_action']}\n"
        if p['deadline']:
            projects_text += f"  Deadline: {p['deadline']}\n"
        if p['risk']:
            projects_text += f"  Risk: {p['risk']}\n"

        if '🔴 High' in p['priority']:
            high_priority.append(p)
        if p['deadline']:
            if p['deadline'] <= tomorrow:
                upcoming_deadlines.append(p)
            elif p['deadline'] <= next_week:
                next_week_deadlines.append(p)

    if checkin_type == "morning":
        system_prompt = """Jesteś PAI - osobistym asystentem AI. Generujesz krótkie wiadomości check-in na Telegram.
Bądź konkretny, zwięzły i motywujący. Max 400 znaków. Nie używaj markdown."""

        user_prompt = f"""Wygeneruj MORNING check-in na {today}.

Projekty Active:
{projects_text}

High priority: {len(high_priority)} projektów
Deadline dziś/jutro: {len(upcoming_deadlines)} projektów

Format:
🌅 Dzień dobry! Check-in {today}

📋 Dziś focus:
• [projekt 1] - [next action]
• [projekt 2] - [next action]

[opcjonalnie: uwaga o deadline lub ryzyku]

Jak Ci mija poranek?"""

    elif checkin_type == "evening":
        system_prompt = """Jesteś PAI - osobistym asystentem AI. Generujesz krótkie wiadomości check-in na Telegram.
Bądź konkretny, zwięzły i wspierający. Max 400 znaków. Nie używaj markdown."""

        user_prompt = f"""Wygeneruj EVENING check-in na {today}.

Projekty Active:
{projects_text}

High priority: {len(high_priority)} projektów

Format:
🌙 Dobry wieczór! Check-in {today}

📊 Jak poszło z:
• [projekt high priority 1]?
• [projekt high priority 2]?

📅 Na jutro: [jeśli są deadline'y]

Jak minął dzień?"""

    elif checkin_type == "weekly":
        # Format completed projects
        completed_text = ""
        if completed:
            for p in completed:
                completed_text += f"- {p['name']} ({p['area']})\n"
        else:
            completed_text = "(brak)"

        # Format stale projects
        stale_text = ""
        if stale:
            for p in stale[:5]:
                stale_text += f"- {p['name']} (ostatni przegląd: {p.get('last_review', 'brak')})\n"
        else:
            stale_text = "(wszystkie aktualne)"

        # Format next week deadlines
        next_week_text = ""
        if next_week_deadlines:
            for p in next_week_deadlines:
                next_week_text += f"- {p['name']} ({p['deadline']})\n"
        else:
            next_week_text = "(brak)"

        system_prompt = """Jesteś PAI - osobistym asystentem AI. Generujesz weekly review na Telegram.
Bądź konkretny, refleksyjny i pomocny. Max 800 znaków. Nie używaj markdown.
Pytaj otwarte pytania, zachęcaj do refleksji."""

        user_prompt = f"""Wygeneruj WEEKLY REVIEW na {today} (niedziela).

AKTYWNE PROJEKTY ({len(projects)}):
{projects_text}

UKOŃCZONE W TYM TYGODNIU ({len(completed) if completed else 0}):
{completed_text}

PROJEKTY BEZ PRZEGLĄDU >7 DNI ({len(stale) if stale else 0}):
{stale_text}

DEADLINE'Y W TYM TYGODNIU:
{next_week_text}

HIGH PRIORITY: {len(high_priority)} projektów

Format:
📅 Weekly Review - {today}

🎉 Ten tydzień:
[podsumuj ukończone lub postępy]

📋 Aktywne projekty ({len(projects)}):
[wymień 2-3 najważniejsze z next action]

⚠️ Wymaga uwagi:
[projekty bez przeglądu lub z ryzykiem]

🎯 Na przyszły tydzień:
[zasugeruj focus na podstawie priorytetów i deadline'ów]

💭 Pytania do refleksji:
- Co poszło dobrze?
- Co można poprawić?
- Czy priorytety są aktualne?"""

    try:
        import openai
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=800 if checkin_type == "weekly" else 500,
            temperature=0.7
        )

        message = response.choices[0].message.content.strip()
        logger.info(f"DeepSeek generated message: {len(message)} chars")
        return message

    except Exception as e:
        logger.exception(f"Error calling DeepSeek: {e}")
        return None


def generate_fallback_message(projects: List[Dict], checkin_type: str,
                               completed: List[Dict] = None) -> str:
    """Generate simple fallback message without AI"""
    today = datetime.now().strftime("%d.%m.%Y")

    if checkin_type == "weekly":
        msg = f"📅 Weekly Review - {today}\n\n"

        if completed:
            msg += f"🎉 Ukończone ({len(completed)}):\n"
            for p in completed[:3]:
                msg += f"• {p['name']}\n"
            msg += "\n"

        high_priority = [p for p in projects if '🔴 High' in p.get('priority', '')]
        if high_priority:
            msg += f"📋 High priority ({len(high_priority)}):\n"
            for p in high_priority[:3]:
                msg += f"• {p['name']}"
                if p.get('next_action'):
                    msg += f" - {p['next_action'][:40]}"
                msg += "\n"

        msg += "\n💭 Jak oceniasz ten tydzień?"
        return msg

    # Morning/Evening fallback
    emoji = "🌅" if checkin_type == "morning" else "🌙"
    greeting = "Dzień dobry" if checkin_type == "morning" else "Dobry wieczór"

    high_priority = [p for p in projects if '🔴 High' in p.get('priority', '')]

    msg = f"{emoji} {greeting}! Check-in {today}\n\n"

    if high_priority:
        msg += "📋 High priority:\n"
        for p in high_priority[:3]:
            msg += f"• {p['name']}"
            if p.get('next_action'):
                msg += f" - {p['next_action'][:50]}"
            msg += "\n"
    else:
        msg += "Brak pilnych projektów. Spokojny dzień!\n"

    msg += "\nJak Ci idzie?"
    return msg


def send_checkin_message(message: str) -> bool:
    """Send check-in message to Telegram"""
    try:
        logger.info(f"Sending check-in to chat {CHAT_ID}")
        send_typing_action(CHAT_ID)

        result = send_message(CHAT_ID, message)

        if result.get('success'):
            logger.info(f"Check-in sent, message IDs: {result.get('message_ids')}")
            return True
        else:
            logger.error(f"Failed to send check-in: {result.get('error')}")
            return False

    except Exception as e:
        logger.exception(f"Error sending Telegram message: {e}")
        return False


def run_checkin(checkin_type: Optional[str] = None):
    """Main check-in routine"""
    if checkin_type is None:
        hour = datetime.now().hour
        weekday = datetime.now().weekday()

        # Sunday evening = weekly review
        if weekday == 6 and hour >= 18:
            checkin_type = "weekly"
        elif hour < 12:
            checkin_type = "morning"
        else:
            checkin_type = "evening"

    logger.info(f"Starting {checkin_type} check-in")

    # Load environment
    load_env()

    # Fetch projects from Notion
    projects = get_notion_projects("🔵 Active")

    if not projects:
        emoji = {"morning": "🌅", "evening": "🌙", "weekly": "📅"}.get(checkin_type, "📋")
        message = f"{emoji} Check-in - nie udało się pobrać projektów z Notion."
        send_checkin_message(message)
        return

    # For weekly review, get additional data
    completed = None
    stale = None
    if checkin_type == "weekly":
        completed = get_recently_completed_projects(days=7)
        stale = get_stale_projects(days=7)

    # Generate message with DeepSeek
    message = generate_checkin_with_deepseek(projects, checkin_type, completed, stale)

    # Fallback if DeepSeek fails
    if not message:
        logger.warning("DeepSeek failed, using fallback message")
        message = generate_fallback_message(projects, checkin_type, completed)

    # Send to Telegram
    success = send_checkin_message(message)

    if success:
        logger.info(f"{checkin_type.capitalize()} check-in completed successfully")
    else:
        logger.error(f"{checkin_type.capitalize()} check-in failed to send")


if __name__ == "__main__":
    checkin_type = sys.argv[1] if len(sys.argv) > 1 else None
    run_checkin(checkin_type)
