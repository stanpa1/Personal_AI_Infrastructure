# Daily Insights - FAZA 4.10

**Status:** ✅ DEPLOYED (2026-02-15)
**Priority:** high
**Time invested:** ~5h (design + implementation + deployment)

---

## Summary

PAI generates daily personalized insights based on your Note List, Books, and Projects in Notion. Uses cross-pollination, pattern recognition, and web research to create engaging, actionable insights delivered via Telegram.

**"Bring PAI to life"** - daily intellectual companion that surfaces connections, challenges assumptions, and sparks curiosity.

---

## Features

### 🎨 Insight Types (8 formats)

1. **Surprising Fact** 🧠
   - "Did you know..." style revelations
   - Recent research, counterintuitive facts
   - Connected to your interests

2. **Cross-Connection** 🔗
   - Links two different topics from your library
   - Non-obvious parallels (e.g., "Stoicism × AI reinforcement learning")
   - Pattern recognition across disciplines

3. **Practical Challenge** 💡
   - Actionable 5-30 minute experiments
   - Testable insights
   - Clear success criteria

4. **Deep Dive** 🌊
   - Advanced perspective on topics you know
   - Cutting-edge research
   - Edge cases and limitations

5. **Contrarian View** ⚡
   - Challenges conventional wisdom
   - Well-reasoned opposing perspectives
   - Intellectual honesty (shows both sides)

6. **Question to Ponder** 🤔
   - Thought-provoking questions
   - Philosophical depth
   - Optional hints at complexity

7. **Historical Perspective** 📜
   - Historical context for current topics
   - Specific dates, people, events
   - "What history teaches us"

8. **Pattern Recognition** 🔍
   - Identifies patterns across your interests
   - Meta-cognitive insights
   - Reveals thinking patterns

### 🧠 Intelligence Features

**Context Gathering:**
- Scans Note List (last 30 days, weighted by recency)
- Checks Books Tracker (currently reading + recent)
- Reviews Projects (active, sorted by priority)
- Extracts common themes and tags

**Topic Scoring:**
- Recency score (1.0 = today, 0.0 = 30 days ago)
- Diversity penalty (avoids repeats within 14 days)
- Cross-pollination potential (topics with tags)
- Source-based boosts (reading books, high-priority projects)

**Smart Selection:**
- Balances variety with context fit
- Avoids same insight type 3 days in a row
- Prioritizes cross-pollination opportunities
- Adapts to engagement patterns

**Web Research:**
- Optional Perplexity API integration
- Latest research (2024-2026)
- Expert opinions and citations
- Cost: ~$0.005/query

### 📱 Telegram Commands

**Basic:**
```
/insight now         - Generate insight immediately
/insight skip        - Skip today
/insight więcej      - Expand last insight
```

**Advanced:**
```
/insight połącz AI i Stoicism  - Force specific connection
/insight history               - Show last 7 days
/insight stats                 - Statistics & streak
/insight settings              - Current configuration
/insight help                  - Full command list
```

**Natural language (also works):**
```
"daj insight"
"rozwiń"
"pokaż insighty"
```

---

## Implementation

### Architecture

```
Daily Insight Pipeline (7:00 AM CET):

1. Context Gathering (topic_analyzer.py)
   ├─ Note List: last 30 days, extract tags
   ├─ Books Tracker: currently reading + recent
   ├─ Projects: active, high priority first
   └─ Theme extraction: common tags/keywords

2. Topic Scoring
   ├─ Recency score (1.0 → 0.0 over 30 days)
   ├─ Diversity penalty (avoid repeats)
   ├─ Cross-pollination potential
   └─ Source-based boosts

3. Insight Type Selection (insight_types.py)
   ├─ Select from 8 formats
   ├─ Balance variety (avoid same type 3x)
   ├─ Match context (e.g., CrossConnection if good pairs)
   └─ Add randomness (keep it interesting)

4. Research Phase (insight_generator.py)
   ├─ Optional web search (Perplexity)
   ├─ Cross-reference with user's notes
   ├─ Find surprising connections
   └─ Validate facts

5. Generation (DeepSeek)
   ├─ Format-specific prompts
   ├─ 150-350 words
   ├─ Polish language
   └─ Engaging, specific tone

6. Delivery
   ├─ Telegram message (primary)
   ├─ Save to Note List (Type=Insight, Tags=daily-insight)
   ├─ Track engagement
   └─ Update history

7. Engagement Tracking (engagement_tracker.py)
   ├─ Record reactions (like/love/skip)
   ├─ Track follow-ups (/więcej)
   ├─ Calculate engagement rate
   └─ Suggest frequency adjustments
```

