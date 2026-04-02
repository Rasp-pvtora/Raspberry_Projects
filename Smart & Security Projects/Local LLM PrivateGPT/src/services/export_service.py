"""CSV export of Q&A history."""

import csv
import io
from typing import List

from src.services.db import get_connection


class ExportService:
    """Export conversations and messages to CSV."""

    @staticmethod
    def export_qa_history(start_date: str | None = None, end_date: str | None = None) -> str:
        """Return CSV content as a string.  Optional date-range filter."""
        query = """
            SELECT
                m.created_at   AS timestamp,
                m.role         AS role,
                m.content      AS content,
                m.model_used   AS model,
                m.citations    AS citations,
                c.title        AS conversation_title
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            WHERE 1=1
        """
        params: List[str] = []
        if start_date:
            query += " AND m.created_at >= ?"
            params.append(start_date)
        if end_date:
            query += " AND m.created_at <= ?"
            params.append(end_date)
        query += " ORDER BY m.created_at ASC"

        with get_connection() as conn:
            rows = conn.execute(query, params).fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "role", "content", "model", "citations", "conversation"])
        for row in rows:
            writer.writerow([row["timestamp"], row["role"], row["content"],
                             row["model"], row["citations"], row["conversation_title"]])
        return output.getvalue()
