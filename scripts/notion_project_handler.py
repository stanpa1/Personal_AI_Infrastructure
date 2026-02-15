#!/usr/bin/env python3
"""
Notion Project Handler for PAI Response Processing.
Detects project-related intents in user messages and updates Notion accordingly.
"""

import os
import re
import logging
import requests
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)

# Notion configuration
NOTION_DATABASE_ID = "f357240c-2d5b-4694-87f8-2f10a174a46e"
NOTION_API_VERSION = "2022-06-28"

# Intent patterns
COMPLETE_PATTERNS = [
    r'\b(zrobione|done|skonczone|skończone|completed|finished|gotowe|zalatwione|załatwione)\b',
    r'\b(zakoncz|zakończ|complete|finish)\s+(.+)',
]

UPDATE_PATTERNS = [
    r'update\s+(.+?):\s*(.+)',
    r'aktualizuj\s+(.+?):\s*(.+)',
    r'zmien\s+(.+?)\s+na\s+(.+)',
    r'zmień\s+(.+?)\s+na\s+(.+)',
    r'ustaw\s+(.+?):\s*(.+)',
    r'next\s+action\s+(.+?):\s*(.+)',
    r'deadline\s+(.+?):\s*(.+)',
    r'termin\s+(.+?):\s*(.+)',
]

# Deadline-specific patterns (to detect field type)
DEADLINE_UPDATE_PATTERNS = [
    r'deadline\s+(.+?):\s*(.+)',
    r'termin\s+(.+?):\s*(.+)',
    r'przesun\s+(.+?)\s+na\s+(.+)',
    r'przesuń\s+(.+?)\s+na\s+(.+)',
]

ADD_PATTERNS = [
    r'(dodaj|nowy|add|utworz|utwórz)\s+(projekt|task|zadanie)[:\s]+(.+)',
    r'(new|create)\s+(project|task)[:\s]+(.+)',
]

# Status mappings
STATUS_COMPLETE = "✅ Done"
STATUS_ACTIVE = "🔵 Active"
STATUS_PLANNED = "📋 Planned"

# Priority mappings
PRIORITY_MAP = {
    'wysoki': '🔴 High',
    'wysokie': '🔴 High',
    'high': '🔴 High',
    'pilne': '🔴 High',
    'sredni': '🟡 Medium',
    'średni': '🟡 Medium',
    'medium': '🟡 Medium',
    'normalny': '🟡 Medium',
    'niski': '🟢 Low',
    'low': '🟢 Low',
}

# Area mappings
AREA_MAP = {
    'dom': '🏠 Home',
    'home': '🏠 Home',
    'praca': '💼 Work',
    'work': '💼 Work',
    'biznes': '💼 Work',
    'business': '💼 Work',
    'zdrowie': '❤️ Health',
    'health': '❤️ Health',
    'finanse': '💰 Finance',
    'finance': '💰 Finance',
    'relacje': '👥 Relationships',
    'relationships': '👥 Relationships',
    'rozwoj': '📚 Growth',
    'rozwój': '📚 Growth',
    'growth': '📚 Growth',
    'learning': '📚 Growth',
}

# Polish day names to weekday number (Monday=0, Sunday=6)
# Includes nominative and genitive forms
POLISH_DAYS = {
    'poniedzialek': 0, 'poniedziałek': 0, 'poniedzialku': 0, 'poniedziałku': 0, 'pon': 0,
    'wtorek': 1, 'wtorku': 1, 'wt': 1,
    'sroda': 2, 'środa': 2, 'srode': 2, 'środę': 2, 'srody': 2, 'środy': 2, 'sr': 2, 'śr': 2,
    'czwartek': 3, 'czwartku': 3, 'czw': 3,
    'piatek': 4, 'piątek': 4, 'piatku': 4, 'piątku': 4, 'pt': 4,
    'sobota': 5, 'sobote': 5, 'sobotę': 5, 'soboty': 5, 'sob': 5,
    'niedziela': 6, 'niedziele': 6, 'niedzielę': 6, 'niedzieli': 6, 'niedz': 6, 'nd': 6,
}

