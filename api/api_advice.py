import os
from dotenv import load_dotenv
import google.genai

# Minimal example: loads key from env and makes a single simple call.
load_dotenv()
API_KEY = os.getenv("AI_API_KEY")
if not API_KEY:
    raise EnvironmentError("Set AI_API_KEY environment variable before running")

client = google.genai.Client(api_key=API_KEY)

def single_request_flow():
    # Pre-coded prompt template that shapes the model output.
    system_template = (
        "You are a supportive, non-judgmental wellbeing coach. "
        "Read the user's input and respond with: 1) a 1-2 sentence empathetic reflection, "
        "2) three short, actionable self-care steps (each 1 sentence), and 3) a brief disclaimer stating this is not medical advice. "
        "Keep the response concise and kind."
    )

    user_input = input("Enter a short user message (single line): ")
    if not user_input.strip():
        print("No input provided. Exiting.")
        return

    full_prompt = system_template + "\n\nUser: " + user_input.strip()
    resp = client.models.generate_content(model="gemini-3-flash-preview", contents=full_prompt)
    print(getattr(resp, "text", resp))


if __name__ == "__main__":
    single_request_flow()
