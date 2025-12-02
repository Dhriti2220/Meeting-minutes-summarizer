import streamlit as st
import os
from datetime import datetime
import tempfile
from functools import lru_cache

from utils.css_loader import load_css
from utils.extract_audio import extract_audio_from_video
from utils.transcription import transcribe_multilingual
from utils.summary import generate_summary
from utils.export import export_to_markdown
from utils.export import LANGUAGE_NAMES

# Page configuration
st.set_page_config(
    page_title="AI Meeting Minutes - Multilingual",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Loading Custom CSS
load_css("styles/style.css")

# Initialize session state
if 'transcription' not in st.session_state:
    st.session_state.transcription = ""
if 'translation' not in st.session_state:
    st.session_state.translation = ""
if 'detected_language' not in st.session_state:
    st.session_state.detected_language = ""
if 'summary' not in st.session_state:
    st.session_state.summary = None
if 'model_loaded' not in st.session_state:
    st.session_state.model_loaded = False

# Hero Section
st.markdown("""
<div class="hero-section">
    <div class="hero-title">🌍 AI Meeting Minutes - Multilingual</div>
    <div class="hero-subtitle">Transcribe & translate meetings from any language to English with AI-powered summarization</div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    meeting_title = st.text_input("📌 Title", "Team Meeting")
    meeting_date = st.date_input("📅 Date", datetime.now())
    
    st.markdown("---")
    
    st.markdown("### ⚡ Performance Settings")
    
    model_size = st.selectbox(
        "Whisper Model",
        ["tiny", "base", "small", "medium"],
        index=1,  # Default to 'base'
        help="Tiny=Fastest, Medium=Most Accurate"
    )
    
    # Performance guide
    perf_guide = {
        "tiny": "⚡ Fastest (~1GB RAM, ~32x speed)",
        "base": "🚀 Fast (~1GB RAM, ~16x speed)",
        "small": "⚖️ Balanced (~2GB RAM, ~6x speed)",
        "medium": "🎯 Accurate (~5GB RAM, ~2x speed)"
    }
    
    st.info(perf_guide[model_size])
    
    st.markdown("---")
    
    st.markdown("### 🌟 Features")
    
    features = [
        ("🌍", "100+ Languages", "Auto-detect & translate"),
        ("🎥", "Video Support", "Extract & process"),
        ("⚡", "Fast Processing", "Optimized models"),
        ("📥", "Export", "Bilingual markdown")
    ]
    
    for icon, title, desc in features:
        st.markdown(f"""
        <div class="feature-card">
            <div class="feature-icon">{icon}</div>
            <div class="feature-title">{title}</div>
            <div style="color: #666; font-size: 0.9rem;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 🗣️ Popular Languages")
    st.markdown("""
    🇮🇳 Hindi • 🇩🇪 German • 🇯🇵 Japanese  
    🇨🇳 Chinese • 🇪🇸 Spanish • 🇫🇷 French  
    🇰🇷 Korean • 🇸🇦 Arabic • 🇷🇺 Russian  
    
    **And 90+ more!**
    """)
    
    st.markdown("---")
    
    st.markdown("### 🔧 Quick Setup")
    st.code("""pip install streamlit
pip install openai-whisper
pip install anthropic torch
# For video: install ffmpeg""", language="bash")

# Main Content Area
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">📤 Upload Audio/Video</div>', unsafe_allow_html=True)
    
    # File type selector
    file_type = st.radio(
        "Select file type:",
        ["Audio File", "Video File"],
        horizontal=True
    )
    
    if file_type == "Audio File":
        uploaded_file = st.file_uploader(
            "Choose your audio file",
            type=['mp3', 'wav', 'm4a', 'flac', 'ogg', 'aac'],
            help="Supported: MP3, WAV, M4A, FLAC, OGG, AAC (Max 25MB recommended)",
            label_visibility="collapsed"
        )
        media_type = 'audio'
    else:
        uploaded_file = st.file_uploader(
            "Choose your video file",
            type=['mp4', 'avi', 'mov', 'mkv', 'webm'],
            help="Supported: MP4, AVI, MOV, MKV, WEBM (Max 100MB recommended)",
            label_visibility="collapsed"
        )
        media_type = 'video'
    
    if uploaded_file:
        if media_type == 'audio':
            st.audio(uploaded_file)
        else:
            st.video(uploaded_file)
        
        # File info
        file_size = len(uploaded_file.getvalue()) / (1024 * 1024)
        
        # Warning for large files
        if file_size > 50:
            st.markdown("""
            <div class="warning-box">
                ⚠️ Large file detected ({:.1f} MB). Processing may take several minutes. 
                Consider using a smaller file or 'tiny' model for faster results.
            </div>
            """.format(file_size), unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background: #f0f2f6; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
            <b>📁 File:</b> {uploaded_file.name}<br>
            <b>💾 Size:</b> {file_size:.2f} MB<br>
            <b>🎬 Type:</b> {media_type.upper()}<br>
            <b>⚡ Model:</b> {model_size.upper()}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Estimate processing time
        estimate_mins = (file_size * 0.3) if model_size == 'tiny' else (file_size * 0.5) if model_size == 'base' else (file_size * 1.0)
        st.caption(f"⏱️ Estimated time: ~{max(1, int(estimate_mins))} minute(s)")
        
        if st.button("🌍 Transcribe, Translate & Summarize", use_container_width=True, type="primary"):
            
            start_time = datetime.now()
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Extract audio (if video)
            if media_type == 'video':
                status_text.markdown("🎬 **Extracting audio from video...**")
                progress_bar.progress(10)
            
            # Step 2: Transcribe in original language
            status_text.markdown("🎙️ **Transcribing (this may take a minute)...**")
            progress_bar.progress(20)
            
            original_text, detected_lang = transcribe_multilingual(
                uploaded_file, 
                media_type, 
                task='transcribe',
                model_size=model_size
            )
            
            if original_text and detected_lang:
                st.session_state.transcription = original_text
                st.session_state.detected_language = detected_lang
                
                lang_display = LANGUAGE_NAMES.get(detected_lang, detected_lang.upper())
                st.markdown(f'<div class="language-badge">Detected: {lang_display}</div>', unsafe_allow_html=True)
                
                progress_bar.progress(50)
                
                # Step 3: Translate to English (if not English)
                if detected_lang != 'en':
                    status_text.markdown("🌍 **Translating to English...**")
                    translation, _ = transcribe_multilingual(
                        uploaded_file, 
                        media_type, 
                        task='translate',
                        model_size=model_size
                    )
                    st.session_state.translation = translation
                else:
                    st.session_state.translation = original_text
                
                progress_bar.progress(75)
                
                # Step 4: Generate summary
                status_text.markdown("🤖 **Generating AI summary...**")
                summary = generate_summary(st.session_state.translation, lang_display)
                st.session_state.summary = summary
                progress_bar.progress(100)
                
                # Calculate processing time
                elapsed = (datetime.now() - start_time).total_seconds()
                
                status_text.markdown(f"""
                <div class="success-box">
                    ✅ Complete! Processed in {elapsed:.1f} seconds
                </div>
                """, unsafe_allow_html=True)
                
                st.balloons()
    
    else:
        st.markdown("""
        <div class="info-box">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🎤🎥</div>
            <div style="font-size: 1.2rem; font-weight: 600;">Upload Audio or Video</div>
            <div style="margin-top: 0.5rem; font-size: 0.9rem;">Support for 100+ languages</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">📊 AI-Generated Summary</div>', unsafe_allow_html=True)
    
    if st.session_state.summary:
        # Show detected language
        if st.session_state.detected_language:
            lang_display = LANGUAGE_NAMES.get(st.session_state.detected_language, 
                                             st.session_state.detected_language.upper())
            st.markdown(f'<div class="language-badge">Original: {lang_display}</div>', 
                       unsafe_allow_html=True)
        
        # Display summary
        st.markdown('<div class="summary-container">', unsafe_allow_html=True)
        st.markdown(st.session_state.summary)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Download button
        if st.session_state.transcription:
            markdown_content = export_to_markdown(
                st.session_state.transcription,
                st.session_state.translation,
                st.session_state.summary,
                meeting_title,
                meeting_date.strftime("%Y-%m-%d"),
                st.session_state.detected_language
            )
            
            st.download_button(
                label="📥 Download Bilingual Minutes",
                data=markdown_content,
                file_name=f"{meeting_title.replace(' ', '_')}_{meeting_date.strftime('%Y%m%d')}.md",
                mime="text/markdown",
                use_container_width=True
            )
    else:
        st.markdown("""
        <div class="info-box">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🌍</div>
            <div style="font-size: 1.2rem; font-weight: 600;">Summary Will Appear Here</div>
            <div style="margin-top: 0.5rem; font-size: 0.9rem;">Upload and process to see results</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Translation Display (if available)
if st.session_state.translation and st.session_state.detected_language != 'en':
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🌍 View English Translation", expanded=False):
        st.markdown('<div class="translation-box">', unsafe_allow_html=True)
        st.markdown("### English Translation")
        st.write(st.session_state.translation)
        st.markdown('</div>', unsafe_allow_html=True)

# Original Transcription (if available)
if st.session_state.transcription:
    st.markdown("<br>", unsafe_allow_html=True)
    lang_display = LANGUAGE_NAMES.get(st.session_state.detected_language, 
                                      st.session_state.detected_language.upper())
    with st.expander(f"📄 View Original Transcription ({lang_display})", expanded=False):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.text_area(
            "Original transcription",
            st.session_state.transcription,
            height=300,
            disabled=True,
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: white; padding: 2rem; background: rgba(255,255,255,0.1); border-radius: 15px;'>
    <p style='font-size: 1.1rem; margin-bottom: 0.5rem;'><b>⚡ Optimized for Speed</b></p>
    <p style='font-size: 0.9rem; opacity: 0.8;'>Model caching • Fast processing • Smart compression</p>
    <p style='font-size: 0.85rem; opacity: 0.7; margin-top: 0.5rem;'>Supporting 100+ languages • Perfect for global teams</p>
</div>
""", unsafe_allow_html=True)