"""Service wrapper for the uploaded sim_test_report package.

The service keeps the binary handproc dependency outside the repository and
loads the report code only when a report action is actually executed.
"""

import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from agent.services._base import BaseService


class SimTestReportService(BaseService):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.repo_root = Path(__file__).resolve().parents[2]
        self.sim_dir = self.repo_root / "sim_test_report"
        self.config_path = self.repo_root / "agent_data" / "config" / "report_runtime.json"

    def runtime_config(self) -> dict:
        default = {
            "handproc_dir": "",
            "python_executable": "",
            "default_output_root": str(self.repo_root / "agent_data" / "reports"),
        }
        if not self.config_path.exists():
            return default
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception:
            return default
        default.update({k: v for k, v in data.items() if v is not None})
        return default

    def available_procedures(self) -> list:
        cfg = self._load_offline_config()
        return [k for k in cfg.keys() if k != "common_config"]

    def check_environment(self, require_handproc=True) -> tuple[bool, str]:
        missing = []
        for pkg in ("numpy", "pandas", "matplotlib", "scipy", "docx", "win32com"):
            if importlib.util.find_spec(pkg) is None:
                missing.append(pkg)

        cfg = self.runtime_config()
        handproc_dir = Path(cfg.get("handproc_dir") or "")
        handproc_file = handproc_dir / "handproc.cp311-win_amd64.pyd"
        if require_handproc and not handproc_file.exists():
            missing.append(f"handproc.cp311-win_amd64.pyd ({handproc_dir})")

        if require_handproc and sys.version_info[:2] != (3, 11):
            py = cfg.get("python_executable") or ""
            if not py:
                missing.append("Python 3.11 executable (report_runtime.json: python_executable)")

        if missing:
            return False, "报告/批量仿真环境缺失: " + ", ".join(missing)
        return True, "报告/批量仿真环境检查通过"

    def default_output_root(self) -> Path:
        root = Path(self.runtime_config().get("default_output_root") or "")
        if not root.is_absolute():
            root = self.repo_root / root
        root.mkdir(parents=True, exist_ok=True)
        return root

    def generate_report(self, result_folder: str, selected_procedures=None) -> str:
        result_path = Path(result_folder)
        if not result_path.exists():
            return f"结果目录不存在: {result_path}"

        ok, msg = self.check_environment(require_handproc=True)
        if not ok:
            return msg

        if sys.version_info[:2] == (3, 11):
            return self._generate_report_in_process(result_path, selected_procedures)
        return self._generate_report_subprocess(result_path, selected_procedures)

    def run_batch_from_template(self, template: dict, progress=None) -> dict:
        ok, msg = self.check_environment(require_handproc=False)
        if not ok:
            raise RuntimeError(msg)

        self._prepare_import_path()
        from control_carsim import ControlCarsim, sanitize_filename

        configs = self._load_offline_config()
        procedures = template.get("procedures") or self.available_procedures()
        output_root = self.default_output_root()
        run_dir = output_root / datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir.mkdir(parents=True, exist_ok=True)

        controller = None
        configurations = self._template_configurations(template)
        restore_after_run = not bool(template.get("keep_final_configuration", False))

        try:
            controller = ControlCarsim()
            controller.create_test_dataset()
            controller.configs = configs
            common = configs.get("common_config", {})
            controller.proc_cate = common.get("Procedure_Category", "")

            self._write_model_info(run_dir, configurations)

            for idx, cfg in enumerate(configurations, 1):
                self._notify(progress, "配置车辆", f"{idx}/{len(configurations)} {cfg['name']}")
                vehicle = cfg["vehicle"]
                vehicle_cat = cfg.get("vehicle_category") or self._resolve_vehicle_category(vehicle)
                if not controller.change_vehicle(vehicle, vehicle_cat):
                    raise RuntimeError(f"切换车型失败: {vehicle}")

                car_dir = run_dir / sanitize_filename(cfg["name"])
                car_dir.mkdir(parents=True, exist_ok=True)
                try:
                    controller.get_crnt_veh_param(vehicle, vehicle_cat, save_path=str(car_dir))
                except Exception:
                    pass

                self._apply_controller_parts(controller, cfg)

                for proc_idx, proc_name in enumerate(procedures, 1):
                    info = configs.get(proc_name)
                    if not info:
                        raise RuntimeError(f"未知报告工况: {proc_name}")
                    proc_ds = info.get("Dataset")
                    self._notify(progress, "执行仿真", f"{cfg['name']} | {proc_idx}/{len(procedures)} {proc_name}")
                    if not controller.change_procedure(proc_ds):
                        raise RuntimeError(f"切换工况失败: {proc_name} ({proc_ds})")
                    success = controller.execute_simulation()
                    if "Step" in proc_ds:
                        controller.step_cond_check()
                    elif "Pulse" in proc_ds:
                        controller.pulse_cond_check()
                    if not success:
                        raise RuntimeError(f"仿真失败: {cfg['name']} / {proc_name}")
                    controller.rename_carsim_output_csv(str(car_dir), proc_name)

            report_path = None
            if template.get("report", {}).get("enabled", True):
                self._notify(progress, "生成报告", str(run_dir))
                report_result = self.generate_report(str(run_dir), selected_procedures=procedures)
                if (
                    report_result.startswith("报告/批量仿真环境缺失")
                    or report_result.startswith("结果目录不存在")
                    or report_result.startswith("报告生成")
                    or not Path(report_result).exists()
                ):
                    raise RuntimeError(report_result)
                report_path = report_result

            return {
                "result_folder": str(run_dir),
                "report_path": report_path,
                "configurations": len(configurations),
                "procedures": procedures,
                "restored_carsim": restore_after_run,
            }
        finally:
            if controller is not None and restore_after_run:
                self._notify(progress, "恢复CarSim", "正在恢复模板执行前的 CarSim 链接配置")
                controller.recover_dataset()

    def _generate_report_in_process(self, result_path: Path, selected_procedures=None) -> str:
        cfg = self.runtime_config()
        handproc_dir = cfg.get("handproc_dir")
        if handproc_dir and handproc_dir not in sys.path:
            sys.path.insert(0, handproc_dir)
        self._prepare_import_path()
        import offline_report_doc

        configs = offline_report_doc.CONFIGS
        if selected_procedures:
            configs = self._filter_configs(configs, selected_procedures)
        output = offline_report_doc.generate_report(str(result_path), configs)
        return output or "报告生成失败，请检查 Word 文件是否被占用。"

    def _generate_report_subprocess(self, result_path: Path, selected_procedures=None) -> str:
        cfg = self.runtime_config()
        py = cfg.get("python_executable")
        if not py:
            return "报告生成需要 Python 3.11，请在 agent_data/config/report_runtime.json 配置 python_executable。"

        code = r"""
import json, sys
from pathlib import Path
result, sim_dir, handproc_dir, selected = sys.argv[1:5]
if handproc_dir:
    sys.path.insert(0, handproc_dir)
sys.path.insert(0, sim_dir)
import offline_report_doc
configs = offline_report_doc.CONFIGS
selected_names = json.loads(selected)
if selected_names:
    configs = {"common_config": configs.get("common_config", {})} | {k: configs[k] for k in selected_names if k in configs}
out = offline_report_doc.generate_report(result, configs)
print(out or "")
"""
        selected = json.dumps(selected_procedures or [], ensure_ascii=False)
        proc = subprocess.run(
            [py, "-c", code, str(result_path), str(self.sim_dir), cfg.get("handproc_dir") or "", selected],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            return f"报告生成失败: {proc.stderr.strip() or proc.stdout.strip()}"
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        return lines[-1] if lines else "报告生成失败：子进程没有返回报告路径。"

    def _prepare_import_path(self):
        sim_dir = str(self.sim_dir)
        if sim_dir not in sys.path:
            sys.path.insert(0, sim_dir)

    def _load_offline_config(self) -> dict:
        path = self.sim_dir / "offline_report_config.json"
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _filter_configs(self, configs: dict, selected: list) -> dict:
        filtered = {"common_config": configs.get("common_config", {})}
        filtered.update({k: configs[k] for k in selected if k in configs})
        return filtered

    def _template_configurations(self, template: dict) -> list:
        if template.get("configurations"):
            return template["configurations"]
        return [{
            "name": template.get("name") or template.get("id") or "workflow",
            "vehicle": template.get("vehicle"),
            "vehicle_category": template.get("vehicle_category"),
            "front_spring": template.get("front_spring"),
            "rear_spring": template.get("rear_spring"),
            "front_antiroll_bar": template.get("front_antiroll_bar"),
            "rear_antiroll_bar": template.get("rear_antiroll_bar"),
            "simulink_model": template.get("simulink_model", ""),
        }]

    def _resolve_vehicle_category(self, vehicle: str) -> str:
        vehicle_info = self._ctx.mod("vehicleInfoDic", {}) if hasattr(self._ctx, "mod") else {}
        raw = vehicle_info.get(vehicle, "")
        match = re.search(r"<(.*?)>", raw)
        return match.group(1) if match else ""

    def _apply_controller_parts(self, controller, cfg: dict):
        if cfg.get("front_spring"):
            controller.change_crnt_spring("F", cfg["front_spring"])
        if cfg.get("rear_spring"):
            controller.change_crnt_spring("R", cfg["rear_spring"])
        if cfg.get("front_antiroll_bar"):
            controller.change_crnt_arb("F", cfg["front_antiroll_bar"])
        if cfg.get("rear_antiroll_bar"):
            controller.change_crnt_arb("R", cfg["rear_antiroll_bar"])
        if cfg.get("simulink_model"):
            controller.change_simulink(cfg["simulink_model"])

    def _write_model_info(self, run_dir: Path, configurations: list):
        lines = ["【各方案配置说明】"]
        for cfg in configurations:
            lines.append(
                f"{cfg.get('name')}: 车型[{cfg.get('vehicle')}] | "
                f"弹簧[{cfg.get('front_spring')}/{cfg.get('rear_spring')}] | "
                f"稳定杆[{cfg.get('front_antiroll_bar')}/{cfg.get('rear_antiroll_bar')}] | "
                f"联合仿真模型[{cfg.get('simulink_model', '')}]"
            )
        (run_dir / "model_info.txt").write_text("\n".join(lines), encoding="utf-8")

    def _notify(self, progress, stage: str, message: str):
        if progress:
            progress(stage, message)