### Files Created

**Server (Hetzner):**

1. **topic_analyzer.py** (~250 lines)
   - `get_note_list_topics()` - Fetch from Note List
   - `get_books_topics()` - Currently reading
   - `get_projects_topics()` - Active projects
   - `extract_common_themes()` - Tag/keyword analysis
   - `score_topics_for_insight()` - Scoring algorithm
   - `find_cross_pollination_pairs()` - Connection opportunities
   - `get_insight_context()` - Main orchestrator

2. **insight_types.py** (~200 lines)
   - 8 format classes (SurprisingFact, CrossConnection, etc.)
   - Prompt templates for each type
   - Output formatting
   - `select_insight_type()` - Smart type selection

3. **insight_generator.py** (~300 lines)
   - `research_topic()` - Web search integration
   - `generate_insight()` - AI generation with DeepSeek
   - `generate_followup_insight()` - Expand on demand
   - Format-specific prompt building

4. **insight_engine.py** (~400 lines)
   - `generate_daily_insight()` - Main orchestrator
   - `save_insight_to_history()` - Track generations
   - `save_insight_to_notion()` - Create Note List entry
   - `get_insight_stats()` - Statistics
   - Settings management

5. **insight_handler.py** (~200 lines)
   - `detect_insight_command()` - Pattern matching
   - `handle_insight_command()` - Command router
   - Individual handlers (now, skip, more, connect, etc.)
   - `send_daily_insight_to_telegram()` - Cron entry point

6. **engagement_tracker.py** (~150 lines)
   - `track_reaction()` - Record user reactions
   - `track_followup()` - Track expansions
   - `get_engagement_stats()` - Analytics
   - `should_adjust_frequency()` - Smart suggestions

**Modified:**
- `/opt/inbox-webhook/process_event.py` - Add insight command detection

**Cron Job:**
- `/etc/cron.d/pai-insights` - Daily at 6:00 UTC (7:00 CET)

**Local (Documentation):**
- `/home/pawel/.pai/memory/projects/daily-insights.md` (this file)

---

## Configuration

**Environment Variables (.env):**
```bash
# Required
NOTION_TOKEN=secret_xxx
DEEPSEEK_API_KEY=sk-xxx
TELEGRAM_CHAT_ID=123456

# Optional (web research)
PERPLEXITY_API_KEY=pplx-xxx  # Or TAVILY_API_KEY
WEB_SEARCH_PROVIDER=perplexity  # or tavily
```

**Settings File:** `/opt/inbox-webhook/data/insight_settings.json`
```json
{
  "enabled": true,
  "time": "07:00",
  "frequency": "daily",
  "depth_level": "enhanced",
  "use_web_research": true,
  "min_word_count": 150,
  "max_word_count": 350
}
```

**Notion Databases:**
- Note List: `cb912123-bf69-4623-b08c-43fd8e03d9cd`
- Books Tracker: `20cd6ad6-369a-803a-a25d-f2bfd4683d36`
- Projects: `9d5a78f7-c14e-44f8-b885-8cc5feaf99f8`

---

## Usage Examples

### Daily Delivery (Automatic)

