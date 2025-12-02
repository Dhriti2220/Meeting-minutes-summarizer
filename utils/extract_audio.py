import tempfile
import os
import streamlit as st

def extract_audio_from_video(video_file):
    """Extract audio from video file using ffmpeg - OPTIMIZED"""
    try:
        import subprocess
        
        # Save video temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_video:
            tmp_video.write(video_file.getvalue())
            video_path = tmp_video.name
        
        # Create temporary audio file
        audio_path = tempfile.mktemp(suffix='.wav')
        
        # Extract audio with faster settings
        subprocess.run([
            'ffmpeg', '-i', video_path,
            '-vn',  # No video
            '-acodec', 'pcm_s16le',
            '-ar', '16000',  # 16kHz is enough for speech
            '-ac', '1',  # Mono
            '-y',  # Overwrite
            audio_path
        ], check=True, capture_output=True, timeout=60)
        
        # Clean up video file
        os.unlink(video_path)
        
        return audio_path
    
    except subprocess.CalledProcessError:
        st.error("⚠️ FFmpeg not found. Install: `sudo apt-get install ffmpeg` or `brew install ffmpeg`")
        return None
    except subprocess.TimeoutExpired:
        st.error("❌ Video processing timed out. Try a shorter video.")
        return None
    except Exception as e:
        st.error(f"❌ Audio extraction error: {str(e)}")
        return None