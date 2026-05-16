import google.generativeai as genai
from typing import List, Dict
from src.config import GEMINI_API_KEY
import time

LLM_MODEL = "gemini-2.5-flash"


class LLMManager:
    """Handles format routing, context assembly, and answer generation."""

    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(LLM_MODEL)
        self.chat_history: list = []

    def determine_format(self, query: str) -> str:
        """Route the query to MARKDOWN, PDF, or EXCEL output format."""
        prompt = (
            "You are a routing assistant. Based on the user's query, decide the best output format.\n"
            "Options:\n"
            '- "MARKDOWN": For general questions, short tables, quick comparisons, or conversational answers.\n'
            '- "PDF": For comprehensive reports, multi-page summaries, long syntheses, or risk factor analyses.\n'
            '- "EXCEL": For heavy numerical data, large multi-year P&L tables, stock price history, or extensive data comparisons.\n\n'
            f"User Query: {query}\n\n"
            "Respond with exactly ONE word: MARKDOWN, PDF, or EXCEL."
        )
        for attempt in range(3):
            try:
                response = self.model.generate_content(prompt)
                choice = response.text.strip().upper().replace(".", "")
                if choice in ("MARKDOWN", "PDF", "EXCEL"):
                    return choice
                return "MARKDOWN"
            except Exception as e:
                if "429" in str(e):
                    time.sleep(10)
                else:
                    print(f"Format routing error: {e}")
                    return "MARKDOWN"
        return "MARKDOWN"

    def construct_context(self, chunks: List[Dict]) -> str:
        """Build the context block from retrieved chunks."""
        if not chunks:
            return "No relevant context was found in the documents."

        parts = ["Here is the relevant information retrieved from the Infosys documents:\n"]
        for i, item in enumerate(chunks):
            meta = item.get("metadata", {})
            source = meta.get("source", "Unknown")
            page = meta.get("page", "N/A")
            chunk_type = meta.get("type", "text")
            quarter = meta.get("quarter", "N/A")
            content = item.get("content", "")

            parts.append(f"--- Chunk {i + 1} ---")
            parts.append(f"Source: {source} | Page: {page} | Type: {chunk_type} | Quarter: {quarter}")
            parts.append(content)
            parts.append("")

        return "\n".join(parts)

    def generate_answer(self, query: str, chunks: List[Dict], output_format: str) -> str:
        """Generate the final answer using retrieved context and chat history."""
        context = self.construct_context(chunks)

        system_prompt = (
            "You are an expert Financial Analyst for Infosys.\n"
            "You must answer the user's query based ONLY on the provided context.\n"
            'If the context does not contain the answer, explicitly say "I do not have enough '
            'information to answer that based on the provided documents."\n\n'
            "CRITICAL RULES:\n"
            "1. ALWAYS cite your sources at the end of each claim in the format: [Source: filename, Page X].\n"
            "2. Pay close attention to quarters and financial years (FY25 vs FY26, Q1 vs Q2).\n"
            "3. Maintain a professional, knowledgeable tone.\n"
            "4. If currency is mentioned, note whether it is USD or INR.\n\n"
            f"The output format is: {output_format}\n"
            "If EXCEL, structure your response as a clean Markdown table with headers.\n"
            "If PDF, provide a well-structured Markdown report with # headings and ## sub-headings.\n"
            "If MARKDOWN, provide a concise, well-formatted response.\n"
        )

        history_str = self._get_history_str()
        prompt = f"{system_prompt}\n\nContext:\n{context}\n\nConversation History:\n{history_str}\n\nUser Query: {query}"

        for attempt in range(3):
            try:
                response = self.model.generate_content(prompt)
                answer = response.text

                # Update history
                self.chat_history.append({"role": "user", "parts": [query]})
                self.chat_history.append({"role": "model", "parts": [answer]})

                # Keep history manageable (last 5 exchanges = 10 items)
                if len(self.chat_history) > 10:
                    self.chat_history = self.chat_history[-10:]

                return answer
            except Exception as e:
                if "429" in str(e):
                    time.sleep(15)
                else:
                    print(f"Generation error: {e}")
                    return "I encountered an error generating the response. Please try again."
        return "I was unable to generate a response due to API rate limits. Please wait a moment and try again."

    def _get_history_str(self) -> str:
        if not self.chat_history:
            return "No previous conversation."
        parts = []
        for turn in self.chat_history[-6:]:  # Last 3 exchanges
            role = turn["role"].capitalize()
            text = turn["parts"][0]
            # Truncate long history entries
            if len(text) > 500:
                text = text[:500] + "..."
            parts.append(f"{role}: {text}")
        return "\n".join(parts)
