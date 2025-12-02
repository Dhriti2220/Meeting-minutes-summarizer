import google.generativeai as genai
import streamlit as st

def generate_summary(text, original_language=""):
    """Generate summary using Claude API or mock - OPTIMIZED"""
    try:
        GEMINI_API_KEY = "YOUR_API_KEY"
        genai.configure(api_key=GEMINI_API_KEY)
        
        lang_context = f" (Originally in {original_language})" if original_language else ""
        
        # Truncate very long texts to speed up
        max_chars = 8000
        text_to_analyze = text[:max_chars] + ("..." if len(text) > max_chars else "")
        
        prompt = f"""Analyze this meeting/video transcription{lang_context} and provide:

1. Meeting/Video Summary (2-3 sentences)
2. Key Discussion Points (bullet points)
3. Action Items (with assignee if mentioned)
4. Decisions Made
5. Deadlines
6. Next Steps

Transcription:
{text_to_analyze}

Format the output in clear sections with markdown."""

        model = genai.GenerativeModel("models/gemma-3-4b-it")
        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        st.error(f"Gemini ERROR: {e}")
        return "Error while generating summary"