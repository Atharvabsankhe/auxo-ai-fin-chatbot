import hashlib
import fitz  # PyMuPDF
import pandas as pd
from typing import List
import os
from src.models import DocumentChunk


class PDFLoader:
    """Loads PDFs using PyMuPDF with page-aware text and table extraction."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)

    def _detect_quarter(self) -> str | None:
        name = self.file_name.lower()
        if "q1" in name:
            return "Q1"
        elif "q2" in name:
            return "Q2"
        elif "q3" in name:
            return "Q3"
        elif "q4" in name:
            return "Q4"
        elif "ar" in name:
            return "FY"
        return None

    def load_and_chunk(self) -> List[DocumentChunk]:
        chunks = []
        doc = fitz.open(self.file_path)
        quarter = self._detect_quarter()

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            if text.strip():
                # Split large pages into ~3000 char chunks with overlap (reduces API calls)
                page_chunks = self._split_text(text.strip(), max_chars=3000, overlap=300)
                for chunk_text in page_chunks:
                    chunk_id = hashlib.sha256(chunk_text.encode()).hexdigest()
                    chunks.append(DocumentChunk(
                        id=chunk_id,
                        content=chunk_text,
                        source=self.file_name,
                        page=page_num + 1,
                        type="text",
                        quarter=quarter,
                    ))

            # Table extraction
            try:
                tables = page.find_tables()
                for table in tables:
                    df = table.to_pandas()
                    if df.empty:
                        continue
                    
                    # Split tables into smaller chunks of 5 rows each to stay under token limits
                    rows_per_chunk = 5
                    for i in range(0, len(df), rows_per_chunk):
                        sub_df = df.iloc[i : i + rows_per_chunk]
                        table_str = sub_df.to_markdown(index=False)
                        if table_str and len(table_str.strip()) > 10:
                            chunk_id = hashlib.sha256(table_str.encode()).hexdigest()
                            chunks.append(DocumentChunk(
                                id=chunk_id,
                                content=f"Table Data (Page {page_num + 1}):\n{table_str}",
                                source=self.file_name,
                                page=page_num + 1,
                                type="table",
                                quarter=quarter,
                            ))
            except Exception:
                pass

        doc.close()
        return chunks

    @staticmethod
    def _split_text(text: str, max_chars: int = 3000, overlap: int = 300) -> List[str]:
        """Split text into overlapping chunks at paragraph boundaries."""
        if len(text) <= max_chars:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + max_chars
            # Try to break at a paragraph boundary
            if end < len(text):
                newline_pos = text.rfind("\n", start + max_chars // 2, end)
                if newline_pos != -1:
                    end = newline_pos + 1
            chunks.append(text[start:end].strip())
            start = end - overlap
        return [c for c in chunks if c]


class ExcelLoader:
    """Loads Excel (.xlsx/.xls) and CSV files using Pandas."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)

    def load_and_chunk(self) -> List[DocumentChunk]:
        chunks = []

        if self.file_path.endswith(".csv"):
            chunks = self._load_csv()
        else:
            chunks = self._load_excel()

        return chunks

    def _load_csv(self) -> List[DocumentChunk]:
        chunks = []
        try:
            df = pd.read_csv(self.file_path)
        except Exception as e:
            print(f"Error reading CSV {self.file_name}: {e}")
            return chunks

        chunk_size = 50
        for i in range(0, len(df), chunk_size):
            sub_df = df.iloc[i : i + chunk_size]
            content = f"Stock price data from {self.file_name}:\n{sub_df.to_markdown(index=False)}"
            chunk_id = hashlib.sha256(content.encode()).hexdigest()
            chunks.append(DocumentChunk(
                id=chunk_id,
                content=content,
                source=self.file_name,
                page=None,
                type="data_row",
                quarter=None,
            ))
        return chunks

    def _load_excel(self) -> List[DocumentChunk]:
        chunks = []
        try:
            excel_file = pd.ExcelFile(self.file_path)
        except Exception as e:
            print(f"Error reading Excel {self.file_name}: {e}")
            return chunks

        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(self.file_path, sheet_name=sheet_name)
                if df.empty:
                    continue

                # For large sheets, chunk by rows
                chunk_size = 30
                if len(df) > chunk_size:
                    for i in range(0, len(df), chunk_size):
                        sub_df = df.iloc[i : i + chunk_size]
                        content = f"Sheet: {sheet_name} (rows {i+1}-{i+len(sub_df)})\n{sub_df.to_markdown(index=False)}"
                        chunk_id = hashlib.sha256(content.encode()).hexdigest()
                        chunks.append(DocumentChunk(
                            id=chunk_id,
                            content=content,
                            source=self.file_name,
                            page=None,
                            type="table",
                            quarter="Multi-Year",
                        ))
                else:
                    content = f"Sheet: {sheet_name}\n{df.to_markdown(index=False)}"
                    chunk_id = hashlib.sha256(content.encode()).hexdigest()
                    chunks.append(DocumentChunk(
                        id=chunk_id,
                        content=content,
                        source=self.file_name,
                        page=None,
                        type="table",
                        quarter="Multi-Year",
                    ))
            except Exception as e:
                print(f"Error reading sheet {sheet_name}: {e}")

        return chunks
