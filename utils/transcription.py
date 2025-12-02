import os
import tempfile
import streamlit as st
from utils.extract_audio import extract_audio_from_video
from utils.load_whisper import load_whisper_model

def transcribe_multilingual(file, file_type='audio', task='transcribe', model_size='base'):
    """
    Transcribe audio/video in any language - OPTIMIZED
    task='transcribe' keeps original language
    task='translate' translates to English
    """
    try:
        # Load cached model
        model = load_whisper_model(model_size)
        if model is None:
            return None, None
        
        # Handle video files
        if file_type == 'video':
            audio_path = extract_audio_from_video(file)
            if not audio_path:
                return None, None
        else:
            # Handle audio files
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(file.getvalue())
                audio_path = tmp_file.name
        
        # Transcribe with optimized settings
        result = model.transcribe(
            audio_path,
            task=task,
            fp16=False,
            language=None,  # Auto-detect
            beam_size=1,  # Default is 5, lower = faster but less accurate
            best_of=1,  # Default is 5
            temperature=0.0,  # Deterministic output
            compression_ratio_threshold=2.4,
            no_speech_threshold=0.6
        )
        
        # Clean up
        os.unlink(audio_path)
        
        detected_lang = result.get('language', 'unknown')
        text = result["text"]
        
        return text, detected_lang
    
    except ImportError:
        st.error("⚠️ Whisper not installed. Run: `pip install openai-whisper`")
        return None, None
    except Exception as e:
        st.error(f"❌ Transcription error: {str(e)}")
        return None, None