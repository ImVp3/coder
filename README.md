# Code Assistant Project

A code generation and documentation management system that leverages AI to assist developers in their coding workflow.

## 🚀 Features


## 📋 Todo list
### ✅ Completed
- [x] Code Generation Graph
- [x] Demo with gradio

### ⏳ In Progress
- [ ] Build Overall Graph
### 🗓️ Planned
- [ ] Codebase embeddings
- [ ] Backend Development with FastAPI
- [ ] Integrate the Agent.

## 🛠️ Technical Stack

- **Backend**: FastAPI
- **Frontend**: Undecided
- **LLM**: API from gemini or GPT
- **RAG**: LangChain, Langgraph

## 📁 Project Structure

```
.
├── src/                # Source code
│   ├── app.py         # Main application entry
│   ├── core/          # Core functionality
│   ├── demo/          # Demo implementations
│   ├── app/           # Application modules
│   └── test/          # Test files
├── data/              # Data files
├── docs/              # Documentation
├── requirements.txt   # Python dependencies
└── .env              # Environment variables
```

## 🔧 Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd code-assistant
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory and add your OpenAI/Google API key:
```
OPENAI_API_KEY= ...
GOOGLE_API_KEY ...
```

## 🚀 Quick Start

1. Start the application:
```bash
python src/app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (typically http://localhost:7860)


## 📝 Notes

- The project is currently using Gradio for the interface but is in the process of transitioning to a client-server/MTV architecture
- Make sure you have a valid OpenAI/Google API key before running the application
- The code generation workflow includes multiple steps: generation, checking, reflection, and decision making
