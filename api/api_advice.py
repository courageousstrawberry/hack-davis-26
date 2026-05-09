import os
from dotenv import load_dotenv
import google.genai

# Minimal example: loads key from env and makes a single simple call.
load_dotenv()
API_KEY = os.getenv("AI_API_KEY")
if not API_KEY:
    raise EnvironmentError("Set AI_API_KEY environment variable before running")

client = google.genai.Client(api_key=API_KEY)


def generate_advice_from_emotion(emotion, confidence=None):
    """
    Build the prompt from the emotion module output and ask Gemini for advice.

    emotion: string like "sad", "happy", "angry"
    confidence: optional float like 0.82
    """
    system_template = (
        "You are a supportive, non-judgmental wellbeing coach for students. "
        "Use the detected emotion to respond with: 1) a 1-2 sentence empathetic reflection, "
        "2) three short, actionable self-care steps (each 1 sentence), and 3) a brief disclaimer stating this is not medical advice. "
        "Keep the response concise and kind."
    )

    emotion_line = f"Detected emotion: {emotion}"
    if confidence is not None:
        emotion_line += f" (confidence: {confidence})"

    full_prompt = system_template + "\n\n" + emotion_line
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=full_prompt,
    )
    return getattr(response, "text", response)

def single_request_flow():
    emotion = input("Enter detected emotion: ").strip()
    if not emotion:
        print("No input provided. Exiting.")
        return

    confidence_raw = input("Enter confidence (optional, press Enter to skip): ").strip()
    confidence = float(confidence_raw) if confidence_raw else None

    resp = generate_advice_from_emotion(emotion, confidence)
    print(resp)


if __name__ == "__main__":
    single_request_flow()
