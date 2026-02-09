# 🔥 WildfireGPT AI  -- Powered Wildfire Risk Assessment Platform

WildfireGPT is an AI-driven consultation platform that delivers role-specific wildfire risk assessments for professionals across emergency response, infrastructure, insurance, logistics, and land management.

Built with Streamlit + Python, it uses a Hybrid AI architecture to adapt responses based on professional context while supporting both cloud and offline local AI modes.



# ✨ Key Features
## 👤 Role-Based AI Personas

* 7 Professional Personas (Emergency, Insurance, Utilities, Logistics, Real Estate, Parks, General)
* Context-aware language and recommendations
* Switch roles without losing conversation history



## 🤖 Hybrid AI Engine

* Local Mode: Offline \& private inference via LM Studio
* Cloud Mode: High-performance inference using Groq (Llama 3)
* OpenAI-compatible API layer



## 📍 Location \& Document Intelligence

* Interactive map for geographic wildfire assessment
* Upload and analyse PDF, DOCX, CSV, TXT
* Context-aware insights based on uploaded data



## 🔒 User \& Admin Management

* Secure authentication (Bcrypt password hashing)
* Persistent chat sessions
* Account recovery via security questions
* Admin dashboard for monitoring and evaluation



## 📄 Reporting \& Export

* Generate PDF consultation reports
* Export chat histories
* Evaluation \& QA reports for AI performance



# 👥 Supported Personas (Persona->Focus Areas->Typical Use Case)
* 👨‍🚒 Emergency Commander -> Evacuation, resources, public safety ->Government response
* 🛡️ Insurance Risk Assessor->Financial exposure, policy risk->Insurance industry
* ⚡ Power Grid Operator->Infrastructure, PSPS, resilience->Utilities
* 🚚 Logistics Manager	->Route planning, supply chains->Transportation
* 🏗️ Real Estate Developer->Building codes, compliance->Construction
* 🏞️ Park Ranger / Tourism->Visitor safety, closures->Tourism \& parks
* 🎓 Other Careers->Generalized risk analysis->Research \& education



# 🏗️ Architecture Overview
* src/assistants/             (AI assistant logic)
* src/modules/account/             (Authentication \& profiles)
* src/modules/account/admin/               (Admin dashboard)
* src/modules/database/            (Session storage)
* src/modules/ui/                  (Streamlit UI components)
* src/modules/test_scenarios/          (Automated persona tests)
* src/evaluation/              (QA \& evaluation tools)



# 🧰 Technology Stack

* Frontend: Streamlit
* Backend: Python 3.10+
* AI: Groq API / LM Studio (local)
* Data Processing: Pandas, PyPDF2, python-docx
* Security: Bcrypt
* Reporting: FPDF



# 🚀 Getting Started
## Prerequisites

* Python 3.10+
* Poetry (recommended) or pip



## Installation
```

git clone https://github.com/Zijian211/wildfireGPT.git
cd wildfireGPT

```


## Install dependencies

```

poetry install #--- Poetry (recommended) ---

pip install -r requirements.txt #--- OR pip ---

```


## Configuration

```
cp .env.example .env

```



## Edit .env:

* GROQ\_API\_KEY (for cloud mode)
* LM Studio settings (for local mode)



## Run the App

```
streamlit run src/wildfireChat.py

```



or

```

poetry run streamlit run src/wildfireChat.py

```

Access at: http://localhost:8501



# 📖 Usage Guide
# First-Time Users

1. Register or log in
2. Confirm location on the map
3. Select your professional persona
4. Choose operation mode:

* Checklist
* Strategic Planning
* Data Analysis
* Dashboard



## Chat \& Analysis

* Ask wildfire-related questions
* Upload documents for contextual analysis
* Switch roles anytime
* Export reports as PDF



## Admin Dashboard

* User management
* Chat inspection (anonymized)
* AI evaluation \& testing
* Persona performance analysis



# 🧪 Testing \& Evaluation
## Run automated persona tests:

```

python run\_tests.py --persona all # --- All personas ---

python run\_tests.py --persona "🛡️ Insurance Risk Assessor" # --- Specific persona ---

python run\_tests.py --persona all --verbose # --- Verbose mode ---

```


## Metrics Tracked

* Response relevance
* Aspect coverage
* Persona accuracy
* Response time



# 🌐 Deployment
## Streamlit Cloud

1. Push to GitHub
2. Connect repository to Streamlit Cloud
3. Set environment variables
4. Deploy 🚀



## Local Deployment

* Configure .env
* Run via Streamlit or Poetry



# 📄 License

MIT License — see LICENSE



# 🙏 Acknowledgements

* Streamlit
* Groq API
* LM Studio
* OpenAI-compatible ecosystem



# 🤝 Contributing \& Support

* Check Issues for bugs or feature requests
* Pull requests are welcome
* Contributions that improve personas or evaluation are especially appreciated
