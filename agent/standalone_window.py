"""Minimal standalone agent window."""

import json
from dataclasses import asdict

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from agent.standalone_service import StandaloneAgentService


class StandaloneAgentWindow(QMainWindow):
    def __init__(self, service: StandaloneAgentService, parent=None):
        super().__init__(parent)
        self.service = service
        self.executor = service.executor
        self.setWindowTitle("Standalone Agent")
        self.resize(1120, 720)
        self._init_ui()
        self._connect_signals()
        self._refresh_all()

    def _init_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)

        header = QHBoxLayout()
        self.connection_label = QLabel("LLM: checking")
        header.addWidget(QLabel("Standalone vdAgent"))
        header.addStretch()
        header.addWidget(self.connection_label)
        root_layout.addLayout(header)

        splitter = QSplitter()
        root_layout.addWidget(splitter, stretch=1)

        chat_panel = QWidget()
        chat_layout = QVBoxLayout(chat_panel)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("Chat with the agent here.")
        chat_layout.addWidget(self.chat_display, stretch=1)

        self.confirm_panel = QWidget()
        confirm_layout = QVBoxLayout(self.confirm_panel)
        self.confirm_label = QLabel("")
        self.confirm_label.setWordWrap(True)
        confirm_layout.addWidget(self.confirm_label)
        confirm_buttons = QHBoxLayout()
        self.confirm_button = QPushButton("Confirm")
        self.cancel_button = QPushButton("Cancel")
        confirm_buttons.addWidget(self.confirm_button)
        confirm_buttons.addWidget(self.cancel_button)
        confirm_layout.addLayout(confirm_buttons)
        self.confirm_panel.setVisible(False)
        chat_layout.addWidget(self.confirm_panel)

        input_row = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("例如: 查询当前配置 / 把前弹簧改成 sport_spring / 运行 CarSim")
        self.send_button = QPushButton("Send")
        input_row.addWidget(self.input_field, stretch=1)
        input_row.addWidget(self.send_button)
        chat_layout.addLayout(input_row)
        splitter.addWidget(chat_panel)

        self.tabs = QTabWidget()
        self.history_view = QTextEdit()
        self.history_view.setReadOnly(True)
        self.changes_view = QTextEdit()
        self.changes_view.setReadOnly(True)
        self.snapshot_view = QTextEdit()
        self.snapshot_view.setReadOnly(True)
        self.actions_view = QTextEdit()
        self.actions_view.setReadOnly(True)
        self.tabs.addTab(self.history_view, "Execution History")
        self.tabs.addTab(self.changes_view, "State Changes")
        self.tabs.addTab(self.snapshot_view, "Current State")
        self.tabs.addTab(self.actions_view, "Actions")
        splitter.addWidget(self.tabs)
        splitter.setSizes([520, 600])

        self.setCentralWidget(root)
        self.chat_display.append("System: Standalone agent is ready. Existing actions are reused through the decoupled state adapter.")

    def _connect_signals(self) -> None:
        self.send_button.clicked.connect(self._send)
        self.input_field.returnPressed.connect(self._send)
        self.confirm_button.clicked.connect(self._confirm)
        self.cancel_button.clicked.connect(self._cancel)
        self.executor.response_ready.connect(self._on_response)
        self.executor.confirm_request.connect(self._on_confirm_request)
        self.executor.action_done.connect(self._on_action_done)
        self.executor.thinking.connect(self._on_thinking)

        self.connection_timer = QTimer(self)
        self.connection_timer.timeout.connect(self._check_connection)
        self.connection_timer.start(10000)
        QTimer.singleShot(200, self._check_connection)

    def _send(self) -> None:
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self.chat_display.append(f"User: {text}")
        self._set_input_enabled(False)
        self.executor.process_user_input(text)

    def _confirm(self) -> None:
        self.confirm_panel.setVisible(False)
        self.chat_display.append("User: Confirm")
        self.executor.confirm_action()

    def _cancel(self) -> None:
        self.confirm_panel.setVisible(False)
        self.chat_display.append("User: Cancel")
        self.executor.cancel_action()
        self._set_input_enabled(True)
        self._refresh_all()

    def _on_response(self, text: str) -> None:
        self.chat_display.append(f"Agent: {text}")
        self._set_input_enabled(True)
        self._refresh_all()

    def _on_confirm_request(self, name: str, params: dict, summary: str) -> None:
        self.chat_display.append(f"Agent requested action: {name}\n{summary}")
        self.confirm_label.setText(f"{name}\n{json.dumps(params, ensure_ascii=False, indent=2)}\n\n{summary}")
        self.confirm_panel.setVisible(True)
        self._set_input_enabled(False)
        self._refresh_all()

    def _on_action_done(self, result: str) -> None:
        self.chat_display.append(f"Action result: {result}")
        self._set_input_enabled(True)
        self._refresh_all()

    def _on_thinking(self, thinking: bool) -> None:
        if thinking:
            self.connection_label.setText("LLM: thinking")
        else:
            self._check_connection()

    def _set_input_enabled(self, enabled: bool) -> None:
        self.input_field.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
        if enabled:
            self.input_field.setFocus()

    def _check_connection(self) -> None:
        connected = self.service.check_connection()
        self.connection_label.setText("LLM: connected" if connected else "LLM: offline")

    def _refresh_all(self) -> None:
        self._refresh_history()
        self._refresh_changes()
        self._refresh_snapshot()
        self._refresh_actions()

    def _refresh_history(self) -> None:
        records = [asdict(record) for record in self.service.state.executions]
        self.history_view.setPlainText(json.dumps(records, ensure_ascii=False, indent=2))

    def _refresh_changes(self) -> None:
        records = [asdict(record) for record in self.service.state.changes]
        self.changes_view.setPlainText(json.dumps(records, ensure_ascii=False, indent=2))

    def _refresh_snapshot(self) -> None:
        self.snapshot_view.setPlainText(json.dumps(self.service.snapshot(), ensure_ascii=False, indent=2))

    def _refresh_actions(self) -> None:
        actions = []
        for name in self.service.registry.get_action_names():
            actions.append(self.service.find_action(name))
        self.actions_view.setPlainText(json.dumps(actions, ensure_ascii=False, indent=2))


def run_standalone_agent(llm_url: str = "http://127.0.0.1:8080") -> int:
    app = QApplication.instance() or QApplication([])
    service = StandaloneAgentService(llm_url=llm_url)
    window = StandaloneAgentWindow(service)
    window.show()
    return app.exec_()
