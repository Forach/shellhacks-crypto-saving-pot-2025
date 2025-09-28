# summarize.py
from typing import List, Dict, Any
from collections import defaultdict
import os

from dotenv import load_dotenv
load_dotenv()

# Env flags/keys
USE_AI_STUDIO = os.getenv("USE_AI_STUDIO", "0") == "1"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
ENV_MODEL = os.getenv("GEMINI_MODEL", "").strip()  # optional override, e.g. "gemini-2.5-flash"


# ---------- Local (fallback) summary ----------
def local_summary(rows: List[Dict[str, Any]], goal: float, currency_sym: str = "$") -> str:
    """Deterministic, no-network summary so your demo never breaks."""
    if not rows or len(rows) == 1:
        return "No activity yet. Invite friends and start saving!"

    txs = [r for r in rows if r.get("action") in ("DEPOSIT", "WITHDRAW")]
    total_in = sum(float(r.get("amount", 0.0)) for r in txs if r.get("action") == "DEPOSIT")
    total_out = sum(float(r.get("amount", 0.0)) for r in txs if r.get("action") == "WITHDRAW")
    net = round(total_in - total_out, 2)
    progress = 0.0 if goal <= 0 else min(100.0, round(100.0 * net / goal, 1))

    contrib = defaultdict(float)
    for r in txs:
        amt = float(r.get("amount", 0.0))
        if r.get("action") == "DEPOSIT":
            contrib[r.get("actor", "Unknown")] += amt
        elif r.get("action") == "WITHDRAW":
            contrib[r.get("actor", "Unknown")] -= amt

    top_str = "No contributors yet."
    if contrib:
        who, amt = max(contrib.items(), key=lambda kv: kv[1])
        top_str = f"Top contributor: {who} ({currency_sym}{amt:,.2f})."

    direction = "on track" if progress >= 66 else ("making progress" if progress >= 33 else "just getting started")
    return (
        f"Group saved {currency_sym}{net:,.2f}. "
        f"Goal: {currency_sym}{goal:,.2f} "
        f"({progress:.1f}% complete) — you're {direction}. {top_str}"
    )


# ---------- Optional Google AI Studio (Gemini) summary ----------
def _pick_model(genai) -> str:
    """Choose a working model id. Prefers env override; otherwise finds a supported one."""
    if ENV_MODEL:
        return ENV_MODEL  # e.g., "gemini-2.5-flash"
    try:
        models = genai.list_models()
        # Keep short names if either "models/<id>" or "<id>" appears
        names = {m.name for m in models if "generateContent" in getattr(m, "supported_generation_methods", [])}
        candidates = [
            "models/gemini-2.5-flash",
            "models/gemini-2.5-pro",
            "models/gemini-2.0-flash-exp",
        ]
        for c in candidates:
            short = c.split("/", 1)[-1]
            if c in names or short in names:
                return short
    except Exception:
        pass
    return "gemini-2.5-flash"


def ai_studio_summary(rows: List[Dict[str, Any]], goal: float, currency_sym: str = "$") -> str:
    """Summarize using Google AI Studio (Gemini). Falls back to local_summary on any error."""
    if not USE_AI_STUDIO or not GOOGLE_API_KEY:
        return local_summary(rows, goal, currency_sym)
    try:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)

        model_id = _pick_model(genai)
        txs = [r for r in rows if r.get("action") in ("DEPOSIT", "WITHDRAW")]
        text_rows = "\n".join(
            f"{r.get('actor','?')} | {r.get('action','?')} | {r.get('amount',0)} | {r.get('note','')}"
            for r in txs[-80:]  # last 80 entries is plenty
        )
        prompt = f"""You are a friendly finance coach
Summarize this shared savings pot in ONE short paragraph.
Be fun and make it engaging!
Include: net saved, progress vs goal, top contributor, and ONE actionable next step.
Use the currency symbol {currency_sym}. Keep it under 90 words.

Goal: {goal}
Rows: actor | action | amount | note
{text_rows}
"""
        model = genai.GenerativeModel(model_id)
        resp = model.generate_content(prompt)
        out = (getattr(resp, "text", "") or "").strip()
        return out[:600] if out else local_summary(rows, goal, currency_sym)
    except Exception:
        return local_summary(rows, goal, currency_sym)
