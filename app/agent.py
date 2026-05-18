"""
SHLAgent — the brain of the recommender.

Flow per turn
─────────────
1. Build search query from recent conversation
2. Detect explicit comparison request (extract named assessments)
3. Retrieve top-K catalog entries via FAISS
4. Build system prompt with catalog context + turn metadata
5. Call LLM (Groq primary, Gemini fallback) for structured JSON output
6. Parse & sanitise the JSON — verify every recommendation exists in catalog
7. Return ChatResponse-compatible dict
"""

import asyncio
import json
import logging
import os
import re
from typing import Optional

from app.retriever import CatalogRetriever
from app.prompts import build_system_prompt, format_catalog_context

logger = logging.getLogger(__name__)

# ── LLM backend selection ────────────────────────────────────────────────────
# Priority: GROQ_API_KEY → GEMINI_API_KEY
# Groq: 30 RPM, 14400 RPD free tier (very generous)
# Gemini: 1500 RPD free tier but stricter RPM
LLM_BACKEND = None  # set during init

MAX_TOKENS     = 1024
RETRIEVE_K     = 15
MAX_USER_TURNS = 8
COMMIT_AT_TURN = 7
MAX_RETRIES    = 3


def _init_groq():
    """Initialise Groq client."""
    from groq import Groq
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return None
    return Groq(api_key=key)


def _init_gemini():
    """Initialise Gemini client."""
    from google import genai
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        return None
    return genai.Client(api_key=key)


def _call_groq(client, system: str, messages: list[dict]) -> str:
    """Call Groq API and return the raw text response."""
    groq_messages = [{"role": "system", "content": system}]
    for m in messages:
        groq_messages.append({
            "role": m["role"] if m["role"] in ("user", "assistant") else "user",
            "content": m["content"],
        })
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=groq_messages,
        max_tokens=MAX_TOKENS,
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()


def _call_gemini(client, system: str, messages: list[dict]) -> str:
    """Call Gemini API and return the raw text response."""
    from google.genai import types
    gemini_contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        gemini_contents.append(
            types.Content(role=role, parts=[types.Part(text=m["content"])])
        )
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=gemini_contents,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=MAX_TOKENS,
            temperature=0.3,
        ),
    )
    return response.text.strip()