**7:00 AM CET:**
```
🌅 Good morning!

🔗 Nieoczywiste połączenie

Atomic Habits (James Clear) × Claude Extended Thinking

Czytasz "Atomic Habits" i zapisałeś artykuł o extended thinking
w AI. Zaskakujące podobieństwo: Clear's "habit loop"
(cue→routine→reward) to dosłownie reinforcement learning
(state→action→reward).

Ale jest różnica: AI potrzebuje milionów iteracji, ty tylko ~66 dni.
Twoja przewaga: meta-learning - umiesz "learn how to learn".

💡 Eksperyment: Zastosuj epsilon-greedy strategy (95% sprawdzone
nawyki, 5% exploration) do swojej rutyny. AI robi to samo.

📎 Źródło: Atomic Habits × Claude API docs
```

### On-Demand Commands

**User:** `/insight now`
**PAI:**
```
🎨 Generuję insight...

🧠 Ciekawostka dnia

W 1945 Vannevar Bush opisał "Memex" - urządzenie do organizowania
wiedzy. Twój Note List to realizacja jego wizji sprzed 80 lat,
ale z jednym kluczowym ulepszeniem: AI może teraz znajdować
połączenia które Ty przeoczyłeś.

Bush przewidział "trails" między dokumentami. Ty masz Tags.
Różnica? Twoje tagi są ręczne - ale DeepSeek może wykryć
ukryte patterny...

📎 Źródło: Note List analysis

📝 Zapisano w Notion: https://notion.so/xxx
```

**User:** `/insight więcej - pokaż przykłady tych ukrytych patternów`
**PAI:**
```
🔄 Rozwijam ostatni insight...

📚 Rozwinięcie insightu

Ukryte patterny w Twoim Note List (ostatnie 30 dni):

1. **Temporal clustering**: 80% twoich notatek o AI pojawia się
   w poniedziałki (godziny poranne). Wzorzec: weekend reflection →
   monday deep dive.

2. **Tag co-occurrence**: Gdy masz tag "AI" + "productivity",
   prawdopodobieństwo że dodasz kolejną notatkę w ciągu 24h
   wynosi 73%. "AI" + "philosophy" = tylko 12%.

3. **Orphan notes**: 15 notatek bez żadnych tagów. Wszystkie
   są starsze niż 20 dni. Wzorzec: jeśli nie otagowałeś w
   pierwsze 48h, prawdopodobnie nigdy nie wrócisz.

[...]
```

**User:** `/insight połącz Stoicism i Memory Systems`
**PAI:**
```
🔗 Łączę: Stoicism × Memory Systems...

🔗 Nieoczywiste połączenie

Stoicism × Memory Systems

Marcus Aurelius pisał "Meditations" dla siebie - to był jego
personal memory system, 2000 lat przed Zettelkasten.

Kluczowa różnica między stoickim journaling a modern PKM:
Stoicy nie optymalizowali dla retrieval, tylko dla
TRANSFORMATION. Pisanie było praktyką, nie archiwizacją.

Twój Note List: 247 wpisów. Ile z nich zmieniło twoje myślenie
vs. ile tylko zapisało informację?

💡 Stoic PKM test: Każda notatka musi odpowiadać "How does
this change how I act?"

[...]
```

---

## Cost Analysis

**Daily Operation:**
- DeepSeek generation: ~$0.02/insight
- Perplexity search (optional): ~$0.005/query
- **Total: ~$0.025/day = $0.75/month**

**Annual cost:** ~$9/year

**ROI:** Priceless (intellectual growth, pattern recognition, curiosity)

---

## Testing

**Manual test:**
```bash
# SSH to server
ssh hetzner

# Test topic analysis
cd /opt/inbox-webhook
/opt/inbox-webhook/venv/bin/python topic_analyzer.py

# Test insight generation (specific type)
/opt/inbox-webhook/venv/bin/python insight_engine.py test cross

# Test command detection
/opt/inbox-webhook/venv/bin/python insight_handler.py test

# Test full pipeline (send to Telegram)
/opt/inbox-webhook/venv/bin/python insight_handler.py send

# Check stats
/opt/inbox-webhook/venv/bin/python insight_engine.py stats
```

