import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent.actions import workflow_actions
from agent.registry import ActionRegistry
from agent.services.sim_test_report_service import SimTestReportService
from agent.services.workflow_template_service import (
    WorkflowTemplateError,
    WorkflowTemplateService,
)
import agent.services.sim_test_report_service as sim_report_module


class FakeSwitch:
    def __init__(self):
        self.checked = None

    def setChecked(self, value):
        self.checked = value


class FakeUi:
    def __init__(self):
        self.plot_switches = {"roll": FakeSwitch(), "pitch": FakeSwitch()}
        self.plot_layout_updated = False

    def update_plot_layout(self):
        self.plot_layout_updated = True


class FakeTuningService:
    def __init__(self):
        self.calls = []

    def select_vehicle(self, value):
        self.calls.append(("vehicle", value))

    def set_front_left_spring(self, value):
        self.calls.append(("front_spring", value))

    def set_rear_left_spring(self, value):
        self.calls.append(("rear_spring", value))

    def set_antiroll_bar(self, is_front, value):
        self.calls.append(("bar", is_front, value))


class FakeReportService:
    def __init__(self, tmp_path):
        self.tmp_path = tmp_path
        self.executed = None

    def available_procedures(self):
        return ["角阶跃", "稳态回转"]

    def default_output_root(self):
        return self.tmp_path / "reports"

    def check_environment(self, require_handproc=True):
        return True, "ok"

    def run_batch_from_template(self, template, progress=None):
        self.executed = template["id"]
        if progress:
            progress("执行仿真", "mock")
        return {
            "result_folder": str(self.tmp_path / "reports" / "run"),
            "report_path": str(self.tmp_path / "reports" / "run" / "report.docx"),
        }


class FakeCtx:
    def __init__(self, tmp_path):
        self.ui = FakeUi()
        self.tuning = FakeTuningService()
        self.report = FakeReportService(tmp_path)
        self.services = {
            "tuning": self.tuning,
            "sim_test_report": self.report,
        }

    def service(self, name):
        return self.services[name]

    def mod(self, name, default=None):
        maps = {
            "vehicleInfoDic": {"Car A": "1:<CAT>Car A"},
            "springInfoDic": {"Spring F": "", "Spring R": ""},
            "AuxMInfoDic": {"Bar F": "", "Bar R": ""},
            "MxTotInfoDic": {},
        }
        return maps.get(name, default)


def valid_template():
    return {
        "id": "demo",
        "name": "Demo",
        "description": "demo flow",
        "vehicle": "Car A",
        "front_spring": "Spring F",
        "rear_spring": "Spring R",
        "front_antiroll_bar": "Bar F",
        "rear_antiroll_bar": "Bar R",
        "procedures": ["角阶跃", "稳态回转"],
        "plot_channels": ["roll", "pitch"],
        "report": {"enabled": True},
        "keep_final_configuration": False,
    }


def build_service(tmp_path, template=None):
    ctx = FakeCtx(tmp_path)
    svc = WorkflowTemplateService(ctx)
    svc.template_dir = tmp_path / "templates"
    svc.template_dir.mkdir()
    (svc.template_dir / "demo.json").write_text(
        json.dumps(template or valid_template(), ensure_ascii=False),
        encoding="utf-8",
    )
    ctx.services["workflow_template"] = svc
    return svc, ctx


def test_template_preview_contains_confirmation_risk_summary(tmp_path):
    svc, _ = build_service(tmp_path)

    summary = svc.format_confirmation_summary("demo")

    assert "一键实验模板: Demo (demo)" in summary
    assert "配置数量: 1" in summary
    assert "工况数量: 2" in summary
    assert "执行后恢复 CarSim 配置: 是" in summary
    assert "风险: 将切换车型/悬架配置并执行批量 CarSim 仿真。" in summary


def test_unknown_plot_channel_is_rejected(tmp_path):
    template = valid_template()
    template["plot_channels"] = ["not_a_channel"]
    svc, _ = build_service(tmp_path, template)

    with pytest.raises(WorkflowTemplateError, match="未知波形通道"):
        svc.load_template("demo")


