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
        # Convert to single prompt
        system = "You are a kind, patient biographer interviewing an elderly person."
        convo = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=400,
            temperature=0.4,
            system=system,
            messages=[{"role": "user", "content": convo}],
        )
        return msg.content[0].text.strip()
