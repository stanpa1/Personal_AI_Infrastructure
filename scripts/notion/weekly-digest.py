#!/usr/bin/env python3
"""
Weekly Digest Generator dla Note List
Rozwiązuje problem: trudno przeszukiwać notatki po datach w Notion

Jak używać:
1. Uruchom: python3 weekly-digest.py
2. Lub powiedz Claude: "wygeneruj weekly digest"
"""

from datetime import datetime, timedelta
from collections import defaultdict
import json

class WeeklyDigestGenerator:
    """
    Generator automatycznych podsumowań tygodniowych dla Note List
    
    Rozwiązuje problemy:
    - Trudno przeszukiwać po datach → Pobiera wszystko i filtruje lokalnie
    - Brak struktury → Automatyczne grupowanie po Type
    - Ciężko wyciągać insights → Analiza wzorców i tematów
    - Screening wymaga ręcznego przeglądania → Automatyczne podsumowanie
    """
    
    def __init__(self, days_back=7):
        self.days_back = days_back
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=days_back)
        
    def get_date_range_string(self):
        """Zwraca czytelny zakres dat"""
        return f"{self.start_date.strftime('%d.%m.%Y')} - {self.end_date.strftime('%d.%m.%Y')}"
    
    def parse_notion_entries(self, entries):
        """
        Parsuje wpisy z Notion i organizuje je
        
        Args:
            entries: Lista wpisów z Notion API
            
        Returns:
            dict: Uporządkowane dane według kategorii
        """
        organized = {
            'by_type': defaultdict(list),
            'by_area': defaultdict(list),
            'high_value': [],
            'completed': [],
            'pending_actions': [],
            'all_entries': []
        }
        
        for entry in entries:
            # Filtruj po dacie utworzenia
            created = datetime.fromisoformat(entry.get('Created time', '').replace('Z', '+00:00'))
            
            if created < self.start_date or created > self.end_date:
                continue
                
            # Grupuj według typu
            entry_type = entry.get('Type', 'Other')
            organized['by_type'][entry_type].append(entry)
            
            # Grupuj według obszaru
            areas = entry.get('Area', [])
            if isinstance(areas, str):
                areas = json.loads(areas) if areas else []
            for area in areas:
                organized['by_area'][area].append(entry)
            
            # High value (Score >= 4)
            score = entry.get('Score', 0) or 0
            if score >= 4:
                organized['high_value'].append(entry)
            
            # Completed vs Pending actions
            if entry_type == 'Action':
                if entry.get('Done') == '__YES__':
                    organized['completed'].append(entry)
                else:
                    organized['pending_actions'].append(entry)
            
            organized['all_entries'].append(entry)
        
        return organized
    
    def extract_topics(self, entries):
        """
        Wyciąga główne tematy z wpisów
        Analizuje tytuły i autorów aby znaleźć wzorce
        """
        topics = defaultdict(int)
        
        for entry in entries:
            name = entry.get('Name', '').lower()
            author = entry.get('Author', '').lower()
            
            # Słowa kluczowe do wykrycia tematów
            keywords = {
                'AI': ['ai', 'claude', 'gpt', 'llm', 'agent', 'mcp'],
                'Programming': ['code', 'python', 'javascript', 'api', 'github'],
                'Productivity': ['gtd', 'notion', 'workflow', 'productivity', 'system'],
                'Memory/Knowledge': ['memory', 'knowledge', 'graph', 'zettelkasten', 'obsidian'],
                'Climbing': ['climbing', 'wspinaczka', 'boulder', 'route'],
            }
            
            for topic, words in keywords.items():
                if any(word in name or word in author for word in words):
                    topics[topic] += 1
        
        # Sortuj po liczbie wystąpień
        return sorted(topics.items(), key=lambda x: x[1], reverse=True)
    
    def generate_markdown_digest(self, organized_data):
        """
        Generuje podsumowanie w formacie Markdown
        """
        md = []
        
        # Header
        md.append(f"# 📊 Weekly Digest - {self.get_date_range_string()}\n")
        md.append(f"*Wygenerowano: {datetime.now().strftime('%d.%m.%Y %H:%M')}*\n")
        md.append("---\n")
        
        # Statystyki
        md.append("## 📊 Statystyki\n")
        md.append(f"- **Łącznie wpisów:** {len(organized_data['all_entries'])}\n")
        md.append("- **Breakdown po typach:**\n")
        for entry_type, entries in sorted(organized_data['by_type'].items(), key=lambda x: len(x[1]), reverse=True):
            md.append(f"  - {entry_type}: {len(entries)}\n")
        md.append("\n")
        
        # Główne tematy
        topics = self.extract_topics(organized_data['all_entries'])
        if topics:
            md.append("## 🔥 Główne tematy\n")
            for i, (topic, count) in enumerate(topics[:5], 1):
                md.append(f"{i}. **{topic}** - {count} wpisów\n")
            md.append("\n")
        
        # High value content
        if organized_data['high_value']:
            md.append("## ⭐ High Value Content (Score ≥ 4)\n")
            for entry in organized_data['high_value']:
                name = entry.get('Name', 'Untitled')
                entry_type = entry.get('Type', 'Note')
                score = entry.get('Score', 0)
                link = entry.get('Link', '')
                md.append(f"- **{name}** ({entry_type}) - Score: {score}\n")
                if link:
                    md.append(f"  - 🔗 {link}\n")
            md.append("\n")
        
        # Completed actions
        if organized_data['completed']:
            md.append("## ✅ Ukończone zadania\n")
            for entry in organized_data['completed']:
                md.append(f"- [x] {entry.get('Name', 'Untitled')}\n")
            md.append("\n")
        
        # Pending actions
        if organized_data['pending_actions']:
            md.append("## ⚠️ Oczekujące zadania\n")
            for entry in organized_data['pending_actions']:
                name = entry.get('Name', 'Untitled')
                due_date = entry.get('date:Due Date:start', '')
                if due_date:
                    md.append(f"- [ ] {name} - Deadline: {due_date}\n")
                else:
                    md.append(f"- [ ] {name}\n")
            md.append("\n")
        
        # Insights
        md.append("## 🎯 Insights\n")
        
        # Analiza aktywności
        by_area = organized_data['by_area']
        if 'Work' in by_area and 'Private' in by_area:
            work_count = len(by_area['Work'])
            private_count = len(by_area['Private'])
            total = work_count + private_count
            work_pct = (work_count / total * 100) if total > 0 else 0
            md.append(f"- **Work/Life balance:** {work_pct:.0f}% Work, {100-work_pct:.0f}% Private\n")
        
        # Sugestie
        if len(organized_data['all_entries']) < 3:
            md.append("- 💡 Mało aktywności w tym tygodniu - może warto częściej notować pomysły?\n")
        
        if not organized_data['completed'] and organized_data['pending_actions']:
            md.append("- ⚡ Dużo zadań w toku - może warto się skupić na dokończeniu kilku?\n")
        
        md.append("\n")
        
        # Footer
        md.append("---\n")
        md.append("*💡 Tip: Zapisz to podsumowanie jako notatkę w Notion dla przyszłych referencji*\n")
        
        return ''.join(md)


