from __future__ import annotations

from app.rag.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


def test_prompt_template_has_placeholders():
    prompt = USER_PROMPT_TEMPLATE.format(question="Q", context="C")
    assert "Question:" in prompt
    assert "Context:" in prompt
    assert "Q" in prompt
    assert "C" in prompt


def test_system_prompt_mentions_grounding_rule():
    assert "Use only the provided context" in SYSTEM_PROMPT
