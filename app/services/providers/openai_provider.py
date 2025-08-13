from __future__ import annotations
from typing import List, Dict
import os
from openai import OpenAI
from flask import current_app


class OpenAIProvider:
    def __init__(self):
        api_key = current_app.config.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"

    def chat(self, messages: List[Dict[str, str]]) -> str:
        # Map to OpenAI format
        response = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.4)
        return response.choices[0].message.content.strip()
