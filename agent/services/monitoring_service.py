"""报警监控 service。"""


class MonitoringService:
    def __init__(self, ctx):
        self._ctx = ctx

    @property
    def _ui(self):
        return self._ctx.ui

    def toggle_alarm(self, enable: bool):
        self._ui.toggle_alarm(enable)
        if hasattr(self._ui, 'alarm_toggle'):
            self._ui.alarm_toggle.setChecked(enable)

    def is_alarm_enabled(self) -> bool:
        return getattr(self._ui, 'alarm_enabled', False)