class SHLAgent:
    def __init__(self, retriever: CatalogRetriever):
        self.retriever = retriever
        # Try Groq first (most reliable free tier), then Gemini
        self._groq_client = _init_groq()
        self._gemini_client = _init_gemini()
        if self._groq_client:
            logger.info("LLM backend: Groq (llama-3.3-70b-versatile)")
        elif self._gemini_client:
            logger.info("LLM backend: Gemini (gemini-2.0-flash)")
        else:
            logger.error("No LLM API key found! Set GROQ_API_KEY or GEMINI_API_KEY.")

    # ── Public ───────────────────────────────────────────────────────────────

    async def respond(self, messages: list) -> dict:
        """
        Accept the full conversation history (list of Message objects or dicts)
        and return a dict matching ChatResponse schema.
        """
        msg_dicts = [
            {"role": m.role, "content": m.content}
            if hasattr(m, "role")
            else {"role": m["role"], "content": m["content"]}
            for m in messages
        ]

        turn_count = sum(1 for m in msg_dicts if m["role"] == "user")

        # ── Retrieve ──────────────────────────────────────────────────────
        search_query = self._build_query(msg_dicts)
        retrieved    = self.retriever.search(search_query, k=RETRIEVE_K)

        comparison_names = self._detect_comparison(msg_dicts[-1]["content"])
        if comparison_names:
            pinned = self.retriever.get_by_names(comparison_names)
            pinned_names = {a["name"] for a in pinned}
            retrieved = pinned + [a for a in retrieved if a["name"] not in pinned_names]

        context = format_catalog_context(retrieved[:RETRIEVE_K])
        system  = build_system_prompt(
            context,
            turn_count=turn_count,
            max_user_turns=MAX_USER_TURNS,
            commit_at_turn=COMMIT_AT_TURN,
        )

        # ── Generate with retry ──────────────────────────────────────────
        text = None
        for attempt in range(MAX_RETRIES):
            try:
                if self._groq_client:
                    text = _call_groq(self._groq_client, system, msg_dicts)
                elif self._gemini_client:
                    text = _call_gemini(self._gemini_client, system, msg_dicts)
                else:
                    raise RuntimeError("No LLM backend configured")
                break
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "rate" in err_str.lower():
                    wait = (attempt + 1) * 10
                    logger.warning("Rate limited, retrying in %ds (attempt %d/%d): %s",
                                   wait, attempt + 1, MAX_RETRIES, err_str[:100])
                    await asyncio.sleep(wait)
                else:
                    raise

        if text is None:
            raise RuntimeError("LLM API rate limit exceeded after retries")

        logger.debug("LLM raw output: %s", text[:400])

        # ── Parse & sanitise ──────────────────────────────────────────────
        return self._parse_and_sanitise(text)

    # ── Private ──────────────────────────────────────────────────────────────

    def _build_query(self, messages: list[dict]) -> str:
        user_msgs = [m["content"] for m in messages if m["role"] == "user"]
        recent = user_msgs[-3:] if len(user_msgs) >= 3 else user_msgs
        return " ".join(recent + [recent[-1]])

    def _detect_comparison(self, text: str) -> list[str]:
        patterns = [
            r"(?:compare|comparing)\s+(.+?)\s+(?:and|with|to|vs\.?)\s+(.+?)(?:\?|$|\.|,)",
            r"difference\s+between\s+(.+?)\s+and\s+(.+?)(?:\?|$|\.|,)",
            r"(.+?)\s+vs\.?\s+(.+?)(?:\?|$|\.|,)",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return [m.group(1).strip(), m.group(2).strip()]
        return []

    def _parse_and_sanitise(self, text: str) -> dict:
        data = self._extract_json(text)
        if data is None:
            logger.error("Could not parse JSON from model output.")
            return self._fallback()

        raw_recs: list[dict] = data.get("recommendations") or []
        clean_recs: list[dict] = []

        for rec in raw_recs[:10]:
            name = str(rec.get("name", "")).strip()
            catalog_entry = self.retriever.get_by_name(name)
            if catalog_entry is None:
                matches = [
                    a for a in self.retriever.catalog
                    if name.lower() in a["name"].lower() or a["name"].lower() in name.lower()
                ]
                catalog_entry = matches[0] if matches else None

            if catalog_entry is None:
                logger.warning("Dropping hallucinated assessment: %r", name)
                continue

            clean_recs.append({
                "name":      catalog_entry["name"],
                "url":       catalog_entry["url"],
                "test_type": rec.get("test_type") or catalog_entry.get("test_type", ""),
            })

        intent = data.get("intent", "")
        reply  = str(data.get("reply") or "").strip()

        if intent in ("CLARIFY", "REFUSE"):
            clean_recs = []

        if intent in ("RECOMMEND", "REFINE") and not clean_recs:
            logger.warning("RECOMMEND intent but 0 valid recs after sanitisation.")

        return {
            "reply":               reply or "Could you tell me more about the role?",
            "recommendations":     clean_recs,
            "end_of_conversation": bool(data.get("end_of_conversation", False)),
        }

    @staticmethod
    def _extract_json(text: str) -> Optional[dict]:
        text = re.sub(r"```(?:json)?", "", text).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None

    @staticmethod
    def _fallback() -> dict:
        return {
            "reply": (
                "I'm not able to process that request. I can only help with "
                "SHL assessment recommendations. Could you describe the role "
                "you're hiring for?"
            ),
            "recommendations":     [],
            "end_of_conversation": False,
        }
