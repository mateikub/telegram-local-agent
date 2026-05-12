from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class Memory:
    id: int
    content: str
    created_at: str


class MemoryStore:
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
                create table if not exists memories (
                    id integer primary key autoincrement,
                    content text not null,
                    created_at text not null
                );
                """
            )

    def add(self, content: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as connection:
            cursor = connection.execute(
                "insert into memories (content, created_at) values (?, ?)",
                (content.strip(), now),
            )
            return int(cursor.lastrowid)

    def recent(self, limit: int = 20) -> list[Memory]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                select id, content, created_at
                from memories
                order by id desc
                limit ?
                """,
                (limit,),
            ).fetchall()
        return [Memory(row["id"], row["content"], row["created_at"]) for row in rows]
