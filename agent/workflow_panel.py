"""Workflow progress console for agent-driven one-click experiments."""

from __future__ import annotations

import os
from typing import Any

try:
    from PyQt5.QtCore import QCoreApplication
    from PyQt5.QtGui import QColor
    from PyQt5.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QTextEdit,
        QPushButton,
        QProgressBar,
        QSplitter,
    )
except ImportError:  # pragma: no cover
    QWidget = object
    QCoreApplication = None


class WorkflowPanel(QWidget):
    """Display workflow state, configuration summary, logs and output links."""

    STAGES = [
        ("load_template", "加载模板"),
        ("validate_environment", "环境校验"),
        ("apply_configuration", "应用配置"),
        ("run_simulation", "执行仿真"),
        ("restore_carsim", "恢复 CarSim"),
        ("generate_report", "生成报告"),
        ("complete", "完成"),
    ]
    STATUS_TEXT = {
        "pending": "待执行",
        "running": "进行中",
        "done": "完成",
        "failed": "失败",
    }
    STATUS_MARK = {
        "pending": "○",
        "running": "●",
        "done": "✓",
        "failed": "×",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_result: dict[str, Any] = {}
        self.stage_states = {key: "pending" for key, _ in self.STAGES}
        self.stage_messages: dict[str, str] = {}
        self.stage_titles = dict(self.STAGES)
        self.current_template: dict[str, Any] = {}
        self._init_ui()
        self._refresh_stage_list()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = QHBoxLayout()
        self.title = QLabel("Agent实验流程")
        self.title.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.status_label = QLabel("等待模板执行")
        self.status_label.setStyleSheet("color: #555;")
        header.addWidget(self.title, 2)
        header.addWidget(self.status_label, 1)
        layout.addLayout(header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        splitter = QSplitter()
        self.stage_list = QListWidget()
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setPlaceholderText("模板执行后显示车型、弹簧、阻尼、稳定杆、工况和输出目录。")
        splitter.addWidget(self.stage_list)
        splitter.addWidget(self.summary_text)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 4)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log, 3)

        button_row = QHBoxLayout()
        self.open_result_btn = QPushButton("打开结果目录")
        self.open_result_btn.setEnabled(False)
        self.open_report_btn = QPushButton("打开报告")
        self.open_report_btn.setEnabled(False)
        self.open_result_btn.clicked.connect(self.open_result_folder)
        self.open_report_btn.clicked.connect(self.open_report)
        button_row.addWidget(self.open_result_btn)
        button_row.addWidget(self.open_report_btn)
        button_row.addStretch()
        layout.addLayout(button_row)

    def start_workflow(self, name: str, description: str = "", template: dict | None = None):
        self.last_result = {}
        self.current_template = template or {}
        self.stage_states = {key: "pending" for key, _ in self.STAGES}
        self.stage_messages = {}
        self.title.setText(f"Agent实验流程 - {name}")
        self.status_label.setText("准备执行")
        self.progress_bar.setValue(0)
        self.log.clear()
        self.open_result_btn.setEnabled(False)
        self.open_report_btn.setEnabled(False)
        self.summary_text.setPlainText(self._format_template_summary(template or {}, description))
        self._refresh_stage_list()
        self.show_workflow()
        self._process_events()

    def update_workflow_event(self, event: dict):
        self.update_stage(
            event.get("stage_key") or event.get("key") or event.get("stage") or "complete",
            title=event.get("stage_title") or event.get("title"),
            status=event.get("status") or "running",
            message=event.get("message") or "",
            progress=event.get("progress"),
            payload=event,
        )

    def update_stage(
        self,
        stage_key: str,
        title: str | None = None,
        status: str = "running",
        message: str = "",
        progress: int | None = None,
        payload: dict | None = None,
    ):
        if stage_key not in self.stage_states:
            self.stage_states[stage_key] = "pending"
            self.stage_titles[stage_key] = title or stage_key
        if title:
            self.stage_titles[stage_key] = title
        self.stage_states[stage_key] = status
        if message:
            self.stage_messages[stage_key] = message

        payload = payload or {}
        self._merge_result(payload)
        self._refresh_summary(payload)
        self._refresh_stage_list()
        self._update_progress(progress)

        log_title = self.stage_titles.get(stage_key, stage_key)
        log_status = self.STATUS_TEXT.get(status, status)
        self.status_label.setText(f"{log_title} - {log_status}")
        self.log.append(f"[{log_status}] {log_title}: {message}".rstrip())
        self._update_buttons()
        self.show_workflow()
        self._process_events()

    def append_stage(self, stage: str, message: str):
        key = self._key_from_title(stage)
        self.update_stage(key, title=stage, status="running", message=message)

    def finish_workflow(self, success: bool, message: str, result: dict | None = None):
        if result:
            self._merge_result(result)
        self.update_stage(
            "complete",
            title="完成",
            status="done" if success else "failed",
            message=message,
            progress=100 if success else None,
            payload=result or {},
        )
        self.status_label.setText("模板执行完成" if success else "模板执行失败")
        self._update_buttons()

    def show_workflow(self):
        self.show()
        self.raise_()

    def open_result_folder(self):
        path = self.last_result.get("result_folder")
        if path:
            os.startfile(path)

    def open_report(self):
        path = self.last_result.get("report_path")
        if path:
            os.startfile(path)

    def _refresh_stage_list(self):
        self.stage_list.clear()
        for key, title in self.stage_titles.items():
            status = self.stage_states.get(key, "pending")
            mark = self.STATUS_MARK.get(status, "○")
            text = f"{mark} {title}  {self.STATUS_TEXT.get(status, status)}"
            message = self.stage_messages.get(key)
            if message:
                text += f"\n  {message}"
            item = QListWidgetItem(text)
            if status == "running":
                item.setForeground(QColor("#0b63ce"))
            elif status == "done":
                item.setForeground(QColor("#1b7f3a"))
            elif status == "failed":
                item.setForeground(QColor("#b00020"))
            self.stage_list.addItem(item)

    def _format_template_summary(self, template: dict, description: str = "") -> str:
        if not template:
            return description or "等待模板执行"
        configs = self._configurations(template)
        procedures = template.get("procedures", [])
        lines = [
            f"模板: {template.get('name', '')} ({template.get('id', '')})",
            f"说明: {template.get('description') or description or ''}",
            f"报告生成: {'开启' if template.get('report', {}).get('enabled', False) else '关闭'}",
            f"执行后恢复 CarSim: {'是' if not template.get('keep_final_configuration', False) else '否'}",
            "",
            "当前配置:",
        ]
        for cfg in configs:
            lines.extend([
                f"- 名称: {cfg.get('name', '')}",
                f"  车型: {cfg.get('vehicle', '')}",
                f"  前/后弹簧: {cfg.get('front_spring', '')} / {cfg.get('rear_spring', '')}",
                f"  前/后阻尼: {cfg.get('front_damper', '')} / {cfg.get('rear_damper', '')}",
                f"  前/后稳定杆: {cfg.get('front_antiroll_bar', '')} / {cfg.get('rear_antiroll_bar', '')}",
                f"  Simulink模型: {cfg.get('simulink_model', '')}",
            ])
        lines.extend([
            "",
            f"工况列表: {', '.join(procedures)}",
            f"输出目录: {self.last_result.get('result_folder', '执行后生成')}",
            f"报告路径: {self.last_result.get('report_path', '执行后生成')}",
        ])
        return "\n".join(lines)

    def _refresh_summary(self, payload: dict):
        if payload.get("result_folder") or payload.get("report_path"):
            self._merge_result(payload)
        if payload.get("current_configuration"):
            self.current_template["_current_configuration"] = payload["current_configuration"]
        if payload.get("current_procedure"):
            self.current_template["_current_procedure"] = payload["current_procedure"]

        summary = self._format_template_summary(self.current_template, "")
        current_cfg = self.current_template.get("_current_configuration")
        current_proc = self.current_template.get("_current_procedure")
        extra = []
        if current_cfg:
            extra.append(f"正在执行配置: {current_cfg.get('name', current_cfg.get('vehicle', ''))}")
        if current_proc:
            extra.append(f"当前工况: {current_proc}")
        if extra:
            summary += "\n\n" + "\n".join(extra)
        self.summary_text.setPlainText(summary)

    def _update_progress(self, progress: int | None):
        if progress is not None:
            self.progress_bar.setValue(max(0, min(100, int(progress))))
            return
        total = len(self.STAGES)
        done = sum(1 for key, _ in self.STAGES if self.stage_states.get(key) == "done")
        failed = any(self.stage_states.get(key) == "failed" for key, _ in self.STAGES)
        value = int(done / total * 100)
        if failed:
            value = max(value, self.progress_bar.value())
        self.progress_bar.setValue(value)

    def _merge_result(self, payload: dict):
        for key in ("result_folder", "report_path"):
            if payload.get(key):
                self.last_result[key] = payload[key]

    def _update_buttons(self):
        self.open_result_btn.setEnabled(bool(self.last_result.get("result_folder")))
        self.open_report_btn.setEnabled(bool(self.last_result.get("report_path")))

    def _key_from_title(self, title: str) -> str:
        for key, known_title in self.STAGES:
            if title == known_title:
                return key
        aliases = {
            "加载模板": "load_template",
            "校验环境": "validate_environment",
            "环境校验": "validate_environment",
            "应用车辆配置": "apply_configuration",
            "配置车辆": "apply_configuration",
            "执行仿真": "run_simulation",
            "恢复CarSim": "restore_carsim",
            "恢复 CarSim": "restore_carsim",
            "生成报告": "generate_report",
            "完成": "complete",
            "失败": "complete",
        }
        return aliases.get(title, "complete")

    def _configurations(self, template: dict) -> list[dict]:
        if template.get("configurations"):
            return template["configurations"]
        if not template:
            return []
        return [{
            "name": template.get("name", ""),
            "vehicle": template.get("vehicle", ""),
            "front_spring": template.get("front_spring", ""),
            "rear_spring": template.get("rear_spring", ""),
            "front_damper": template.get("front_damper", ""),
            "rear_damper": template.get("rear_damper", ""),
            "front_antiroll_bar": template.get("front_antiroll_bar", ""),
            "rear_antiroll_bar": template.get("rear_antiroll_bar", ""),
            "simulink_model": template.get("simulink_model", ""),
        }]

    def _process_events(self):
        if QCoreApplication is not None:
            QCoreApplication.processEvents()
