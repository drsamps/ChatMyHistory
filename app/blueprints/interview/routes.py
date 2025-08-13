from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_file, make_response
from flask_login import login_required, current_user
from ...extensions import db
from ...models.interview import Interview, Message
from ...models.summary import Summary
from ...services.llm import get_chat_response, summarize_transcript
import io


interview_bp = Blueprint("interview", __name__)


@interview_bp.get("/")
@login_required
def list_interviews():
    interviews = (
        Interview.query.filter_by(user_id=current_user.id)
        .order_by(Interview.created_at.desc())
        .all()
    )

    # Suggested topics – complementary areas commonly included in a life history
    recommended_topics = [
        "Childhood",
        "Family",
        "School",
        "Work and Career",
        "Relationships",
        "Marriage",
        "Children",
        "Hobbies",
        "Travel",
        "Traditions",
        "Turning Points",
        "Faith and Beliefs",
        "Homes and Places Lived",
        "Military Service",
        "Community Service",
        "Health and Challenges",
        "Technology in Your Life",
        "Daily Life and Routines",
        "Holidays and Celebrations",
        "Favorite Books and Movies",
        "Lessons Learned",
        "Advice to Descendants",
    ]

    existing_titles_lower = {i.title.strip().lower() for i in interviews if i.title}
    suggestions = [
        t for t in recommended_topics if t.strip().lower() not in existing_titles_lower
    ][:10]

    return render_template(
        "interview/list.html", interviews=interviews, suggestions=suggestions
    )


@interview_bp.post("/")
@login_required
def create_interview():
    title = request.form.get("title", "").strip() or "Untitled Topic"
    interview = Interview(user_id=current_user.id, title=title)
    db.session.add(interview)
    db.session.commit()
    return redirect(url_for("interview.view_interview", interview_id=interview.id))


