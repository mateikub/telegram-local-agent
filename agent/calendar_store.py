from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class Appointment:
    id: int
    title: str
    starts_at: str
    notes: str
    created_at: str


class CalendarStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def init(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                create table if not exists appointments (
                    id integer primary key autoincrement,
                    title text not null,
                    starts_at text not null,
                    notes text not null default '',
                    created_at text not null
                );
                """
            )

    def add(self, title: str, starts_at: str, notes: str = "") -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as connection:
            cursor = connection.execute(
                """
                insert into appointments (title, starts_at, notes, created_at)
                values (?, ?, ?, ?)
                """,
                (title.strip(), starts_at.strip(), notes.strip(), now),
            )
            return int(cursor.lastrowid)

    def upcoming(self, limit: int = 20) -> list[Appointment]:
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as connection:
            rows = connection.execute(
                """
                select id, title, starts_at, notes, created_at
                from appointments
                where starts_at >= ?
                order by starts_at
                limit ?
                """,
                (now, limit),
            ).fetchall()
        return [
            Appointment(
                row["id"],
                row["title"],
                row["starts_at"],
                row["notes"],
                row["created_at"],
            )
            for row in rows
        ]

    def delete(self, appointment_id: int) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                "delete from appointments where id = ?", (appointment_id,)
            )
            return cursor.rowcount > 0
