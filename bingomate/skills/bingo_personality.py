"""Bingo personality skills for expressive, privacy-first assistance."""

from __future__ import annotations

import random

from bingomate.skills.base import SkillResult


BINGO_EXPRESSIONS = {
    "excitement": [
        "Bingo is ready.",
        "That is a solid step forward.",
        "Good signal; let us verify it.",
        "Nice progress.",
        "Systems look promising.",
    ],
    "curiosity": [
        "What changed in the lab?",
        "I want to inspect the signal path.",
        "Let us check the evidence.",
        "That is worth measuring.",
    ],
    "encouragement": [
        "You have a workable path.",
        "Keep the loop tight: observe, test, improve.",
        "This is the right kind of practical edge work.",
        "Small verified steps beat guesses.",
    ],
    "concern": [
        "I need permission before changing that.",
        "That action can affect hardware state.",
        "Let us make the safety boundary explicit.",
        "I need a confirmation before proceeding.",
    ],
    "success": [
        "Verified and ready.",
        "That check passed.",
        "The lab state improved.",
        "Result confirmed.",
    ],
    "celebration": [
        "Bingo has a clean win.",
        "That is demo-worthy.",
        "This is good portfolio material.",
        "Strong progress with evidence.",
    ],
}


class BingoExpressionSkill:
    """Returns concise Bingo expressions for dashboard and voice moments."""

    name = "bingo_express"
    description = "Adds Bingo expressions that stay clear, useful, and privacy-aware."
    source = "builtin"
    requires_approval = False

    def run(self, prompt: str, context: dict[str, object]) -> SkillResult:
        emotion = prompt.lower().strip()
        if emotion not in BINGO_EXPRESSIONS:
            expression = random.choice(BINGO_EXPRESSIONS["excitement"])
            return SkillResult(
                True,
                f"Expression type '{emotion}' not recognized; using excitement.",
                {"expression": expression, "emotion": emotion},
            )
        expression = random.choice(BINGO_EXPRESSIONS[emotion])
        return SkillResult(True, f"Bingo expression selected for {emotion}.", {"expression": expression, "emotion": emotion})


class BingoObservationSkill:
    """Generates warm but grounded observations about user progress."""

    name = "bingo_observe"
    description = "Makes useful observations about user progress, lab status, and achievements."
    source = "builtin"
    requires_approval = False

    def run(self, prompt: str, context: dict[str, object]) -> SkillResult:
        achievement_type = context.get("achievement_type", "progress") if context else "progress"
        observations = {
            "problem_solved": [
                "You closed a real engineering loop.",
                "The issue is now backed by evidence, not guesses.",
                "That was a practical debugging win.",
            ],
            "skill_learned": [
                "This is a reusable skill for the lab.",
                "You added a capability that compounds over time.",
                "That knowledge belongs in the playbook.",
            ],
            "code_written": [
                "The code path is now easier to demo and test.",
                "This implementation moves BingoMate closer to a real edge product.",
                "Good implementation work; now validate it on hardware.",
            ],
            "experiment_run": [
                "The experiment created useful evidence.",
                "Capture the result before changing variables.",
                "That is the right kind of repeatable lab work.",
            ],
            "progress": [
                "Progress is visible and testable.",
                "The lab setup is getting more useful.",
                "This can become strong industrial IoT portfolio work.",
            ],
        }
        observation_list = observations.get(str(achievement_type), observations["progress"])
        observation = random.choice(observation_list)
        return SkillResult(
            True,
            f"Bingo observation prepared for {achievement_type}.",
            {"observation": observation, "achievement_type": achievement_type, "input": prompt},
        )


class BingoHelpfulTipSkill:
    """Offers concise next-step framing for edge lab tasks."""

    name = "bingo_helpful_tip"
    description = "Offers practical tips and next-step framing for hardware, software, and demos."
    source = "builtin"
    requires_approval = False

    def run(self, prompt: str, context: dict[str, object]) -> SkillResult:
        tip_prefix = random.choice(
            [
                "Practical next step: ",
                "Best verification path: ",
                "Lowest-risk move: ",
                "Demo-focused improvement: ",
                "Hardware-safe approach: ",
            ]
        )
        return SkillResult(True, "Bingo prepared a practical tip.", {"tip_prefix": tip_prefix, "topic": prompt})


class BingoPrivacyAcknowledgmentSkill:
    """Acknowledges privacy and permission-sensitive actions."""

    name = "bingo_privacy_check"
    description = "Handles privacy and permission requests with explicit local-first language."
    source = "builtin"
    requires_approval = False

    def run(self, prompt: str, context: dict[str, object]) -> SkillResult:
        action_type = prompt.lower().strip()
        actions = {
            "delete": "Before deleting anything, confirm the target and backup state. This may be irreversible.",
            "access": "I will state exactly what I need to access and keep the data local unless you opt in.",
            "share": "Before sharing data, confirm the destination, content, and whether cloud assist is allowed.",
            "execute": "Before executing an action, confirm the command and expected hardware impact.",
            "modify": "Before modifying files or device state, confirm the exact scope.",
        }
        message = actions.get(action_type, actions["execute"])
        return SkillResult(
            True,
            f"Bingo privacy check prepared for {action_type}.",
            {"permission_request": message, "action_type": action_type},
        )