# English day names
ENGLISH_DAYS = {
    'monday': 0, 'mon': 0,
    'tuesday': 1, 'tue': 1,
    'wednesday': 2, 'wed': 2,
    'thursday': 3, 'thu': 3,
    'friday': 4, 'fri': 4,
    'saturday': 5, 'sat': 5,
    'sunday': 6, 'sun': 6,
}

# Polish month names
POLISH_MONTHS = {
    'stycznia': 1, 'styczen': 1, 'styczeń': 1, 'sty': 1,
    'lutego': 2, 'luty': 2, 'lut': 2,
    'marca': 3, 'marzec': 3, 'mar': 3,
    'kwietnia': 4, 'kwiecien': 4, 'kwiecień': 4, 'kwi': 4,
    'maja': 5, 'maj': 5,
    'czerwca': 6, 'czerwiec': 6, 'cze': 6,
    'lipca': 7, 'lipiec': 7, 'lip': 7,
    'sierpnia': 8, 'sierpien': 8, 'sierpień': 8, 'sie': 8,
    'wrzesnia': 9, 'września': 9, 'wrzesien': 9, 'wrzesień': 9, 'wrz': 9,
    'pazdziernika': 10, 'października': 10, 'pazdziernik': 10, 'październik': 10, 'paz': 10, 'paź': 10,
    'listopada': 11, 'listopad': 11, 'lis': 11,
    'grudnia': 12, 'grudzien': 12, 'grudzień': 12, 'gru': 12,
}

# English month names
ENGLISH_MONTHS = {
    'january': 1, 'jan': 1,
    'february': 2, 'feb': 2,
    'march': 3, 'mar': 3,
    'april': 4, 'apr': 4,
    'may': 5,
    'june': 6, 'jun': 6,
    'july': 7, 'jul': 7,
    'august': 8, 'aug': 8,
    'september': 9, 'sep': 9, 'sept': 9,
    'october': 10, 'oct': 10,
    'november': 11, 'nov': 11,
    'december': 12, 'dec': 12,
}


