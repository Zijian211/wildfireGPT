import pandas as pd
from pypdf import PdfReader
from docx import Document
import io

class FileManager:
    @staticmethod
    def process_file(uploaded_file):
        """
        Identifies the file type and extracts text content.
        Returns a formatted string: "File Context (filename): content..."
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

            # --- DOCX Processing ---
            elif file_type in ['docx', 'doc']:
                doc = Document(uploaded_file)
                for para in doc.paragraphs:
                    text_content += para.text + "\n"

            # --- CSV Processing ---
            elif file_type == 'csv':
                df = pd.read_csv(uploaded_file)
                text_content = df.to_string(index=False)

            # --- Plain Text ---
            elif file_type == 'txt':
                text_content = uploaded_file.read().decode("utf-8")

            else:
                return f"[System: Unsupported file type '{file_type}']"

            # --- Truncation Safety ---
            # --- Limit content to ~15,000 characters to prevent crashing the context window ---
            if len(text_content) > 15000:
                text_content = text_content[:15000] + "\n...[Content Truncated due to length]..."

            return f"File Context ({uploaded_file.name}):\n{text_content}\n"

        except Exception as e:
            return f"[System: Error reading file {uploaded_file.name}: {str(e)}]"