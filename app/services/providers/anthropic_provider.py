from __future__ import annotations
from typing import List, Dict
import os
import anthropic
from flask import current_app


class AnthropicProvider:
    def __init__(self):
        api_key = current_app.config.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Client(api_key=api_key)
        self.model = "claude-3-haiku-20240307"

    def chat(self, messages: List[Dict[str, str]]) -> str:
        # Anthropic supports a "system" field and chat-style list
        system = None
        content_messages: List[Dict[str, str]] = []
        for m in messages:
            if m.get("role") == "system" and system is None:
                system = m.get("content", "").strip()
                continue
            content_messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})

        msg = self.client.messages.create(
            model=self.model,
            max_tokens=400,
            temperature=0.4,
            system=system or "You are a kind, patient biographer interviewing an elderly person.",
            messages=content_messages or [{"role": "user", "content": "Hello"}],
        )
        return msg.content[0].text.strip()