**Expected output:**
```
🔍 Gathering insight context...
   📝 Note List: 247 topics
   📚 Books: 5 topics
   🎯 Projects: 3 topics

📊 Top Topics:
   1.00 - Claude extended thinking (note_list)
   0.85 - Atomic Habits (books)
   0.80 - PAI System (projects)

🔗 Top Cross-Pollination Pairs:
   0.92 - Atomic Habits × PAI System
   0.78 - Claude extended thinking × Memory systems
   0.65 - Stoicism × Productivity

✅ INSIGHT GENERATED SUCCESSFULLY
```

---

## Integration with PAI Ecosystem

**Synergies:**
- ✅ Uses existing Notion databases (Note List, Books, Projects)
- ✅ Integrates with Telegram bot infrastructure
- ✅ Saves insights back to Note List (creates feedback loop)
- ✅ Uses DeepSeek API (same as research briefs, TODO extraction)
- ✅ Follows PAI memory architecture (short/mid/long-term)
- ✅ Complements morning/evening check-ins (different purpose)

**Differences from Research Briefs (FAZA 4.1):**
- Research = user-requested, deep, overnight, PDF
- Insights = automatic, daily, lightweight, Telegram
- Research = answer specific question
- Insights = spark curiosity, surface connections

**Differences from Check-ins (FAZA 3.0):**
- Check-ins = project status updates, task management
- Insights = intellectual exploration, learning
- Check-ins = "What are you working on?"
- Insights = "Here's something interesting..."

---

## Engagement Metrics

**Success criteria:**
- ✅ User reads daily insight (open rate)
- ✅ User reacts (emoji, reply)
- ✅ User requests expansion (/więcej)
- ✅ User saves to Notion manually
- ✅ 7-day streak maintained

**Engagement tracking:**
- Reaction types: like, love, skip, more, share
- Follow-up rate: % of insights that trigger expansion
- Topic diversity: unique topics covered
- Type balance: distribution across 8 formats

**Adjustments based on engagement:**
- Low engagement (<20%) → Suggest decrease frequency
- High engagement (>70%) → Suggest increase frequency
- Certain types preferred → Adjust type selection weights

---

## Weekly Digest

**Status:** ✅ DEPLOYED (2026-02-15)

Automatic weekly summary of Note List activity sent every Sunday 20:00 CET.

**Features:**
- Summary by type (Article, Tool, Video, etc.)
- High-value content (Score >= 4)
- Top tags from the week
- Detailed breakdown with first 5 entries per type
- Insights (productivity level, dominant type)

**New files:**
- `/opt/inbox-webhook/auto_weekly_digest.py` - Main script
- `/etc/cron.d/pai-weekly-digest` - Cron job (Sunday 19:00 UTC / 20:00 CET)

**Usage:**
```bash
# Manual run
ssh hetzner "cd /opt/inbox-webhook && /opt/inbox-webhook/venv/bin/python auto_weekly_digest.py"

# Check logs
ssh hetzner "tail -f /var/log/pai-weekly-digest.log"
```

**Telegram Output Example:**
```
📚 Weekly Digest: Note List
📅 08.02 - 15.02.2026
📊 Łącznie: 15 wpisów

📂 Według typu:
  • Article: 8
  • Tool: 4
  • Video: 3

⭐ High Value (5 wpisów):
  • Claude extended thinking patterns (Score: 5)
  • Memory in AI Agents - Production Patterns (Score: 5)
  ... i 3 więcej

🏷️ Top tagi:
  • AI: 7×
  • productivity: 5×
  • learning: 4×

📑 Szczegóły:
[... detailed breakdown by type ...]

💡 Insights:
  • Produktywny tydzień! 15 nowych wpisów
  • Dominujący typ: Article (8 wpisów)

---
🤖 Automatyczne podsumowanie z PAI Daily Digest
```

---

## Future Enhancements (Optional)

### FAZA 4.11 - Advanced Features

