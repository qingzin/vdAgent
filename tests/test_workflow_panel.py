import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt5")
from PyQt5.QtWidgets import QApplication

from agent.workflow_panel import WorkflowPanel


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication(sys.argv)
    return instance


def template():
    return {
        "id": "demo",
        "name": "Demo",
        "description": "demo flow",
        "vehicle": "Car A",
        "front_spring": "Spring F",
        "rear_spring": "Spring R",
        "front_damper": "Damper F",
        "rear_damper": "Damper R",
        "front_antiroll_bar": "Bar F",
        "rear_antiroll_bar": "Bar R",
        "procedures": ["角阶跃", "稳态回转"],
        "plot_channels": ["roll", "pitch"],
        "report": {"enabled": True},
        "keep_final_configuration": False,
    }


def test_workflow_panel_tracks_stage_state_and_summary(app, tmp_path):
    panel = WorkflowPanel()

    panel.start_workflow("Demo", "demo flow", template())
    panel.update_stage(
        "run_simulation",
        title="执行仿真",
        status="running",
        message="Demo | 1/2 角阶跃",
        progress=60,
        payload={"current_procedure": "角阶跃", "result_folder": str(tmp_path)},
    )

    assert panel.stage_states["run_simulation"] == "running"
    assert panel.progress_bar.value() == 60
    assert "前/后阻尼: Damper F / Damper R" in panel.summary_text.toPlainText()
    assert "当前工况: 角阶跃" in panel.summary_text.toPlainText()
    assert panel.open_result_btn.isEnabled() is True


def test_workflow_panel_finish_enables_report_button(app, tmp_path):
    panel = WorkflowPanel()
    report = tmp_path / "report.docx"
    report.write_text("mock", encoding="utf-8")

    panel.start_workflow("Demo", "demo flow", template())
    panel.finish_workflow(
        True,
        "done",
        {"result_folder": str(tmp_path), "report_path": str(report)},
    )

    assert panel.stage_states["complete"] == "done"
    assert panel.progress_bar.value() == 100
    assert panel.open_result_btn.isEnabled() is True
    assert panel.open_report_btn.isEnabled() is True
