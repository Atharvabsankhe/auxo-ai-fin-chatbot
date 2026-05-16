# Reflection

### 1. What makes your chatbot feel intelligent rather than just doing keyword search? What did you specifically do to get there?
The intelligence comes from three architectural decisions:
1.  **Format Routing Classifier**: Instead of a "one-size-fits-all" text response, a lightweight prompt acts as a router. It reads the user's intent and decides if the output should be Markdown, PDF, or Excel. This makes it feel like an analyst who understands *how* data should be presented, not just what the data is.
2.  **Hybrid Retrieval (BM25 + Dense)**: Pure dense retrieval fails at exact financial figures (e.g., distinguishing $1.2B from $1.4B). By fusing Gemini embeddings with BM25 via Reciprocal Rank Fusion (RRF), the system grasps semantic intent ("how is the company doing") while nailing keyword precision ("what was the EPS in Q2").
3.  **Table-Aware Ingestion**: Standard recursive character splitters destroy financial tables. The ingestion layer explicitly uses `pymupdf.find_tables()` to convert tables to Markdown before embedding, preserving the row/column context so the LLM can reason over tabular data.
4.  **Metadata Tagging**: Every chunk is tagged with its source, quarter, and page. The system prompt forces the LLM to cite these, which dramatically reduces hallucinations and anchors the answers in reality.

### 2. Where does it still fall short? What would a real analyst notice that your system gets wrong or misses?
-   **Currency Nuances**: A real analyst knows that the Infosys Annual Report might be reported in INR, while the `ifrs-usd` press releases are in USD. The current model might conflate these or fail to do exchange rate conversions unless explicitly prompted.
-   **Footnotes & Caveats**: Financial sheets have dense footnotes (e.g., "adjusted for one-time tax benefit"). The PDF table extractor often separates footnotes from the main table, meaning the LLM might miss critical context and report a GAAP vs Non-GAAP figure incorrectly.
-   **Cross-Sheet Mathematics**: While the LLM can read data, asking it to calculate a complex CAGR across 5 years from raw CSV chunks can lead to arithmetic hallucinations. A real analyst uses Excel for the math; the LLM tries to guess the math.

### 3. Which AI tools did you use to build this, and what did you have to fix or override yourself?
-   **Gemini 2.0 Flash (`google-generativeai`)**: Used for both embeddings (`text-embedding-004`) and generation. It's incredibly fast, which is necessary for the routing + generation pipeline.
-   **ChromaDB**: Used as the vector store for dense embeddings.
-   **Rank_BM25**: Used for the sparse retrieval index.
-   **What I had to override/build myself**:
    -   I had to build the **Reciprocal Rank Fusion (RRF)** logic manually to merge the ChromaDB distance scores with the BM25 BM25Okapi scores, as there's no native "hybrid search" box that does exactly what I wanted locally.
    -   I had to build the **Output Parser / Generator Router**. The LLM generates markdown strings, but I wrote the parsers (using Pandas/Regex for Excel and ReportLab for PDF) to intercept that markdown and convert it into downloadable files dynamically.
