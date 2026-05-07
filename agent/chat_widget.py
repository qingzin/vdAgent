"""
Chat Widget - 嵌入 PyQt 的聊天面板
放置在主窗口右侧，与现有 Sidebar Dock 并列
"""

from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QFrame,
    QMessageBox, QSizePolicy, QDialog, QRadioButton,
    QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QTextCursor

from agent.llm_config import LLMConfig


class LLMSettingsDialog(QDialog):
    """LLM 配置设置对话框"""

    def __init__(self, config: LLMConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("LLM 设置")
        self.setWindowFlags(
            Qt.Dialog | Qt.CustomizeWindowHint |
            Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        )
        self.setMinimumWidth(420)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        # 模式选择
        mode_group = QGroupBox("连接模式")
        mode_layout = QHBoxLayout()
        self.local_radio = QRadioButton("本地 LLM")
        self.remote_radio = QRadioButton("远程 API")
        self.local_radio.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self.local_radio)
        mode_layout.addWidget(self.remote_radio)
        mode_layout.addStretch()
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # 本地设置
        local_group = QGroupBox("本地设置")
        local_form = QFormLayout()
        self.local_url_edit = QLineEdit()
        local_form.addRow("服务地址:", self.local_url_edit)
        local_group.setLayout(local_form)
        layout.addWidget(local_group)

        # 远程设置
        remote_group = QGroupBox("远程 API 设置")
        remote_form = QFormLayout()
        self.remote_url_edit = QLineEdit()
        self.remote_key_edit = QLineEdit()
        self.remote_key_edit.setEchoMode(QLineEdit.Password)
        self.remote_model_edit = QLineEdit()
        remote_form.addRow("API 地址:", self.remote_url_edit)
        remote_form.addRow("API Key:", self.remote_key_edit)
        remote_form.addRow("模型名称:", self.remote_model_edit)
        remote_group.setLayout(remote_form)
        layout.addWidget(remote_group)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9; color: white;
                border: none; border-radius: 4px;
                padding: 8px 20px; font-weight: bold;
            }
            QPushButton:hover { background-color: #357abd; }
        """)
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self._load_config()

    def _load_config(self):
        if self.config.is_local:
            self.local_radio.setChecked(True)
        else:
            self.remote_radio.setChecked(True)
        self.local_url_edit.setText(self.config.local_url)
        self.remote_url_edit.setText(self.config.remote_url)
        self.remote_key_edit.setText(self.config.remote_api_key)
        self.remote_model_edit.setText(self.config.remote_model)

    def _on_mode_changed(self):
        is_local = self.local_radio.isChecked()
        self.local_url_edit.setEnabled(is_local)
        self.remote_url_edit.setEnabled(not is_local)
        self.remote_key_edit.setEnabled(not is_local)
        self.remote_model_edit.setEnabled(not is_local)

    def _on_save(self):
        self.config.mode = "local" if self.local_radio.isChecked() else "remote"
        self.config.local_url = self.local_url_edit.text().strip()
        self.config.remote_url = self.remote_url_edit.text().strip()
        self.config.remote_api_key = self.remote_key_edit.text().strip()
        self.config.remote_model = self.remote_model_edit.text().strip()
        self.config.save()
        self.accept()


class ConfirmDialog(QDialog):
    """非模态确认对话框 — 始终置顶，不受 Dock 布局裁剪影响。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("确认操作")
        self.setWindowFlags(
            Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint |
            Qt.WindowStaysOnTopHint
        )
        self.setMinimumWidth(400)
        self.setMaximumWidth(600)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 4px;
                padding: 12px;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.summary_label)

        btn_layout = QHBoxLayout()
        self.confirm_btn = QPushButton(" 确认执行")
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745; color: white;
                border: none; border-radius: 4px;
                padding: 8px 20px; font-weight: bold;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        self.cancel_btn = QPushButton(" 取消")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545; color: white;
                border: none; border-radius: 4px;
                padding: 8px 20px; font-weight: bold;
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        btn_layout.addStretch()
        btn_layout.addWidget(self.confirm_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def set_summary(self, text: str):
        self.summary_label.setText(f" 确认执行？\n{text}")


class ChatWidget(QDockWidget):
    """Agent 聊天面板 DockWidget"""

    def __init__(self, executor, parent=None):
        super().__init__("AI 助手", parent)
        self.executor = executor
        self.setFeatures(
            QDockWidget.DockWidgetClosable |
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable
        )
        self.setMinimumWidth(380)

        self._init_ui()
        self._connect_signals()
        self._confirm_pending = False
        self._active_confirmation_id = None

    def showEvent(self, event):
        """Dock 重新显示时恢复确认对话框。"""
        super().showEvent(event)
        if (
            self._confirm_pending
            and self.executor.has_pending_confirmation(self._active_confirmation_id)
        ):
            self.confirm_dialog.show()
            self.confirm_dialog.raise_()

    def _init_ui(self):
        """初始化聊天面板 UI"""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # --- 顶部标题栏 ---
        header = QHBoxLayout()
        title_label = QLabel("🤖 AI 控制助手")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title_label.setFont(title_font)
        header.addWidget(title_label)

        # 状态指示灯
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #888; font-size: 14px;")
        self.status_dot.setToolTip("LLM 连接状态")
        header.addWidget(self.status_dot)

        header.addStretch()

        # LLM 设置按钮
        settings_btn = QPushButton("设置")
        settings_btn.setFixedWidth(50)
        settings_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 12px;
            }
            QPushButton:hover { background: #e0e0e0; }
        """)
        settings_btn.clicked.connect(self._open_settings)
        header.addWidget(settings_btn)

        # 清空按钮
        clear_btn = QPushButton("清空")
        clear_btn.setFixedWidth(50)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 12px;
            }
            QPushButton:hover { background: #e0e0e0; }
        """)
        clear_btn.clicked.connect(self._clear_chat)
        header.addWidget(clear_btn)

        layout.addLayout(header)

        # --- 分隔线 ---
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # --- 聊天记录区域 ---
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Microsoft YaHei", 10))
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.chat_display, stretch=1)

        # --- 持久确认条：主确认入口，避免独立弹窗丢失时流程卡住 ---
        self.confirm_panel = QFrame()
        self.confirm_panel.setFrameShape(QFrame.StyledPanel)
        self.confirm_panel.setStyleSheet("""
            QFrame {
                background-color: #fff8e1;
                border: 1px solid #ffb300;
                border-radius: 4px;
            }
            QLabel {
                color: #333;
                font-size: 12px;
            }
        """)
        confirm_panel_layout = QVBoxLayout()
        confirm_panel_layout.setContentsMargins(10, 8, 10, 8)
        confirm_panel_layout.setSpacing(6)
        self.confirm_panel_label = QLabel()
        self.confirm_panel_label.setWordWrap(True)
        confirm_panel_layout.addWidget(self.confirm_panel_label)

        confirm_panel_btns = QHBoxLayout()
        confirm_panel_btns.addStretch()
        self.panel_confirm_btn = QPushButton("确认执行")
        self.panel_cancel_btn = QPushButton("取消")
        self.panel_confirm_btn.clicked.connect(self._on_confirm)
        self.panel_cancel_btn.clicked.connect(self._on_cancel)
        confirm_panel_btns.addWidget(self.panel_confirm_btn)
        confirm_panel_btns.addWidget(self.panel_cancel_btn)
        confirm_panel_layout.addLayout(confirm_panel_btns)
        self.confirm_panel.setLayout(confirm_panel_layout)
        self.confirm_panel.setVisible(False)
        layout.addWidget(self.confirm_panel)

        # --- 确认对话框（独立窗口，始终可见）---
        self.confirm_dialog = ConfirmDialog(self)
        self.confirm_btn = self.confirm_dialog.confirm_btn
        self.cancel_btn = self.confirm_dialog.cancel_btn

        # --- 思考中指示器（默认隐藏）---
        self.thinking_label = QLabel("⏳ AI 正在思考...")
        self.thinking_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-style: italic;
                padding: 4px;
                font-size: 12px;
            }
        """)
        self.thinking_label.setVisible(False)
        layout.addWidget(self.thinking_label)

        # --- 输入区域 ---
        input_layout = QHBoxLayout()
        input_layout.setSpacing(4)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText('输入指令，如"把车型换成 SUV_baseline"')
        self.input_field.setFont(QFont("Microsoft YaHei", 10))
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #4a90d9;
            }
        """)
        input_layout.addWidget(self.input_field, stretch=1)

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedWidth(60)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #357abd; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        input_layout.addWidget(self.send_btn)

        layout.addLayout(input_layout)

        # --- 底部提示 ---
        hint = QLabel("按 Enter 发送 | 所有操作需确认后执行")
        hint.setStyleSheet("color: #999; font-size: 10px;")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        container.setLayout(layout)
        self.setWidget(container)

        # 欢迎消息
        self._append_system_message(
            "你好！我是 AI 控制助手。\n"
            "你可以用自然语言告诉我你想做的操作，例如：\n"
            "• 把车型换成 XXX\n"
            "• 把摩擦增益改成 1.5\n"
            "• 发送平台指令 4\n"
            "• 运行 CarSim"
        )

    def _connect_signals(self):
        """连接信号和槽"""
        # 用户输入
        self.input_field.returnPressed.connect(self._on_send)
        self.send_btn.clicked.connect(self._on_send)

        # Agent 信号
        self.executor.response_ready.connect(self._on_agent_response)
        self.executor.confirm_request.connect(self._on_confirm_request)
        self.executor.action_done.connect(self._on_action_done)
        self.executor.thinking.connect(self._on_thinking)

    def _on_send(self):
        """发送用户消息"""
        text = self.input_field.text().strip()
        if not text:
            return

        self.input_field.clear()
        self._append_user_message(text)

        # 禁用输入直到收到回复
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)

        self.executor.process_user_input(text)

    def _on_agent_response(self, text):
        """收到 Agent 文本回复"""
        self._confirm_pending = False
        self._active_confirmation_id = None
        self._hide_confirm_panel()
        self.confirm_dialog.hide()
        self._append_agent_message(text)
        self._enable_input()

    def _on_confirm_request(self, confirmation_id, name, params, summary):
        """收到确认请求"""
        self._confirm_pending = True
        self._active_confirmation_id = confirmation_id
        self._append_agent_message(f"我将执行以下操作：\n{summary}")
        self._show_confirm_panel(confirmation_id, name, summary)
        self._recreate_confirm_dialog(confirmation_id)
        self.confirm_dialog.set_summary(summary)
        self.confirm_dialog.show()
        self.confirm_dialog.raise_()
        self.confirm_dialog.activateWindow()
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)

    def _on_confirm(self, confirmation_id=None, dialog=None):
        """用户确认执行"""
        confirmation_id = confirmation_id or self._active_confirmation_id
        is_active = confirmation_id == self._active_confirmation_id
        if is_active:
            self._confirm_pending = False
            self._active_confirmation_id = None
            self._hide_confirm_panel()
            self._append_user_message(" 确认执行")
        (dialog or self.confirm_dialog).hide()
        self.executor.confirm_action(confirmation_id)

    def _on_cancel(self, confirmation_id=None, dialog=None):
        """用户取消执行"""
        confirmation_id = confirmation_id or self._active_confirmation_id
        is_active = confirmation_id == self._active_confirmation_id
        if is_active:
            self._confirm_pending = False
            self._active_confirmation_id = None
            self._hide_confirm_panel()
            self._append_user_message(" 取消")
        (dialog or self.confirm_dialog).hide()
        self.executor.cancel_action(confirmation_id)
        if is_active:
            self._enable_input()

    def _on_action_done(self, result):
        """操作执行完成"""
        if not self.executor.has_pending_confirmation(self._active_confirmation_id):
            self._confirm_pending = False
            self._active_confirmation_id = None
            self._hide_confirm_panel()
            self.confirm_dialog.hide()
        self._append_system_message(f"✅ {result}")
        if not self._confirm_pending:
            self._enable_input()

    def _on_thinking(self, is_thinking):
        """思考状态变化"""
        self.thinking_label.setVisible(is_thinking)

    def _enable_input(self):
        """重新启用输入"""
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()

    def _clear_chat(self):
        """清空聊天记录"""
        self._confirm_pending = False
        self._active_confirmation_id = None
        self.chat_display.clear()
        self.executor.clear_history()
        self._hide_confirm_panel()
        self.confirm_dialog.hide()
        self._enable_input()
        self._append_system_message("对话已清空。请输入新的指令。")

    def _show_confirm_panel(self, confirmation_id, action_name, summary):
        self.confirm_panel_label.setText(
            f"待确认操作 ({action_name})\n确认编号: {confirmation_id}\n{summary}"
        )
        self.confirm_panel.setVisible(True)

    def _hide_confirm_panel(self):
        self.confirm_panel.setVisible(False)
        self.confirm_panel_label.clear()

    def _recreate_confirm_dialog(self, confirmation_id):
        """Create a fresh dialog for each request to avoid stale hidden Qt windows."""
        old_dialog = getattr(self, "confirm_dialog", None)
        if old_dialog is not None:
            try:
                old_dialog.hide()
            except RuntimeError:
                pass

        self.confirm_dialog = ConfirmDialog(self)
        self.confirm_btn = self.confirm_dialog.confirm_btn
        self.cancel_btn = self.confirm_dialog.cancel_btn
        dialog = self.confirm_dialog
        self.confirm_btn.clicked.connect(
            lambda checked=False, cid=confirmation_id, dlg=dialog: self._on_confirm(cid, dlg)
        )
        self.cancel_btn.clicked.connect(
            lambda checked=False, cid=confirmation_id, dlg=dialog: self._on_cancel(cid, dlg)
        )

    # --- 消息渲染 ---

    def _append_user_message(self, text):
        self.chat_display.append(
            f'<div style="margin: 4px 0; text-align: right;">'
            f'<span style="background-color: #4a90d9; color: white; '
            f'padding: 6px 10px; border-radius: 8px; '
            f'display: inline-block; max-width: 80%; text-align: left;">'
            f'{text}</span></div>'
        )
        self._scroll_to_bottom()

    def _append_agent_message(self, text):
        # 替换换行为 <br>
        html_text = text.replace('\n', '<br>')
        self.chat_display.append(
            f'<div style="margin: 4px 0;">'
            f'<span style="background-color: #e8e8e8; color: #333; '
            f'padding: 6px 10px; border-radius: 8px; '
            f'display: inline-block; max-width: 80%;">'
            f'🤖 {html_text}</span></div>'
        )
        self._scroll_to_bottom()

    def _append_system_message(self, text):
        html_text = text.replace('\n', '<br>')
        self.chat_display.append(
            f'<div style="margin: 4px 0; text-align: center;">'
            f'<span style="color: #888; font-size: 11px;">'
            f'{html_text}</span></div>'
        )
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextCursor(cursor)

    def append_system_message(self, text: str):
        """供外部调用的系统消息追加方法。"""
        self._append_system_message(text)

    def _open_settings(self):
        """打开 LLM 设置对话框。"""
        config = self.executor.llm_client.config
        dialog = LLMSettingsDialog(config, self.window())
        if dialog.exec_() == QDialog.Accepted:
            mode_text = "本地 LLM" if config.is_local else "远程 API"
            self._append_system_message(f"LLM 模式已切换为: {mode_text}")
            # 立即检查新连接状态
            QTimer.singleShot(500, lambda: self.update_connection_status(
                self.executor.llm_client is not None and
                self.executor.llm_client.check_connection()
            ))

    def update_connection_status(self, connected: bool):
        """更新 LLM 连接状态指示"""
        config = self.executor.llm_client.config if self.executor.llm_client else None
        if config and not config.is_local:
            self.status_dot.setStyleSheet("color: #ff9800; font-size: 14px;")
            self.status_dot.setToolTip(f"远程 API: {config.remote_model}")
            return
        if connected:
            self.status_dot.setStyleSheet("color: #28a745; font-size: 14px;")
            self.status_dot.setToolTip("LLM 已连接")
        else:
            self.status_dot.setStyleSheet("color: #dc3545; font-size: 14px;")
            self.status_dot.setToolTip("LLM 未连接")
        """更新 LLM 连接状态指示"""
        if connected:
            self.status_dot.setStyleSheet("color: #28a745; font-size: 14px;")
            self.status_dot.setToolTip("LLM 已连接")
        else:
            self.status_dot.setStyleSheet("color: #dc3545; font-size: 14px;")
            self.status_dot.setToolTip("LLM 未连接")
