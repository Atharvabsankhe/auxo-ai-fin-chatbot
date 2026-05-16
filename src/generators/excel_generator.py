import os
import re
import pandas as pd
from src.config import Config
import uuid


class ExcelGenerator:
    """Converts LLM markdown table output into a formatted Excel file."""

    def __init__(self):
        self.output_dir = Config.OUTPUT_DIR

    def generate(self, content: str) -> str:
        """Extract markdown tables from content and write to Excel. Returns file path."""
        filename = f"{uuid.uuid4().hex[:8]}_data.xlsx"
        filepath = os.path.join(self.output_dir, filename)

        tables = self._extract_tables(content)

        if not tables:
            # Fallback: put raw text in a cell
            df = pd.DataFrame([{"Content": content}])
            df.to_excel(filepath, index=False)
            return filepath

        try:
            with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
                for idx, df in enumerate(tables):
                    sheet_name = f"Table_{idx + 1}" if len(tables) > 1 else "Data"
                    df.to_excel(writer, index=False, sheet_name=sheet_name)
        except Exception as e:
            print(f"Error writing Excel: {e}")
            df = pd.DataFrame([{"Raw Content": content}])
            df.to_excel(filepath, index=False)

        return filepath

    @staticmethod
    def _extract_tables(content: str) -> list:
        """Parse all markdown tables from the content into DataFrames."""
        lines = content.split("\n")
        tables = []
        i = 0

        while i < len(lines):
            # Find start of a table
            if lines[i].strip().startswith("|"):
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    table_lines.append(lines[i].strip())
                    i += 1

                df = ExcelGenerator._parse_table(table_lines)
                if df is not None and not df.empty:
                    tables.append(df)
            else:
                i += 1

        return tables

    @staticmethod
    def _parse_table(table_lines: list) -> pd.DataFrame | None:
        """Parse markdown table lines into a DataFrame."""
        data_rows = []
        for line in table_lines:
            # Skip separator rows like |---|---|
            if re.match(r"^\|[\s\-:|]+\|$", line):
                continue
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if cells:
                data_rows.append(cells)

        if len(data_rows) < 2:
            return None

        headers = data_rows[0]
        rows = data_rows[1:]

        # Ensure all rows have same number of columns as headers
        rows = [r + [""] * (len(headers) - len(r)) for r in rows]
        rows = [r[: len(headers)] for r in rows]

        return pd.DataFrame(rows, columns=headers)
