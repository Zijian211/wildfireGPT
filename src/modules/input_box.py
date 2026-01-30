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
# -----------------------------

class InputBox:
    @staticmethod
    def render():
        """
        Renders input. If an error occurs, it RAISES the exception
        so the Debug Doctor in the main app can catch it.
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
        
        # --- Process Audio ---
        if audio:
            
            # --- 1. Convert ---
            audio_bytes = audio['bytes']
            sound = AudioSegment.from_file(io.BytesIO(audio_bytes))
            
            # --- 2. Silence Check (Prevents API errors from quiet mics) ---
            if sound.dBFS < -50:
                st.toast("⚠️ Audio too quiet. Please speak up!", icon="🔇")
                return None

            # --- 3. Export ---
            wav_buffer = io.BytesIO()
            sound.export(wav_buffer, format="wav")
            wav_buffer.seek(0)
            
            # --- 4. Transcribe ---
            r = sr.Recognizer()
            with sr.AudioFile(wav_buffer) as source:
                audio_data = r.record(source)
                # This line will CRASH if API fails -> Doctor will catch it now!
                voice_text = r.recognize_google(audio_data)

        # --- 2. TEXT INPUT ---
        text_input = st.chat_input("Ask me anything?", key="main_chat_input")

        if voice_text:
            return voice_text
        elif text_input:
            return text_input
        
        return None