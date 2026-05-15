from types import SimpleNamespace

from agent.services.tuning_service import TuningService


class FakeButton:
    def __init__(self, text=""):
        self._text = text

    def setText(self, value):
        self._text = value

    def text(self):
        return self._text


class FakeSpinBox:
    def __init__(self):
        self.value = None

    def setValue(self, value):
        self.value = value


class FakeUi:
    def __init__(self):
        self.select_frontSpring_button = FakeButton("old spring")
        self.select_frontAuxM_button = FakeButton("old bar")
        self.select_car_button = FakeButton("old car")
        self.frontSpringEditText = FakeSpinBox()
        self.calls = []

    def onFrontSpringChange(self, value):
        self.calls.append(("front_spring", self.select_frontSpring_button.text(), value))

    def OnFrontSpringTextChanged(self):
        self.calls.append(("front_spring_value", self.frontSpringEditText.value))

    def onFrontAuxMChange(self, value):
        self.calls.append(("front_bar", self.select_frontAuxM_button.text(), value))

    def onCarChange(self, value):
        self.calls.append(("vehicle", self.select_car_button.text(), value))


def build_service():
    ui = FakeUi()
    module = SimpleNamespace(
        carsim=object(),
        vehicleInfoDic={"car A": "Vehicle:<group>:x"},
        springInfoDic={"spring A": "Spring:<group>:x"},
        AuxMInfoDic={"bar A": "Bar:<group>:x"},
        MxTotInfoDic={},
    )
    ctx = SimpleNamespace(ui=ui, main_module=module)
    return TuningService(ctx), ui


def test_named_spring_uses_manual_gui_callback_path():
    service, ui = build_service()

    service.set_front_left_spring("spring A")

    assert ui.select_frontSpring_button.text() == "spring A"
    assert ui.calls == [("front_spring", "spring A", "spring A")]


def test_numeric_spring_uses_manual_edit_callback_path():
    service, ui = build_service()

    service.set_front_left_spring("123.5")

    assert ui.frontSpringEditText.value == 123.5
    assert ui.calls == [("front_spring_value", 123.5)]


def test_antiroll_bar_uses_manual_gui_callback_path():
    service, ui = build_service()

    service.set_antiroll_bar(True, "bar A")

    assert ui.select_frontAuxM_button.text() == "bar A"
    assert ui.calls == [("front_bar", "bar A", "bar A")]


def test_vehicle_uses_manual_gui_callback_path():
    service, ui = build_service()

    service.select_vehicle("car A")

    assert ui.select_car_button.text() == "car A"
    assert ui.calls == [("vehicle", "car A", "car A")]
