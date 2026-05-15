from agent.actions import misc_actions
from agent.registry import ActionRegistry


class TextField:
    def __init__(self, value):
        self._value = value

    def text(self):
        return self._value


class FakeUi:
    carName = "SUV"
    run_scheme = 2
    alarm_enabled = True

    def __init__(self):
        self.offset_x = TextField("1")
        self.offset_y = TextField("2")
        self.offset_z = TextField("3")
        self.preset_car_model = ""
        self.preset_tuning_parts = ""
        self.preset_evaluator = ""
        self.preset_condition = ""


class FakeMetadataService:
    def get_all(self):
        return {}

    def set_fields(self, **kwargs):
        return {k: v for k, v in kwargs.items() if v is not None}


class FakeTuningService:
    def get_current_setup(self):
        return "当前车型: SUV; 前稳定杆: 1150"


class FakeSceneService:
    def get_map(self):
        return "性能广场"

    def get_start_point(self):
        return "默认起点"

    def get_condition(self):
        return "单移线"


class FakeRecordingService:
    def get_status(self):
        return "当前记录状态: 未记录"


class FakeHapticService:
    def get_all(self):
        return {"friction": 1, "damping": 2}


class FakeCtx:
    def __init__(self):
        self.ui = FakeUi()
        self.services = {
            "metadata": FakeMetadataService(),
            "tuning": FakeTuningService(),
            "scene": FakeSceneService(),
            "recording": FakeRecordingService(),
            "haptic": FakeHapticService(),
        }

    def service(self, name):
        return self.services.get(name)


def test_get_system_status_returns_core_state():
    registry = ActionRegistry()
    misc_actions.register(registry, FakeCtx())

    result = registry.execute("get_system_status", {})

    assert "当前车型: SUV" in result
    assert "性能广场" in result
    assert "当前记录状态: 未记录" in result
    assert "摩擦=1" in result
    assert "平台位置偏置: X=1, Y=2, Z=3" in result
    assert "报警监控: 开启" in result
