"""Template manager panel for building one-click experiment templates."""

from __future__ import annotations

try:
    from PyQt5.QtCore import Qt, QCoreApplication
    from PyQt5.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QFormLayout,
        QLabel,
        QLineEdit,
        QTextEdit,
        QPushButton,
        QComboBox,
        QCheckBox,
        QMessageBox,
        QGroupBox,
        QScrollArea,
        QCompleter,
    )
except ImportError:  # pragma: no cover
    QWidget = object
    QCoreApplication = None


class WorkflowTemplateManagerPanel(QWidget):
    """Create and save workflow templates without changing main.py."""

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self._ctx = ctx
        self._workflow = ctx.service("workflow_template")
        self._init_ui()
        self.refresh_options()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        title = QLabel("Agent模板管理")
        title.setStyleSheet("font-size: 15px; font-weight: bold;")
        root.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        form_root = QVBoxLayout(body)

        basic_group = QGroupBox("模板信息")
        basic_form = QFormLayout(basic_group)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如：领导演示一键实验")
        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("可选；留空时根据模板名自动生成")
        self.description_edit = QTextEdit()
        self.description_edit.setFixedHeight(64)
        self.description_edit.setPlaceholderText("模板用途说明")
        basic_form.addRow("模板名", self.name_edit)
        basic_form.addRow("模板ID", self.id_edit)
        basic_form.addRow("说明", self.description_edit)
        form_root.addWidget(basic_group)

        config_group = QGroupBox("车辆与配置")
        config_form = QFormLayout(config_group)
        self.vehicle_combo = self._combo()
        self.front_spring_combo = self._combo()
        self.rear_spring_combo = self._combo()
        self.front_damper_combo = self._combo()
        self.rear_damper_combo = self._combo()
        self.front_bar_combo = self._combo()
        self.rear_bar_combo = self._combo()
        self.simulink_combo = self._combo()
        self.simulink_combo.setPlaceholderText("可选")
        config_form.addRow("车型", self.vehicle_combo)
        config_form.addRow("前弹簧", self.front_spring_combo)
        config_form.addRow("后弹簧", self.rear_spring_combo)
        config_form.addRow("前阻尼", self.front_damper_combo)
        config_form.addRow("后阻尼", self.rear_damper_combo)
        config_form.addRow("前稳定杆", self.front_bar_combo)
        config_form.addRow("后稳定杆", self.rear_bar_combo)
        config_form.addRow("Simulink模型", self.simulink_combo)
        form_root.addWidget(config_group)

        workflow_group = QGroupBox("流程选项")
        workflow_form = QFormLayout(workflow_group)
        self.procedure_combo = self._combo()
        self.procedure_add_btn = QPushButton("添加工况")
        self.procedure_text = QTextEdit()
        self.procedure_text.setFixedHeight(58)
        proc_row = QHBoxLayout()
        proc_row.addWidget(self.procedure_combo, 1)
        proc_row.addWidget(self.procedure_add_btn)
        self.procedure_add_btn.clicked.connect(self.add_procedure)
        workflow_form.addRow("工况", proc_row)
        workflow_form.addRow("已选工况", self.procedure_text)

        self.plot_combo = self._combo()
        self.plot_add_btn = QPushButton("添加波形")
        self.plot_text = QTextEdit()
        self.plot_text.setFixedHeight(58)
        plot_row = QHBoxLayout()
        plot_row.addWidget(self.plot_combo, 1)
        plot_row.addWidget(self.plot_add_btn)
        self.plot_add_btn.clicked.connect(self.add_plot_channel)
        workflow_form.addRow("波形", plot_row)
        workflow_form.addRow("已选波形", self.plot_text)

        self.report_check = QCheckBox("生成报告")
        self.report_check.setChecked(True)
        self.restore_check = QCheckBox("执行后恢复 CarSim")
        self.restore_check.setChecked(True)
        workflow_form.addRow("", self.report_check)
        workflow_form.addRow("", self.restore_check)
        form_root.addWidget(workflow_group)

        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFixedHeight(120)
        root.addWidget(self.preview)

        row = QHBoxLayout()
        self.refresh_btn = QPushButton("刷新选项")
        self.preview_btn = QPushButton("预览模板")
        self.save_btn = QPushButton("保存模板")
        self.run_btn = QPushButton("保存并执行")
        self.refresh_btn.clicked.connect(self.refresh_options)
        self.preview_btn.clicked.connect(self.preview_template)
        self.save_btn.clicked.connect(self.save_template)
        self.run_btn.clicked.connect(self.save_and_run)
        row.addWidget(self.refresh_btn)
        row.addWidget(self.preview_btn)
        row.addWidget(self.save_btn)
        row.addWidget(self.run_btn)
        row.addStretch()
        root.addLayout(row)

    def refresh_options(self):
        options = self._workflow.template_options()
        self._set_combo_items(self.vehicle_combo, options.get("vehicles", []))
        self._set_combo_items(self.front_spring_combo, options.get("springs", []))
        self._set_combo_items(self.rear_spring_combo, options.get("springs", []))
        self._set_combo_items(self.front_damper_combo, options.get("dampers", []))
        self._set_combo_items(self.rear_damper_combo, options.get("dampers", []))
        self._set_combo_items(self.front_bar_combo, options.get("antiroll_bars", []))
        self._set_combo_items(self.rear_bar_combo, options.get("antiroll_bars", []))
        self._set_combo_items(self.procedure_combo, options.get("procedures", []))
        self._plot_items = {
            f"{item['key']} - {item['label']}": item["key"]
            for item in options.get("plot_channels", [])
        }
        self._set_combo_items(self.plot_combo, list(self._plot_items.keys()))
        self._process_events()

    def add_procedure(self):
        self._append_unique_line(self.procedure_text, self.procedure_combo.currentText().strip())

    def add_plot_channel(self):
        text = self.plot_combo.currentText().strip()
        key = self._plot_items.get(text, text.split(" - ", 1)[0].strip())
        self._append_unique_line(self.plot_text, key)

    def preview_template(self):
        template = self._template_from_ui()
        self.preview.setPlainText(self._format_template(template))

    def save_template(self) -> dict | None:
        try:
            result = self._workflow.save_template(self._template_from_ui())
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))
            return None
        self.id_edit.setText(result["id"])
        self.preview.setPlainText(f"模板已保存：{result['path']}")
        QMessageBox.information(self, "保存成功", f"模板已保存：{result['id']}")
        return result

    def save_and_run(self):
        result = self.save_template()
        if not result:
            return
        show_panel = getattr(self._ctx, "show_workflow_panel", None)
        if callable(show_panel):
            show_panel()
        message = self._workflow.execute(result["id"])
        self.preview.setPlainText(message)

    def _template_from_ui(self) -> dict:
        name = self.name_edit.text().strip()
        if not name:
            raise ValueError("请填写模板名")
        procedures = self._lines(self.procedure_text)
        plot_channels = self._lines(self.plot_text)
        if not procedures:
            raise ValueError("请至少添加一个工况")
        if not plot_channels:
            raise ValueError("请至少添加一个波形通道")
        return {
            "id": self.id_edit.text().strip(),
            "name": name,
            "description": self.description_edit.toPlainText().strip(),
            "vehicle": self.vehicle_combo.currentText().strip(),
            "vehicle_category": "",
            "front_spring": self.front_spring_combo.currentText().strip(),
            "rear_spring": self.rear_spring_combo.currentText().strip(),
            "front_damper": self.front_damper_combo.currentText().strip(),
            "rear_damper": self.rear_damper_combo.currentText().strip(),
            "front_antiroll_bar": self.front_bar_combo.currentText().strip(),
            "rear_antiroll_bar": self.rear_bar_combo.currentText().strip(),
            "simulink_model": self.simulink_combo.currentText().strip(),
            "procedures": procedures,
            "plot_channels": plot_channels,
            "report": {"enabled": self.report_check.isChecked()},
            "keep_final_configuration": not self.restore_check.isChecked(),
        }

    def _format_template(self, template: dict) -> str:
        lines = [
            f"模板: {template['name']}",
            f"车型: {template['vehicle']}",
            f"前/后弹簧: {template['front_spring']} / {template['rear_spring']}",
            f"前/后阻尼: {template['front_damper']} / {template['rear_damper']}",
            f"前/后稳定杆: {template['front_antiroll_bar']} / {template['rear_antiroll_bar']}",
            f"工况: {', '.join(template['procedures'])}",
            f"波形: {', '.join(template['plot_channels'])}",
            f"报告: {'生成' if template['report']['enabled'] else '不生成'}",
            f"执行后恢复 CarSim: {'是' if not template['keep_final_configuration'] else '否'}",
        ]
        return "\n".join(lines)

    def _combo(self) -> QComboBox:
        combo = QComboBox()
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.NoInsert)
        combo.setMaxVisibleItems(16)
        return combo

    def _set_combo_items(self, combo: QComboBox, items: list[str]):
        current = combo.currentText().strip()
        combo.clear()
        combo.addItems([str(item) for item in items if str(item)])
        combo.setCurrentText(current)
        completer = QCompleter(combo.model(), combo)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        combo.setCompleter(completer)

    def _append_unique_line(self, text_edit: QTextEdit, value: str):
        if not value:
            return
        lines = self._lines(text_edit)
        if value not in lines:
            lines.append(value)
        text_edit.setPlainText("\n".join(lines))

    def _lines(self, text_edit: QTextEdit) -> list[str]:
        return [
            line.strip()
            for line in text_edit.toPlainText().splitlines()
            if line.strip()
        ]

    def _process_events(self):
        if QCoreApplication is not None:
            QCoreApplication.processEvents()
