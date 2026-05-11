"""Lightweight workflow progress panel for agent-driven demo flows."""

try:
    from PyQt5.QtCore import Qt, QCoreApplication
    from PyQt5.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QTextEdit,
        QPushButton,
    )
except ImportError:  # pragma: no cover
    QWidget = object
    Qt = None
    QCoreApplication = None


class WorkflowPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_result = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.title = QLabel("Agent实验流程")
        self.title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.title)

        self.subtitle = QLabel("等待模板执行")
        self.subtitle.setWordWrap(True)
        layout.addWidget(self.subtitle)

        self.stage_list = QListWidget()
        layout.addWidget(self.stage_list, 2)

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

    def start_workflow(self, name: str, description: str = ""):
        self.last_result = {}
        self.title.setText(f"Agent实验流程 - {name}")
        self.subtitle.setText(description or "")
        self.stage_list.clear()
        self.log.clear()
        self.open_result_btn.setEnabled(False)
        self.open_report_btn.setEnabled(False)
        self._process_events()

    def append_stage(self, stage: str, message: str):
        text = f"{stage}: {message}"
        self.stage_list.addItem(text)
        self.stage_list.scrollToBottom()
        self.log.append(text)
        self._process_events()

    def finish_workflow(self, success: bool, message: str, result: dict = None):
        self.last_result = result or {}
        self.append_stage("完成" if success else "失败", message)
        self.open_result_btn.setEnabled(bool(self.last_result.get("result_folder")))
        self.open_report_btn.setEnabled(bool(self.last_result.get("report_path")))

    def open_result_folder(self):
        path = self.last_result.get("result_folder")
        if path:
            import os
            os.startfile(path)

    def open_report(self):
        path = self.last_result.get("report_path")
        if path:
            import os
            os.startfile(path)

    def _process_events(self):
        if QCoreApplication is not None:
            QCoreApplication.processEvents()
