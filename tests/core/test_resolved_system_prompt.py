"""AgentConfig.system_prompt / system_prompt_path must override the default."""

from openjarvis.core.config import AgentConfig


def test_default_used_when_nothing_set():
    cfg = AgentConfig()
    assert cfg.resolved_system_prompt() == cfg.default_system_prompt


def test_inline_prompt_wins():
    cfg = AgentConfig(system_prompt="Tu es Jarvis.")
    assert cfg.resolved_system_prompt() == "Tu es Jarvis."


def test_prompt_file_used(tmp_path):
    f = tmp_path / "p.md"
    f.write_text("Réponds en français.", encoding="utf-8")
    cfg = AgentConfig(system_prompt_path=str(f))
    assert cfg.resolved_system_prompt() == "Réponds en français."


def test_missing_file_falls_back(tmp_path):
    cfg = AgentConfig(system_prompt_path=str(tmp_path / "absent.md"))
    assert cfg.resolved_system_prompt() == cfg.default_system_prompt
