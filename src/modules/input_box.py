import streamlit as st
import speech_recognition as sr
from streamlit_mic_recorder import mic_recorder
import io
import os
from pydub import AudioSegment

# --- SMART FFMPEG DETECTION ---
local_ffmpeg = r"E:\ffmpeg\ffmpeg\bin\ffmpeg.exe"
local_ffprobe = r"E:\ffmpeg\ffmpeg\bin\ffprobe.exe"

if os.path.exists(local_ffmpeg):
    AudioSegment.converter = local_ffmpeg
    AudioSegment.ffprobe = local_ffprobe
    print(f"✅ Local Mode: Using FFmpeg at {local_ffmpeg}")
else:
    print("☁️ Cloud Mode: Using system default FFmpeg")

# --- INPUT BOX CLASS ---
class InputBox:
    @staticmethod
    def render():
        """
        Renders the Voice and Text input widgets.
        Returns the text string entered by the user (or transcribed from voice).
        """
        voice_text = None
        
        # --- 1. VOICE INPUT ---
        col_mic, col_buffer = st.columns([1, 8])
        with col_mic:
            audio = mic_recorder(
                start_prompt="🎤",
                stop_prompt="🛑",
                key='recorder',
                just_once=True,
                use_container_width=False
            )
        
        # --- Process Audio if recorded ---
        if audio:
            try:
                # --- 1. Get raw bytes from browser ---
                audio_bytes = audio['bytes']
                
                # --- 2. Convert to WAV using pydub ---
                sound = AudioSegment.from_file(io.BytesIO(audio_bytes))
                
                # --- 3. Export to a memory buffer as WAV ---
                wav_buffer = io.BytesIO()
                sound.export(wav_buffer, format="wav")
                wav_buffer.seek(0)
                
                # --- 4. Transcribe ---
                r = sr.Recognizer()
                with sr.AudioFile(wav_buffer) as source:
                    audio_data = r.record(source)
                    voice_text = r.recognize_google(audio_data)
                    
            except Exception as e:
                st.warning(f"Audio processing error: {e}")

        # --- 2. TEXT INPUT ---
        text_input = st.chat_input("Ask me anything?")

        # --- 3. RETURN RESULT ---
        return voice_text if voice_text else text_input