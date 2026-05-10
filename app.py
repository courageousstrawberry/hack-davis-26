import os
import sys
import base64
import tempfile
import json
import traceback
import subprocess

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.genai as genai
from google.genai import types

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api.emotion_module import load_model, process_and_predict

app = Flask(__name__)
CORS(app)

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_models", "combined_emotion_cnn.pth")
load_model(MODEL_PATH)

gemini = genai.Client(api_key=os.getenv("AI_API_KEY"))
GEMINI_MODEL = "gemini-3.1-pro-preview"


def to_wav(audio_bytes: bytes, mime_type: str):
    """Convert any audio bytes to a wav file using ffmpeg directly. Returns (wav_path, wav_bytes)."""
    # Write original audio to temp file
    if "webm" in mime_type:
        ext = ".webm"
    elif "mp3" in mime_type or "mpeg" in mime_type:
        ext = ".mp3"
    elif "mp4" in mime_type or "m4a" in mime_type:
        ext = ".m4a"
    elif "ogg" in mime_type:
        ext = ".ogg"
    else:
        ext = ".wav"

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(audio_bytes)
        src_path = f.name

    if ext == ".wav":
        return src_path, audio_bytes

    wav_path = src_path + ".wav"
    # Use ffmpeg directly for reliable conversion
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", src_path, "-ar", "16000", "-ac", "1", "-f", "wav", wav_path],
        capture_output=True, text=True
    )
    os.unlink(src_path)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")

    with open(wav_path, "rb") as f:
        wav_bytes = f.read()
    return wav_path, wav_bytes


@app.route("/predict-emotion", methods=["POST"])
def predict_emotion():
    data = request.get_json()
    audio_b64 = data.get("audio")
    mime_type = data.get("mimeType", "audio/webm")
    if not audio_b64:
        return jsonify({"error": "Missing audio"}), 400
    wav_path = None
    try:
        wav_path, _ = to_wav(base64.b64decode(audio_b64), mime_type)
        emotion = process_and_predict(wav_path)
        return jsonify({"emotion": emotion})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        if wav_path and os.path.exists(wav_path):
            os.unlink(wav_path)


@app.route("/analyze-audio", methods=["POST"])
def analyze_audio():
    data = request.get_json()
    audio_b64 = data.get("audio")
    mime_type = data.get("mimeType", "audio/webm")
    if not audio_b64:
        return jsonify({"error": "Missing audio"}), 400
    wav_path = None
    try:
        wav_path, wav_bytes = to_wav(base64.b64decode(audio_b64), mime_type)
        response = gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav"),
                (
                    "Transcribe this audio clip. "
                    "Return ONLY valid JSON: {\"transcript\": \"what was said\"}. "
                    "No markdown, no extra text."
                ),
            ],
        )
        raw = response.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(raw)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        if wav_path and os.path.exists(wav_path):
            os.unlink(wav_path)


@app.route("/generate-suggestions", methods=["POST"])
def generate_suggestions():
    data = request.get_json()
    emotion = data.get("emotion", "")
    categories = data.get("categories", [])
    text = data.get("text", "")
    transcript = data.get("transcript", "")

    context_parts = []
    if emotion:
        context_parts.append(f"Detected emotion from voice: {emotion}")
    if categories:
        context_parts.append(f"Issue areas: {', '.join(categories)}")
    if transcript:
        context_parts.append(f"What they said: \"{transcript}\"")
    if text:
        context_parts.append(f"Additional context: \"{text}\"")

    prompt = (
        "You are a supportive, empathetic wellbeing assistant. "
        "Given the following context about a user, return a JSON object with:\n"
        "- \"transcript\": a brief empathetic one-sentence summary of their situation\n"
        "- \"suggestions\": an array of 4-6 objects each with \"title\" (short) and \"detail\" (1-2 sentences), "
        "tailored specifically to their emotional state and issues.\n\n"
        "Context: " + ". ".join(context_parts) + "\n\n"
        "Respond ONLY with valid JSON, no markdown, no extra text."
    )

    try:
        response = gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        raw = response.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(raw)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
