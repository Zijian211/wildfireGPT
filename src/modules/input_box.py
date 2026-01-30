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
        Renders input. 
        CRITICAL: This function does NOT catch API errors. 
        It lets them crash so 'wildfireChat.py' can diagnose them with the Doctor.
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
            # --- 1. Convert bytes to audio source ---
            audio_bytes = audio['bytes']
            sound = AudioSegment.from_file(io.BytesIO(audio_bytes))
            
            # --- 2. Silence Check (Prevents API errors from quiet mics) ---
            if sound.dBFS < -50:
                st.toast("⚠️ Audio too quiet. Please speak up!", icon="🔇")
                return None

            # --- 3. Export to a memory buffer as WAV ---
            wav_buffer = io.BytesIO()
            sound.export(wav_buffer, format="wav")
            wav_buffer.seek(0)
            
            # --- 4. Transcribe ---
            # --- If API fails (connection/limit), it will crash upwards to the Doctor ---
            r = sr.Recognizer()
            with sr.AudioFile(wav_buffer) as source:
                audio_data = r.record(source)
                voice_text = r.recognize_google(audio_data)

        # --- 2. TEXT INPUT ---
        text_input = st.chat_input("Ask me anything?", key="main_chat_input")

        if voice_text:
            return voice_text
        elif text_input:
            return text_input
        
        return None