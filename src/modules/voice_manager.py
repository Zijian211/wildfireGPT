import streamlit as st
import speech_recognition as sr

class VoiceManager:
    @staticmethod
    def record_and_transcribe():
        """
        Records audio from the microphone and uses Google Speech Recognition 
        to transcribe it to text.
        """
        r = sr.Recognizer()
        
        # --- Use a container to make the Input button deployed properly ---
        if st.button("🎙️ Voice Input", key="voice_btn", help="Click to speak"):
            with st.spinner("Listening..."):
                try:
                    with sr.Microphone() as source:
                        # --- Adjust for ambient noise for 0.5s ---
                        r.adjust_for_ambient_noise(source, duration=0.5)
                        
                        # --- Listen (max 10 seconds of phrase) ---
                        audio = r.listen(source, timeout=5, phrase_time_limit=10)
                        
                    # --- Transcribe ---
                    text = r.recognize_google(audio)
                    return text
                
                except sr.WaitTimeoutError:
                    st.warning("No speech detected.")
                    return None
                except sr.UnknownValueError:
                    st.warning("Could not understand audio.")
                    return None
                except sr.RequestError:
                    st.error("Network error regarding Voice API.")
                    return None
                except Exception as e:
                    st.error(f"Microphone error: {e}")
                    return None
        return None