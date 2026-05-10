import os
import json
import logging
from dotenv import load_dotenv
import google.genai
from google.genai import errors as genai_errors

_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
load_dotenv(os.path.join(_ROOT_DIR, ".env"))

API_KEY = os.getenv("AI_API_KEY")
if not API_KEY:
    raise EnvironmentError("Set AI_API_KEY environment variable before running")

MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3.1-flash-lite-preview")
logging.info(f"api_advice module loaded. MODEL_NAME={MODEL_NAME}, API_KEY masked={API_KEY[:6] if API_KEY else 'NONE'}...{API_KEY[-4:] if API_KEY else ''}")


def get_client():
    """Create a fresh Gemini client from the current process environment."""
    api_key = os.getenv("AI_API_KEY")
    logging.info(f"get_client() called: api_key present={bool(api_key)}, masked={api_key[:6] if api_key else 'NONE'}...{api_key[-4:] if api_key else ''}")
    if not api_key:
        raise EnvironmentError("Set AI_API_KEY environment variable before running")
    return google.genai.Client(api_key=api_key)


def generate_suggestions(emotion, categories=None, transcript=None, user_notes=None, confidence=None):
    """
    Integrate ML model output + data to generate Gemini suggestions.
    
    Args:
        emotion: string from emotion model ("sad", "happy", "angry", etc.)
        categories: list of issue areas user selected
        transcript: what the user said (speech-to-text)
        user_notes: additional text from user
        confidence: confidence score from ML model (0-1)
    
    Returns:
        dict with 'transcript' summary and 'suggestions' array
    """
    
    # Build context from all available data
    context_parts = []
    
    if emotion:
        emotion_str = f"Detected emotion: {emotion}"
        if confidence is not None:
            emotion_str += f" (confidence: {confidence:.2f})"
        context_parts.append(emotion_str)
    
    if categories:
        context_parts.append(f"Issue areas: {', '.join(categories)}")
    
    if transcript:
        context_parts.append(f"What they said: \"{transcript}\"")
    
    if user_notes:
        context_parts.append(f"Additional context: \"{user_notes}\"")
    
    context_block = "\n".join(context_parts)
    
    # System prompt for wellbeing coaching
    system_prompt = (
        "You are a supportive, empathetic wellbeing assistant. "
        "Given the user's emotional state and situation, return a JSON response with:\n"
        "- 'transcript': a brief empathetic 1-2 sentence summary of their situation\n"
        "- 'suggestions': an array of 4-6 objects with 'title' (short action) and 'detail' (1-2 sentences). "
        "Make suggestions specific, actionable, and tailored to their emotion and issues.\n"
        "Respond ONLY with valid JSON, no markdown, no extra text."
    )
    
    user_prompt = f"Context:\n{context_block}\n\nProvide helpful, compassionate suggestions tailored to this person's emotional state and situation."
    
    logging.info(f"generate_suggestions: About to call get_client()")
    client = get_client()
    logging.info(f"generate_suggestions: client created successfully, calling generate_content with model={MODEL_NAME}")

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                {"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_prompt}]}
            ],
        )
        logging.info(f"generate_suggestions: API call succeeded")

        response_text = response.text.strip()
        # Handle markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        return result
    except genai_errors.ClientError as e:
        message = str(e)
        logging.error(f"Gemini client error: {message}")
        print(f"Gemini client error: {message}")
        raise RuntimeError(message) from e
    except (json.JSONDecodeError, AttributeError) as e:
        logging.error(f"Error parsing Gemini response: {e}")
        print(f"Error parsing Gemini response: {e}")
        raise RuntimeError(f"Could not parse Gemini response: {e}") from e


def single_request_flow():
    """Interactive test for generating suggestions with all context."""
    emotion = input("Enter detected emotion: ").strip()
    if not emotion:
        print("No input provided. Exiting.")
        return

    confidence_raw = input("Enter confidence score (0-1, optional): ").strip()
    confidence = float(confidence_raw) if confidence_raw else None

    categories_raw = input("Enter issue areas (comma-separated, optional): ").strip()
    categories = [c.strip() for c in categories_raw.split(",")] if categories_raw else None

    transcript = input("What did they say (transcript, optional): ").strip() or None
    user_notes = input("Additional notes (optional): ").strip() or None

    result = generate_suggestions(emotion, categories, transcript, user_notes, confidence)
    print("\n" + "="*50)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    single_request_flow()
