from __future__ import annotations
from typing import List, Dict, Optional
from flask import current_app
from ..models.interview import Message
from .providers.openai_provider import OpenAIProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.google_provider import GoogleProvider


def _provider():
    provider = current_app.config.get("LLM_PROVIDER", "openai")
    if provider == "anthropic":
        return AnthropicProvider()
    if provider == "google":
        return GoogleProvider()
    return OpenAIProvider()


def _default_system_prompt() -> Dict[str, str]:
    return {
        "role": "system",
        "content": (
            "You are a kind, patient biographer interviewing an elderly person. "
            "Ask one question at a time. Keep questions short, warm, and specific."
        ),
    }


def get_chat_response(interview_id: int) -> str:
    history: List[Message] = (
        Message.query.filter_by(interview_id=interview_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    messages: List[Dict[str, str]] = [
        {"role": m.role, "content": m.content}
        for m in history
    ]

    if not messages:
        messages = [_default_system_prompt()]

    return _provider().chat(messages)


def summarize_transcript(
    messages: List[Dict[str, str]], *, output_format: str = "html", person_name: Optional[str] = None
) -> str:
    """Generate a structured summary of an interview transcript.

    messages: list of {role, content} across the interview.
    output_format: 'html' | 'markdown' | 'text'
    """
    system = (
        "You are an expert biographer and editor. Given an interview transcript, "
        "produce an engaging, well-organized, and visually engaging personal history. "
        "Write warmly, faithful to the speaker's voice. Avoid inventing facts."
    )

    # Personalization for heading
    heading_name = person_name or "the speaker"

    if output_format == "html":
        instructions = (
            "Return RAW HTML (no Markdown fences) with these sections in order: "
            f"<h1>From the personal history of {heading_name} ❤️</h1> (emoji at the end), a short <p> intro, "
            "<h2>Chapters 📖</h2> with multiple <section> elements each containing <h3>Chapter title 🔸</h3> and <p> blocks, "
            "a <h2>Themes 🎯</h2> list (<ul><li>), and <h2>Timeline 🗓️</h2> of dated events if present. "
            "Wrap 3–7 standout phrases in <em class='standout'>…</em> to subtly highlight them. "
            "Use only simple tags: h1,h2,h3,p,section,ul,ol,li,blockquote,em,strong. "
            "DO NOT include any backticks or code fences."
        )
    elif output_format == "markdown":
        instructions = (
            f"Return Markdown beginning with: # From the personal history of {heading_name} ❤️ (emoji at the end). "
            "Then an introductory paragraph, ## Chapters (### per chapter), ## Themes as a bullet list, and ## Timeline if applicable. "
            "Emphasize 3–7 standout phrases with *italics*. Do not include code fences."
        )
    else:
        instructions = (
            "Return a plain text narrative summary, followed by sections for THEMES and TIMELINE if applicable."
        )

    prompt_messages: List[Dict[str, str]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": instructions},
        {"role": "user", "content": "Here is the interview transcript:"},
    ]

    transcript_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
    prompt_messages.append({"role": "user", "content": transcript_text})

    return _provider().chat(prompt_messages)
