# AuxoAI Financial Analyst Chatbot

A genuinely intelligent financial analyst chatbot built for the AuxoAI engineering take-home assignment. It uses a Hybrid RAG architecture to answer complex, multi-document financial queries accurately.

## 🚀 Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Atharvabsankhe/auxo-ai-fin-chatbot.git
   cd auxo-ai-fin-chatbot
   ```

2. **Setup Virtual Environment & Dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Environment Variables**:
   Create a `.env` file in the root directory and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

4. **Add Data Documents**:
   Place the required Infosys documents into the `data/` directory.

---

## 🖥️ Running the Application

### Option A: Modern Web Dashboard (Recommended)
This launches the FastAPI backend and the Vite-powered "ChatGPT-style" UI.

1. **Build the Frontend**:
   ```bash
   cd frontend && npm install && npm run build && cd ..
   ```

2. **Start the Unified Server**:
   ```bash
   source venv/bin/activate
   python api.py
   ```
   Now visit **`http://localhost:8000`** in your browser.

### Option B: Interactive CLI
For those who prefer the terminal:
```bash
python main.py
```

---

## 🏗️ Architecture
- **Hybrid Search**: Combines ChromaDB (semantic) and BM25 (keyword) using Reciprocal Rank Fusion (RRF).
- **Intelligent Routing**: LLM autonomously decides whether to output Markdown, PDF, or Excel based on user intent.
- **Resilient Ingestion**: SHA-256 content hashing prevents redundant indexing and API waste.

## 📄 Generated Outputs
Any dynamically generated PDF reports or Excel sheets will be accessible via the **Sidebar** in the Web UI or saved locally in the `output/` directory.

## 📈 Sample Conversations
See `sample_conversations/mock_conversations.md` for 6 detailed analyst scenarios.
