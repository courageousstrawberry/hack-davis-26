import streamlit as st
import os
from google import genai
from google.genai import types

# 1. SETUP GEMINI CLIENT
# This automatically looks for GEMINI_API_KEY in your environment variables
try:
    client = genai.Client()
except Exception as e:
    st.error("Missing API Key! Please set GEMINI_API_KEY in your environment.")

def analyze_audio_with_gemini(audio_bytes):
    """Sends the audio file to Gemini to get the transcript and emotional response."""
    prompt = """
    Listen to this audio clip. You are an empathetic mental health journaling companion.
    1. Transcribe exactly what the user said.
    2. Analyze the acoustic tone of their voice and tell me their primary emotion (e.g. Happy, Sad, Frustrated, Neutral).
    3. If they say sad words but have a completely flat/neutral tone, assume they are emotionally numb or in shock.
    4. Provide a 2-sentence empathetic response validating their feelings, followed by one journaling prompt to help them.
    """
    
    # Send the raw audio bytes directly to the Gemini 2.5 Flash model
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            prompt,
            types.Part.from_bytes(
                data=audio_bytes,
                mime_type='audio/wav',
            )
        ]
    )
    return response.text

# 2. BUILD THE STREAMLIT UI
st.title("🎙️ AI Mood Journal (Powered by Gemini)")
st.write("Record a voice journal entry, and I'll analyze your words and tone to help you process your emotions.")

# This widget lets the user record audio from their laptop microphone
audio_value = st.audio_input("Record your journal entry:")

# 3. PROCESS THE AUDIO WHEN RECORDED
if audio_value is not None:
    st.success("Recording captured! Analyzing your tone of voice...")
    
    # Read the audio file into memory
    audio_bytes = audio_value.read()
    
    # Optional: You can play the audio back to the user
    st.audio(audio_bytes, format="audio/wav")
    
    with st.spinner("Gemini is listening and thinking..."):
        try:
            # Call our Gemini function
            result = analyze_audio_with_gemini(audio_bytes)
            
            # Display the result
            st.markdown("### 🧠 Gemini's Analysis & Response")
            st.info(result)
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
            
st.markdown("---")
st.caption("Hackathon Project combining PyTorch ML Models and Google Gemini native audio processing.")