from __future__ import annotations

import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SKILL_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,63}$")


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    description: str
    template: str
    requires_approval: bool
    enabled: bool
    created_at: float
    updated_at: float


class SkillStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    def init(self) -> None:
        conn = sqlite3.connect(self.path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS template_skills (
                    name TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    template TEXT NOT NULL,
                    requires_approval INTEGER NOT NULL,
                    enabled INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def add_template_skill(
        self,
        name: str,
        description: str,
        template: str,
        requires_approval: bool = True,
    ) -> SkillDefinition:
        normalized_name = validate_skill_name(name)
        clean_description = description.strip()
        clean_template = template.strip()
        if not clean_description:
            raise ValueError("Skill description is required.")
        if not clean_template:
            raise ValueError("Skill template is required.")

        now = time.time()
        definition = SkillDefinition(
            name=normalized_name,
            description=clean_description,
            template=clean_template,
            requires_approval=requires_approval,
            enabled=True,
            created_at=now,
            updated_at=now,
        )
        conn = sqlite3.connect(self.path)
        try:
            conn.execute(
                """
                INSERT INTO template_skills
                    (name, description, template, requires_approval, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    definition.name,
                    definition.description,
                    definition.template,
                    1 if definition.requires_approval else 0,
                    1 if definition.enabled else 0,
                    definition.created_at,
                    definition.updated_at,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Skill already exists: {definition.name}") from exc
        finally:
            conn.close()
        return definition

    def list_template_skills(self, enabled_only: bool = True) -> list[SkillDefinition]:
        conn = sqlite3.connect(self.path)
        try:
            if enabled_only:
                rows = conn.execute(
                    """
                    SELECT name, description, template, requires_approval, enabled, created_at, updated_at
                    FROM template_skills
                    WHERE enabled = 1
                    ORDER BY name ASC
                    """
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT name, description, template, requires_approval, enabled, created_at, updated_at
                    FROM template_skills
                    ORDER BY name ASC
                    """
                ).fetchall()
        finally:
            conn.close()
        return [row_to_skill_definition(row) for row in rows]

    def get(self, name: str) -> SkillDefinition | None:
        conn = sqlite3.connect(self.path)
        try:
            row = conn.execute(
                """
                SELECT name, description, template, requires_approval, enabled, created_at, updated_at
                FROM template_skills
                WHERE name = ?
                """,
                (name,),
            ).fetchone()
        finally:
            conn.close()
        return row_to_skill_definition(row) if row else None

    def delete(self, name: str) -> bool:
        conn = sqlite3.connect(self.path)
        try:
            cursor = conn.execute("DELETE FROM template_skills WHERE name = ?", (name,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()


def validate_skill_name(name: str) -> str:
    normalized = name.strip().lower().replace("-", "_")
    if not SKILL_NAME_PATTERN.fullmatch(normalized):
        raise ValueError("Skill name must match ^[a-z][a-z0-9_]{2,63}$.")
    return normalized


def row_to_skill_definition(row: tuple[Any, ...]) -> SkillDefinition:
    name, description, template, requires_approval, enabled, created_at, updated_at = row
    return SkillDefinition(
        name=str(name),
        description=str(description),
        template=str(template),
        requires_approval=bool(requires_approval),
        enabled=bool(enabled),
        created_at=float(created_at),
        updated_at=float(updated_at),
    )