def test_execute_template_applies_setup_plots_and_runs_report(tmp_path):
    svc, ctx = build_service(tmp_path)

    result = svc.execute("demo")

    assert "模板执行完成" in result
    assert ctx.tuning.calls == [
        ("vehicle", "Car A"),
        ("front_spring", "Spring F"),
        ("rear_spring", "Spring R"),
        ("bar", True, "Bar F"),
        ("bar", False, "Bar R"),
    ]
    assert ctx.ui.plot_switches["roll"].checked is True
    assert ctx.ui.plot_switches["pitch"].checked is True
    assert ctx.ui.plot_layout_updated is True
    assert ctx.report.executed == "demo"


def test_workflow_action_uses_template_summary_callback(tmp_path):
    _, ctx = build_service(tmp_path)
    registry = ActionRegistry()
    workflow_actions.register(registry, ctx)

    summary = registry.format_action_summary("run_workflow_template", {"template_id": "demo"})

    assert "一键实验模板: Demo (demo)" in summary
    assert "预计输出目录:" in summary


def test_report_environment_reports_missing_handproc(tmp_path):
    ctx = SimpleNamespace(ui=object())
    svc = SimTestReportService(ctx)
    svc.config_path = tmp_path / "report_runtime.json"
    svc.config_path.write_text(
        json.dumps({
            "handproc_dir": str(tmp_path / "missing"),
            "python_executable": "",
            "default_output_root": str(tmp_path / "reports"),
        }),
        encoding="utf-8",
    )

    ok, msg = svc.check_environment(require_handproc=True)

    assert ok is False
    assert "handproc.cp311-win_amd64.pyd" in msg


def test_report_batch_restores_carsim_after_run(monkeypatch, tmp_path):
    class FakeController:
        restored = False

        def create_test_dataset(self):
            pass

        def change_vehicle(self, vehicle, category):
            return True

        def get_crnt_veh_param(self, *args, **kwargs):
            pass

        def change_crnt_spring(self, *args):
            pass

        def change_crnt_arb(self, *args):
            pass

        def change_procedure(self, proc):
            return True

        def execute_simulation(self):
            return True

        def step_cond_check(self):
            pass

        def rename_carsim_output_csv(self, folder, name):
            Path(folder).mkdir(parents=True, exist_ok=True)
            (Path(folder) / f"{name}.csv").write_text("TimeStep,Ay\n0,0\n", encoding="utf-8")

        def recover_dataset(self):
            FakeController.restored = True

    monkeypatch.setattr(
        sim_report_module.SimTestReportService,
        "check_environment",
        lambda self, require_handproc=True: (True, "ok"),
    )
    monkeypatch.setattr(
        sim_report_module.SimTestReportService,
        "_load_offline_config",
        lambda self: {
            "common_config": {"Procedure_Category": "cat"},
            "角阶跃": {"Dataset": "Step"},
        },
    )
    def fake_generate_report(self, result_folder, selected_procedures=None):
        report_path = Path(result_folder) / "report.docx"
        report_path.write_text("mock report", encoding="utf-8")
        return str(report_path)

    monkeypatch.setattr(
        sim_report_module.SimTestReportService,
        "generate_report",
        fake_generate_report,
    )

    def fake_prepare_import_path(self):
        pass

    monkeypatch.setattr(sim_report_module.SimTestReportService, "_prepare_import_path", fake_prepare_import_path)
    monkeypatch.setitem(__import__("sys").modules, "control_carsim", SimpleNamespace(
        ControlCarsim=FakeController,
        sanitize_filename=lambda value: value,
    ))

    ctx = SimpleNamespace(
        ui=object(),
        mod=lambda name, default=None: {"Car A": "1:<CAT>Car A"} if name == "vehicleInfoDic" else default,
    )
    svc = SimTestReportService(ctx)
    svc.config_path = tmp_path / "report_runtime.json"
    svc.config_path.write_text(
        json.dumps({"default_output_root": str(tmp_path / "reports")}),
        encoding="utf-8",
    )
    template = valid_template()
    template["procedures"] = ["角阶跃"]

    result = svc.run_batch_from_template(template)

    assert result["restored_carsim"] is True
    assert FakeController.restored is True
