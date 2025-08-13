from __future__ import annotations
from typing import List, Dict, Optional
import os
from datetime import datetime
from flask import current_app, session
from flask_login import current_user
from ..models.interview import Message
from ..models.persona import Persona, PersonaStyle, CommStyle
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


def _default_system_prompt(*, interview_id: Optional[int] = None) -> Dict[str, str]:
    # If a persona is selected for this interview, use a neutral base instruction
    # so the persona styles fully shape tone and language.
    has_selected_persona = False
    if interview_id is not None:
        try:
            sel = session.get(f"sel_persona_{interview_id}")
            has_selected_persona = bool(sel)
        except Exception:
            has_selected_persona = False
    content = (
        "You are a biographer interviewing someone to write their personal history. "
        "Ask one question at a time. Keep questions specific and related to the topic of discussion, "
        "unless the user chooses to pivot the topic of discussion."
    ) if has_selected_persona else (
        "You are a kind, patient biographer interviewing an elderly person. "
        "Ask one question at a time. Keep questions short, warm, and specific."
    )
    return {"role": "system", "content": content}


def _active_persona_system_suffix(*, interview_id: Optional[int] = None) -> Optional[str]:
	try:
		if not current_user.is_authenticated:
			return None
		# Determine persona precedence: per-interview selection, then user default, then system default
		persona: Optional[Persona] = None
		if interview_id is not None:
			try:
				pid_raw = session.get(f"sel_persona_{interview_id}")
				if pid_raw:
					p_tmp = Persona.query.get(int(pid_raw))
					if p_tmp and (p_tmp.is_system or p_tmp.user_id == current_user.id):
						persona = p_tmp
			except Exception:
				persona = None
		if not persona:
			persona = (
				Persona.query.filter_by(user_id=current_user.id, is_default=True).first()
				or Persona.query.filter_by(is_system=True, is_default=True).first()
			)
		if not persona:
			return None
		# Load styles in sort order
		style_ids = [ps.comm_style_id for ps in persona.styles]
		if not style_ids:
			return None
		styles = (
			CommStyle.query.filter(CommStyle.id.in_(style_ids))
			.order_by(CommStyle.sort.asc(), CommStyle.style_name.asc())
			.all()
		)
		prompts = [s.prompt.strip() for s in styles if s.prompt and s.visible]
		return "\n\n".join(prompts) if prompts else None
	except Exception:
		return None


def _selected_persona_and_styles(interview_id: Optional[int]) -> Optional[Dict[str, object]]:
	"""Return selected Persona and its styles (sorted), if any."""
	try:
		if not current_user.is_authenticated:
			return None
		persona: Optional[Persona] = None
		if interview_id is not None:
			pid_raw = session.get(f"sel_persona_{interview_id}")
			if pid_raw:
				try:
					p_tmp = Persona.query.get(int(pid_raw))
					if p_tmp and (p_tmp.is_system or p_tmp.user_id == current_user.id):
						persona = p_tmp
				except Exception:
					persona = None
		if not persona:
			persona = (
				Persona.query.filter_by(user_id=current_user.id, is_default=True).first()
				or Persona.query.filter_by(is_system=True, is_default=True).first()
			)
		if not persona:
			return None
		styles = (
			CommStyle.query.join(PersonaStyle, PersonaStyle.comm_style_id == CommStyle.id)
			.filter(PersonaStyle.persona_id == persona.id, CommStyle.visible == True)  # noqa: E712
			.order_by(CommStyle.sort.asc(), CommStyle.style_name.asc())
			.all()
		)
		return {"persona": persona, "styles": styles}
	except Exception:
		return None


def _style_constraints_block(interview_id: Optional[int]) -> Optional[str]:
	meta = _selected_persona_and_styles(interview_id)
	if not meta:
		return None
	styles: List[CommStyle] = meta["styles"]  # type: ignore[assignment]
	if not styles:
		return None
	lines = [
		"BEGIN COMMUNICATION STYLE CONSTRAINTS",
		"Apply ALL of the following constraints simultaneously. Do not ignore any.",
		"These constraints OVERRIDE any prior instructions in this conversation.",
	]
	for s in styles:
		lines.append(f"- Style '{s.style_name}': {s.prompt.strip()}")
	lines += [
		"END COMMUNICATION STYLE CONSTRAINTS",
		"You must follow every constraint above in all replies. If constraints conflict, prioritize: language and output format > safety > persona tone > brevity.",
	]
	return "\n".join(lines)


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

    # Ensure a system message exists and is augmented with persona styles
    suffix = _active_persona_system_suffix(interview_id=interview_id)
    style_block = _style_constraints_block(interview_id)
    # Prefer the structured style constraints block; fall back to raw suffix if needed
    composed_suffix = style_block if style_block else suffix

    if messages and messages[0]["role"] == "system":
        if composed_suffix:
            messages[0]["content"] = f"{messages[0]['content'].rstrip()}\n\n{composed_suffix}"
    else:
        base = _default_system_prompt(interview_id=interview_id)
        if composed_suffix:
            base["content"] = f"{base['content']}\n\n{composed_suffix}"
        messages = [base] + messages

    # Call provider
    response_text = _provider().chat(messages)

    # Optional debug dump for admins
    try:
        dbg_key = f"debug_chat_{interview_id}"
        if session.get(dbg_key) == "1" and current_user.is_authenticated and current_user.is_admin:
            try:
                os.makedirs("debugs", exist_ok=True)
            except Exception:
                pass
            ts = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
            fname = os.path.join("debugs", f"debug-chat-{ts}.txt")
            # Build dump: provider, system prompt (first message), assistant+user messages, response
            sys_msg = next((m for m in messages if m["role"] == "system"), None)
            user_msgs = [m for m in messages if m["role"] == "user"]
            assistant_msgs = [m for m in messages if m["role"] == "assistant"]
            try:
                prov = _provider()
                provider_name = prov.__class__.__name__
                provider_model = getattr(prov, "model", "<unknown>")
            except Exception:
                provider_name = "<unknown>"
                provider_model = "<unknown>"
            meta = _selected_persona_and_styles(interview_id)
            with open(fname, "a", encoding="utf-8") as f:
                f.write(f"=== PROVIDER ===\n{name:=<{1}}".replace("name", ""))
                f.write(f"provider={provider_name} model={provider_model}\n\n")
                if meta:
                    p = meta["persona"]
                    styles = meta["styles"]
                    f.write(f"=== SELECTED PERSONA ===\n")
                    f.write(f"id={p.id} name={p.name} system={p.is_system} default={p.is_default}\n")
                    f.write("Styles (sorted):\n")
                    for s in styles:
                        f.write(f"- {s.style_name} (key={s.key})\n")
                    f.write("\n")
                f.write("=== SYSTEM PROMPT ===\n")
                if sys_msg:
                    f.write(sys_msg.get("content", "") + "\n\n")
                else:
                    f.write("<none>\n\n")
                f.write("=== ASSISTANT MESSAGES (HISTORY) ===\n")
                for i, m in enumerate(assistant_msgs, 1):
                    f.write(f"[{i}] {m.get('content','')}\n")
                f.write("\n")
                f.write("=== USER MESSAGES ===\n")
                for i, m in enumerate(user_msgs, 1):
                    f.write(f"[{i}] {m.get('content','')}\n")
                f.write("\n=== LLM RESPONSE ===\n")
                f.write(response_text + "\n")
    except Exception:
        pass

    return response_text


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
