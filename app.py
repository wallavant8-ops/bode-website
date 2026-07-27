"""Bode Hardware - Flask Website with Admin Panel"""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).parent
CONTENT_FILE = BASE_DIR / "content.json"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = "bode-hardware-secret-2024"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}


def load_content():
    with open(CONTENT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_content(data):
    with open(CONTENT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def t(content, lang="en"):
    """Helper: get translated text from content dict or string"""
    if isinstance(content, dict):
        key = f"text_{lang}" if f"text_{lang}" in content else f"title_{lang}" if f"title_{lang}" in content else f"label_{lang}"
        for k in content:
            if k.endswith(f"_{lang}"):
                return content[k]
        return content.get("text_en", str(content))
    return str(content)


# ========== FRONTEND ROUTES ==========

@app.route("/")
def home():
    data = load_content()
    lang = request.args.get("lang", request.cookies.get("lang", "en"))
    return render_template("index.html", data=data, lang=lang)


@app.route("/about")
def about():
    data = load_content()
    lang = request.args.get("lang", request.cookies.get("lang", "en"))
    return render_template("about.html", data=data, lang=lang)


@app.route("/contact")
def contact():
    data = load_content()
    lang = request.args.get("lang", request.cookies.get("lang", "en"))
    return render_template("contact.html", data=data, lang=lang)


# ========== ADMIN PANEL ==========

@app.route("/admin")
def admin():
    data = load_content()
    images = sorted(UPLOAD_DIR.glob("*"), key=os.path.getmtime, reverse=True)
    image_list = [f.name for f in images if f.suffix.lower() in {".png",".jpg",".jpeg",".gif",".webp",".svg"}]
    return render_template("admin.html", data=data, images=image_list)


@app.route("/admin/save", methods=["POST"])
def admin_save():
    data = load_content()
    form = request.form.to_dict(flat=True)

    # Update site info
    for key in ["name", "tagline", "email", "phone", "address", "logo_text"]:
        if f"site.{key}" in form:
            data["site"][key] = form[f"site.{key}"]

    # Update banner
    for key in ["title_en", "title_es", "subtitle_en", "subtitle_es"]:
        if f"banner.{key}" in form:
            data["banner"][key] = form[f"banner.{key}"]

    # Update about
    for key in ["title_en", "title_es", "tagline_en", "tagline_es",
                "content_en", "content_es", "content2_en", "content2_es",
                "content3_en", "content3_es"]:
        if f"about.{key}" in form:
            data["about"][key] = form[f"about.{key}"]

    # Update features
    for i in range(len(data["features"])):
        for key in ["title_en", "title_es", "text_en", "text_es", "icon"]:
            fkey = f"feature.{i}.{key}"
            if fkey in form:
                data["features"][i][key] = form[fkey]

    # Update stats
    for i in range(len(data["stats"])):
        for key in ["number", "label_en", "label_es"]:
            fkey = f"stat.{i}.{key}"
            if fkey in form:
                data["stats"][i][key] = form[fkey]

    # Update certifications
    for i in range(len(data["certifications"])):
        for key in ["title_en", "title_es", "icon"]:
            fkey = f"cert.{i}.{key}"
            if fkey in form:
                data["certifications"][i][key] = form[fkey]

    # Update CTA
    for key in ["title_en", "title_es", "text_en", "text_es", "button_en", "button_es"]:
        if f"cta.{key}" in form:
            data["cta"][key] = form[f"cta.{key}"]

    # Update slides
    slide_count = len(data.get("slides", []))
    for i in range(slide_count):
        for key in ["image", "icon", "bg", "title_en", "title_es", "title_pt",
                     "subtitle_en", "subtitle_es", "subtitle_pt",
                     "btn_en", "btn_es", "btn_pt", "link"]:
            fkey = f"slide.{i}.{key}"
            if fkey in form:
                if "slides" not in data:
                    data["slides"] = []
                if i >= len(data["slides"]):
                    data["slides"].append({})
                data["slides"][i][key] = form[fkey]

    save_content(data)
    return redirect(url_for("admin") + "?saved=1")


@app.route("/admin/upload", methods=["POST"])
def admin_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No filename"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
        file.save(UPLOAD_DIR / filename)
        return jsonify({"success": True, "filename": filename, "url": f"/static/uploads/{filename}"})
    return jsonify({"error": "Invalid file type"}), 400


@app.route("/admin/delete-image/<filename>", methods=["POST"])
def admin_delete_image(filename):
    filepath = UPLOAD_DIR / secure_filename(filename)
    if filepath.exists():
        filepath.unlink()
        return jsonify({"success": True})
    return jsonify({"error": "File not found"}), 404


@app.route("/admin/cert-image/<int:index>", methods=["POST"])
def admin_cert_image(index):
    """Set certification image"""
    data = load_content()
    filename = request.json.get("filename", "") if request.is_json else request.form.get("filename", "")
    if 0 <= index < len(data["certifications"]):
        data["certifications"][index]["image"] = filename
        save_content(data)
        return jsonify({"success": True})
    return jsonify({"error": "Invalid index"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
