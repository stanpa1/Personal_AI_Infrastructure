"""
PAI Search API
Provides search, context, and project management endpoints for Nexus Voice Interface
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import glob
import re
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PAI Search API", version="2.0.0")

# CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth ---
PAI_TOKEN = os.getenv("PAI_API_TOKEN", "change-this-token")

def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    if authorization != f"Bearer {PAI_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid token")
    return True

# --- Models ---

class SearchRequest(BaseModel):
    query: str
    category: str = "all"
    limit: int = 5

class NoteRequest(BaseModel):
    content: str
    tags: List[str] = []
    source: str = "api"

class NotionQueryRequest(BaseModel):
    filter: Optional[str] = None

class ProjectUpdateRequest(BaseModel):
    name: str
    status: Optional[str] = None
    next_action: Optional[str] = None
    deadline: Optional[str] = None

class ProjectCreateRequest(BaseModel):
    name: str
    area: Optional[str] = None
    priority: Optional[str] = "medium"
    next_action: Optional[str] = None
    deadline: Optional[str] = None

# --- PAI Memory Paths ---
PAI_CONTEXT = os.getenv("PAI_CONTEXT_PATH", "/opt/inbox-webhook/pai-context")

# --- Notion Configuration ---
NOTION_DATABASE_ID = "f357240c-2d5b-4694-87f8-2f10a174a46e"
NOTION_API_VERSION = "2022-06-28"

def get_notion_headers():
    """Get Notion API headers"""
    token = os.environ.get('NOTION_API_TOKEN')
    if not token:
        raise ValueError("NOTION_API_TOKEN not set")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json"
    }

# --- Helper Functions ---

def extract_snippet(content: str, query_words: List[str], max_len: int = 500) -> str:
    """Extract relevant snippet around first query word match"""
    content_lower = content.lower()

    for word in query_words:
        pos = content_lower.find(word)
        if pos != -1:
            start = max(0, pos - 100)
            end = min(len(content), pos + max_len - 100)
            snippet = content[start:end]

            if start > 0:
                parts = snippet.split(" ", 1)
                snippet = "..." + (parts[1] if len(parts) > 1 else parts[0])
            if end < len(content):
                parts = snippet.rsplit(" ", 1)
                snippet = (parts[0] if len(parts) > 1 else parts[0]) + "..."

            return snippet

    return content[:max_len] + "..." if len(content) > max_len else content


def parse_deadline(text: str) -> Optional[str]:
    """Parse natural language deadline to ISO date string"""
    if not text:
        return None

    text_lower = text.lower().strip()
    today = datetime.now()

    # Remove prefixes
    for prefix in ['do ', 'na ', 'deadline ', 'termin ', 'before ', 'by ', 'until ']:
        if text_lower.startswith(prefix):
            text_lower = text_lower[len(prefix):].strip()

    # Today
    if text_lower in ['dziś', 'dzis', 'dzisiaj', 'today', 'teraz']:
        return today.strftime('%Y-%m-%d')

    # Tomorrow
    if text_lower in ['jutro', 'tomorrow']:
        return (today + timedelta(days=1)).strftime('%Y-%m-%d')

    # Day after tomorrow
    if text_lower in ['pojutrze', 'day after tomorrow']:
        return (today + timedelta(days=2)).strftime('%Y-%m-%d')

    # "za X dni"
    days_match = re.search(r'za\s+(\d+)\s*(dni|dzień|dnia|day|days)', text_lower)
    if days_match:
        days = int(days_match.group(1))
        return (today + timedelta(days=days)).strftime('%Y-%m-%d')

    # "za tydzień" / "next week"
    if re.search(r'za\s+tydzien|za\s+tydzień|in\s+a\s+week|next\s+week', text_lower):
        return (today + timedelta(weeks=1)).strftime('%Y-%m-%d')

    # Polish days
    polish_days = {
        'poniedzialek': 0, 'poniedziałek': 0, 'poniedzialku': 0, 'poniedziałku': 0,
        'wtorek': 1, 'wtorku': 1,
        'sroda': 2, 'środa': 2, 'srode': 2, 'środę': 2,
        'czwartek': 3, 'czwartku': 3,
        'piatek': 4, 'piątek': 4, 'piatku': 4, 'piątku': 4,
        'sobota': 5, 'sobote': 5, 'sobotę': 5,
        'niedziela': 6, 'niedziele': 6, 'niedzielę': 6,
    }

    for day_name, weekday in polish_days.items():
        if day_name in text_lower:
            days_ahead = weekday - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

    # English days
    english_days = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6,
    }

    for day_name, weekday in english_days.items():
        if day_name in text_lower:
            days_ahead = weekday - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

    # ISO format passthrough
    if re.match(r'\d{4}-\d{2}-\d{2}', text_lower):
        return text_lower

    return None


# --- Notion Project Functions ---

def get_notion_projects(status_filter: str = None) -> List[dict]:
    """Fetch projects from Notion database"""
    try:
        headers = get_notion_headers()
        url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"

        payload = {
            "sorts": [
                {"property": "Priority", "direction": "ascending"},
                {"property": "Action Deadline", "direction": "ascending"}
            ]
        }

        if status_filter:
            payload["filter"] = {
                "property": "Status",
                "select": {"equals": status_filter}
            }
        else:
            # Default: Active and Planned
            payload["filter"] = {
                "or": [
                    {"property": "Status", "select": {"equals": "🔵 Active"}},
                    {"property": "Status", "select": {"equals": "📋 Planned"}}
                ]
            }

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

            priority = props.get('Priority', {}).get('select', {})
            priority_name = priority.get('name', '') if priority else ''

            status = props.get('Status', {}).get('select', {})
            status_name = status.get('name', '') if status else ''

            next_action_prop = props.get('Next Action', {}).get('rich_text', [])
            next_action = next_action_prop[0].get('plain_text', '') if next_action_prop else ''

            deadline_prop = props.get('Action Deadline', {}).get('date', {})
            deadline = deadline_prop.get('start', '') if deadline_prop else ''

            projects.append({
                'id': page['id'],
                'name': name,
                'area': area_name,
                'priority': priority_name,
                'status': status_name,
                'next_action': next_action,
                'deadline': deadline
            })

        return projects

    except Exception as e:
        print(f"Error fetching Notion projects: {e}")
        return []


def find_project_by_name(query: str, projects: List[dict]) -> Optional[dict]:
    """Find project by fuzzy name matching"""
    if not query or not projects:
        return None

    query_lower = query.lower().strip()

    # Exact substring match first
    for project in projects:
        name = project['name'].lower()
        if query_lower in name or name in query_lower:
            return project

    # Fuzzy match
    from difflib import SequenceMatcher
    best_match = None
    best_ratio = 0.5

    for project in projects:
        name = project['name'].lower()
        ratio = SequenceMatcher(None, query_lower, name).ratio()

        # Check word matches
        words = query_lower.split()
        for word in words:
            if len(word) > 3 and word in name:
                ratio = max(ratio, 0.7)

        if ratio > best_ratio:
            best_ratio = ratio
            best_match = project

    return best_match


def update_notion_project(project_id: str, updates: dict) -> tuple:
    """Update a project in Notion"""
    try:
        headers = get_notion_headers()
        url = f"https://api.notion.com/v1/pages/{project_id}"

        properties = {}

        if updates.get('status'):
            status_map = {
                'done': '✅ Done',
                'zrobione': '✅ Done',
                'active': '🔵 Active',
                'aktywny': '🔵 Active',
                'planned': '📋 Planned',
                'planowany': '📋 Planned',
                'paused': '⏸️ Paused',
                'wstrzymany': '⏸️ Paused',
            }
            status = status_map.get(updates['status'].lower(), updates['status'])
            properties['Status'] = {'select': {'name': status}}

        if updates.get('next_action'):
            properties['Next Action'] = {
                'rich_text': [{'text': {'content': updates['next_action']}}]
            }

        if updates.get('deadline'):
            deadline_date = parse_deadline(updates['deadline'])
            if deadline_date:
                properties['Action Deadline'] = {'date': {'start': deadline_date}}

        # Always update Last Review
        properties['Last Review'] = {'date': {'start': datetime.now().strftime('%Y-%m-%d')}}

        response = requests.patch(url, headers=headers, json={'properties': properties}, timeout=30)

        if response.ok:
            return True, "OK"
        else:
            return False, response.json().get('message', response.text)

    except Exception as e:
        return False, str(e)


def create_notion_project(data: dict) -> tuple:
    """Create a new project in Notion"""
    try:
        headers = get_notion_headers()
        url = "https://api.notion.com/v1/pages"

        priority_map = {
            'high': '🔴 High', 'wysoki': '🔴 High', 'pilne': '🔴 High',
            'medium': '🟡 Medium', 'sredni': '🟡 Medium', 'średni': '🟡 Medium',
            'low': '🟢 Low', 'niski': '🟢 Low',
        }

        area_map = {
            'home': '🏠 Home', 'dom': '🏠 Home',
            'work': '💼 Work', 'praca': '💼 Work',
            'health': '❤️ Health', 'zdrowie': '❤️ Health',
            'finance': '💰 Finance', 'finanse': '💰 Finance',
            'growth': '📚 Growth', 'rozwoj': '📚 Growth', 'rozwój': '📚 Growth',
        }

        properties = {
            'Name': {'title': [{'text': {'content': data['name']}}]},
            'Status': {'select': {'name': '🔵 Active'}},
            'Priority': {'select': {'name': priority_map.get(data.get('priority', '').lower(), '🟡 Medium')}},
            'Last Review': {'date': {'start': datetime.now().strftime('%Y-%m-%d')}}
        }

        if data.get('area'):
            area = area_map.get(data['area'].lower(), data['area'])
            properties['Area'] = {'select': {'name': area}}

        if data.get('next_action'):
            properties['Next Action'] = {
                'rich_text': [{'text': {'content': data['next_action']}}]
            }

        if data.get('deadline'):
            deadline_date = parse_deadline(data['deadline'])
            if deadline_date:
                properties['Action Deadline'] = {'date': {'start': deadline_date}}

        payload = {
            'parent': {'database_id': NOTION_DATABASE_ID},
            'properties': properties
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.ok:
            page_id = response.json().get('id')
            return page_id, "OK"
        else:
            return None, response.json().get('message', response.text)

    except Exception as e:
        return None, str(e)


def get_recently_completed_projects(days: int = 7) -> List[dict]:
    """Fetch projects completed in the last N days"""
    try:
        headers = get_notion_headers()
        url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"

        week_ago = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        payload = {
            "filter": {
                "and": [
                    {"property": "Status", "select": {"equals": "✅ Done"}},
                    {"property": "Last Review", "date": {"on_or_after": week_ago}}
                ]
            }
        }

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

            projects.append({'name': name, 'area': area_name})

        return projects

    except Exception as e:
        print(f"Error fetching completed projects: {e}")
        return []


# --- Endpoints ---

@app.get("/api/health")
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "pai-search-api",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "pai_context_path": PAI_CONTEXT,
        "pai_context_exists": os.path.exists(PAI_CONTEXT)
    }


@app.post("/api/search")
def search_pai(req: SearchRequest, _=Depends(verify_token)):
    """Search PAI memory for information."""
    results = []
    query_lower = req.query.lower()
    query_words = [w for w in query_lower.split() if len(w) > 2]

    if not query_words:
        return {"query": req.query, "category": req.category, "count": 0, "results": []}

    search_paths = []
    if req.category == "all":
        search_paths = [
            f"{PAI_CONTEXT}/projects/*.md",
            f"{PAI_CONTEXT}/short-term/*.md",
            f"{PAI_CONTEXT}/*.md",
            f"{PAI_CONTEXT}/**/*.md",
            f"{PAI_CONTEXT}/inbox/**/*.json",
        ]
    elif req.category == "projects":
        search_paths = [f"{PAI_CONTEXT}/projects/*.md"]
    elif req.category == "notes":
        search_paths = [f"{PAI_CONTEXT}/short-term/*.md"]
    elif req.category == "inbox":
        search_paths = [f"{PAI_CONTEXT}/inbox/**/*.json"]
    elif req.category == "voice":
        search_paths = [f"{PAI_CONTEXT}/inbox/voice-sessions/*.json"]

    seen_files = set()

    for pattern in search_paths:
        for filepath in glob.glob(pattern, recursive=True):
            if filepath in seen_files:
                continue
            seen_files.add(filepath)

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    content_lower = content.lower()
                    score = sum(1 for word in query_words if word in content_lower)

                    if score > 0:
                        snippet = extract_snippet(content, query_words, max_len=500)
                        results.append({
                            "file": os.path.basename(filepath),
                            "path": filepath.replace(PAI_CONTEXT, ""),
                            "score": score,
                            "snippet": snippet,
                            "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                        })
            except Exception:
                continue

    results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "query": req.query,
        "category": req.category,
        "count": len(results[:req.limit]),
        "total_found": len(results),
        "results": results[:req.limit]
    }


@app.get("/api/context")
def get_context(_=Depends(verify_token)):
    """Return current PAI context for injection into voice assistant"""
    context = {
        "timestamp": datetime.now().isoformat(),
        "today": datetime.now().strftime("%A, %B %d, %Y"),
        "active_projects": [],
        "recent_notes": [],
        "telos": None
    }

    # Load telos if exists
    telos_path = f"{PAI_CONTEXT}/USER/TELOS.md"
    if os.path.exists(telos_path):
        with open(telos_path, 'r', encoding='utf-8') as f:
            context["telos"] = f.read()[:1000]

    # Load active projects from Notion
    notion_projects = get_notion_projects("🔵 Active")
    for p in notion_projects[:5]:
        context["active_projects"].append({
            "name": p['name'],
            "area": p['area'],
            "priority": p['priority'],
            "next_action": p['next_action'],
            "deadline": p['deadline']
        })

    # Load recent notes from short-term memory
    notes_dir = f"{PAI_CONTEXT}/short-term"
    if os.path.exists(notes_dir):
        note_files = sorted(glob.glob(f"{notes_dir}/*.md"), key=os.path.getmtime, reverse=True)[:5]
        for filepath in note_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    context["recent_notes"].append({
                        "file": os.path.basename(filepath),
                        "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                        "content": f.read()[:300]
                    })
            except Exception:
                continue

    return context


@app.post("/api/notes")
def add_note(req: NoteRequest, _=Depends(verify_token)):
    """Save a quick note to PAI memory"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"voice_note_{timestamp}.md"

    notes_dir = f"{PAI_CONTEXT}/short-term"
    os.makedirs(notes_dir, exist_ok=True)
    filepath = os.path.join(notes_dir, filename)

    tags_str = ", ".join(req.tags) if req.tags else "voice-note"
    note_content = f"""# Voice Note

**Date:** {datetime.now().isoformat()}
**Source:** {req.source}
**Tags:** {tags_str}

---

{req.content}
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(note_content)

    return {
        "status": "saved",
        "file": filename,
        "path": f"/short-term/{filename}",
        "timestamp": datetime.now().isoformat()
    }


# --- Project Management Endpoints ---

@app.get("/api/projects")
def get_projects(status: Optional[str] = None, _=Depends(verify_token)):
    """Get projects from Notion"""
    status_map = {
        'active': '🔵 Active',
        'done': '✅ Done',
        'planned': '📋 Planned',
        'paused': '⏸️ Paused',
    }

    status_filter = status_map.get(status.lower()) if status else None
    projects = get_notion_projects(status_filter)

    return {
        "count": len(projects),
        "status_filter": status,
        "projects": projects
    }


@app.patch("/api/projects")
def update_project(req: ProjectUpdateRequest, _=Depends(verify_token)):
    """Update a project in Notion"""
    projects = get_notion_projects()
    project = find_project_by_name(req.name, projects)

    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{req.name}' not found")

    updates = {}
    if req.status:
        updates['status'] = req.status
    if req.next_action:
        updates['next_action'] = req.next_action
    if req.deadline:
        updates['deadline'] = req.deadline

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    success, msg = update_notion_project(project['id'], updates)

    if success:
        return {
            "status": "updated",
            "project": project['name'],
            "updates": updates,
            "message": f"Updated '{project['name']}'"
        }
    else:
        raise HTTPException(status_code=500, detail=f"Update failed: {msg}")


@app.post("/api/projects")
def create_project(req: ProjectCreateRequest, _=Depends(verify_token)):
    """Create a new project in Notion"""
    data = {
        'name': req.name,
        'area': req.area,
        'priority': req.priority,
        'next_action': req.next_action,
        'deadline': req.deadline
    }

    page_id, msg = create_notion_project(data)

    if page_id:
        return {
            "status": "created",
            "project": req.name,
            "id": page_id,
            "message": f"Created project '{req.name}'"
        }
    else:
        raise HTTPException(status_code=500, detail=f"Creation failed: {msg}")


@app.get("/api/weekly-review")
def get_weekly_review(_=Depends(verify_token)):
    """Get data for weekly review"""
    active_projects = get_notion_projects("🔵 Active")
    completed_projects = get_recently_completed_projects(days=7)

    # Find projects with upcoming deadlines
    today = datetime.now().strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    upcoming_deadlines = [
        p for p in active_projects
        if p.get('deadline') and today <= p['deadline'] <= next_week
    ]

    high_priority = [
        p for p in active_projects
        if '🔴 High' in p.get('priority', '')
    ]

    # Find stale projects (not reviewed in 7 days)
    # Note: This requires Last Review field which we don't fetch by default

    return {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "active_count": len(active_projects),
            "completed_this_week": len(completed_projects),
            "high_priority_count": len(high_priority),
            "upcoming_deadlines_count": len(upcoming_deadlines)
        },
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        "high_priority": high_priority,
        "upcoming_deadlines": upcoming_deadlines,
        "reflection_questions": [
            "Co poszło dobrze w tym tygodniu?",
            "Co można było zrobić lepiej?",
            "Czy priorytety są nadal aktualne?",
            "Jaki jest główny cel na przyszły tydzień?"
        ]
    }


@app.post("/api/notion/{database}")
def query_notion(database: str, req: NotionQueryRequest, _=Depends(verify_token)):
    """Query Notion databases"""
    if database == "projects":
        projects = get_notion_projects()
        return {"database": database, "count": len(projects), "results": projects}

    return {
        "database": database,
        "filter": req.filter,
        "status": "not_implemented",
        "message": "Use /api/projects for project queries"
    }


# --- Voice Session Webhook ---

class VoiceSessionData(BaseModel):
    id: str
    timestamp: int
    duration: int
    transcripts: List[dict]

@app.post("/api/voice-session")
def save_voice_session(data: VoiceSessionData, _=Depends(verify_token)):
    """Webhook endpoint for Nexus to POST transcripts after session ends"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"voice_session_{timestamp}.json"

    sessions_dir = f"{PAI_CONTEXT}/inbox/voice-sessions"
    os.makedirs(sessions_dir, exist_ok=True)
    filepath = os.path.join(sessions_dir, filename)

    session_data = {
        "id": data.id,
        "timestamp": data.timestamp,
        "duration": data.duration,
        "transcripts": data.transcripts,
        "saved_at": datetime.now().isoformat()
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, indent=2)

    return {
        "status": "saved",
        "file": filename,
        "path": f"/inbox/voice-sessions/{filename}"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
