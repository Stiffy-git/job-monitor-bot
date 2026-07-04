"""SQLite database for tracking posted vacancies."""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from scoring import score_vacancy


class VacancyDB:
    def __init__(self, db_path: str = "vacancies.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS vacancies (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                company TEXT,
                url TEXT,
                salary TEXT,
                city TEXT,
                remote INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                posted_at TIMESTAMP,
                found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                shown_at TIMESTAMP,
                shown_today INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

    def exists(self, vacancy_id: str) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM vacancies WHERE id = ?", (vacancy_id,)
        )
        return cur.fetchone() is not None

    def mark_found(self, vacancy_id: str, source: str, title: str,
                   company: str, url: str, salary: str, city: str,
                   remote: bool = False, posted_at: Optional[str] = None):
        if self.exists(vacancy_id):
            return False

        vacancy_dict = {
            "title": title,
            "company": company,
            "salary": salary,
            "remote": remote,
            "source": source,
        }
        score = score_vacancy(vacancy_dict)

        self.conn.execute(
            """INSERT INTO vacancies
               (id, source, title, company, url, salary, city, remote, score, posted_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (vacancy_id, source, title, company, url, salary, city,
             1 if remote else 0, score, posted_at)
        )
        self.conn.commit()
        return True

    def mark_shown(self, vacancy_ids: list[str]):
        """Mark vacancies as shown today."""
        now = datetime.now().isoformat()
        for vid in vacancy_ids:
            self.conn.execute(
                "UPDATE vacancies SET shown_at = ?, shown_today = 1 WHERE id = ?",
                (now, vid)
            )
        self.conn.commit()

    def reset_daily_shown(self):
        """Reset shown_today flag (call at midnight or new day)."""
        self.conn.execute("UPDATE vacancies SET shown_today = 0")
        self.conn.commit()

    def get_new_vacancies(self, limit: int = 30) -> list[dict]:
        """Get new vacancies not shown today, balanced across sources.

        Ensures each source gets fair representation.
        """
        sources = ['hh', 'superjob', 'habr', 'zarplata']
        result = []
        seen_ids = set()

        # First pass: pick top 2-3 from EACH source (guaranteed rotation)
        per_source_first = max(2, limit // (len(sources) + 1))
        for source in sources:
            cur = self.conn.execute(
                """SELECT id, source, title, company, url, salary, city, remote, score
                   FROM vacancies WHERE shown_today = 0
                   ORDER BY score DESC LIMIT ?""",
                (per_source_first,)
            )
            for row in cur.fetchall():
                if row[0] not in seen_ids:
                    result.append(row)
                    seen_ids.add(row[0])

        # Second pass: fill remaining evenly from each source
        if len(result) < limit:
            remaining = limit - len(result)
            per_source_fill = max(1, remaining // len(sources))
            extra = remaining - (per_source_fill * len(sources))

            for i, source in enumerate(sources):
                n = per_source_fill + (1 if i < extra else 0)
                placeholders = ','.join('?' * len(seen_ids)) if seen_ids else 'NULL'
                query = f"""
                    SELECT id, source, title, company, url, salary, city, remote, score
                    FROM vacancies WHERE shown_today = 0 AND source = ?
                    AND id NOT IN ({placeholders})
                    ORDER BY score DESC LIMIT ?
                """
                params = [source] + list(seen_ids) + [n] if seen_ids else [source, n]
                cur = self.conn.execute(query, params)
                for row in cur.fetchall():
                    if row[0] not in seen_ids and len(result) < limit:
                        result.append(row)
                        seen_ids.add(row[0])

        return result[:limit]

    def get_today_shown(self) -> list:
        """Get all vacancies shown today."""
        cur = self.conn.execute(
            """SELECT id, source, title, company, url, salary, city, remote, score
               FROM vacancies WHERE shown_today = 1
               ORDER BY score DESC"""
        )
        return cur.fetchall()

    def get_stats(self):
        cur = self.conn.execute(
            "SELECT COUNT(*), SUM(CASE WHEN shown_at IS NOT NULL THEN 1 ELSE 0 END) FROM vacancies"
        )
        total, shown = cur.fetchone()
        return {
            "total": total or 0,
            "shown": shown or 0,
            "pending": (total or 0) - (shown or 0)
        }

    def get_source_stats(self):
        cur = self.conn.execute(
            """SELECT source, COUNT(*), AVG(score)
               FROM vacancies GROUP BY source"""
        )
        return cur.fetchall()

    def cleanup_old(self, days: int = 30):
        self.conn.execute(
            """DELETE FROM vacancies
               WHERE found_at < datetime('now', ?)""",
            (f"-{days} days",)
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