def parse_deadline(text: str) -> Optional[str]:
    """
    Parse natural language deadline to ISO date string (YYYY-MM-DD).

    Supports:
    - Relative: jutro, pojutrze, za X dni, za tydzień, za miesiąc
    - Days: do piątku, w poniedziałek, friday, next monday
    - Dates: 15 lutego, 15.02, 15/02, 2026-02-15
    - Keywords: dziś/dzisiaj/today, tomorrow

    Returns:
        ISO date string (YYYY-MM-DD) or None if not parseable
    """
    if not text:
        return None

    text_lower = text.lower().strip()
    today = datetime.now()

    # Remove common prefixes
    for prefix in ['do ', 'na ', 'deadline ', 'termin ', 'before ', 'by ', 'until ']:
        if text_lower.startswith(prefix):
            text_lower = text_lower[len(prefix):].strip()

    # === RELATIVE DATES ===

    # Today
    if text_lower in ['dziś', 'dzis', 'dzisiaj', 'today', 'teraz']:
        return today.strftime('%Y-%m-%d')

    # Tomorrow
    if text_lower in ['jutro', 'tomorrow']:
        return (today + timedelta(days=1)).strftime('%Y-%m-%d')

    # Day after tomorrow
    if text_lower in ['pojutrze', 'day after tomorrow']:
        return (today + timedelta(days=2)).strftime('%Y-%m-%d')

    # "za X dni" / "in X days"
    days_match = re.search(r'za\s+(\d+)\s*(dni|dzień|dnia|day|days)', text_lower)
    if days_match:
        days = int(days_match.group(1))
        return (today + timedelta(days=days)).strftime('%Y-%m-%d')

    days_match_en = re.search(r'in\s+(\d+)\s*(days?)', text_lower)
    if days_match_en:
        days = int(days_match_en.group(1))
        return (today + timedelta(days=days)).strftime('%Y-%m-%d')

    # "za tydzień" / "in a week" / "next week"
    if re.search(r'za\s+tydzien|za\s+tydzień|in\s+a\s+week|next\s+week', text_lower):
        return (today + timedelta(weeks=1)).strftime('%Y-%m-%d')

    # "za X tygodni" / "in X weeks"
    weeks_match = re.search(r'za\s+(\d+)\s*(tygodni|tygodn|weeks?)', text_lower)
    if weeks_match:
        weeks = int(weeks_match.group(1))
        return (today + timedelta(weeks=weeks)).strftime('%Y-%m-%d')

    weeks_match_en = re.search(r'in\s+(\d+)\s*(weeks?)', text_lower)
    if weeks_match_en:
        weeks = int(weeks_match_en.group(1))
        return (today + timedelta(weeks=weeks)).strftime('%Y-%m-%d')

    # "za miesiąc" / "in a month"
    if re.search(r'za\s+miesi[aą]c|in\s+a\s+month|next\s+month', text_lower):
        # Approximate: 30 days
        return (today + timedelta(days=30)).strftime('%Y-%m-%d')

    # === DAY OF WEEK ===

    # Check Polish days
    for day_name, weekday in POLISH_DAYS.items():
        if day_name in text_lower:
            # Find next occurrence of this weekday
            days_ahead = weekday - today.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

    # Check English days
    for day_name, weekday in ENGLISH_DAYS.items():
        if day_name in text_lower:
            days_ahead = weekday - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            # "next monday" should be next week even if today is monday
            if 'next' in text_lower and days_ahead == 7:
                days_ahead = 7
            return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

    # === SPECIFIC DATES ===

    # ISO format: 2026-02-15
    iso_match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', text_lower)
    if iso_match:
        return f"{iso_match.group(1)}-{int(iso_match.group(2)):02d}-{int(iso_match.group(3)):02d}"

    # European format: 15.02.2026 or 15.02 or 15/02/2026 or 15/02
    euro_match = re.search(r'(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?', text_lower)
    if euro_match:
        day = int(euro_match.group(1))
        month = int(euro_match.group(2))
        year = euro_match.group(3)
        if year:
            year = int(year)
            if year < 100:
                year += 2000
        else:
            year = today.year
            # If the date has passed this year, assume next year
            try:
                target = datetime(year, month, day)
                if target < today:
                    year += 1
            except ValueError:
                pass
        try:
            return f"{year}-{month:02d}-{day:02d}"
        except:
            pass

    # "15 lutego" or "february 15"
    # Polish: day + month name
    pl_date_match = re.search(r'(\d{1,2})\s+([a-ząćęłńóśźż]+)', text_lower)
    if pl_date_match:
        day = int(pl_date_match.group(1))
        month_name = pl_date_match.group(2)
        month = POLISH_MONTHS.get(month_name) or ENGLISH_MONTHS.get(month_name)
        if month:
            year = today.year
            try:
                target = datetime(year, month, day)
                if target < today:
                    year += 1
                return f"{year}-{month:02d}-{day:02d}"
            except ValueError:
                pass

    # English: month name + day (e.g., "february 15")
    en_date_match = re.search(r'([a-z]+)\s+(\d{1,2})', text_lower)
    if en_date_match:
        month_name = en_date_match.group(1)
        day = int(en_date_match.group(2))
        month = ENGLISH_MONTHS.get(month_name) or POLISH_MONTHS.get(month_name)
        if month:
            year = today.year
            try:
                target = datetime(year, month, day)
                if target < today:
                    year += 1
                return f"{year}-{month:02d}-{day:02d}"
            except ValueError:
                pass

    # "koniec tygodnia" / "end of week" / "weekend"
    if re.search(r'koniec\s+tygodnia|weekend|end\s+of\s+week', text_lower):
        # Next Friday
        days_ahead = 4 - today.weekday()  # Friday = 4
        if days_ahead <= 0:
            days_ahead += 7
        return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

    # "koniec miesiąca" / "end of month"
    if re.search(r'koniec\s+miesi[aą]ca|end\s+of\s+month', text_lower):
        # Last day of current month
        if today.month == 12:
            next_month = datetime(today.year + 1, 1, 1)
        else:
            next_month = datetime(today.year, today.month + 1, 1)
        last_day = next_month - timedelta(days=1)
        return last_day.strftime('%Y-%m-%d')

    logger.debug(f"Could not parse deadline from: {text}")
    return None


