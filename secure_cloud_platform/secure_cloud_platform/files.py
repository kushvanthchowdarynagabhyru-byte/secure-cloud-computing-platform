import os
import uuid
from flask import (
    Blueprint, render_template, redirect, url_for, request,
    flash, send_file, current_app, abort
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from io import BytesIO

from models import db, File, User, AuditLog
from utils.crypto_utils import (
    generate_data_key, encrypt_bytes, decrypt_bytes,
    wrap_key, unwrap_key, InvalidToken
)
from utils.decorators import admin_required

files_bp = Blueprint("files", __name__)

# Basic extension allowlist - adjust to your needs
ALLOWED_EXTENSIONS = {
    "txt", "pdf", "png", "jpg", "jpeg", "gif", "docx", "xlsx",
    "pptx", "csv", "zip", "md", "json"
}


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _log(action, detail=""):
    entry = AuditLog(
        username=current_user.username,
        action=action,
        detail=detail,
        ip_address=request.remote_addr,
    )
    db.session.add(entry)
    db.session.commit()


@files_bp.route("/")
@login_required
def dashboard():
    my_files = File.query.filter_by(owner_id=current_user.id).order_by(File.uploaded_at.desc()).all()
    return render_template("dashboard.html", files=my_files)


@files_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        uploaded = request.files.get("file")

        if not uploaded or uploaded.filename == "":
            flash("Please choose a file to upload.", "error")
            return redirect(url_for("files.upload"))

        if not _allowed_file(uploaded.filename):
            flash("That file type is not allowed.", "error")
            return redirect(url_for("files.upload"))

        original_filename = secure_filename(uploaded.filename)
        raw_bytes = uploaded.read()

        # --- Envelope encryption ---
        data_key = generate_data_key()
        ciphertext = encrypt_bytes(raw_bytes, data_key)
        wrapped_key = wrap_key(data_key, current_app.config["MASTER_KEY"])

        # Store under a random name on disk so filenames never leak metadata
        stored_filename = f"{uuid.uuid4().hex}.enc"
        stored_path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_filename)

        with open(stored_path, "wb") as f:
            f.write(ciphertext)

        file_record = File(
            original_filename=original_filename,
            stored_filename=stored_filename,
            encrypted_key=wrapped_key,
            size_bytes=len(raw_bytes),
            owner_id=current_user.id,
        )
        db.session.add(file_record)
        db.session.commit()

        _log("upload", f"Uploaded '{original_filename}' ({len(raw_bytes)} bytes)")
        flash(f"'{original_filename}' uploaded and encrypted successfully.", "success")
        return redirect(url_for("files.dashboard"))

    return render_template("upload.html")


@files_bp.route("/download/<int:file_id>")
@login_required
def download(file_id):
    file_record = File.query.get_or_404(file_id)

    # Authorization check: owner or admin only
    if file_record.owner_id != current_user.id and not current_user.is_admin():
        _log("download_denied", f"Attempted access to file id {file_id}")
        abort(403)

    stored_path = os.path.join(current_app.config["UPLOAD_FOLDER"], file_record.stored_filename)
    if not os.path.exists(stored_path):
        flash("File data not found on server.", "error")
        return redirect(url_for("files.dashboard"))

    try:
        data_key = unwrap_key(file_record.encrypted_key, current_app.config["MASTER_KEY"])
        with open(stored_path, "rb") as f:
            ciphertext = f.read()
        plaintext = decrypt_bytes(ciphertext, data_key)
    except InvalidToken:
        flash("Decryption failed: file integrity could not be verified.", "error")
        _log("decrypt_failed", f"file id {file_id}")
        return redirect(url_for("files.dashboard"))

    _log("download", f"Downloaded '{file_record.original_filename}'")
    return send_file(
        BytesIO(plaintext),
        download_name=file_record.original_filename,
        as_attachment=True,
    )


@files_bp.route("/delete/<int:file_id>", methods=["POST"])
@login_required
def delete(file_id):
    file_record = File.query.get_or_404(file_id)

    if file_record.owner_id != current_user.id and not current_user.is_admin():
        abort(403)

    stored_path = os.path.join(current_app.config["UPLOAD_FOLDER"], file_record.stored_filename)
    if os.path.exists(stored_path):
        os.remove(stored_path)

    _log("delete", f"Deleted '{file_record.original_filename}'")
    db.session.delete(file_record)
    db.session.commit()

    flash("File deleted.", "success")
    return redirect(url_for("files.dashboard"))


@files_bp.route("/admin")
@login_required
@admin_required
def admin_panel():
    all_files = File.query.order_by(File.uploaded_at.desc()).all()
    all_users = User.query.order_by(User.created_at.desc()).all()
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(50).all()
    return render_template(
        "admin.html", files=all_files, users=all_users, logs=recent_logs
    )
