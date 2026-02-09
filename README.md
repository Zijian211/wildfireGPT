# 🔥 WildfireGPT - AI-Powered Wildfire Risk Assessment Platform

WildfireGPT is a comprehensive AI-powered consultation platform designed to provide specialized wildfire risk assessments for various professional personas. Built with **Streamlit** and **Python**, it features a sophisticated "Hybrid AI" architecture that adapts to different user roles and provides context-aware recommendations.

## 🚀 Key Features

### 🔐 1. Professional Role-Based System
* **Multi-Persona Support:** 7 specialized professional roles with tailored AI responses
* **Role-Specific Focus:** Each persona has customized system prompts and risk assessment priorities
* **Smart Context Switching:** Maintains conversation history when switching between roles
* **Real-time Adaptation:** AI adjusts responses based on selected profession and operation mode

### 👥 2. User Management System
* **Secure Authentication:** Complete sign-up and login functionality with password hashing (Bcrypt)
* **Session Management:** Auto-saves chat history and restores sessions upon login
* **Security Questions:** Account recovery with customizable security questions
* **Admin Dashboard:** Comprehensive user management and system monitoring tools

### 📊 3. Advanced AI Capabilities
* **Persona-Aware Responses:** AI adapts language and focus areas based on selected role
* **Document Analysis:** Upload and analyze PDF, DOCX, CSV, and TXT files for context
* **Location Intelligence:** Interactive map integration for geographical risk assessment
* **Hybrid AI Engine:**
  * **Local Mode:** Connects to **LM Studio** for offline, private use
  * **Cloud Mode:** Automatically switches to **Groq API** (Llama 3) when deployed

### 🧪 4. Testing & Evaluation Framework
* **Automated Persona Testing:** Comprehensive test suite for all professional roles
* **Scenario-Based Testing:** Pre-defined test cases for each persona
* **Performance Metrics:** Aspect coverage analysis and response quality assessment
* **Admin Testing Interface:** Built-in testing dashboard for quality assurance

### 📄 5. Professional Reporting
* **PDF Export:** Generate formatted consultation reports with one click
* **Chat History:** Complete conversation logging and session management
* **Evaluation Reports:** Detailed test performance analysis for system improvement

## 👥 Professional Personas Supported

| Persona | Focus Areas | Use Case |
|---------|------------|----------|
| 👨‍🚒 **Emergency Commander (Gov)** | Evacuation planning, Resource allocation, Public safety | Government emergency response |
| 🛡️ **Insurance Risk Assessor** | Financial exposure, Policy analysis, Risk mitigation | Insurance industry risk assessment |
| ⚡ **Power Grid Operator** | Infrastructure vulnerability, PSPS protocols, Grid resilience | Utility company operations |
| 🚚 **Logistics Manager** | Supply chain disruption, Route planning, Inventory management | Transportation and logistics |
| 🏗️ **Real Estate Developer** | Building codes, Material costs, Compliance requirements | Construction and development |
| 🏞️ **Park Ranger / Tourism** | Visitor safety, Park closures, Economic impact | Tourism and park management |
| 🎓 **Other Careers** | Custom role adaptation, General risk assessment | Researchers, Students, etc. |

## 🛠️ Technical Architecture

### Core Components
src/
├── assistants/ # AI assistant implementations
├── modules/
│ ├── account/ # Authentication & user management
│ ├── admin/ # Admin dashboard components
│ ├── database/ # Session and profile management
│ └── ui/ # User interface components
├── test_scenarios/ # Automated testing framework
└── evaluation/ # System evaluation tools

text

### Key Technologies
* **Frontend:** Streamlit with custom UI components
* **Backend:** Python 3.10+ with async support
* **AI Integration:** OpenAI-compatible API (Groq/LM Studio)
* **Data Processing:** Pandas, PyPDF2, python-docx
* **Security:** Bcrypt for password hashing
* **Reporting:** FPDF for PDF generation

## 📋 Installation & Setup

### Prerequisites
* Python 3.10+
* [Poetry](https://python-poetry.org/) (Recommended) or Pip

### 1. Clone the Repository
```bash
git clone https://github.com/Zijian211/wildfireGPT.git
cd wildfireGPT
2. Install Dependencies
bash
# Using Poetry (Recommended)
poetry install

# OR using pip
pip install -r requirements.txt
3. Configuration
bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings:
# - GROQ_API_KEY (for cloud mode)
# - Local LM Studio settings (for offline mode)
4. Run the Application
bash
# Development mode
streamlit run src/wildfireChat.py

# Or with poetry
poetry run streamlit run src/wildfireChat.py
🎯 Usage Guide
1. First-Time Setup
Register a new account or use admin credentials

Confirm location on the interactive map

Select your professional role from the sidebar

Choose operation mode (Checklist, Strategic Plan, Data Analysis, Dashboard)

2. Chat Interface
Ask questions related to your wildfire risk concerns

Upload documents for context-specific analysis

Switch personas at any time without losing conversation history

Generate reports of your consultation session

3. Admin Features
User Management: View and manage registered users

Chat Inspector: Review user sessions (safely anonymized)

System Evaluation: Run quality assessments on AI responses

AI Testing: Execute automated persona tests and view results

🔧 Development
Running Tests
bash
# Run all persona tests
python run_tests.py --persona all --output test_results.json

# Test specific persona
python run_tests.py --persona "🛡️ Insurance Risk Assessor"

# With verbose output
python run_tests.py --persona all --verbose
Project Structure
src/wildfireChat.py - Main application entry point

src/assistants/ - AI assistant implementations

src/modules/admin/ - Admin dashboard components

src/test_scenarios/ - Automated testing framework

run_tests.py - Command-line test runner

📈 Evaluation Metrics
The system tracks:

Response Relevance: How well answers match user roles and questions

Aspect Coverage: Percentage of expected focus areas addressed

Response Time: AI processing speed for different scenarios

Persona Accuracy: How well AI adapts to different professional roles

🚀 Deployment
Cloud Deployment (Streamlit Cloud)
Push code to GitHub repository

Connect to Streamlit Cloud

Set environment variables in cloud dashboard

Deploy with automatic scaling

Local Deployment
Configure .env file for local LM Studio

Run with streamlit run src/wildfireChat.py

Access at http://localhost:8501

📄 License
MIT License - see LICENSE file for details

🙏 Acknowledgements
Streamlit for the powerful web app framework

Groq API for high-performance AI inference

LM Studio for local AI model serving

OpenAI API compatibility layer for seamless integration

📞 Support
For issues, feature requests, or contributions:

Check the Issues page

Create a new issue with detailed description

Pull requests welcome for bug fixes and enhancements

Note: This project is for educational and research purposes. Always consult with certified wildfire safety professionals for critical safety decisions.

text

## Key Updates Made:

1. **Added Professional Personas Section** - Lists all 7 roles with their focus areas
2. **Enhanced Testing Framework Description** - Details about the automated testing system
3. **Updated Architecture** - Shows the new modular structure with admin and testing components
4. **Usage Guide** - More detailed instructions for different user types
5. **Development Section** - Includes test runner commands and project structure
6. **Evaluation Metrics** - Describes what the system tracks for quality assurance
7. **Persona-Specific Examples** - Shows how each role gets tailored responses

The README now accurately reflects:
- The persona-based system you implemented
- The admin testing interface
- The automated test runner
- The professional use cases
- The technical architecture with separate admin modules