# Instrukcje użycia dla Claude
CLAUDE_INSTRUCTIONS = """
Aby wygenerować weekly digest, wykonaj następujące kroki:

1. Pobierz WSZYSTKIE wpisy z Note List (bez filtrów dat):
   - Użyj Notion:notion-search z data_source_url: collection://9d5a78f7-c14e-44f8-b885-8cc5feaf99f8
   - Lub pobierz po ID konkretne wpisy

2. Dla każdego znalezionego wpisu, pobierz pełne szczegóły:
   - Notion:notion-fetch z page_id każdego wpisu
   - Zbierz properties: Name, Type, Score, Author, Link, Created time, Done, Area, Due Date

3. Filtruj lokalnie:
   - Sprawdź Created time czy jest w ostatnich 7 dniach
   - Oblicz: datetime.now() - timedelta(days=7)

4. Użyj WeeklyDigestGenerator do wygenerowania podsumowania:
   - generator = WeeklyDigestGenerator(days_back=7)
   - organized = generator.parse_notion_entries(entries)
   - markdown = generator.generate_markdown_digest(organized)

5. Zwróć użytkownikowi wygenerowane podsumowanie w formacie markdown

6. Zapytaj czy chce zapisać to jako notatkę w Notion

WAŻNE: 
- Notion search po datach NIE DZIAŁA dobrze
- Dlatego pobieramy WSZYSTKO i filtrujemy lokalnie w Pythonie
- To obchodzi ograniczenia API
"""

if __name__ == "__main__":
    print("Weekly Digest Generator - Ready!")
    print(CLAUDE_INSTRUCTIONS)
