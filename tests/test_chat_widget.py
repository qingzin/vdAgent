import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication

from agent.chat_widget import ChatWidget


class FakeExecutor(QObject):
    response_ready = pyqtSignal(str)
    confirm_request = pyqtSignal(str, str, dict, str)
    action_done = pyqtSignal(str)
    thinking = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._pending_confirmation_id = None
        self.confirmed_ids = []
        self.canceled_ids = []

    def has_pending_confirmation(self, confirmation_id=None):
        if self._pending_confirmation_id is None:
            return False
        return confirmation_id in (None, self._pending_confirmation_id)

    def process_user_input(self, text):
        pass

    def confirm_action(self, confirmation_id=None):
        self.confirmed_ids.append(confirmation_id)
        self._pending_confirmation_id = None

    def cancel_action(self, confirmation_id=None):
        self.canceled_ids.append(confirmation_id)
        self._pending_confirmation_id = None

    def clear_history(self):
        self._pending_confirmation_id = None


def _app():
    return QApplication.instance() or QApplication(sys.argv)


def test_confirm_dialog_passes_current_confirmation_id_each_time():
    app = _app()
    executor = FakeExecutor()
    widget = ChatWidget(executor)

    dialogs = []
    for i in range(3):
        confirmation_id = f"confirm-{i}"
        executor._pending_confirmation_id = confirmation_id
        widget._on_confirm_request(
            confirmation_id,
            f"action_{i}",
            {"step": i},
            f"summary {i}",
        )
        app.processEvents()

        assert widget._active_confirmation_id == confirmation_id
        assert widget.confirm_dialog.isVisible()
        dialogs.append(widget.confirm_dialog)

        widget._on_confirm()
        app.processEvents()

    assert executor.confirmed_ids == ["confirm-0", "confirm-1", "confirm-2"]
    assert len({id(dialog) for dialog in dialogs}) == 3

    widget.close()
    app.processEvents()


def test_old_confirm_dialog_button_keeps_old_confirmation_id():
    app = _app()
    executor = FakeExecutor()
    widget = ChatWidget(executor)

    executor._pending_confirmation_id = "confirm-old"
    widget._on_confirm_request("confirm-old", "old_action", {}, "old")
    old_dialog = widget.confirm_dialog
    app.processEvents()

    executor._pending_confirmation_id = "confirm-new"
    widget._on_confirm_request("confirm-new", "new_action", {}, "new")
    new_dialog = widget.confirm_dialog
    app.processEvents()

    old_dialog.confirm_btn.click()
    app.processEvents()

    assert executor.confirmed_ids[-1] == "confirm-old"
    assert widget._active_confirmation_id == "confirm-new"
    assert new_dialog.isVisible()

    widget.close()
    app.processEvents()
