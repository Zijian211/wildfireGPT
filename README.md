# 🔥 WildfireGPT - Intelligent Fire Safety Consultant

**WildfireGPT** is an AI-powered consultation tool designed to assist homeowners and safety inspectors with wildfire risk assessment, evacuation planning, and property hardening. 

Built with **Streamlit** and **Python**, it features a robust "Hybrid AI" architecture that runs offline (for privacy) or on the Cloud (for deployment) without changing code.

## 🚀 Key Features

### 🔐 1. Secure Authentication System
* **User Accounts:** Complete Sign-up and Login functionality.
* **Security:** Passwords are hashed and salted using **Bcrypt** (Industry Standard).
* **Session Management:** Users remain logged in during their session.
* **Admin Dashboard:** Special admin access to view users and manage database.

### 📄 2. Professional Reporting
* **PDF Export:** Users can download a formatted "Consultation Report" of their chat session with one click.
* **Chat History:** Conversations are auto-saved to disk (JSONL format) and reloaded upon next login.

### 🧠 3. Advanced AI Capabilities (RAG)
* **Document Analysis:** Users can upload PDF documents (e.g., *Local Fire Codes*, *Insurance Policies*).
* **Context-Aware:** The AI ingests the document and answers questions specifically based on that file.
* **Hybrid Engine:** * **Local Mode:** Connects to **LM Studio** (Llama 3) for offline, private use.
    * **Cloud Mode:** Automatically switches to **Groq API** (Llama 3 8b) when deployed to the web.

---

## 🛠️ Installation & Setup

### Prerequisites
* Python 3.10+
* [Poetry](https://python-poetry.org/) (Recommended) or Pip

### 1. Clone the Repository
```bash
git clone [https://github.com/Zijian211/wildfireGPT.git)
cd wildfire-gpt
