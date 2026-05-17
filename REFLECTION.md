# Reflection

### 1. What makes your chatbot feel intelligent rather than just doing keyword search? What did you specifically do to get there?
 Instead of just throwing text at an LLM, I built a hybrid search system. It uses ChromaDB for the "vibes" (semantic meaning) and BM25 for the exact keyword matches (like finding specific numbers), and then squishes them together using Reciprocal Rank Fusion (RRF). 

On top of that, it doesn't just spit out a boring chat message. It actually *thinks* about what you're asking and routes the output to an Excel file or a polished PDF report if you ask for data or a summary! I even built a lightning-fast rule-based router so it feels instant.

### 2. Where does it still fall short? What would a real analyst notice that your system gets wrong or misses?
A real Wall Street analyst would probably catch it slipping on currency conversions. Infosys reports in INR, but the press releases are in USD, and sometimes the LLM might get confused if it doesn't pay super close attention to the symbols. 

Also, LLMs are historically pretty terrible at math! If you ask it to calculate a complex 5-year CAGR from raw data, it might hallucinate a number instead of doing the actual arithmetic. Oh, and those tiny little footnotes at the bottom of financial tables? The PDF parser sometimes drops them, meaning the LLM might give you GAAP numbers when you actually wanted Non-GAAP!

### 3. Which AI tools did you use to build this, and what did you have to fix or override yourself?
I used Google's Gemini (via `google-generativeai`) for both the embeddings and the super-fast text generation, plus ChromaDB for the vector database. 

Use AntiGravity to build up my UI and took reccomendations from Claude and whenever i had doubts, i use to clearify it.

But honestly, I resolved this and planned the whole flow myself! I had to override a ton of stuff to make it production-ready. For example, I completely ripped out the standard blocking retry loops and built a "fail-fast" mechanism so the Render server wouldn't time out with 502 Bad Gateway errors. I also had to custom-build the entire RRF hybrid logic, serialize the BM25 index to a pickle file for instant 0-second boot times, and write custom Regex/Pandas parsers to intercept the LLM's markdown and turn it into downloadable Excel sheets!
