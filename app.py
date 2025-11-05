# app.py
# File Integrity Checker — Flask (SHA-256), Single Baseline (persistent baseline.json)

from flask import Flask, render_template, request, redirect, url_for, flash
import hashlib, json, os, time
from typing import Tuple

app = Flask(__name__)
app.secret_key = "change-this-secret"            # needed for flash messages
BASELINE_PATH = "baseline.json"

# ---------- helpers ----------
def sha256_stream(fileobj) -> Tuple[str, int]:
    """Compute SHA-256 hex of an uploaded file stream (chunked) and return (hash_hex, size_bytes)."""
    fileobj.seek(0)
    h = hashlib.sha256()
    size = 0
    for chunk in iter(lambda: fileobj.read(1024 * 1024), b""):
        h.update(chunk)
        size += len(chunk)
    fileobj.seek(0)
    return h.hexdigest(), size

def load_baseline():
    if not os.path.isfile(BASELINE_PATH):
        return None
    with open(BASELINE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_baseline_record(name: str, size: int, hash_hex: str):
    data = {
        "name": name,
        "size": size,
        "hash": hash_hex,
        "saved_at": int(time.time())
    }
    with open(BASELINE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data

def human_time(ts: int) -> str:
    return time.strftime("%d %b %Y, %I:%M %p", time.localtime(ts))

# ---------- routes ----------
@app.route("/", methods=["GET"])
def index():
    base = load_baseline()
    return render_template("index.html", baseline=base, human_time=human_time)

@app.route("/save_baseline", methods=["POST"])
def save_baseline_route():
    file = request.files.get("baseline_file")
    if not file or file.filename == "":
        flash("Please choose a file.", "warn")
        return redirect(url_for("index"))
    hash_hex, size = sha256_stream(file.stream)
    # use the original filename as-is (no saving to disk, so no need for secure_filename)
    save_baseline_record(file.filename, size, hash_hex)
    flash("Baseline saved successfully.", "ok")
    return redirect(url_for("index"))

@app.route("/verify", methods=["POST"])
def verify_route():
    base = load_baseline()
    if not base:
        flash("No baseline found. Save one first.", "warn")
        return redirect(url_for("index"))

    file = request.files.get("verify_file")
    if not file or file.filename == "":
        flash("Please choose a file to verify.", "warn")
        return redirect(url_for("index"))

    hash_hex, _ = sha256_stream(file.stream)
    if hash_hex == base["hash"]:
        flash(f"MATCH ✓ — SHA-256: {hash_hex}", "ok")
    else:
        flash(f"MISMATCH ✗ — Expected: {base['hash']} | Actual: {hash_hex}", "bad")
    return redirect(url_for("index"))

@app.route("/delete_baseline", methods=["POST"])
def delete_baseline():
    if os.path.isfile(BASELINE_PATH):
        os.remove(BASELINE_PATH)
        flash("Baseline deleted.", "ok")
    else:
        flash("No baseline to delete.", "warn")
    return redirect(url_for("index"))

if __name__ == "__main__":
    # pip install flask
    app.run(debug=True)
