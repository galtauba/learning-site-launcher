from pathlib import Path
from launcher.editor.runner import launch_editor_process


def test_development_editor_process_can_find_launcher_package():
    fixture = Path(__file__).parents[1] / "fixtures" / "editor_success"
    result = launch_editor_process(fixture)
    assert result.exit_code == 0, result.stderr
    assert "editor fixture completed" in result.stdout
