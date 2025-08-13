from flask import Blueprint, jsonify, redirect, url_for

api_bp = Blueprint("api", __name__)


@api_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@api_bp.get("/styles")
def styles_redirect():
    return redirect(url_for("admin.dashboard"))
