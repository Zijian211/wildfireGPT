🔥 WildfireGPT

AI-Powered Wildfire Risk Assessment Platform

WildfireGPT is an AI-driven consultation platform that delivers role-specific wildfire risk assessments for professionals across emergency response, infrastructure, insurance, logistics, and land management.

Built with Streamlit + Python, it uses a Hybrid AI architecture to adapt responses based on professional context while supporting both cloud and offline local AI modes.

✨ Key Features
👤 Role-Based AI Personas

7 Professional Personas (Emergency, Insurance, Utilities, Logistics, Real Estate, Parks, General)

Context-aware language and recommendations

Switch roles without losing conversation history

🤖 Hybrid AI Engine

Local Mode: Offline & private inference via LM Studio

Cloud Mode: High-performance inference using Groq (Llama 3)

OpenAI-compatible API layer

📍 Location & Document Intelligence

Interactive map for geographic wildfire assessment

Upload and analyze PDF, DOCX, CSV, TXT

Context-aware insights based on uploaded data

🔒 User & Admin Management

Secure authentication (Bcrypt password hashing)

Persistent chat sessions

Account recovery via security questions

Admin dashboard for monitoring and evaluation

📄 Reporting & Export

Generate PDF consultation reports

Export chat histories

Evaluation & QA reports for AI performance

👥 Supported Personas
Persona	Focus Areas	Typical Use Case
👨‍🚒 Emergency Commander	Evacuation, resources, public safety	Government response
🛡️ Insurance Risk Assessor	Financial exposure, policy risk	Insurance industry
⚡ Power Grid Operator	Infrastructure, PSPS, resilience	Utilities
🚚 Logistics Manager	Route planning, supply chains	Transportation
🏗️ Real Estate Developer	Building codes, compliance	Construction
🏞️ Park Ranger / Tourism	Visitor safety, closures	Tourism & parks
🎓 Other Careers	Generalized risk analysis	Research & education
🏗️ Architecture Overview
src/
├── assistants/              # AI assistant logic
├── modules/
│   ├── account/             # Authentication & profiles
│   ├── admin/               # Admin dashboard
│   ├── database/            # Session storage
│   ├── ui/                  # Streamlit UI components
│   └ test_scenarios/          # Automated persona tests
└── evaluation/              # QA & evaluation tools
🧰 Technology Stack

Frontend: Streamlit

Backend: Python 3.10+

AI: Groq API / LM Studio (local)

Data Processing: Pandas, PyPDF2, python-docx

Security: Bcrypt

Reporting: FPDF

🚀 Getting Started
Prerequisites

Python 3.10+

Poetry (recommended) or pip

Installation
git clone https://github.com/Zijian211/wildfireGPT.git
cd wildfireGPT
Install dependencies
# Poetry (recommended)
poetry install


# OR pip
pip install -r requirements.txt
Configuration
cp .env.example .env

Edit .env:

GROQ_API_KEY (for cloud mode)

LM Studio settings (for local mode)

Run the App
streamlit run src/wildfireChat.py

or

poetry run streamlit run src/wildfireChat.py

Access at: http://localhost:8501

📖 Usage Guide
First-Time Users

Register or log in

Confirm location on the map

Select your professional persona

Choose operation mode:

Checklist

Strategic Planning

Data Analysis

Dashboard

Chat & Analysis

Ask wildfire-related questions

Upload documents for contextual analysis

Switch roles anytime

Export reports as PDF

Admin Dashboard

User management

Chat inspection (anonymized)

AI evaluation & testing

Persona performance analysis

🧪 Testing & Evaluation

Run automated persona tests:

# All personas
python run_tests.py --persona all


# Specific persona
python run_tests.py --persona "🛡️ Insurance Risk Assessor"


# Verbose mode
python run_tests.py --persona all --verbose
Metrics Tracked

Response relevance

Aspect coverage

Persona accuracy

Response time

🌐 Deployment
Streamlit Cloud

Push to GitHub

Connect repository to Streamlit Cloud

Set environment variables

Deploy 🚀

Local Deployment

Configure .env

Run via Streamlit or Poetry

📄 License

MIT License — see LICENSE

🙏 Acknowledgements

Streamlit

Groq API

LM Studio

OpenAI-compatible ecosystem

🤝 Contributing & Support

Check Issues for bugs or feature requests

Pull requests are welcome

Contributions that improve personas or evaluation are especially appreciated