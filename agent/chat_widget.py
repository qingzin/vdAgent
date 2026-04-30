"""
Chat Widget - 嵌入 PyQt 的聊天面板
放置在主窗口右侧，与现有 Sidebar Dock 并列
"""

from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QFrame,
    QMessageBox, QSizePolicy, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QTextCursor


class ConfirmDialog(QDialog):
    """非模态确认对话框 — 始终置顶，不受 Dock 布局裁剪影响。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("确认操作")
        self.setWindowFlags(
            Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint
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

        # 确认/取消
        self.confirm_btn.clicked.connect(self._on_confirm)
        self.cancel_btn.clicked.connect(self._on_cancel)

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
        self.confirm_dialog.hide()
        self._append_agent_message(text)
        self._enable_input()

    def _on_confirm_request(self, name, params, summary):
        """收到确认请求"""
        self._append_agent_message(f"我将执行以下操作：\n{summary}")
        self.confirm_dialog.set_summary(summary)
        self.confirm_dialog.show()
        self.confirm_dialog.raise_()
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)

    def _on_confirm(self):
        """用户确认执行"""
        self.confirm_dialog.hide()
        self._append_user_message(" 确认执行")
        self.executor.confirm_action()

    def _on_cancel(self):
        """用户取消执行"""
        self.confirm_dialog.hide()
        self._append_user_message(" 取消")
        self.executor.cancel_action()
        self._enable_input()

    def _on_action_done(self, result):
        """操作执行完成"""
        self.confirm_dialog.hide()
        self._append_system_message(f"✅ {result}")
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
        self.chat_display.clear()
        self.executor.clear_history()
        self.confirm_dialog.hide()
        self._enable_input()
        self._append_system_message("对话已清空。请输入新的指令。")

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

    def update_connection_status(self, connected: bool):
        """更新 LLM 连接状态指示"""
        if connected:
            self.status_dot.setStyleSheet("color: #28a745; font-size: 14px;")
            self.status_dot.setToolTip("LLM 已连接")
        else:
            self.status_dot.setStyleSheet("color: #dc3545; font-size: 14px;")
            self.status_dot.setToolTip("LLM 未连接")
