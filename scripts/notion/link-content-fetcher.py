#!/usr/bin/env python3
"""
Link Content Fetcher dla Note List
Rozwiązuje problem: wpisy z Reddit/X mają tylko link, treść jest ukryta

Automatycznie:
1. Wykrywa wpisy z linkiem ale bez treści w Note field
2. Pobiera treść ze strony (Reddit, X, etc.)
3. Dodaje podsumowanie do Note field w Notion
"""

class LinkContentFetcher:
    """
    Automatyczne pobieranie i dodawanie treści z linków do wpisów w Notion
    """
    
    def __init__(self):
        self.reddit_posts = []
        self.x_posts = []
        self.other_links = []
    
    def detect_empty_content_entries(self, entries):
        """
        Wykrywa wpisy które mają link ale nie mają treści
        
        Returns:
            list: Wpisy wymagające pobrania treści
        """
        needs_fetch = []
        
        for entry in entries:
            has_link = entry.get('Link', '') != ''
            has_no_content = not entry.get('Note') or entry.get('Note').strip() == ''
            
            if has_link and has_no_content:
                needs_fetch.append(entry)
        
        return needs_fetch
    
    def categorize_links(self, entries):
        """
        Kategoryzuje linki według źródła
        """
        for entry in entries:
            link = entry.get('Link', '')
            
            if 'reddit.com' in link:
                self.reddit_posts.append(entry)
            elif 'x.com' in link or 'twitter.com' in link:
                self.x_posts.append(entry)
            else:
                self.other_links.append(entry)
    
    def fetch_reddit_content(self, url):
        """
        Pobiera treść z Reddit (używając web_fetch)
        
        For Claude: Use web_fetch tool to get the content
        """
        # Claude will use: web_fetch tool with the URL
        # Then extract the main post content and top comments
        pass
    
    def fetch_x_content(self, url):
        """
        Pobiera treść z X/Twitter
        """
        # Claude will use: web_fetch tool
        pass
    
    def generate_summary(self, content, max_length=500):
        """
        Generuje krótkie podsumowanie treści dla Note field
        
        Args:
            content: Pełna treść postu
            max_length: Maksymalna długość podsumowania
            
        Returns:
            str: Podsumowanie w formacie:
                 "📝 [Source]: [Title/Main point]
                  Key points:
                  - Point 1
                  - Point 2
                  [Link]"
        """
        # Claude will use LLM to summarize
        pass
    
    def update_notion_entry(self, entry_id, summary):
        """
        Aktualizuje wpis w Notion - dodaje podsumowanie do Note field
        
        For Claude: Use Notion:notion-update-page
        """
        pass


# Workflow dla Claude
CLAUDE_WORKFLOW = """
WORKFLOW: Automatyczne pobieranie treści dla wpisów z Reddit/X

KROK 1: Wykryj wpisy wymagające pobrania treści
----------------------------------------
For each entry in Weekly Digest:
    if entry.Link exists AND entry.Note is empty:
        add to needs_fetch list

KROK 2: Pobierz treść z każdego linku
----------------------------------------
For each entry in needs_fetch:
    1. Use web_fetch(entry.Link)
    2. Extract main content:
       - Reddit: Post title, body, top 2-3 comments
       - X: Tweet text, thread if applicable
       - Other: Main article text
    
KROK 3: Wygeneruj podsumowanie
----------------------------------------
For each fetched content:
    Use LLM to create summary in format:
    
    "📝 Reddit: Claude 'soul document' discussion
    
    Main point: Thread discussing Anthropic's 80-page constitutional AI document
    
    Key insights:
    - Document defines Claude's personality and ethics
    - Debate: Is 80 pages enough for aligned AI?
    - Comparison to human moral development
    
    Top comment: 'Quality > quantity, but context matters'
    
    🔗 reddit.com/r/ClaudeAI/..."

KROK 4: Aktualizuj Notion
----------------------------------------
For each entry:
    Use Notion:notion-update-page to add summary to Note field

KROK 5: Dodaj do Weekly Digest
----------------------------------------
Now these entries can be included in Weekly Digest with full context!

WAŻNE:
- Podsumowanie w Note field (nie content) - bo content może być długi
- Format czytelny i scannable
- Max ~500 znaków (żeby było przejrzyste)
- Zawsze link na końcu
"""

# Przykład użycia dla Claude
EXAMPLE_USAGE = """
# Przykład: Wpis "Claude soul"

## Przed:
{
    "Name": "Claude soul",
    "Link": "reddit.com/r/ClaudeAI",
    "Note": "",  # PUSTE!
    "Type": "",
    "Score": 0
}

## Po użyciu Link Content Fetcher:

Claude wywołuje:
1. web_fetch("reddit.com/r/ClaudeAI/...")
2. Wyciąga treść postu + top comments
3. Generuje podsumowanie
4. notion-update-page() z nowym Note

{
    "Name": "Claude soul",
    "Link": "reddit.com/r/ClaudeAI",
    "Note": "📝 Reddit: Claude's 80-page 'soul document'
    
    Discussion about Anthropic's constitutional AI document that defines Claude's personality.
    
    Key points:
    - Document shapes Claude's ethics and behavior
    - Community debate on sufficiency of 80 pages
    - Comparison to human moral frameworks
    
    Top insight: Quality of guidelines matters more than quantity
    
    🔗 Full thread: reddit.com/r/...",
    
    "Type": "Article",
    "Score": 4
}

## Teraz w Weekly Digest:
Wpis będzie miał pełen kontekst i może być przeanalizowany!
"""

if __name__ == "__main__":
    print("Link Content Fetcher - Ready!")
    print(CLAUDE_WORKFLOW)
    print("\n" + "="*50 + "\n")
    print(EXAMPLE_USAGE)
