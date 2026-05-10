import os
import sys
import base64
import tempfile
import traceback
import subprocess
import shutil
import logging

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.genai as genai

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api.emotion_module import load_model, process_and_predict
from api.api_advice import generate_suggestions as generate_advice_suggestions

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.DEBUG)


def log_request_preview(data: dict):
    """Log a safe preview of incoming JSON request data for debugging 400 errors."""
    try:
        logging.debug(f"Request keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        audio = data.get("audio") if isinstance(data, dict) else None
        mime = data.get("mimeType") if isinstance(data, dict) else None
        if audio:
            logging.debug(f"audio base64 length: {len(audio)}")
            try:
                import base64 as _b64
                _b = _b64.b64decode(audio, validate=True)
                logging.debug(f"audio decodes OK, bytes: {len(_b)}")
            except Exception:
                logging.exception("audio base64 decode failed")
        else:
            logging.debug("No audio field in request")
        if mime:
            logging.debug(f"mimeType: {mime}")
    except Exception:
        logging.exception("Failed to log request preview")


@app.before_request
def log_incoming_request():
    try:
        logging.info(f"Incoming HTTP request: {request.method} {request.path} Host={request.host}")
    except Exception:
        logging.exception("Failed to log incoming request")


def _mask_key(k: str) -> str:
    if not k:
        return "<missing>"
    if len(k) <= 8:
        return k[:2] + "..." + k[-2:]
    return k[:4] + "..." + k[-4:]


logging.info("AI_API_KEY present: %s", bool(os.getenv("AI_API_KEY")))
logging.info("AI_API_KEY masked: %s", _mask_key(os.getenv("AI_API_KEY")))

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_models", "combined_emotion_cnn.pth")
load_model(MODEL_PATH)

gemini = genai.Client(api_key=os.getenv("AI_API_KEY"))
GEMINI_MODEL = "gemini-3.1-pro-preview"

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
_whisper_model = None


def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise RuntimeError(
                "faster-whisper is not installed. Install dependencies and restart the backend."
            ) from e

        _whisper_model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device="cpu",
            compute_type="int8",
        )

    return _whisper_model


def transcribe_audio(wav_path: str) -> str:
    model = get_whisper_model()
    segments, _info = model.transcribe(
        wav_path,
        beam_size=1,
        vad_filter=True,
    )
    return " ".join(segment.text.strip() for segment in segments).strip()


def to_wav(audio_bytes: bytes, mime_type: str):
    """Convert any audio bytes to a wav file using ffmpeg directly. Returns (wav_path, wav_bytes)."""
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise RuntimeError(
            "ffmpeg was not found on PATH. Install ffmpeg and restart your terminal, then try again."
        )

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
        [ffmpeg_path, "-y", "-i", src_path, "-ar", "16000", "-ac", "1", "-f", "wav", wav_path],
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


@app.route("/analyze-and-suggest", methods=["POST"])
def analyze_and_suggest():
    """Full pipeline: convert audio, transcribe, run ML model, then generate Gemini suggestions."""
    data = request.get_json()
    audio_b64 = data.get("audio")
    mime_type = data.get("mimeType", "audio/webm")
    categories = data.get("categories", []) or None
    text = data.get("text", "") or None

    if not audio_b64:
        return jsonify({"error": "Missing audio"}), 400

    wav_path = None
    try:
        logging.info("About to call analyze_and_suggest pipeline")
        logging.info("AI_API_KEY at request time: %s", bool(os.getenv("AI_API_KEY")))
        
        wav_path, wav_bytes = to_wav(base64.b64decode(audio_b64), mime_type)

        # 1) Transcribe locally with Whisper
        transcript = transcribe_audio(wav_path)

        # 2) Run ML model to detect emotion
        emotion = process_and_predict(wav_path)

        # 3) Generate suggestions using integrated api_advice helper
        advice = generate_advice_suggestions(
            emotion=emotion,
            categories=categories,
            transcript=transcript,
            user_notes=text,
            confidence=None,
        )

        # Return combined payload
        return jsonify({
            "emotion": emotion,
            "transcript": transcript,
            "advice": advice,
        })
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
        wav_path, _ = to_wav(base64.b64decode(audio_b64), mime_type)
        transcript = transcribe_audio(wav_path)
        return jsonify({"transcript": transcript})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        if wav_path and os.path.exists(wav_path):
            os.unlink(wav_path)


@app.route("/generate-suggestions", methods=["POST"])
def generate_suggestions():
    """
    Integrate ML model output + all data to generate Gemini suggestions.
    Uses emotion + categories + transcript + notes to provide tailored advice.
    """
    data = request.get_json()
    emotion = data.get("emotion", "")
    categories = data.get("categories", []) or None
    text = data.get("text", "") or None
    transcript = data.get("transcript", "") or None
    confidence = data.get("confidence", None)

    try:
        result = generate_advice_suggestions(
            emotion=emotion,
            categories=categories,
            transcript=transcript,
            user_notes=text,
            confidence=confidence
        )
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/test-suggestions", methods=["POST"])
def test_suggestions():
    """Simple test endpoint to debug suggestions without audio processing."""
    try:
        logging.info("test-suggestions endpoint called")
        result = generate_advice_suggestions(
            emotion="sad",
            categories=["relationship"],
            transcript="test",
            user_notes="test notes",
            confidence=0.8
        )
        return jsonify(result)
    except Exception as e:
        logging.error(f"test-suggestions error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/ping", methods=["GET"])
def ping():
    """Health-check endpoint."""
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    # Print registered routes at startup for debugging
    print("Registered routes at startup:")
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        print(rule.rule, sorted(rule.methods))
    app.run(host="0.0.0.0", port=5000, debug=False)