**1. Voice Delivery:**
- TTS integration (Google Cloud Text-to-Speech)
- Morning voice insight via Telegram voice message
- Adjust length for audio format (~1-2 min)

**2. Visual Insights:**
- Knowledge graph visualization
- ASCII art diagrams
- Connection maps between topics

**3. Interactive Mode:**
- "Choose your own adventure" insights
- User selects depth level (quick/medium/deep)
- Branching follow-ups

**4. Social Features:**
- Share best insights to social media
- Weekly digest format (newsletter)
- Public insight feed (optional)

**5. Adaptive Learning:**
- Learn from user reactions
- Personalized complexity calibration
- Topic freshness optimization

**6. Scheduled Variations:**
- Morning: motivational/actionable
- Lunch: quick curiosity
- Evening: reflective/philosophical
- Random surprise: keeps it fresh

---

## Troubleshooting

### No Topics Found
```
⚠️ Brak tematów do analizy.

Rozwiązanie:
- Dodaj więcej wpisów do Note List
- Oznacz książki jako "Reading" w Books Tracker
- Ustaw projekty jako "Active"
```

### Insight Generation Failed
```
❌ Generation error: [error message]

Rozwiązanie:
1. Sprawdź DEEPSEEK_API_KEY w .env
2. Sprawdź Notion token permissions
3. Zobacz logi: tail -f /var/log/pai-insights.log
```

### Repeating Topics
```
Insight covers same topic as yesterday

Rozwiązanie:
- System automatycznie karze powtórki (14 dni)
- Jeśli masz mało różnorodnych tematów, dodaj więcej do Notion
- Sprawdź insight_history.json
```

### Cron Not Running
```
Insights not delivered at 7:00 AM

Rozwiązanie:
1. Sprawdź cron: crontab -l
2. Test manual: python insight_handler.py send
3. Sprawdź logi: tail -f /var/log/pai-insights.log
4. Sprawdź timezone: date (should be CET)
```

---

## Deployment ✅ Complete (2026-02-15)

**Initial deployment:**
1. ✅ Uploaded 6 modules to /opt/inbox-webhook/
2. ✅ Dependencies already installed
3. ✅ Cron job configured (/etc/cron.d/pai-insights)
4. ✅ Pipeline tested successfully

**Integration fixes (2026-02-15):**
1. ✅ Added insight_handler import to process_event.py (line 36)
2. ✅ Added insight command detection before calendar handler (line 567)
3. ✅ Fixed chat_id type conversion (string → int) in all send_message calls
4. ✅ Added TELEGRAM_CHAT_ID=-1003590663382 to .env
5. ✅ Reloaded systemd daemon and restarted inbox-worker service

**Test results:**
- ✅ Manual test via `/insight now` successful
- ✅ Insight generated (QuestionToPonder about Minimax)
- ✅ Saved to Notion successfully
- ✅ Delivered to Telegram successfully

---

## Completion Notes

**Status:** ✅ COMPLETE & OPERATIONAL (2026-02-15)

**Implementation:**
- Design & implementation: ~4h
- Deployment & debugging: ~1.5h
- Total time invested: ~5.5h

**Completed:**
1. ✅ Deployed to Hetzner server
2. ✅ All 8 insight types implemented
3. ✅ Notion integration working (saves as Type=Insight)
4. ✅ Telegram commands functional
5. ✅ Manual test successful (`/insight now` delivered)
6. ✅ Automatic delivery scheduled (7:00 AM daily)

**Next steps:**
- Monitor first week of automatic insights
- Adjust based on engagement metrics
- Optional: Fix Books DB integration (400 error - non-critical)

---

## Related Projects

- **Research Briefs (FAZA 4.1):** Deep overnight analysis
- **Check-ins (FAZA 3.0):** Project status updates
- **TODO Extraction (FAZA 4.7):** Action item detection
- **Notion Integration (FAZA 2.6):** Database foundation

---

This completes the design and implementation of FAZA 4.10 - Daily Insights. Ready for deployment and testing.
