# AI Conversation Archive - FAZA 4.6

**Status:** ✅ MVP COMPLETE (2026-02-15)
**Priority:** medium

---

## Summary

System do archiwizacji wartościowych rozmów z różnych platform AI (ChatGPT, Claude, Gemini, Perplexity) eksportowanych przez Chrome extension → automatyczne przetwarzanie → Notion Note List.

---

## Architecture

```
Chrome Extension → Export to Google Docs → Google Drive (Gemini_Dziennik folder)
    ↓
n8n: Google Drive Trigger (hourly poll)
    ↓
n8n: Download File (convert Google Docs to plain text)
    ↓
n8n: HTTP Request → https://inbox.stankowski.io/webhook
    ↓
Hetzner: conversation_handler.py
    ├─ Parse metadata (platform, date, title)
    ├─ Summarize (DeepSeek - 100-200 words if >1000 chars)
    ├─ Extract TODOs
    └─ Classify Type/Tags (DeepSeek)
    ↓
Notion Note List
    ├─ Name: conversation title
    ├─ Type: "Conversation" (rich_text)
    ├─ Tags: auto-detected (multi_select)
    ├─ Author: "{Platform} - {Date}"
    ├─ Note: summary
    └─ Children: full summary + TODO checkboxes
```

---

## Implementation Complete

### n8n Workflow ✅

**Name:** "Google Drive → PAI Conversation Archive"
**ID:** PiYgRzVAgW3JSrv9 (modified from GitHub upload workflow)

**Nodes:**
1. Google Drive Trigger → Folder: Gemini_Dziennik
2. Download File → Convert to plain text
3. Send to Webhook → POST https://inbox.stankowski.io/webhook

**Authentication:** X-Webhook-Secret header

### Hetzner Backend ✅

**Files:**
- `/opt/inbox-webhook/conversation_handler.py` - Main processor
- `/opt/inbox-webhook/main.py` - Added ConversationEvent model + `/webhook` endpoint

**Dependencies installed:**
- `notion-client` (2.7.0)

**Processing pipeline:**
1. `parse_conversation_metadata()` - Extract title, platform, date
2. `summarize_conversation()` - DeepSeek summary if >1000 chars
3. `extract_todos()` - Regex patterns for action items
4. `classify_content()` - DeepSeek Type/Tags classification
5. `save_to_notion()` - Create page in Note List

**Cost:** ~$0.02-0.05 per conversation (DeepSeek)

### Test Result ✅

```json
{
  "status": "success",
  "page_id": "308d6ad6-369a-81c2-840f-fc80b355ad0c",
  "title": "How to build a personal AI system",
  "platform": "Claude",
  "summary_length": 921,
  "todos_count": 2
}
```

---

## Chrome Extension

**Name:** ChatGPT AI Backup & Export
**URL:** https://chromewebstore.google.com/detail/chatgpt-ai-backup-export/oedpeddiacomhhfieanenlmdghkolgng

**Platforms supported:**
- ChatGPT
- Claude.ai
- Gemini
- Perplexity

**Export method:**
1. Click extension during conversation
2. Export to Google Docs
3. Save to "Gemini_Dziennik" folder on Google Drive

---

## User Workflow

1. Have valuable conversation in ChatGPT/Claude/Gemini/Perplexity
2. Click Chrome extension → "Export to Google Docs"
3. Save to "Gemini_Dziennik" folder
4. Wait ~1 hour (n8n polls hourly)
5. Conversation auto-processed:
   - Summarized (DeepSeek)
   - TODOs extracted
   - Classified (Type + Tags)
   - Saved to Notion
6. Query via voice app: "find conversations about X"
7. Appears in weekly digest (NotionDigest)

---

## Notion Schema

**Database:** Note List (cb912123-bf69-4623-b08c-43fd8e03d9cd)

**Fields used:**
- `Name` (title) - Conversation title (first 100 chars)
- `Type` (rich_text) - "Conversation"
- `Tags` (multi_select) - Auto-detected keywords (2-5 tags)
- `Author` (rich_text) - "{Platform} - {Date}" (e.g. "ChatGPT - 2026-02-15")
- `Note` (rich_text) - Summary (max 2000 chars)
- `Children` blocks:
  - Paragraph: full summary
  - Heading 3: "Action Items" (if TODOs found)
  - To-do blocks: extracted TODOs

---

## Processing Details

### Platform Detection

Heuristics from filename and content:
- "chatgpt" / "openai" → ChatGPT
- "claude" → Claude
- "gemini" / "bard" → Gemini
- "perplexity" → Perplexity

### Summarization

**Trigger:** Content > 1000 chars
**Model:** DeepSeek (deepseek-chat)
**Prompt:** "Summarize in 100-200 words, focus on main topic, key insights, conclusions. Use Polish if Polish, otherwise English."
**Max tokens:** 400
**Fallback:** First 500 chars if API fails

### TODO Extraction

**Patterns:**
- `TODO:`, `To do:`, `Action item:`, `Next step:`
- `[ ]` checkbox format
- `I will`, `I'll`, `I should`, `Need to`

**Limits:** 10-200 chars per TODO, max 10 TODOs

### Classification

