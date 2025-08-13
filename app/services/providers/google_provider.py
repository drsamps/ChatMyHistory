from __future__ import annotations
from typing import List, Dict
import os
import google.generativeai as genai
from flask import current_app


class GoogleProvider:
    def __init__(self):
        api_key = current_app.config.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def chat(self, messages: List[Dict[str, str]]) -> str:
        # Flatten messages into a conversation string
        convo = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        resp = self.model.generate_content(convo)
        return resp.text.strip()
