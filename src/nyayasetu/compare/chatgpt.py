import os
import re
from typing import Any, Dict, List, Tuple

import httpx


class ChatGPTBaseline:
    """Ungrounded OpenAI call used only to contrast NyayaSetu's verified answers."""

    LOOSE_CITATION = re.compile(
        r"\b(BNS|BNSS|BSA|IPC|CrPC|CRPC|IEA)\s*(?:section|sec\.?)?\s*(\d+[A-Z]?(?:\([a-z0-9]+\))?)",
        re.IGNORECASE,
    )
    SECTION_OF = re.compile(
        r"\b(?:section|sec\.?)\s*(\d+[A-Z]?(?:\([a-z0-9]+\))?)\s*(?:of\s+(?:the\s+)?)?(BNS|BNSS|BSA|IPC|CrPC|CRPC|IEA)\b",
        re.IGNORECASE,
    )

    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    def available(self) -> bool:
        return bool(self.api_key)

    def extract_loose_citations(self, text: str) -> List[Tuple[str, str]]:
        found: List[Tuple[str, str]] = []
        for m in self.SECTION_OF.finditer(text or ""):
            found.append((m.group(2).upper().replace("CRPC", "CRPC"), m.group(1)))
        for m in self.LOOSE_CITATION.finditer(text or ""):
            pair = (m.group(1).upper().replace("CRPC", "CRPC"), m.group(2))
            if pair not in found:
                found.append(pair)
        return found

    def ask(self, query: str, timeout: float = 45.0) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "available": False,
                "model": self.model,
                "answer": None,
                "error": "OPENAI_API_KEY is not set. Add it to .env to run the live ChatGPT comparison.",
                "tokens_used": 0,
            }

        system = (
            "You are ChatGPT, a general assistant. Answer the user's legal question "
            "from general knowledge. Do not claim access to a private statute database."
        )
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "temperature": 0.2,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": query},
                        ],
                    },
                )
            if resp.status_code >= 400:
                return {
                    "available": True,
                    "model": self.model,
                    "answer": None,
                    "error": f"OpenAI HTTP {resp.status_code}: {resp.text[:400]}",
                    "tokens_used": 0,
                }
            payload = resp.json()
            answer = payload["choices"][0]["message"]["content"]
            usage = payload.get("usage") or {}
            return {
                "available": True,
                "model": self.model,
                "answer": answer,
                "error": None,
                "tokens_used": usage.get("total_tokens", 0),
            }
        except Exception as exc:
            return {
                "available": True,
                "model": self.model,
                "answer": None,
                "error": str(exc),
                "tokens_used": 0,
            }