**Model:** DeepSeek (deepseek-chat)
**Output:** JSON with `type`, `tags`, `area`
**Tags:** 2-5 short English keywords
**Fallback:** `{'type': 'Conversation', 'tags': [], 'area': 'Private'}`

---

## Integration with PAI

**Synergies:**
- ✅ Reuses DeepSeek API (already configured)
- ✅ Reuses Notion API (already configured)
- ✅ Same n8n infrastructure as inbox system
- ✅ Same webhook pattern as inbox
- ✅ Voice app search works (existing `searchNotes` tool)
- ✅ Weekly digest includes conversations (NotionDigest)

**New code:**
- `conversation_handler.py` (~300 lines)
- `ConversationEvent` model in main.py
- `/webhook` endpoint in main.py (~50 lines)
- Modified n8n workflow (GitHub → webhook)

---

## Activation Steps

1. ✅ n8n workflow created and configured
2. ⚠️ **ACTION REQUIRED:** Activate workflow in n8n UI
   - Go to https://n8n.stankowski.io/
   - Open "Google Drive → PAI Conversation Archive"
   - Click "Activate" button
3. ✅ Hetzner handler deployed and tested
4. ✅ Notion schema validated
5. ✅ Test conversation processed successfully

---

## Next Steps (Optional)

### Phase 2: Enhanced Features
- [ ] Archive full text to separate location (Google Drive folder)
- [ ] Telegram notification when conversation imported
- [ ] Observatory tab for recent conversation imports
- [ ] Stats: conversations per platform, trending topics

### Phase 3: Voice Integration
- [ ] PAI API endpoint: `GET /api/conversations`
- [ ] Voice tool: `searchConversations` (optional - `searchNotes` already works)

### Phase 4: Analytics
- [ ] Track conversation topics over time
- [ ] Most discussed themes
- [ ] Platform usage statistics

---

## Relationship to BAZA WIEDZY

Historical context: User previously conceptualized similar system called "BAZA WIEDZY" involving:
- Gemini for mobile/voice capture
- Google Docs export
- Claude Code as "Konsolidator Wiedzy"
- GitHub for storage

**Status:** This implementation (FAZA 4.6) achieves the same goals but with better architecture:
- Multiple AI platforms (not just Gemini)
- Automated processing (not manual prompts)
- Notion database (not local files - better search, mobile access)
- Bidirectional integration (voice app can query)

**Key insights preserved:**
- "Konsolidator Wiedzy" pattern (merge fragmented notes) → ✅ Summarization
- Timeline generation → ✅ Date tracking
- TODO extraction → ✅ Implemented
- Weekly review → ✅ NotionDigest already includes these

---

## Cost Analysis

**Per conversation:**
- Summarization (if >1000 chars): ~$0.02 (DeepSeek)
- Classification: ~$0.03 (DeepSeek)
- **Total:** ~$0.05 per conversation

**Monthly estimate (assuming 10 conversations/month):**
- Processing: $0.50
- Storage: $0 (Notion free tier)
- **Total:** <$1/month

---

## Success Metrics

- ✅ Can export conversation from any platform (ChatGPT, Claude, Gemini, Perplexity)
- ✅ Summary generated automatically (not full 10k+ word transcript)
- ✅ Searchable via voice app (existing tools work)
- ✅ TODOs extracted and actionable
- ⚠️ <1 hour from export to searchable in Notion (depends on n8n poll frequency)

---

## Known Issues / Limitations

1. **n8n poll frequency:** Hourly by default - could be changed to faster polling
2. **Title extraction:** Best-effort heuristics - may miss some titles
3. **Platform detection:** Heuristic-based - might misidentify some platforms
4. **Summary quality:** DeepSeek good but not perfect - could upgrade to GPT-4 if needed
5. **No deduplication:** Same conversation exported twice will create 2 entries

---

## Files Reference

**Local:**
- BAZA WIEDZY concept: `/mnt/c/Users/Zalman S3/Downloads/BAZA WIEDZY.txt`
- Original n8n workflow: `/mnt/c/Users/Zalman S3/Downloads/Google Drive → GitHub Auto Upload.json`

**Server:**
- Handler: `/opt/inbox-webhook/conversation_handler.py`
- Main API: `/opt/inbox-webhook/main.py`
- Env vars: `/opt/inbox-webhook/.env`
  - DEEPSEEK_API_KEY
  - NOTION_API_TOKEN
  - WEBHOOK_SECRET=9P9gkqxaGCCJDNiEcCtj09sjB7nDVMLSt_QXPbF2GMg

**n8n:**
- Workflow: "Google Drive → PAI Conversation Archive"
- Endpoint: https://inbox.stankowski.io/webhook
- Auth: X-Webhook-Secret header

---

## Related Projects

- **Inbox System (FAZA 1-4.5):** Telegram voice/photo processing
- **NotionDigest (FAZA 2.6):** Weekly digest generator
- **NotionAutoType (FAZA 2.6):** Auto Type/Tags classification
- **Link Enricher (FAZA 3.5):** X/Reddit content fetching
- **Observatory (FAZA 4.3):** Real-time dashboard

**This completes the knowledge capture ecosystem:**
- Telegram → Instant thoughts/voice
- Chrome Extension → Deep AI conversations
- Voice App → Query both sources
- Notion → Single source of truth
