import streamlit as st
import pandas as pd
from pypdf import PdfReader
import io
from docx import Document

class FileManager:
    def __init__(self):
        """
        Initializes the FileManager.
        """
        pass

    def render(self):
        """
        Displays the file uploader UI. 
        """
        st.markdown("### 📂 Upload Context")
        
        # --- 1. The Upload Widget ---
        uploaded_file = st.file_uploader(
            "Attach data (PDF, DOCX, CSV, TXT) for analysis:", 
            type=["pdf", "docx", "csv", "txt"]
        )
        
        # --- 2. Process the file if the user uploads one ---
        if uploaded_file is not None:
            # --- Check if this is a new file to avoid re-processing on every click ---
            if st.session_state.get('last_uploaded_filename') != uploaded_file.name:
                
                with st.spinner("Processing file..."):
                    text_content = self.process_file(uploaded_file)
                
                # --- Save to Session State ---
                if text_content and "Error" not in text_content:
                    st.session_state['pending_file_context'] = text_content
                    st.session_state['last_uploaded_filename'] = uploaded_file.name
                    st.success(f"✅ Loaded: {uploaded_file.name}")
                    st.rerun()
                else:
                    st.error(text_content)

        # --- 3. Show active file and Clear button ---
        if st.session_state.get('pending_file_context'):
            st.info(f"📎 Active: {st.session_state.get('last_uploaded_filename')}")
            if st.button("🗑️ Clear Context"):
                st.session_state['pending_file_context'] = None
                st.session_state['last_uploaded_filename'] = None
                st.rerun()

    def process_file(self, uploaded_file):
        """
        Reads the file and extracts text.
        """
        if uploaded_file is None:
            return None

        file_type = uploaded_file.name.split('.')[-1].lower()
        text_content = ""

        try:
            # --- PDF Processing ---
            if file_type == 'pdf':
                reader = PdfReader(uploaded_file)
                for page in reader.pages:
                    extract = page.extract_text()
                    if extract:
                        text_content += extract + "\n"
            
            # --- DOCX Processing (NEW) ---
            elif file_type in ['docx', 'doc']:
                try:
                    from docx import Document
                except ImportError:
                    return "❌ Error: Please run 'pip install python-docx' to read Word files."
                
                doc = Document(uploaded_file)
                for para in doc.paragraphs:
                    text_content += para.text + "\n"

            # --- CSV Processing ---
            elif file_type == 'csv':
                df = pd.read_csv(uploaded_file)
                text_content = df.to_string(index=False)

            # --- Plain Text ---
            elif file_type == 'txt':
                uploaded_file.seek(0)
                text_content = uploaded_file.read().decode("utf-8")
            
            else:
                return f"⚠️ Unsupported file type: {file_type}"

            # --- Truncation Safety (Limit to ~15k chars) ---
            if len(text_content) > 15000:
                text_content = text_content[:15000] + "\n...[Content Truncated]..."

            return f"File Context ({uploaded_file.name}):\n{text_content}\n"

        except Exception as e:
            return f"❌ Error reading file: {str(e)}"