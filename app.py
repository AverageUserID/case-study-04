from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import ValidationError
from models import SurveySubmission, StoredSurveyRecord
from storage import append_json_line
import hashlib

app = Flask(__name__)
# Allow cross-origin requests so the static HTML can POST from localhost or file://
CORS(app, resources={r"/v1/*": {"origins": "*"}})

def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

@app.route("/ping", methods=["GET"])
def ping():
    """Simple health check endpoint."""
    return jsonify({
        "status": "ok",
        "message": "API is alive",
        "utc_time": datetime.now(timezone.utc).isoformat()
    })

@app.post("/v1/survey")
def submit_survey():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "invalid_json", "detail": "Body must be application/json"}), 400

    try:
        submission = SurveySubmission(**payload)
    except ValidationError as ve:
        return jsonify({"error": "validation_error", "detail": ve.errors()}), 422

    # Hash PII before creating StoredSurveyRecord
    hashed_email = sha256_hex(submission.email)
    hashed_age = sha256_hex(str(submission.age))

    if submission.submission_id:   
        submission_id = submission.submission_id
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H")  # YYYYMMDDHH
        submission_id = sha256_hex(f"{submission.email}{timestamp}")
    
    data = submission.dict(exclude={"user_agent", "email", "age", "submission_id"})
    record = StoredSurveyRecord(
        **data,
        submission_id=submission_id,
        email=hashed_email,
        age=hashed_age,
        received_at=datetime.now(timezone.utc),
        ip=request.headers.get("X-Forwarded-For", request.remote_addr or ""),
        user_agent=request.headers.get("User-Agent")
    )

    append_json_line(record.dict())
    return jsonify({"status": "ok"}), 201

if __name__ == "__main__":
    app.run(port=5000, debug=True)