@interview_bp.get("/<int:interview_id>")
@login_required
def view_interview(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    if interview.user_id != current_user.id and not current_user.is_admin:
        flash("Not authorized", "danger")
        return redirect(url_for("interview.list_interviews"))
    messages = Message.query.filter_by(interview_id=interview.id).order_by(Message.created_at.asc()).all()
    # Try to load existing session summary (if any) for quick link/UI cue
    summary = Summary.query.filter_by(interview_id=interview.id, kind="session").first()
    return render_template("interview/detail.html", interview=interview, messages=messages, summary=summary)


@interview_bp.post("/<int:interview_id>/send")
@login_required
def send_message(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    if interview.user_id != current_user.id and not current_user.is_admin:
        flash("Not authorized", "danger")
        return redirect(url_for("interview.list_interviews"))

    content = request.form.get("content", "").strip()
    if not content:
        return redirect(url_for("interview.view_interview", interview_id=interview.id))

    user_msg = Message(interview_id=interview.id, role="user", content=content)
    db.session.add(user_msg)
    db.session.commit()

    assistant_content = get_chat_response(interview_id=interview.id)
    assistant_msg = Message(interview_id=interview.id, role="assistant", content=assistant_content)
    db.session.add(assistant_msg)
    db.session.commit()

    return redirect(url_for("interview.view_interview", interview_id=interview.id))


@interview_bp.post("/<int:interview_id>/rename")
@login_required
def rename_interview(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    if interview.user_id != current_user.id and not current_user.is_admin:
        flash("Not authorized", "danger")
        return redirect(url_for("interview.list_interviews"))

    new_title = request.form.get("title", "").strip() or "Untitled Topic"
    interview.title = new_title
    db.session.commit()
    flash("Topic title updated.", "success")
    return redirect(url_for("interview.view_interview", interview_id=interview.id))


@interview_bp.post("/<int:interview_id>/change-topic")
@login_required
def change_topic(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    if interview.user_id != current_user.id and not current_user.is_admin:
        flash("Not authorized", "danger")
        return redirect(url_for("interview.list_interviews"))

    # Nudge the assistant to gracefully switch to a fresh topic
    system_instruction = (
        "The conversation appears to be staying on the same topic. "
        "Please gracefully pivot to a different aspect of the person's life that has not been covered yet. "
        "Avoid repeating prior questions. Offer a fresh angle (e.g., childhood, school, work, relationships, hobbies, travels, traditions, or turning points). "
        "Ask exactly one concise, warm question to begin the new topic."
    )

    sys_msg = Message(interview_id=interview.id, role="system", content=system_instruction)
    db.session.add(sys_msg)
    db.session.commit()

    assistant_content = get_chat_response(interview_id=interview.id)
    assistant_msg = Message(interview_id=interview.id, role="assistant", content=assistant_content)
    db.session.add(assistant_msg)
    db.session.commit()

    return redirect(url_for("interview.view_interview", interview_id=interview.id))


@interview_bp.post("/<int:interview_id>/summarize")
@login_required
def summarize_interview(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    if interview.user_id != current_user.id and not current_user.is_admin:
        flash("Not authorized", "danger")
        return redirect(url_for("interview.list_interviews"))

    # Fetch transcript
    history = (
        Message.query.filter_by(interview_id=interview.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    if not history:
        flash("No messages to summarize yet.", "warning")
        return redirect(url_for("interview.view_interview", interview_id=interview.id))

    convo = [{"role": m.role, "content": m.content} for m in history]

    # Generate structured HTML summary via LLM
    def _strip_code_fences(text: str) -> str:
        t = text.strip()
        if t.startswith("```"):
            # Remove leading ```lang and trailing ```
            first_newline = t.find("\n")
            if first_newline != -1:
                t = t[first_newline + 1 :]
            if t.endswith("```"):
                t = t[:-3]
            return t.strip()
        return t

    try:
        person_name = current_user.name if current_user.is_authenticated else None
        html = summarize_transcript(convo, output_format="html", person_name=person_name)
        html = _strip_code_fences(html)
    except Exception as e:
        flash(f"Summarization failed: {e}", "danger")
        return redirect(url_for("interview.view_interview", interview_id=interview.id))

    # Upsert summary record
    summary = Summary.query.filter_by(interview_id=interview.id, kind="session").first()
    if summary:
        summary.content = html
    else:
        summary = Summary(user_id=interview.user_id, interview_id=interview.id, kind="session", format="html", content=html)
        db.session.add(summary)
    db.session.commit()

    return redirect(url_for("interview.view_summary", interview_id=interview.id))


@interview_bp.get("/<int:interview_id>/summary")
@login_required
def view_summary(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    if interview.user_id != current_user.id and not current_user.is_admin:
        flash("Not authorized", "danger")
        return redirect(url_for("interview.list_interviews"))

    summary = Summary.query.filter_by(interview_id=interview.id, kind="session").first()
    if not summary:
        # Offer to create one if missing
        flash("No summary yet. Generate one from the interview page.", "info")
        return redirect(url_for("interview.view_interview", interview_id=interview.id))

    return render_template("interview/summary.html", interview=interview, summary=summary)


@interview_bp.get("/<int:interview_id>/export/markdown")
@login_required
def export_summary_markdown(interview_id: int):
    interview = Interview.query.get_or_404(interview_id)
    if interview.user_id != current_user.id and not current_user.is_admin:
        flash("Not authorized", "danger")
        return redirect(url_for("interview.list_interviews"))

    history = (
        Message.query.filter_by(interview_id=interview.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    if not history:
        flash("No messages to summarize yet.", "warning")
        return redirect(url_for("interview.view_interview", interview_id=interview.id))

    convo = [{"role": m.role, "content": m.content} for m in history]

    def _strip_code_fences(text: str) -> str:
        t = text.strip()
        if t.startswith("```"):
            first_newline = t.find("\n")
            if first_newline != -1:
                t = t[first_newline + 1 :]
            if t.endswith("```"):
                t = t[:-3]
            return t.strip()
        return t

    person_name = current_user.name if current_user.is_authenticated else None
    md = summarize_transcript(convo, output_format="markdown", person_name=person_name)
    md = _strip_code_fences(md)

    response = make_response(md)
    response.headers["Content-Type"] = "text/markdown; charset=utf-8"
    response.headers["Content-Disposition"] = (
        f"attachment; filename=interview_{interview.id}_summary.md"
    )
    return response


@interview_bp.get("/<int:interview_id>/export/pdf")
@login_required
def export_summary_pdf(interview_id: int):
    try:
        from xhtml2pdf import pisa  # type: ignore
    except Exception:
        flash("PDF export requires xhtml2pdf. Please install dependencies and retry.", "danger")
        return redirect(url_for("interview.view_summary", interview_id=interview_id))

    interview = Interview.query.get_or_404(interview_id)
    if interview.user_id != current_user.id and not current_user.is_admin:
        flash("Not authorized", "danger")
        return redirect(url_for("interview.list_interviews"))

    summary = Summary.query.filter_by(interview_id=interview.id, kind="session").first()
    if not summary:
        flash("No summary available to export. Generate one first.", "warning")
        return redirect(url_for("interview.view_interview", interview_id=interview.id))

    html_doc = f"""
    <html><head>
    <meta charset='utf-8'>
    <style>
      body {{ font-family: DejaVu Sans, Arial, sans-serif; }}
      h1, h2, h3 {{ color: #111; }}
      .standout {{ font-style: italic; }}
    </style>
    </head><body>
    {summary.content}
    </body></html>
    """

    buffer = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html_doc), dest=buffer)  # type: ignore
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"interview_{interview.id}_summary.pdf",
    )