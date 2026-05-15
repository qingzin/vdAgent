"""报警监控 service。"""


from agent.services._base import BaseService

class MonitoringService(BaseService):


    def toggle_alarm(self, enable: bool):
        self._ui.toggle_alarm(enable)
        if hasattr(self._ui, 'alarm_toggle'):
            self._ui.alarm_toggle.setChecked(enable)

    def is_alarm_enabled(self) -> bool:
        return getattr(self._ui, 'alarm_enabled', False)
