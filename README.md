# AuxoAI Financial Analyst Chatbot

A genuinely intelligent financial analyst chatbot built for the AuxoAI engineering take-home assignment. It uses a Hybrid RAG architecture to answer complex, multi-document financial queries accurately.

## Key Features
- **Hybrid Retrieval**: Combines Gemini dense embeddings with BM25 sparse retrieval (using Reciprocal Rank Fusion) for both semantic understanding and exact figure/ticker matching.
- **Dynamic Output Routing**: Automatically determines if an answer is best presented as a chat message (Markdown), a professional PDF report, or an Excel sheet.
- **Context-Aware Memory**: Handles follow-up questions intelligently.
- **Source Citations**: Every claim is backed by document and page citations.
- **Table-Aware Chunking**: Uses `pymupdf` and `pandas` to keep financial tables intact during chunking.

## Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd auxo-ai
   ```

2. **Set up the virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Environment Variables**:
   Create a `.env` file in the root directory (use `.env.example` as a template) and add your free Gemini API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

4. **Add Data Documents**:
   Place the required Infosys documents into the `data/` directory:
   - `infosys-ar-25.pdf`
   - `ifrs-usd-press-release_q1.pdf` ... `q4.pdf`
   - `investor-sheet.xlsx`
   - `500209.csv`

## Running the Chatbot

Start the interactive CLI:
```bash
python main.py
```

The system will ingest the documents, index them into ChromaDB, and build the BM25 index. Once ready, you can start asking questions!

## Generated Outputs
Any dynamically generated PDF reports or Excel sheets will be saved in the `output/` directory.

## Sample Conversations
See the `sample_conversations/` directory for examples of the chatbot generating PDF reports and Excel sheets.
