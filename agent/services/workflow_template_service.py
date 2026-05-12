"""Workflow template loading, validation and execution."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from agent.actions._helpers import fuzzy_resolve
from agent.actions.plot_actions import PLOT_CHANNELS
from agent.services._base import BaseService


class WorkflowTemplateError(ValueError):
    pass


class WorkflowTemplateService(BaseService):
    REQUIRED_TOP_LEVEL = {
        "id",
        "name",
        "description",
        "vehicle",
        "front_spring",
        "rear_spring",
        "front_damper",
        "rear_damper",
        "front_antiroll_bar",
        "rear_antiroll_bar",
        "procedures",
        "plot_channels",
        "report",
        "keep_final_configuration",
    }

    STAGE_TITLES = {
        "load_template": "加载模板",
        "validate_environment": "环境校验",
        "apply_configuration": "应用配置",
        "set_plots": "设置波形",
        "run_simulation": "执行仿真",
        "restore_carsim": "恢复 CarSim",
        "generate_report": "生成报告",
        "complete": "完成",
    }

    def __init__(self, ctx):
        super().__init__(ctx)
        self.repo_root = Path(__file__).resolve().parents[2]
        self.template_dir = self.repo_root / "agent_data" / "workflow_templates"
        self.template_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self) -> list:
        templates = []
        for path in sorted(self.template_dir.glob("*.json")):
            try:
                template = self._read(path)
                self.validate(template)
                templates.append(self._summary_dict(template))
            except Exception as e:
                templates.append({
                    "id": path.stem,
                    "name": path.name,
                    "description": f"模板无效: {e}",
                    "valid": False,
                })
        return templates

    def template_options(self) -> dict:
        """Return selectable values used by the template manager panel."""
        return {
            "vehicles": sorted(self._ctx.mod("vehicleInfoDic", {}).keys()),
            "springs": sorted(self._ctx.mod("springInfoDic", {}).keys()),
            "antiroll_bars": sorted({
                *self._ctx.mod("AuxMInfoDic", {}).keys(),
                *self._ctx.mod("MxTotInfoDic", {}).keys(),
            }),
            "dampers": self._damper_options(),
            "procedures": self._ctx.service("sim_test_report").available_procedures(),
            "plot_channels": [
                {"key": key, "label": label}
                for key, label in PLOT_CHANNELS.items()
            ],
        }

    def save_template(self, template: dict) -> dict:
        template = dict(template)
        template["id"] = self._template_id(template.get("id") or template.get("name") or "workflow")
        template.setdefault("description", "")
        template.setdefault("vehicle_category", "")
        template.setdefault("simulink_model", "")
        template.setdefault("report", {"enabled": True})
        template.setdefault("keep_final_configuration", False)
        self.validate(template)
        path = self.template_dir / f"{template['id']}.json"
        path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
        summary = self._summary_dict(template)
        summary["path"] = str(path)
        return summary

    def load_template(self, template_id: str) -> dict:
        path = self.template_dir / f"{template_id}.json"
        if not path.exists():
            candidates = [p.stem for p in self.template_dir.glob("*.json")]
            resolved, err = fuzzy_resolve(template_id, candidates)
            if err:
                raise WorkflowTemplateError(f"未找到模板 {template_id}。可用模板: {candidates}")
            path = self.template_dir / f"{resolved}.json"
        template = self._read(path)
        self.validate(template)
        return template

    def preview(self, template_id: str) -> str:
        return self.format_confirmation_summary(template_id)

    def format_confirmation_summary(self, template_id: str) -> str:
        template = self.load_template(template_id)
        configurations = self._configurations(template)
        procedures = template.get("procedures", [])
        report_enabled = bool(template.get("report", {}).get("enabled", False))
        output_root = self._ctx.service("sim_test_report").default_output_root()
        lines = [
            f"一键实验模板: {template['name']} ({template['id']})",
            f"说明: {template.get('description', '')}",
            f"配置数量: {len(configurations)}",
            f"工况数量: {len(procedures)}，工况: {', '.join(procedures)}",
            f"阻尼配置: {self._format_damper_summary(configurations)}",
            f"波形通道: {', '.join(template.get('plot_channels', []))}",
            f"预计输出目录: {output_root}\\<时间戳>",
            f"报告生成: {'开启' if report_enabled else '关闭'}",
            f"执行后恢复 CarSim 配置: {'否，保留最终配置' if template.get('keep_final_configuration') else '是'}",
            "风险: 将切换车型和悬架配置，执行批量 CarSim 仿真，并在结束后恢复 CarSim 配置。",
        ]
        return "\n".join(lines)

    def execute(self, template_id: str) -> str:
        panel = getattr(self._ctx, "workflow_panel", None)
        show_panel = getattr(self._ctx, "show_workflow_panel", None)
        if callable(show_panel):
            show_panel()

        current_stage = "load_template"
        template = self.load_template(template_id)
        self._panel_call(panel, "start_workflow", template["name"], template["description"], template)
        self._emit(
            panel,
            "load_template",
            status="done",
            message=f"{template['id']} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            progress=10,
        )

        try:
            current_stage = "validate_environment"
            self._emit(panel, current_stage, status="running", message="检查模板、报告配置和依赖", progress=15)
            self.validate(template)
            report_service = self._ctx.service("sim_test_report")
            require_handproc = bool(template.get("report", {}).get("enabled", True))
            ok, msg = report_service.check_environment(require_handproc=require_handproc)
            if not ok:
                raise WorkflowTemplateError(msg)
            self._emit(panel, current_stage, status="done", message=msg, progress=25)

            current_stage = "apply_configuration"
            self._emit(
                panel,
                current_stage,
                status="running",
                message="切换车型、弹簧、稳定杆；阻尼将在批量仿真中应用",
                progress=30,
                payload={"current_configuration": self._configurations(template)[0]},
            )
            for cfg in self._configurations(template):
                self._apply_ui_configuration(cfg)
            self._emit(panel, current_stage, status="done", message="车辆配置已应用", progress=38)

            current_stage = "set_plots"
            channels = template.get("plot_channels", [])
            self._emit(panel, current_stage, status="running", message=", ".join(channels), progress=42)
            self._apply_plot_channels(channels)
            self._emit(panel, current_stage, status="done", message="波形通道已显示", progress=45)

            current_stage = "run_simulation"
            self._emit(panel, current_stage, status="running", message="开始批量仿真", progress=50)

            def progress(event_or_stage: Any, message: str | None = None):
                if isinstance(event_or_stage, dict):
                    self._emit_from_event(panel, event_or_stage)
                    return
                key = self._stage_key_from_title(str(event_or_stage))
                self._emit(panel, key, title=str(event_or_stage), status="running", message=message or "")

            result = report_service.run_batch_from_template(template, progress=progress)
            final_msg = (
                f"模板执行完成。\n结果目录: {result['result_folder']}\n"
                f"报告: {result.get('report_path') or '未生成'}"
            )
            self._emit(panel, "complete", status="done", message="流程完成", progress=100, payload=result)
            self._panel_call(panel, "finish_workflow", True, final_msg, result)
            return final_msg
        except Exception as e:
            msg = f"模板执行失败: {e}"
            self._emit(panel, current_stage, status="failed", message=str(e))
            self._panel_call(panel, "finish_workflow", False, msg, {})
            return msg

    def validate(self, template: dict):
        missing = sorted(k for k in self.REQUIRED_TOP_LEVEL if k not in template)
        if missing:
            raise WorkflowTemplateError(f"缺少必填字段: {', '.join(missing)}")

        if not isinstance(template.get("procedures"), list) or not template["procedures"]:
            raise WorkflowTemplateError("procedures 必须是非空列表")
        if not isinstance(template.get("plot_channels"), list):
            raise WorkflowTemplateError("plot_channels 必须是列表")
        if not isinstance(template.get("report"), dict) or "enabled" not in template["report"]:
            raise WorkflowTemplateError("report.enabled 必须声明")
        if not isinstance(template.get("keep_final_configuration"), bool):
            raise WorkflowTemplateError("keep_final_configuration 必须是布尔值")

        available = set(self._ctx.service("sim_test_report").available_procedures())
        unknown_procs = [p for p in template["procedures"] if p not in available]
        if unknown_procs:
            raise WorkflowTemplateError(f"未知工况: {', '.join(unknown_procs)}")

        unknown_channels = [c for c in template["plot_channels"] if c not in PLOT_CHANNELS]
        if unknown_channels:
            raise WorkflowTemplateError(f"未知波形通道: {', '.join(unknown_channels)}")

        for cfg in self._configurations(template):
            if not cfg.get("vehicle"):
                raise WorkflowTemplateError("每个配置都必须包含 vehicle")

    def _apply_ui_configuration(self, cfg: dict):
        tuning = self._ctx.service("tuning")
        tuning.select_vehicle(self._resolve("vehicleInfoDic", cfg["vehicle"], "车型"))
        if cfg.get("front_spring"):
            tuning.set_front_left_spring(self._resolve("springInfoDic", cfg["front_spring"], "前弹簧"))
        if cfg.get("rear_spring"):
            tuning.set_rear_left_spring(self._resolve("springInfoDic", cfg["rear_spring"], "后弹簧"))
        if cfg.get("front_antiroll_bar"):
            tuning.set_antiroll_bar(True, self._resolve_bar(cfg["front_antiroll_bar"], "前稳定杆"))
        if cfg.get("rear_antiroll_bar"):
            tuning.set_antiroll_bar(False, self._resolve_bar(cfg["rear_antiroll_bar"], "后稳定杆"))

    def _apply_plot_channels(self, channels: list):
        ui = self._ui
        if not hasattr(ui, "plot_switches"):
            return
        for switch in ui.plot_switches.values():
            switch.setChecked(False)
        for channel in channels:
            if channel in ui.plot_switches:
                ui.plot_switches[channel].setChecked(True)
        if hasattr(ui, "update_plot_layout"):
            ui.update_plot_layout()

    def _resolve(self, dict_name: str, value: str, label: str) -> str:
        values = list(self._ctx.mod(dict_name, {}).keys())
        if not values:
            return value
        resolved, err = fuzzy_resolve(value, values)
        if err:
            raise WorkflowTemplateError(f"{label}无法匹配: {value}。{err}")
        return resolved

    def _resolve_bar(self, value: str, label: str) -> str:
        values = list({**self._ctx.mod("AuxMInfoDic", {}), **self._ctx.mod("MxTotInfoDic", {})}.keys())
        if not values:
            return value
        resolved, err = fuzzy_resolve(value, values)
        if err:
            raise WorkflowTemplateError(f"{label}无法匹配: {value}。{err}")
        return resolved

    def _configurations(self, template: dict) -> list:
        if template.get("configurations"):
            return template["configurations"]
        return [{
            "name": template["name"],
            "vehicle": template["vehicle"],
            "vehicle_category": template.get("vehicle_category"),
            "front_spring": template["front_spring"],
            "rear_spring": template["rear_spring"],
            "front_damper": template["front_damper"],
            "rear_damper": template["rear_damper"],
            "front_antiroll_bar": template["front_antiroll_bar"],
            "rear_antiroll_bar": template["rear_antiroll_bar"],
            "simulink_model": template.get("simulink_model", ""),
        }]

    def _summary_dict(self, template: dict) -> dict:
        return {
            "id": template["id"],
            "name": template["name"],
            "description": template.get("description", ""),
            "configurations": len(self._configurations(template)),
            "procedures": template.get("procedures", []),
            "report_enabled": bool(template.get("report", {}).get("enabled", False)),
            "valid": True,
        }

    def _damper_options(self) -> list:
        names = set()
        for dict_name in ("damperInfoDic", "DamperInfoDic", "dmpInfoDic", "DmpInfoDic"):
            names.update(self._ctx.mod(dict_name, {}).keys())
        names.update(self._dataset_names("Suspension: Damper"))
        return sorted(names)

    def _dataset_names(self, library: str) -> list:
        carsim = self._ctx.mod("carsim")
        if carsim is None or not hasattr(carsim, "GetDatasetList"):
            return []
        try:
            raw_items = carsim.GetDatasetList(library) or []
        except Exception:
            return []
        names = []
        for item in raw_items:
            match = re.search(r"(.*):<(.*?)>(.*)", str(item))
            names.append(match.group(3).strip() if match else str(item).split(":", 1)[-1].strip())
        return [name for name in names if name]

    def _template_id(self, value: str) -> str:
        value = str(value or "").strip().lower()
        value = re.sub(r"\s+", "_", value)
        value = re.sub(r"[^0-9a-zA-Z_\-\u4e00-\u9fff]+", "_", value)
        value = value.strip("_-")
        return value or f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _format_damper_summary(self, configurations: list) -> str:
        parts = []
        for cfg in configurations:
            parts.append(
                f"{cfg.get('name', cfg.get('vehicle', '配置'))}: "
                f"前[{cfg.get('front_damper', '')}] / 后[{cfg.get('rear_damper', '')}]"
            )
        return "; ".join(parts)

    def _read(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def _emit(
        self,
        panel,
        stage_key: str,
        *,
        title: str | None = None,
        status: str = "running",
        message: str = "",
        progress: int | None = None,
        payload: dict | None = None,
    ):
        event = {
            "stage_key": stage_key,
            "stage_title": title or self.STAGE_TITLES.get(stage_key, stage_key),
            "status": status,
            "message": message,
            "progress": progress,
        }
        if payload:
            event.update(payload)
        if panel is None:
            return
        if hasattr(panel, "update_workflow_event"):
            panel.update_workflow_event(event)
        elif hasattr(panel, "update_stage"):
            panel.update_stage(
                event["stage_key"],
                title=event["stage_title"],
                status=event["status"],
                message=event["message"],
                progress=event["progress"],
                payload=event,
            )
        else:
            self._panel_call(panel, "append_stage", event["stage_title"], event["message"])

    def _emit_from_event(self, panel, event: dict):
        key = event.get("stage_key") or event.get("key") or self._stage_key_from_title(event.get("stage_title", ""))
        self._emit(
            panel,
            key,
            title=event.get("stage_title") or event.get("title"),
            status=event.get("status") or "running",
            message=event.get("message") or "",
            progress=event.get("progress"),
            payload=event,
        )

    def _stage_key_from_title(self, title: str) -> str:
        for key, known_title in self.STAGE_TITLES.items():
            if title == known_title:
                return key
        aliases = {
            "配置车辆": "apply_configuration",
            "应用车辆配置": "apply_configuration",
            "校验环境": "validate_environment",
            "设置波形显示": "set_plots",
            "恢复CarSim": "restore_carsim",
        }
        return aliases.get(title, "run_simulation")

    def _panel_call(self, panel, method: str, *args):
        if panel is None:
            return
        func = getattr(panel, method, None)
        if func is not None:
            func(*args)
