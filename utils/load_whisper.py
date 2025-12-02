import streamlit as st
import whisper

# Cache the Whisper model to load only once
@st.cache_resource
def load_whisper_model(model_size='base'):
    """Load Whisper model once and cache it"""
    try:
        return whisper.load_model(model_size)
    except ImportError:
        st.error("⚠️ Whisper not installed. Run: `pip install openai-whisper`")
        return None
    except Exception as e:
        st.error(f"❌ Model loading error: {str(e)}")
        return None