"""Template manager panel modelled after control_carsim_qt selection flow."""

from __future__ import annotations

import itertools
import re

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
        QCheckBox,
        QMessageBox,
        QGroupBox,
        QSplitter,
        QTreeWidget,
        QTreeWidgetItem,
        QListWidget,
        QListWidgetItem,
        QTableWidget,
        QTableWidgetItem,
        QAbstractItemView,
        QMenu,
        QScrollArea,
    )
except ImportError:  # pragma: no cover
    QWidget = object
    QCoreApplication = None


class WorkflowTemplateManagerPanel(QWidget):
    """Create workflow templates from vehicle-specific component selections."""

    TABLE_COLUMNS = [
        "配置名称",
        "基准车型",
        "F.Spr",
        "R.Spr",
        "F.Dmp",
        "R.Dmp",
        "F.Bar",
        "R.Bar",
        "Simulink",
    ]

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self._ctx = ctx
        self._workflow = ctx.service("workflow_template")
        self._proc_checks: list[QCheckBox] = []
        self._vehicle_items: list[QTreeWidgetItem] = []
        self._init_ui()
        self.refresh_options()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        header = QLabel("Agent模板管理")
        header.setStyleSheet("font-size: 15px; font-weight: bold;")
        root.addWidget(header)

        basic = QGroupBox("模板信息")
        basic_form = QFormLayout(basic)
        self.name_edit = QLineEdit()
        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("可选；留空时根据模板名自动生成")
        self.description_edit = QTextEdit()
        self.description_edit.setFixedHeight(56)
        basic_form.addRow("模板名", self.name_edit)
        basic_form.addRow("模板ID", self.id_edit)
        basic_form.addRow("说明", self.description_edit)
        root.addWidget(basic)

        splitter = QSplitter()
        splitter.addWidget(self._build_vehicle_panel())
        splitter.addWidget(self._build_config_panel())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        root.addWidget(splitter, 1)

        bottom = QSplitter()
        bottom.addWidget(self._build_workflow_panel())
        bottom.addWidget(self._build_result_panel())
        bottom.setStretchFactor(0, 1)
        bottom.setStretchFactor(1, 2)
        root.addWidget(bottom, 1)

        actions = QHBoxLayout()
        self.refresh_btn = QPushButton("刷新车型")
        self.generate_btn = QPushButton("生成配置")
        self.preview_btn = QPushButton("预览模板")
        self.save_btn = QPushButton("保存模板")
        self.run_btn = QPushButton("保存并执行")
        self.refresh_btn.clicked.connect(self.refresh_options)
        self.generate_btn.clicked.connect(self.generate_configurations)
        self.preview_btn.clicked.connect(self.preview_template)
        self.save_btn.clicked.connect(self.save_template)
        self.run_btn.clicked.connect(self.save_and_run)
        actions.addWidget(self.refresh_btn)
        actions.addWidget(self.generate_btn)
        actions.addWidget(self.preview_btn)
        actions.addWidget(self.save_btn)
        actions.addWidget(self.run_btn)
        actions.addStretch()
        root.addLayout(actions)

    def _build_vehicle_panel(self):
        group = QGroupBox("1. 选择基准车型")
        layout = QVBoxLayout(group)
        self.vehicle_filter = QLineEdit()
        self.vehicle_filter.setPlaceholderText("搜索车型")
        self.vehicle_filter.textChanged.connect(self._filter_vehicle_tree)
        self.vehicle_tree = QTreeWidget()
        self.vehicle_tree.setHeaderLabel("车型库 (Category / Dataset)")
        self.vehicle_tree.itemClicked.connect(self.on_vehicle_clicked)
        self.vehicle_status = QLabel("选择车型后加载适配部件")
        self.vehicle_status.setStyleSheet("color: #138496")
        layout.addWidget(self.vehicle_filter)
        layout.addWidget(self.vehicle_tree, 1)
        layout.addWidget(self.vehicle_status)
        return group

    def _build_config_panel(self):
        group = QGroupBox("2. 悬架配置 (Ctrl/Shift 多选)")
        layout = QVBoxLayout(group)
        front = QHBoxLayout()
        self.list_f_spr = self._create_list_widget("前弹簧 [F.Spring]")
        self.list_f_dmp = self._create_list_widget("前阻尼 [F.Damper]")
        self.list_f_bar = self._create_list_widget("前稳定杆 [F.Bar]")
        front.addWidget(self.list_f_spr["container"])
        front.addWidget(self.list_f_dmp["container"])
        front.addWidget(self.list_f_bar["container"])
        rear = QHBoxLayout()
        self.list_r_spr = self._create_list_widget("后弹簧 [R.Spring]")
        self.list_r_dmp = self._create_list_widget("后阻尼 [R.Damper]")
        self.list_r_bar = self._create_list_widget("后稳定杆 [R.Bar]")
        rear.addWidget(self.list_r_spr["container"])
        rear.addWidget(self.list_r_dmp["container"])
        rear.addWidget(self.list_r_bar["container"])
        sim = QHBoxLayout()
        self.list_simulink = self._create_list_widget("Simulink模型 [Simulink]")
        sim.addWidget(self.list_simulink["container"])
        layout.addLayout(front)
        layout.addLayout(rear)
        layout.addLayout(sim)
        return group

    def _build_workflow_panel(self):
        group = QGroupBox("3. 工况选择")
        layout = QVBoxLayout(group)
        self.proc_select_all = QCheckBox("全选工况")
        self.proc_select_all.stateChanged.connect(self._toggle_all_procedures)
        layout.addWidget(self.proc_select_all)
        self.proc_box = QScrollArea()
        self.proc_box.setWidgetResizable(True)
        self.proc_widget = QWidget()
        self.proc_layout = QVBoxLayout(self.proc_widget)
        self.proc_box.setWidget(self.proc_widget)
        layout.addWidget(self.proc_box, 1)
        self.report_check = QCheckBox("生成报告")
        self.report_check.setChecked(True)
        self.restore_check = QCheckBox("执行后恢复 CarSim")
        self.restore_check.setChecked(True)
        layout.addWidget(self.report_check)
        layout.addWidget(self.restore_check)
        return group

    def _build_result_panel(self):
        group = QGroupBox("4. 配置表与预览")
        layout = QVBoxLayout(group)
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.TABLE_COLUMNS))
        self.table.setHorizontalHeaderLabels(self.TABLE_COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_table_context_menu)
        layout.addWidget(self.table, 2)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFixedHeight(110)
        layout.addWidget(self.preview)
        return group

    def refresh_options(self):
        options = self._workflow.template_options()
        self._load_vehicle_tree(options.get("vehicles", []))
        self._load_procedures(options.get("procedures", []))
        self._process_events()

    def on_vehicle_clicked(self, item, _col):
        if item.childCount() > 0 or item.parent() is None:
            return
        vehicle = item.text(0)
        category = item.data(0, Qt.UserRole + 1) or ""
        self.vehicle_status.setText(f"正在加载 {vehicle} 的适配部件...")
        self._process_events()
        try:
            options = self._workflow.vehicle_component_options(vehicle, category)
        except Exception as e:
            self.vehicle_status.setText(f"按车型加载失败：{e}")
            self._load_fallback_components()
            return
        self._update_list(self.list_f_spr["widget"], options.get("front_springs", []))
        self._update_list(self.list_f_dmp["widget"], options.get("front_dampers", []))
        self._update_list(self.list_f_bar["widget"], options.get("front_antiroll_bars", []))
        self._update_list(self.list_r_spr["widget"], options.get("rear_springs", []))
        self._update_list(self.list_r_dmp["widget"], options.get("rear_dampers", []))
        self._update_list(self.list_r_bar["widget"], options.get("rear_antiroll_bars", []))
        self._update_list(self.list_simulink["widget"], options.get("simulink_models", []))
        self.vehicle_status.setText(f"车型 {vehicle} 部件加载完成")

    def generate_configurations(self):
        current = self.vehicle_tree.currentItem()
        if current is None or current.parent() is None:
            QMessageBox.warning(self, "提示", "请先选择车型")
            return
        vehicle = current.text(0)
        category = current.data(0, Qt.UserRole + 1) or ""
        lists = [
            self._selected_values(self.list_f_spr["widget"]),
            self._selected_values(self.list_r_spr["widget"]),
            self._selected_values(self.list_f_dmp["widget"]),
            self._selected_values(self.list_r_dmp["widget"]),
            self._selected_values(self.list_f_bar["widget"]),
            self._selected_values(self.list_r_bar["widget"]),
            self._selected_values(self.list_simulink["widget"]),
        ]
        combos = list(itertools.product(*lists))
        if not combos:
            QMessageBox.information(self, "提示", "未生成任何配置")
            return
        existing = {
            tuple(self.table.item(row, col).text() for col in range(1, 9))
            for row in range(self.table.rowCount())
        }
        added = 0
        for combo in combos:
            signature = (vehicle,) + combo
            if signature in existing:
                continue
            self._append_configuration_row(vehicle, category, combo)
            added += 1
        self.preview.setPlainText(f"已添加 {added} 个配置")

    def preview_template(self):
        try:
            template = self._template_from_ui()
        except Exception as e:
            QMessageBox.warning(self, "预览失败", str(e))
            return
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
        self.preview.setPlainText(self._workflow.execute(result["id"]))

    def show_table_context_menu(self, pos):
        menu = QMenu()
        delete_action = menu.addAction("删除选中行")
        if menu.exec_(self.table.mapToGlobal(pos)) == delete_action:
            self.delete_selected_rows()

    def delete_selected_rows(self):
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.table.removeRow(row)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete and self.table.hasFocus():
            self.delete_selected_rows()
            return
        super().keyPressEvent(event)

    def _template_from_ui(self) -> dict:
        name = self.name_edit.text().strip()
        if not name:
            raise ValueError("请填写模板名")
        configurations = self._table_configurations()
        if not configurations:
            raise ValueError("请先生成至少一个配置")
        procedures = [cb.text() for cb in self._proc_checks if cb.isChecked()]
        if not procedures:
            raise ValueError("请至少勾选一个工况")
        first = configurations[0]
        return {
            "id": self.id_edit.text().strip(),
            "name": name,
            "description": self.description_edit.toPlainText().strip(),
            "vehicle": first["vehicle"],
            "vehicle_category": first.get("vehicle_category", ""),
            "front_spring": first["front_spring"],
            "rear_spring": first["rear_spring"],
            "front_damper": first["front_damper"],
            "rear_damper": first["rear_damper"],
            "front_antiroll_bar": first["front_antiroll_bar"],
            "rear_antiroll_bar": first["rear_antiroll_bar"],
            "simulink_model": first.get("simulink_model", ""),
            "configurations": configurations,
            "procedures": procedures,
            "report": {"enabled": self.report_check.isChecked()},
            "keep_final_configuration": not self.restore_check.isChecked(),
        }

    def _table_configurations(self) -> list[dict]:
        configs = []
        for row in range(self.table.rowCount()):
            car_item = self.table.item(row, 1)
            configs.append({
                "name": self.table.item(row, 0).text(),
                "vehicle": car_item.text(),
                "vehicle_category": car_item.data(Qt.UserRole) or "",
                "front_spring": self.table.item(row, 2).text(),
                "rear_spring": self.table.item(row, 3).text(),
                "front_damper": self.table.item(row, 4).text(),
                "rear_damper": self.table.item(row, 5).text(),
                "front_antiroll_bar": self.table.item(row, 6).text(),
                "rear_antiroll_bar": self.table.item(row, 7).text(),
                "simulink_model": self.table.item(row, 8).text(),
            })
        return configs

    def _append_configuration_row(self, vehicle: str, category: str, combo: tuple):
        row = self.table.rowCount()
        self.table.setRowCount(row + 1)
        short_name = vehicle.split(" ")[0].split("_")[0][:7] or "cfg"
        values = [f"{short_name}_{row + 1}", vehicle, *combo]
        for col, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setToolTip(str(value))
            if col == 1:
                item.setData(Qt.UserRole, category)
            self.table.setItem(row, col, item)
        self.table.scrollToItem(self.table.item(row, 0))

    def _format_template(self, template: dict) -> str:
        lines = [
            f"模板: {template['name']}",
            f"配置数量: {len(template.get('configurations', []))}",
            "配置明细:",
        ]
        for cfg in template.get("configurations", []):
            lines.extend([
                f"- {cfg.get('name', '')}",
                f"  车型: {cfg.get('vehicle', '')}",
                f"  前/后弹簧: {cfg.get('front_spring', '')} / {cfg.get('rear_spring', '')}",
                f"  前/后阻尼: {cfg.get('front_damper', '')} / {cfg.get('rear_damper', '')}",
                f"  前/后稳定杆: {cfg.get('front_antiroll_bar', '')} / {cfg.get('rear_antiroll_bar', '')}",
                f"  Simulink: {cfg.get('simulink_model', '')}",
            ])
        lines.extend([
            f"工况: {', '.join(template['procedures'])}",
            f"报告: {'生成' if template['report']['enabled'] else '不生成'}",
            f"执行后恢复 CarSim: {'是' if not template['keep_final_configuration'] else '否'}",
        ])
        return "\n".join(lines)

    def _load_vehicle_tree(self, vehicles: list):
        self.vehicle_tree.clear()
        self._vehicle_items = []
        groups = {}
        for vehicle in vehicles:
            category = vehicle.get("category") or "未分类"
            groups.setdefault(category, []).append(vehicle)
        for category in sorted(groups):
            parent = QTreeWidgetItem(self.vehicle_tree)
            parent.setText(0, category)
            parent.setFlags(parent.flags() & ~Qt.ItemIsSelectable)
            for vehicle in groups[category]:
                child = QTreeWidgetItem(parent)
                child.setText(0, vehicle["name"])
                child.setToolTip(0, vehicle["name"])
                child.setData(0, Qt.UserRole, vehicle.get("raw", ""))
                child.setData(0, Qt.UserRole + 1, vehicle.get("category", ""))
                self._vehicle_items.append(child)
        self.vehicle_tree.collapseAll()

    def _filter_vehicle_tree(self, text: str):
        text = text.strip().lower()
        for item in self._vehicle_items:
            visible = not text or text in item.text(0).lower()
            item.setHidden(not visible)
            if item.parent() is not None:
                item.parent().setExpanded(bool(text and visible))

    def _load_fallback_components(self):
        options = self._workflow.template_options()
        self._update_list(self.list_f_spr["widget"], ["ori", *options.get("springs", [])])
        self._update_list(self.list_r_spr["widget"], ["ori", *options.get("springs", [])])
        self._update_list(self.list_f_dmp["widget"], ["ori", *options.get("dampers", [])])
        self._update_list(self.list_r_dmp["widget"], ["ori", *options.get("dampers", [])])
        self._update_list(self.list_f_bar["widget"], ["ori", *options.get("antiroll_bars", [])])
        self._update_list(self.list_r_bar["widget"], ["ori", *options.get("antiroll_bars", [])])
        self._update_list(self.list_simulink["widget"], ["ori"])

    def _load_procedures(self, procedures: list[str]):
        self._clear_layout(self.proc_layout)
        self._proc_checks = []
        for name in procedures:
            cb = QCheckBox(str(name))
            cb.stateChanged.connect(self._update_select_all_state)
            self.proc_layout.addWidget(cb)
            self._proc_checks.append(cb)
        self.proc_layout.addStretch()

    def _toggle_all_procedures(self, state):
        checked = state == Qt.Checked
        for cb in self._proc_checks:
            cb.blockSignals(True)
            cb.setChecked(checked)
            cb.blockSignals(False)

    def _update_select_all_state(self):
        if not self._proc_checks:
            return
        self.proc_select_all.blockSignals(True)
        self.proc_select_all.setChecked(all(cb.isChecked() for cb in self._proc_checks))
        self.proc_select_all.blockSignals(False)

    def _create_list_widget(self, title: str) -> dict:
        container = QWidget()
        layout = QVBoxLayout(container)
        label = QLabel(title)
        label.setStyleSheet("font-weight: bold;")
        widget = QListWidget()
        widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(label)
        layout.addWidget(widget)
        self._update_list(widget, ["ori"])
        return {"container": container, "widget": widget}

    def _update_list(self, list_widget: QListWidget, items: list):
        list_widget.clear()
        if not items:
            items = ["<无可用/不适用>"]
        for idx, text in enumerate(items):
            item = QListWidgetItem(str(text))
            item.setToolTip(str(text))
            if text == "<无可用/不适用>":
                item.setFlags(Qt.NoItemFlags)
            list_widget.addItem(item)
            if idx == 0 and item.flags() & Qt.ItemIsSelectable:
                item.setSelected(True)

    def _selected_values(self, list_widget: QListWidget) -> list[str]:
        selected = [
            item.text()
            for item in list_widget.selectedItems()
            if item.flags() & Qt.ItemIsSelectable
        ]
        return selected or ["ori"]

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _process_events(self):
        if QCoreApplication is not None:
            QCoreApplication.processEvents()