def get_notion_headers() -> Dict:
    """Get headers for Notion API requests"""
    token = os.environ.get('NOTION_API_TOKEN')
    if not token:
        raise ValueError("NOTION_API_TOKEN not set")

    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json"
    }


def get_all_projects() -> List[Dict]:
    """Fetch all active and planned projects from Notion"""
    try:
        headers = get_notion_headers()
        url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"

        # Query for Active and Planned projects
        payload = {
            "filter": {
                "or": [
                    {"property": "Status", "select": {"equals": "🔵 Active"}},
                    {"property": "Status", "select": {"equals": "📋 Planned"}}
                ]
            }
        }

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

            projects.append({
                'id': page['id'],
                'name': name,
                'area': area_name,
                'priority': priority_name,
                'status': status_name,
                'next_action': next_action,
            })

        logger.info(f"Fetched {len(projects)} projects from Notion")
        return projects

    except Exception as e:
        logger.exception(f"Error fetching Notion projects: {e}")
        return []


def find_project_by_name(query: str, projects: List[Dict]) -> Optional[Dict]:
    """
    Find project by fuzzy name matching.
    Returns best matching project if similarity > 0.5
    """
    if not query or not projects:
        return None

    query_lower = query.lower().strip()
    best_match = None
    best_ratio = 0.5  # Minimum threshold

    for project in projects:
        name = project['name'].lower()

        # Exact substring match gets priority
        if query_lower in name or name in query_lower:
            return project

        # Fuzzy match
        ratio = SequenceMatcher(None, query_lower, name).ratio()

        # Also check partial matches
        words = query_lower.split()
        for word in words:
            if len(word) > 3 and word in name:
                ratio = max(ratio, 0.7)

        if ratio > best_ratio:
            best_ratio = ratio
            best_match = project

    if best_match:
        logger.info(f"Matched '{query}' to '{best_match['name']}' (ratio: {best_ratio:.2f})")

    return best_match


def detect_project_intent(text: str) -> Dict:
    """
    Detect project-related intent from user message.

    Returns:
        {
            'type': 'complete' | 'update' | 'add' | None,
            'project_name': str | None,
            'details': str,
            'field': str | None  # for updates: 'next_action', 'deadline', etc.
        }
    """
    if not text:
        return {'type': None, 'project_name': None, 'details': '', 'field': None}

    text_lower = text.lower().strip()

    # Remove @pai prefix if present
    if text_lower.startswith('@pai'):
        text_lower = text_lower[4:].strip()

    # Check for completion patterns
    for pattern in COMPLETE_PATTERNS:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            # Try to extract project name from the text
            # Pattern: "project_name - zrobione" or "zrobione project_name"
            parts = re.split(r'\s*[-:]\s*', text_lower)
            project_name = None

            for part in parts:
                part = part.strip()
                # Skip the completion word itself
                if not re.search(pattern, part, re.IGNORECASE) and len(part) > 2:
                    project_name = part
                    break

            # If no project name found, try extracting from full text
            if not project_name:
                # Remove completion words and see what's left
                cleaned = re.sub(pattern, '', text_lower, flags=re.IGNORECASE).strip()
                if cleaned and len(cleaned) > 2:
                    project_name = cleaned.strip(' -:')

            return {
                'type': 'complete',
                'project_name': project_name,
                'details': '',
                'field': 'status'
            }

    # Check for deadline-specific update patterns first
    for pattern in DEADLINE_UPDATE_PATTERNS:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) >= 2:
                project_name = groups[-2].strip()
                details = groups[-1].strip()

                return {
                    'type': 'update',
                    'project_name': project_name,
                    'details': details,
                    'field': 'deadline'
                }

    # Check for general update patterns
    for pattern in UPDATE_PATTERNS:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) >= 2:
                project_name = groups[-2].strip()
                details = groups[-1].strip()

                # Auto-detect if this looks like a deadline
                field = 'next_action'
                if parse_deadline(details):
                    # If the details can be parsed as a date, it's likely a deadline
                    field = 'deadline'

                return {
                    'type': 'update',
                    'project_name': project_name,
                    'details': details,
                    'field': field
                }

    # Check for add patterns
    for pattern in ADD_PATTERNS:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            groups = match.groups()
            details = groups[-1].strip() if groups else text_lower

            return {
                'type': 'add',
                'project_name': None,
                'details': details,
                'field': None
            }

    return {'type': None, 'project_name': None, 'details': '', 'field': None}


