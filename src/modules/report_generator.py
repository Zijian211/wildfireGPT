from fpdf import FPDF
import datetime

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Wildfire GPT - Consultation Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(username, messages):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    # --- Title Section ---
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Wildfire Risk Analysis Report", 0, 1, 'L')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Generated for: {username}", 0, 1, 'L')
    pdf.cell(0, 10, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, 'L')
    pdf.ln(5)

    # --- Chat History ---
    for msg in messages:
        role = msg['role'].upper()
        content = msg['content']
        
        if isinstance(content, str):
            # --- Set color based on role (Blue for User, Black for AI) ---
            if role == "USER":
                pdf.set_text_color(0, 0, 255) # --- Blue ---
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(0, 10, f"User:", 0, 1, 'L')
            else:
                pdf.set_text_color(0, 0, 0) # --- Black ---
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(0, 10, f"Assistant:", 0, 1, 'L')

            # --- Reset font for body ---
            pdf.set_font("Arial", size=11)
            pdf.set_text_color(50, 50, 50)
            
            # --- Use multi_cell for text wrapping -- Handle potential encoding issues by replacing characters fpdf doesn't like ---
            safe_content = content.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 7, safe_content)
            pdf.ln(5)

    # --- Return PDF as bytes ---
    return bytes(pdf.output())