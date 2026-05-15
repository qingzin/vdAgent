import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication

from agent.chat_widget import ChatWidget
from agent.runtime_events import AgentEvent


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
        if confirmation_id == self._pending_confirmation_id:
            self._pending_confirmation_id = None

    def cancel_action(self, confirmation_id=None):
        self.canceled_ids.append(confirmation_id)
        if confirmation_id == self._pending_confirmation_id:
            self._pending_confirmation_id = None

    def clear_history(self):
        self._pending_confirmation_id = None


class FakeEventExecutor(FakeExecutor):
    event_emitted = pyqtSignal(object)


def _app():
    return QApplication.instance() or QApplication(sys.argv)


def test_confirm_dialog_passes_current_confirmation_id_each_time():
    app = _app()
    executor = FakeExecutor()
    widget = ChatWidget(executor)
    widget.show()
    app.processEvents()

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
        assert widget.confirm_panel.isVisible()
        assert confirmation_id in widget.confirm_panel_label.text()
        dialogs.append(widget.confirm_dialog)

        widget.panel_confirm_btn.click()
        app.processEvents()

    assert executor.confirmed_ids == ["confirm-0", "confirm-1", "confirm-2"]
    assert len({id(dialog) for dialog in dialogs}) == 3

    widget.close()
    app.processEvents()


def test_old_confirm_dialog_button_keeps_old_confirmation_id():
    app = _app()
    executor = FakeExecutor()
    widget = ChatWidget(executor)
    widget.show()
    app.processEvents()

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
    assert widget.confirm_panel.isVisible()
    assert new_dialog.isVisible()

    widget.close()
    app.processEvents()


def test_confirm_panel_works_when_dialog_is_hidden():
    app = _app()
    executor = FakeExecutor()
    widget = ChatWidget(executor)
    widget.show()
    app.processEvents()

    executor._pending_confirmation_id = "confirm-panel"
    widget._on_confirm_request("confirm-panel", "panel_action", {}, "panel summary")
    widget.confirm_dialog.hide()
    app.processEvents()

    assert widget.confirm_panel.isVisible()
    widget.panel_confirm_btn.click()
    app.processEvents()

    assert executor.confirmed_ids == ["confirm-panel"]
    assert not widget.confirm_panel.isVisible()

    widget.close()
    app.processEvents()


def test_action_done_does_not_clear_active_confirmation_panel():
    app = _app()
    executor = FakeExecutor()
    widget = ChatWidget(executor)
    widget.show()
    app.processEvents()

    executor._pending_confirmation_id = "confirm-active"
    widget._on_confirm_request("confirm-active", "active_action", {}, "active summary")
    app.processEvents()

    widget._on_action_done("previous action done")
    app.processEvents()

    assert widget._active_confirmation_id == "confirm-active"
    assert widget.confirm_panel.isVisible()

    widget.close()
    app.processEvents()


def test_action_done_followed_by_next_confirm_keeps_next_panel_visible():
    app = _app()
    executor = FakeExecutor()
    widget = ChatWidget(executor)
    widget.show()
    app.processEvents()

    executor._pending_confirmation_id = "confirm-first"
    widget._on_confirm_request("confirm-first", "first_action", {}, "first summary")
    app.processEvents()

    widget.panel_confirm_btn.click()
    widget._on_action_done("first action done")
    executor._pending_confirmation_id = "confirm-second"
    widget._on_confirm_request("confirm-second", "second_action", {}, "second summary")
    app.processEvents()

    assert widget._active_confirmation_id == "confirm-second"
    assert widget.confirm_panel.isVisible()
    assert "second_action" in widget.confirm_panel_label.text()
    assert "confirm-second" in widget.confirm_panel_label.text()

    widget.close()
    app.processEvents()


def test_chat_widget_consumes_runtime_approval_event():
    app = _app()
    executor = FakeEventExecutor()
    widget = ChatWidget(executor)
    widget.show()
    app.processEvents()

    executor._pending_confirmation_id = "approval-1"
    executor.event_emitted.emit(AgentEvent(
        stream="approval",
        event_type="approval_requested",
        payload={
            "approval_id": "approval-1",
            "action_name": "set_spring",
            "params": {"position": "front"},
            "summary": "set spring",
        },
    ))
    app.processEvents()

    assert widget._active_confirmation_id == "approval-1"
    assert widget.confirm_panel.isVisible()
    assert "set_spring" in widget.confirm_panel_label.text()

    widget.close()
    app.processEvents()