def parse_new_project(details: str) -> Dict:
    """
    Parse new project details from user input.

    Input examples:
    - "zakup laptopa, dom, priorytet wysoki"
    - "wymiana opon, deadline piątek"
    - "spotkanie z Nikiem, praca, medium"

    Returns:
        {
            'name': str,
            'area': str | None,
            'priority': str | None,
            'deadline': str | None,
            'next_action': str | None
        }
    """
    result = {
        'name': '',
        'area': None,
        'priority': '🟡 Medium',  # Default
        'deadline': None,
        'next_action': None
    }

    # Split by comma
    parts = [p.strip() for p in details.split(',')]

    if not parts:
        return result

    # First part is usually the name
    result['name'] = parts[0]

    for part in parts[1:]:
        part_lower = part.lower()

        # Check for priority
        for key, value in PRIORITY_MAP.items():
            if key in part_lower:
                result['priority'] = value
                break

        # Check for area
        for key, value in AREA_MAP.items():
            if key in part_lower:
                result['area'] = value
                break

        # Check for deadline - try to parse natural language
        deadline_match = re.search(r'(deadline|termin|do|na)[:\s]+(.+)', part_lower)
        if deadline_match:
            result['deadline'] = deadline_match.group(2).strip()
        elif not result['deadline']:
            # Try parsing the whole part as a deadline
            parsed = parse_deadline(part)
            if parsed:
                result['deadline'] = part

        # Check for next action
        action_match = re.search(r'(next action|akcja|action)[:\s]+(.+)', part_lower)
        if action_match:
            result['next_action'] = action_match.group(2)

    return result


def update_notion_project(project_id: str, updates: Dict) -> Tuple[bool, str]:
    """
    Update a project in Notion.

    Args:
        project_id: Notion page ID
        updates: Dict with fields to update:
            - status: str
            - next_action: str
            - deadline: str (date)
            - notes: str (append)

    Returns:
        (success: bool, message: str)
    """
    try:
        headers = get_notion_headers()
        url = f"https://api.notion.com/v1/pages/{project_id}"

        properties = {}

        if 'status' in updates:
            properties['Status'] = {'select': {'name': updates['status']}}

        if 'next_action' in updates:
            properties['Next Action'] = {
                'rich_text': [{'text': {'content': updates['next_action']}}]
            }

        if 'deadline' in updates:
            deadline_str = updates['deadline']
            # Try to parse natural language deadline
            deadline_date = parse_deadline(deadline_str)
            if not deadline_date:
                # If parsing failed and it looks like ISO format, use as-is
                if re.match(r'\d{4}-\d{2}-\d{2}', deadline_str):
                    deadline_date = deadline_str
                else:
                    logger.warning(f"Could not parse deadline: {deadline_str}")
                    deadline_date = None

            if deadline_date:
                properties['Action Deadline'] = {'date': {'start': deadline_date}}

        # Always update Last Review
        properties['Last Review'] = {'date': {'start': datetime.now().strftime('%Y-%m-%d')}}

        payload = {'properties': properties}

        response = requests.patch(url, headers=headers, json=payload, timeout=30)

        if response.ok:
            logger.info(f"Updated project {project_id}: {updates}")
            return True, "OK"
        else:
            error = response.json().get('message', response.text)
            logger.error(f"Failed to update Notion: {error}")
            return False, error

    except Exception as e:
        logger.exception(f"Error updating Notion project: {e}")
        return False, str(e)


