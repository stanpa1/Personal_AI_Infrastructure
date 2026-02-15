# 📊 Weekly Digest - Szablon

## Jak używać tego narzędzia

### Krok 1: Pobierz dane z Notion
Każda niedziela wieczorem lub poniedziałek rano, uruchamiasz:
```
"Claude, wygeneruj weekly digest za ostatni tydzień"
```

### Krok 2: Claude automatycznie:
1. Pobiera wszystkie wpisy z ostatnich 7 dni z Note List
2. Grupuje je według typu (Article, Book, Action, Idea, etc.)
3. Wyciąga kluczowe tematy i wzorce
4. Tworzy podsumowanie w formacie poniżej

### Krok 3: Zapisz do Notion (opcjonalne)
Możesz zapisać wygenerowane podsumowanie jako nową notatkę w Note List:
- Name: "📊 Weekly Summary - [data]"
- Type: "Note"
- Area: ["Private"]

---

## 📋 Format Weekly Digest

### 📊 Statystyki
- **Okres:** [data początkowa] - [data końcowa]
- **Łącznie wpisów:** [liczba]
- **Breakdown po typach:**
  - Articles: [liczba]
  - Ideas: [liczba]
  - Actions: [liczba]
  - Books: [liczba]
  - Shopping: [liczba]
  - Other: [liczba]

### 🔥 Główne tematy
1. **[Temat 1]** - [krótki opis + liczba wpisów]
2. **[Temat 2]** - [krótki opis + liczba wpisów]
3. **[Temat 3]** - [krótki opis + liczba wpisów]

### 📚 Top Content (Score ≥ 4 lub warte uwagi)
1. **[Tytuł]** ([Type]) - [krótki opis]
   - Link: [jeśli dostępny]
   - Score: [jeśli >0]
2. **[Tytuł]** ([Type]) - [krótki opis]

### ✅ Completed Actions
- [x] [Action 1]
- [x] [Action 2]

### 📝 New Ideas to Review
- [ ] [Idea 1]
- [ ] [Idea 2]

### ⚠️ Pending Actions (Not Done)
- [ ] [Action 1] - [deadline jeśli jest]
- [ ] [Action 2]

### 🎯 Insights & Patterns
- [Obserwacja 1 o twoich zainteresowaniach/wzorcach]
- [Obserwacja 2]
- [Sugestia na przyszłość]

### 🔗 Quick Links
- [Link do wszystkich wpisów z tego tygodnia w Notion]

---

## 🛠️ Troubleshooting

### Jeśli brakuje wpisów:
- Upewnij się że wpisy mają ustawioną datę Created time
- Sprawdź czy są w data source: 9d5a78f7-c14e-44f8-b885-8cc5feaf99f8

### Jeśli chcesz zmienić zakres dat:
Powiedz Claude: "Wygeneruj digest za okres [data] - [data]"

### Jeśli chcesz więcej detali:
Powiedz Claude: "Pokaż pełne treści wpisów o [temat]"

---

## 📅 Rekomendowany ritual

**Niedziela 20:00 lub Poniedziałek 9:00:**
1. Powiedz: "Claude, weekly digest"
2. Przejrzyj podsumowanie (2-3 min)
3. Zanotuj główne wnioski
4. Zdecyduj co wymaga follow-up w nadchodzącym tygodniu
