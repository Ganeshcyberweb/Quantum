"""Aspect-based sentiment: detect what reviews talk about and how they feel.

Keyword-driven topic detection over hotel reviews. For each theme we collect
the polarity of every review mentioning it and summarize the sentiment.
"""

import re

# Theme -> keywords. Matching is whole-word (case-insensitive) to avoid false
# hits like "ac" inside "place".
THEMES = {
    "Cleanliness": [
        "clean", "dirty", "spotless", "filthy", "hygiene", "hygienic",
        "tidy", "stain", "stained", "dust", "dusty",
    ],
    "Staff & Service": [
        "staff", "service", "reception", "receptionist", "friendly", "rude",
        "helpful", "manager", "host", "courteous", "polite", "attentive",
    ],
    "Location": [
        "location", "located", "central", "centrally", "nearby", "view",
        "beach", "downtown", "convenient", "walk", "walking", "distance",
    ],
    "Food & Dining": [
        "food", "breakfast", "restaurant", "meal", "meals", "dinner", "lunch",
        "buffet", "coffee", "delicious", "tasty", "menu",
    ],
    "Value for Money": [
        "price", "priced", "value", "expensive", "cheap", "worth",
        "overpriced", "affordable", "cost", "money",
    ],
    "Room & Comfort": [
        "room", "rooms", "bed", "beds", "bathroom", "comfortable", "comfy",
        "spacious", "small", "cramped", "noise", "noisy", "quiet", "shower",
    ],
    "Amenities": [
        "pool", "wifi", "wi-fi", "gym", "parking", "spa", "amenities",
        "elevator", "lift", "facilities",
    ],
}

# Pre-compile one regex per theme: \b(kw1|kw2|...)\b
_THEME_PATTERNS = {
    theme: re.compile(r"\b(" + "|".join(re.escape(k) for k in kws) + r")\b", re.IGNORECASE)
    for theme, kws in THEMES.items()
}


def _label(avg_polarity):
    if avg_polarity > 0.1:
        return "Positive"
    if avg_polarity < -0.1:
        return "Negative"
    return "Neutral"


def analyze_aspects(analyzed_reviews):
    """Summarize sentiment per theme.

    `analyzed_reviews` is a list of dicts with at least "text" and "polarity".
    Returns a list of {theme, mentions, label, pct_positive, avg} sorted by
    how often each theme is mentioned (most-discussed first).
    """
    results = []
    for theme, pattern in _THEME_PATTERNS.items():
        polarities = [
            r["polarity"] for r in analyzed_reviews if pattern.search(r["text"] or "")
        ]
        if not polarities:
            continue
        avg = sum(polarities) / len(polarities)
        pct_positive = round(sum(1 for p in polarities if p > 0) / len(polarities) * 100)
        results.append({
            "theme": theme,
            "mentions": len(polarities),
            "label": _label(avg),
            "pct_positive": pct_positive,
            "avg": round(avg, 2),
        })

    results.sort(key=lambda x: x["mentions"], reverse=True)
    return results