def create_notion_project(data: Dict) -> Tuple[Optional[str], str]:
    """
    Create a new project in Notion.

    Args:
        data: Dict with project details:
            - name: str (required)
            - area: str
            - priority: str
            - deadline: str
            - next_action: str

    Returns:
        (page_id: str | None, message: str)
    """
    try:
        headers = get_notion_headers()
        url = "https://api.notion.com/v1/pages"

        properties = {
            'Name': {
                'title': [{'text': {'content': data['name']}}]
            },
            'Status': {'select': {'name': STATUS_ACTIVE}},
            'Priority': {'select': {'name': data.get('priority', '🟡 Medium')}},
            'Last Review': {'date': {'start': datetime.now().strftime('%Y-%m-%d')}}
        }

        if data.get('area'):
            properties['Area'] = {'select': {'name': data['area']}}

        if data.get('next_action'):
            properties['Next Action'] = {
                'rich_text': [{'text': {'content': data['next_action']}}]
            }

        if data.get('deadline'):
            deadline_str = data['deadline']
            deadline_date = parse_deadline(deadline_str)
            if not deadline_date and re.match(r'\d{4}-\d{2}-\d{2}', deadline_str):
                deadline_date = deadline_str
            if deadline_date:
                properties['Action Deadline'] = {'date': {'start': deadline_date}}

        payload = {
            'parent': {'database_id': NOTION_DATABASE_ID},
            'properties': properties
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.ok:
            page_id = response.json().get('id')
            logger.info(f"Created project '{data['name']}' with ID {page_id}")
            return page_id, "OK"
        else:
            error = response.json().get('message', response.text)
            logger.error(f"Failed to create Notion project: {error}")
            return None, error

    except Exception as e:
        logger.exception(f"Error creating Notion project: {e}")
        return None, str(e)


def format_confirmation(action: str, project_name: str, details: str = None, field: str = None) -> str:
    """Format user-friendly confirmation message"""
    if action == 'complete':
        return f"Oznaczylem '{project_name}' jako Done!"
    elif action == 'update':
        if field == 'deadline':
            parsed_date = parse_deadline(details) if details else None
            if parsed_date:
                return f"Ustawiłem deadline '{project_name}' na {parsed_date}"
            return f"Zaktualizowałem deadline '{project_name}': {details}"
        return f"Zaktualizowałem '{project_name}': {details}"
    elif action == 'add':
        return f"Dodałem nowy projekt: '{project_name}'"
    else:
        return f"Zaktualizowano: {project_name}"


def process_project_update(user_text: str, ai_response: str = None) -> Dict:
    """
    Main entry point for processing project updates.
    Analyzes user text and optionally AI response for project commands.

    Returns:
        {
            'updated': bool,
            'action': str | None,
            'project': str | None,
            'confirmation': str | None,
            'error': str | None
        }
    """
    result = {
        'updated': False,
        'action': None,
        'project': None,
        'confirmation': None,
        'error': None
    }

    # First detect intent from user text
    intent = detect_project_intent(user_text)

    if not intent['type']:
        logger.debug(f"No project intent detected in: {user_text[:100]}")
        return result

    logger.info(f"Detected intent: {intent}")

    # Fetch current projects
    projects = get_all_projects()

    if intent['type'] == 'complete':
        # Find the project
        if intent['project_name']:
            project = find_project_by_name(intent['project_name'], projects)
            if project:
                success, msg = update_notion_project(project['id'], {'status': STATUS_COMPLETE})
                if success:
                    result['updated'] = True
                    result['action'] = 'complete'
                    result['project'] = project['name']
                    result['confirmation'] = format_confirmation('complete', project['name'])
                else:
                    result['error'] = msg
            else:
                result['error'] = f"Nie znalazłem projektu pasującego do '{intent['project_name']}'"
        else:
            result['error'] = "Nie rozpoznałem nazwy projektu. Podaj np. 'antena gsm - zrobione'"

    elif intent['type'] == 'update':
        # Find the project and update
        if intent['project_name']:
            project = find_project_by_name(intent['project_name'], projects)
            if project:
                updates = {intent['field']: intent['details']}
                success, msg = update_notion_project(project['id'], updates)
                if success:
                    result['updated'] = True
                    result['action'] = 'update'
                    result['project'] = project['name']
                    result['field'] = intent['field']
                    result['confirmation'] = format_confirmation('update', project['name'], intent['details'], intent['field'])
                else:
                    result['error'] = msg
            else:
                result['error'] = f"Nie znalazłem projektu pasującego do '{intent['project_name']}'"
        else:
            result['error'] = "Nie rozpoznałem nazwy projektu"

    elif intent['type'] == 'add':
        # Parse and create new project
        project_data = parse_new_project(intent['details'])
        if project_data['name']:
            page_id, msg = create_notion_project(project_data)
            if page_id:
                result['updated'] = True
                result['action'] = 'add'
                result['project'] = project_data['name']
                result['confirmation'] = format_confirmation('add', project_data['name'])
            else:
                result['error'] = msg
        else:
            result['error'] = "Nie podałeś nazwy projektu"

    return result


# For testing
if __name__ == "__main__":
    import sys
    from pathlib import Path
    from dotenv import load_dotenv

    # Load environment
    load_dotenv(Path('/opt/inbox-webhook/.env'))

    logging.basicConfig(level=logging.INFO)

    # Test deadline parsing
    if len(sys.argv) > 1 and sys.argv[1] == '--test-deadline':
        test_deadlines = [
            "jutro",
            "pojutrze",
            "do piątku",
            "w poniedziałek",
            "za 3 dni",
            "za tydzień",
            "15 lutego",
            "15.02",
            "friday",
            "next monday",
            "koniec tygodnia",
            "koniec miesiąca",
            "2026-02-20",
        ]
        if len(sys.argv) > 2:
            test_deadlines = [" ".join(sys.argv[2:])]

        print("=== Testing parse_deadline() ===")
        for dl in test_deadlines:
            result = parse_deadline(dl)
            print(f"  '{dl}' -> {result}")
        sys.exit(0)

    test_messages = [
        "antena gsm - zrobione",
        "matryce międzynarodowe zrobione",
        "@pai update matryce: spotkanie z Nikiem we wtorek",
        "aktualizuj antena: zamówić nową część",
        "dodaj projekt: zakup laptopa, dom, priorytet wysoki",
        "@pai nowy projekt: wymiana opon, deadline jutro",
        "deadline antena: do piątku",
        "termin matryce: 15 lutego",
        "przesuń antena na za tydzień",
    ]

    if len(sys.argv) > 1:
        test_messages = [" ".join(sys.argv[1:])]

    for msg in test_messages:
        print(f"\n--- Testing: '{msg}' ---")
        intent = detect_project_intent(msg)
        print(f"Intent: {intent}")

        if intent['type'] == 'add':
            parsed = parse_new_project(intent['details'])
            print(f"Parsed project: {parsed}")
        elif intent['type'] == 'update' and intent['field'] == 'deadline':
            parsed_date = parse_deadline(intent['details'])
            print(f"Parsed deadline: {intent['details']} -> {parsed_date}")
