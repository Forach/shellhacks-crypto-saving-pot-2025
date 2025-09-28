from datetime import datetime

CURRENCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "CAD": "C$", "AUD": "A$", "JPY": "¥"
}

def pretty_time(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

def is_positive_number(s: str) -> bool:
    try:
        return float(s) > 0
    except:
        return False

def fmt_money(amount: float, code: str = "USD") -> str:
    sym = CURRENCY_SYMBOLS.get(code, "$")
    return f"{sym}{amount:,.2f}"

import unicodedata, re

def clean_ai_text(text: str) -> str:
    """Normalize, strip accidental markdown, collapse spaces."""
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text)
    # remove asterisks (both normal * and math ∗) that cause Markdown bolding
    t = t.replace("**", "").replace("∗∗", "")
    # collapse whitespace/newlines
    t = re.sub(r"\s+", " ", t).strip()
    return t
import os