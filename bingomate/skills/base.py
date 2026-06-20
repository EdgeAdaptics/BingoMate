from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

from bingomate.skills.store import SkillDefinition, SkillStore


@dataclass(frozen=True)
class SkillResult:
    ok: bool
    message: str
    data: dict[str, object]


class Skill(Protocol):
    name: str
    description: str
    source: str
    requires_approval: bool

    def run(self, prompt: str, context: dict[str, object]) -> SkillResult:
        ...


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def unregister(self, name: str) -> None:
        self._skills.pop(name, None)

    def names(self) -> list[str]:
        return sorted(self._skills)

    def describe(self) -> list[dict[str, object]]:
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "source": getattr(skill, "source", "builtin"),
                "requires_approval": getattr(skill, "requires_approval", False),
            }
            for skill in sorted(self._skills.values(), key=lambda item: item.name)
        ]

    def run(self, name: str, prompt: str, context: dict[str, object] | None = None) -> SkillResult:
        if name not in self._skills:
            return SkillResult(False, f"Unknown skill: {name}", {})
        return self._skills[name].run(prompt, context or {})


class EchoSkill:
    name = "echo"
    description = "Development skill that returns the prompt and context."
    source = "builtin"
    requires_approval = False

    def run(self, prompt: str, context: dict[str, object]) -> SkillResult:
        return SkillResult(True, "echo complete", {"prompt": prompt, "context": context})


class ReminderDraftSkill:
    name = "reminder_draft"
    description = "Drafts a local reminder suggestion without scheduling it."
    source = "builtin"
    requires_approval = True

    def run(self, prompt: str, context: dict[str, object]) -> SkillResult:
        return SkillResult(
            True,
            "Reminder suggestion prepared; user approval is required before scheduling.",
            {"suggestion": prompt, "requires_user_approval": True},
        )


class TemplateSkill:
    source = "local-template"

    def __init__(self, definition: SkillDefinition) -> None:
        self.name = definition.name
        self.description = definition.description
        self.template = definition.template
        self.requires_approval = definition.requires_approval

    def run(self, prompt: str, context: dict[str, object]) -> SkillResult:
        context_json = json.dumps(context, default=str, sort_keys=True)
        output = self.template.replace("{prompt}", prompt).replace("{context}", context_json)
        return SkillResult(
            True,
            "Template skill prepared a local response.",
            {
                "output": output,
                "requires_user_approval": self.requires_approval,
                "source": self.source,
            },
        )


def build_default_registry(skill_store: SkillStore | None = None) -> SkillRegistry:
    registry = SkillRegistry()
    registry.register(EchoSkill())
    registry.register(ReminderDraftSkill())
    if skill_store:
        for definition in skill_store.list_template_skills():
            registry.register(TemplateSkill(definition))
    return registry
