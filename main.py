import os
import glob
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from src.config import Config
from src.ingestion.loaders import PDFLoader, ExcelLoader
from src.retrieval.vector_store import VectorStore
from src.retrieval.hybrid_search import HybridRetriever
from src.core.llm_manager import LLMManager
from src.generators.pdf_generator import PDFGenerator
from src.generators.excel_generator import ExcelGenerator

console = Console()


class AnalystChatbot:
    def __init__(self):
        console.print("[dim]Initializing vector store...[/dim]")
        self.vector_store = VectorStore()
        self.retriever = HybridRetriever(self.vector_store)
        self.llm = LLMManager()
        self.pdf_gen = PDFGenerator()
        self.excel_gen = ExcelGenerator()

    def ingest_documents(self):
        console.print("\n[bold green]📄 Loading documents...[/bold green]")
        chunks = []

        # Load PDFs
        pdf_files = sorted(glob.glob(os.path.join(Config.DATA_DIR, "*.pdf")))
        for pdf_path in pdf_files:
            name = os.path.basename(pdf_path)
            console.print(f"  Processing [cyan]{name}[/cyan]")
            loader = PDFLoader(pdf_path)
            new_chunks = loader.load_and_chunk()
            console.print(f"    → {len(new_chunks)} chunks extracted")
            chunks.extend(new_chunks)

        # Load Excel (.xlsx, .xls) and CSV
        data_files = (
            sorted(glob.glob(os.path.join(Config.DATA_DIR, "*.xlsx")))
            + sorted(glob.glob(os.path.join(Config.DATA_DIR, "*.xls")))
            + sorted(glob.glob(os.path.join(Config.DATA_DIR, "*.csv")))
        )
        for sheet_path in data_files:
            name = os.path.basename(sheet_path)
            console.print(f"  Processing [cyan]{name}[/cyan]")
            loader = ExcelLoader(sheet_path)
            new_chunks = loader.load_and_chunk()
            console.print(f"    → {len(new_chunks)} chunks extracted")
            chunks.extend(new_chunks)

        if not chunks:
            console.print("[bold red]No documents found in data/ directory.[/bold red]")
            return

        console.print(f"\n[bold green]🔗 Indexing {len(chunks)} chunks (this may take a few minutes)...[/bold green]")
        self.retriever.index_chunks(chunks)
        console.print("[bold green]✅ Ready! Start asking questions.[/bold green]\n")

    def chat_loop(self):
        console.print(Panel.fit(
            "  Infosys Financial Analyst Chatbot  ",
            border_style="blue",
            subtitle="Type 'exit' to quit",
        ))

        while True:
            try:
                query = Prompt.ask("\n[bold cyan]You[/bold cyan]")
            except (KeyboardInterrupt, EOFError):
                break

            if query.strip().lower() in ("exit", "quit", "q"):
                console.print("[dim]Goodbye![/dim]")
                break

            if not query.strip():
                continue

            with console.status("[bold green]Thinking...[/bold green]"):
                # 1. Determine output format
                format_choice = self.llm.determine_format(query)
                console.print(f"[dim]Format: {format_choice}[/dim]")

                # 2. Retrieve relevant context
                retrieved_chunks = self.retriever.search(query, top_k=5)

                # 3. Generate answer
                answer = self.llm.generate_answer(query, retrieved_chunks, format_choice)

            # 4. Route output
            if format_choice == "PDF":
                console.print(Panel(Markdown(answer), title="📊 Analyst Response", border_style="green"))
                pdf_path = self.pdf_gen.generate(answer)
                console.print(f"\n[bold yellow]📄 PDF Report saved:[/bold yellow] {pdf_path}")

            elif format_choice == "EXCEL":
                console.print(Panel(Markdown(answer), title="📊 Analyst Response", border_style="green"))
                excel_path = self.excel_gen.generate(answer)
                console.print(f"\n[bold yellow]📊 Excel Sheet saved:[/bold yellow] {excel_path}")

            else:
                console.print(Panel(Markdown(answer), title="📊 Analyst Response", border_style="green"))

    def chat(self, query: str) -> dict:
        """Programmatic interface for the API to interact with the chatbot."""
        format_choice = self.llm.determine_format(query)
        retrieved_chunks = self.retriever.search(query, top_k=3)
        answer = self.llm.generate_answer(query, retrieved_chunks, format_choice)

        result = {"answer": answer, "format": format_choice, "file_path": None}
        if format_choice == "PDF":
            result["file_path"] = self.pdf_gen.generate(answer)
        elif format_choice == "EXCEL":
            result["file_path"] = self.excel_gen.generate(answer)

        return result


if __name__ == "__main__":
    bot = AnalystChatbot()
    bot.ingest_documents()
    bot.chat_loop()
