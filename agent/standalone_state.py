"""Standalone agent state and SimulatorUI-compatible adapter.

The standalone window must reuse the existing action registry without importing
``main.py``.  This module provides a small in-memory simulator facade that
matches the parts of ``SimulatorUI`` and module globals used by actions.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ChangeRecord:
    target: str
    before: Any
    after: Any
    source: str = "state"
    created_at: str = field(default_factory=_now_iso)


@dataclass
class ExecutionRecord:
    action_name: str
    params: Dict[str, Any]
    result: str
    changes: List[ChangeRecord]
    status: str = "ok"
    created_at: str = field(default_factory=_now_iso)


@dataclass
class StandaloneAgentState:
    changes: List[ChangeRecord] = field(default_factory=list)
    executions: List[ExecutionRecord] = field(default_factory=list)


class StateTracker:
    def __init__(self, state: Optional[StandaloneAgentState] = None):
        self.state = state or StandaloneAgentState()
        self._action_start_index = 0

    def record_change(self, target: str, before: Any, after: Any,
                      source: str = "state") -> None:
        if before == after:
            return
        self.state.changes.append(ChangeRecord(
            target=target,
            before=before,
            after=after,
            source=source,
        ))

    def begin_action(self) -> None:
        self._action_start_index = len(self.state.changes)

    def finish_action(self, action_name: str, params: Dict[str, Any],
                      result: str) -> ExecutionRecord:
        changes = self.state.changes[self._action_start_index:]
        status = "error" if str(result).startswith(("执行失败", "错误", "failed")) else "ok"
        record = ExecutionRecord(
            action_name=action_name,
            params=dict(params or {}),
            result=str(result),
            changes=list(changes),
            status=status,
        )
        self.state.executions.append(record)
        return record


class TrackedLineEdit:
    def __init__(self, tracker: StateTracker, name: str, value: Any = ""):
        self._tracker = tracker
        self._name = name
        self._value = str(value)

    def text(self) -> str:
        return self._value

    def setText(self, value: Any) -> None:
        before = self._value
        self._value = str(value)
        self._tracker.record_change(self._name, before, self._value, "widget")


class TrackedSpinBox:
    def __init__(self, tracker: StateTracker, name: str, value: float = 0.0):
        self._tracker = tracker
        self._name = name
        self._value = value

    def value(self) -> float:
        return self._value

    def setValue(self, value: float) -> None:
        before = self._value
        self._value = value
        self._tracker.record_change(self._name, before, self._value, "widget")


class TrackedButton:
    def __init__(self, tracker: StateTracker, name: str, text: str = ""):
        self._tracker = tracker
        self._name = name
        self._text = text

    def text(self) -> str:
        return self._text

    def setText(self, text: str) -> None:
        before = self._text
        self._text = str(text)
        self._tracker.record_change(self._name, before, self._text, "widget")


class TrackedCheckBox:
    def __init__(self, tracker: StateTracker, name: str, checked: bool = False):
        self._tracker = tracker
        self._name = name
        self._checked = bool(checked)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool) -> None:
        before = self._checked
        self._checked = bool(checked)
        self._tracker.record_change(self._name, before, self._checked, "widget")


class TrackedComboBox:
    def __init__(self, tracker: StateTracker, name: str, items: List[Any]):
        self._tracker = tracker
        self._name = name
        self._items = []
        for item in items:
            if isinstance(item, tuple):
                self._items.append(item)
            else:
                self._items.append((str(item), None))
        self._index = 0 if self._items else -1

    def count(self) -> int:
        return len(self._items)

    def itemText(self, index: int) -> str:
        return self._items[index][0]

    def itemData(self, index: int) -> Any:
        return self._items[index][1]

    def currentText(self) -> str:
        if self._index < 0:
            return ""
        return self._items[self._index][0]

    def setCurrentIndex(self, index: int) -> None:
        if index < 0 or index >= len(self._items):
            return
        before = self.currentText()
        self._index = index
        self._tracker.record_change(self._name, before, self.currentText(), "widget")

    def setCurrentText(self, text: str) -> None:
        for idx, item in enumerate(self._items):
            if item[0] == text:
                self.setCurrentIndex(idx)
                return
        before = self.currentText()
        self._items.append((str(text), None))
        self._index = len(self._items) - 1
        self._tracker.record_change(self._name, before, self.currentText(), "widget")


class FakeCarsim:
    def __init__(self, tracker: StateTracker):
        self._tracker = tracker
        self._blue_links = {
            "#BlueLink0": ["Suspension: Spring", "baseline_front_spring", "demo"],
            "#BlueLink2": ["Suspension: Auxiliary Roll Moment", "baseline_bar", "demo"],
            "#BlueLink3": ["Suspension: Spring", "baseline_right_spring", "demo"],
        }
        self._yellow = {}

    def GoHome(self) -> None:
        self._tracker.record_change("carsim.navigation", None, "home", "carsim")

    def BlueLink(self, link: str, library: str, dataset: str, group: str) -> None:
        before = tuple(self._blue_links.get(link, ["", "", ""]))
        self._blue_links[link] = [library, dataset, group]
        self._tracker.record_change(f"carsim.{link}", before, tuple(self._blue_links[link]), "carsim")

    def GetBlueLink(self, link: str):
        return self._blue_links.get(link, ["", "", "demo"])

    def Yellow(self, key: str, value: Any) -> None:
        before = self._yellow.get(key)
        self._yellow[key] = value
        self._tracker.record_change(f"carsim.yellow.{key}", before, value, "carsim")

    def Gotolibrary(self, library: str, dataset: str, category: str) -> None:
        self._tracker.record_change("carsim.library", None, f"{library}/{dataset}/{category}", "carsim")

    def GetRing(self, _name: str) -> str:
        return "CONSTANT"

    def GetYellow(self, key: str) -> Any:
        return self._yellow.get(key, 100.0)


class FakePlot:
    def __init__(self, tracker: StateTracker, name: str):
        self._tracker = tracker
        self._name = name
        self._range = (0.0, 12.0)

    def setXRange(self, x_min: float, x_max: float) -> None:
        before = self._range
        self._range = (float(x_min), float(x_max))
        self._tracker.record_change(f"plot.{self._name}.x_range", before, self._range, "plot")


class StandaloneSimulatorAdapter:
    """Small facade that records changes made by existing actions."""

    TRACKED_ATTRS = {
        "carName",
        "frontSpringName",
        "rearSpringName",
        "frontRightSpringName",
        "rearRightSpringName",
        "frontAuxMName",
        "rearAuxMName",
        "gain_fri",
        "gain_dam",
        "gain_feedback",
        "gain_sa",
        "gain_all",
        "sw_rate",
        "record_disusx",
        "is_video_recording",
        "is_par_save",
        "auto_record",
        "preset_car_model",
        "preset_tuning_parts",
        "preset_evaluator",
        "preset_condition",
        "run_scheme",
    }

    def __init__(self, tracker: StateTracker):
        object.__setattr__(self, "_tracker", tracker)
        object.__setattr__(self, "_initialized", False)

        self.run_scheme = 1
        self.carName = "baseline_sedan"
        self.frontSpringName = "baseline_front_spring"
        self.rearSpringName = "baseline_rear_spring"
        self.frontRightSpringName = "baseline_front_right_spring"
        self.rearRightSpringName = "baseline_rear_right_spring"
        self.frontAuxMName = "baseline_front_bar"
        self.rearAuxMName = "baseline_rear_bar"
        self.gain_fri = 0
        self.gain_dam = 0
        self.gain_feedback = 0
        self.gain_sa = 0
        self.gain_all = 1
        self.sw_rate = 10
        self.record_disusx = False
        self.is_video_recording = False
        self.is_par_save = False
        self.auto_record = 0
        self.preset_car_model = ""
        self.preset_tuning_parts = ""
        self.preset_evaluator = ""
        self.preset_condition = ""
        self.is_recording_imu = False
        self.is_recording_carsim = False
        self.is_recording_moog = False
        self.is_recording_disusx = False
        self.is_recording_visual_compensator = False

        self.select_car_button = TrackedButton(tracker, "ui.select_car_button", self.carName)
        self.select_frontSpring_button = TrackedButton(tracker, "ui.select_frontSpring_button", self.frontSpringName)
        self.select_rearSpring_button = TrackedButton(tracker, "ui.select_rearSpring_button", self.rearSpringName)
        self.select_frontRightSpring_button = TrackedButton(tracker, "ui.select_frontRightSpring_button", self.frontRightSpringName)
        self.select_rearRightSpring_button = TrackedButton(tracker, "ui.select_rearRightSpring_button", self.rearRightSpringName)
        self.select_frontAuxM_button = TrackedButton(tracker, "ui.select_frontAuxM_button", self.frontAuxMName)
        self.select_rearAuxM_button = TrackedButton(tracker, "ui.select_rearAuxM_button", self.rearAuxMName)
        self.frontSpringEditText = TrackedSpinBox(tracker, "ui.frontSpringEditText", 0)
        self.rearSpringEditText = TrackedSpinBox(tracker, "ui.rearSpringEditText", 0)
        self.gain_fri_spinbox = TrackedSpinBox(tracker, "ui.gain_fri_spinbox", self.gain_fri)
        self.gain_dam_spinbox = TrackedSpinBox(tracker, "ui.gain_dam_spinbox", self.gain_dam)
        self.gain_feedback_spinbox = TrackedSpinBox(tracker, "ui.gain_feedback_spinbox", self.gain_feedback)
        self.gain_sa_spinbox = TrackedSpinBox(tracker, "ui.gain_sa_spinbox", self.gain_sa)
        self.gain_all_spinbox = TrackedSpinBox(tracker, "ui.gain_all_spinbox", self.gain_all)
        self.sw_rate_spinbox = TrackedSpinBox(tracker, "ui.sw_rate_spinbox", self.sw_rate)
        self.offset_x = TrackedLineEdit(tracker, "ui.offset_x", "0")
        self.offset_y = TrackedLineEdit(tracker, "ui.offset_y", "0")
        self.offset_z = TrackedLineEdit(tracker, "ui.offset_z", "0")
        self.run_button = TrackedCheckBox(tracker, "ui.run_button", False)
        self.alarm_toggle = TrackedCheckBox(tracker, "ui.alarm_toggle", False)

        for attr, default in _visual_line_edits().items():
            setattr(self, attr, TrackedLineEdit(tracker, f"ui.{attr}", default))

        self.condition_combo = TrackedComboBox(tracker, "ui.condition_combo", ["baseline", "double_lane_change", "sine_steer"])
        self.map_combo = TrackedComboBox(tracker, "ui.map_combo", [("proving_ground", {"id": 1}), ("city_loop", {"id": 2})])
        self.start_point_combo = TrackedComboBox(tracker, "ui.start_point_combo", ["start_a", "start_b"])
        self.scenario_combo = TrackedComboBox(tracker, "ui.scenario_combo", ["single_lane", "cornering", "comfort", "custom"])
        self.plot_switches = {
            key: TrackedCheckBox(tracker, f"plot_switch.{key}", False)
            for key in _plot_channels()
        }
        self.plots = {
            key: FakePlot(tracker, key)
            for key in _plot_channels()
        }

        object.__setattr__(self, "_initialized", True)

    def __setattr__(self, name: str, value: Any) -> None:
        before = getattr(self, name, None)
        object.__setattr__(self, name, value)
        if getattr(self, "_initialized", False) and name in self.TRACKED_ATTRS:
            self._tracker.record_change(f"ui.{name}", before, value, "adapter")

    def CurrentVehicleSpringPage(self, page: int) -> None:
        self._tracker.record_change("ui.current_spring_page", None, page, "adapter")

    def UpdateTuningParam(self) -> None:
        self._tracker.record_change("ui.tuning_params_refreshed", False, True, "adapter")

    def RunDspace(self) -> None:
        self._tracker.record_change("simulation.last_run_scheme", None, self.run_scheme, "adapter")

    def OpenSimulink(self) -> None:
        self._tracker.record_change("simulation.workspace", None, "open_simulink", "adapter")

    def BuildDspace(self) -> None:
        self._tracker.record_change("simulation.workspace", None, "build_dspace", "adapter")

    def viewOfflineData(self) -> None:
        self._tracker.record_change("analysis.view", None, "offline_data", "adapter")

    def start_record(self) -> None:
        self.is_recording_imu = True
        self.is_recording_carsim = True
        self.is_recording_moog = True
        self._tracker.record_change("recording.status", "stopped", "recording", "adapter")

    def finish_record(self) -> None:
        self.is_recording_imu = False
        self.is_recording_carsim = False
        self.is_recording_moog = False
        self._tracker.record_change("recording.status", "recording", "stopped", "adapter")

    def video_recording(self, enabled: bool) -> None:
        self.is_video_recording = bool(enabled)

    def save_haptic_gain(self) -> None:
        self._tracker.record_change("haptic.saved", False, True, "adapter")

    def one_click_start(self) -> None:
        self._tracker.record_change("platform.command_sequence", None, "reset,consent,engage", "adapter")

    def one_click_stop(self) -> None:
        self._tracker.record_change("platform.command_sequence", None, "disengage,off", "adapter")

    def sendDataPlatformOffset2(self, x: float, y: float, z: float) -> None:
        self._tracker.record_change("platform.offset", None, {"x": x, "y": y, "z": z}, "adapter")

    def confirm_scenario_settings(self) -> None:
        self._tracker.record_change(
            "scene.confirmed",
            None,
            {
                "condition": self.condition_combo.currentText(),
                "map": self.map_combo.currentText(),
                "start_point": self.start_point_combo.currentText(),
            },
            "adapter",
        )

    def ApplyVisualCompensation(self) -> None:
        self._tracker.record_change("visual.motion_profile_applied", False, True, "adapter")

    def ApplyVisualDelayCompensation(self) -> None:
        self._tracker.record_change("visual.delay_profile_applied", False, True, "adapter")

    def toggle_plotting(self, enabled: bool) -> None:
        self._tracker.record_change("plotting.running", not bool(enabled), bool(enabled), "adapter")

    def stop_plotting(self) -> None:
        self._tracker.record_change("plotting.running", True, False, "adapter")

    def clear_plots(self) -> None:
        self._tracker.record_change("plotting.data", "buffered", "cleared", "adapter")

    def toggle_all_plots_on(self) -> None:
        for switch in self.plot_switches.values():
            switch.setChecked(True)
        self._tracker.record_change("plotting.visibility", "partial", "all_on", "adapter")

    def toggle_all_plots_off(self) -> None:
        for switch in self.plot_switches.values():
            switch.setChecked(False)
        self._tracker.record_change("plotting.visibility", "partial", "all_off", "adapter")

    def update_plot_layout(self) -> None:
        visible = sorted(
            name for name, switch in self.plot_switches.items()
            if switch.isChecked()
        )
        self._tracker.record_change("plotting.visible_channels", None, visible, "adapter")

    def toggle_alarm(self, enabled: bool) -> None:
        self._tracker.record_change("alarm.enabled", not bool(enabled), bool(enabled), "adapter")

    def snapshot(self) -> Dict[str, Any]:
        return {
            "vehicle": self.carName,
            "front_spring": self.frontSpringName,
            "rear_spring": self.rearSpringName,
            "front_right_spring": self.frontRightSpringName,
            "rear_right_spring": self.rearRightSpringName,
            "front_antiroll": self.frontAuxMName,
            "rear_antiroll": self.rearAuxMName,
            "scene": {
                "condition": self.condition_combo.currentText(),
                "map": self.map_combo.currentText(),
                "start_point": self.start_point_combo.currentText(),
            },
            "haptic": {
                "friction": self.gain_fri,
                "damping": self.gain_dam,
                "feedback": self.gain_feedback,
                "saturation": self.gain_sa,
                "overall": self.gain_all,
                "steer_rate": self.sw_rate,
            },
            "recording": {
                "recording": any([
                    self.is_recording_imu,
                    self.is_recording_carsim,
                    self.is_recording_moog,
                    self.is_recording_disusx,
                    self.is_recording_visual_compensator,
                ]),
                "record_disusx": self.record_disusx,
                "video": self.is_video_recording,
                "par_save": self.is_par_save,
                "auto_record": self.auto_record,
            },
            "platform_offset": {
                "x": self.offset_x.text(),
                "y": self.offset_y.text(),
                "z": self.offset_z.text(),
            },
            "plotting": {
                "running": self.run_button.isChecked(),
                "visible_channels": sorted(
                    name for name, switch in self.plot_switches.items()
                    if switch.isChecked()
                ),
                "alarm_enabled": self.alarm_toggle.isChecked(),
                "alarm_scenario": self.scenario_combo.currentText(),
            },
        }


def _visual_line_edits() -> Dict[str, str]:
    return {
        "xOffsetEditText": "0",
        "yOffsetEditText": "0",
        "zOffsetEditText": "0",
        "rollOffsetEditText": "0",
        "pitchOffsetEditText": "0",
        "yawOffsetEditText": "0",
        "xGainEditText": "1",
        "yGainEditText": "1",
        "zGainEditText": "1",
        "rollGainEditText": "1",
        "pitchGainEditText": "1",
        "yawGainEditText": "1",
        "sampleTimeEditText": "0.001",
        "delayTimeEditText": "60",
        "freqEditText": "1.5",
        "posAccEditText": "3",
        "negAccEditText": "3",
    }


def _plot_channels() -> List[str]:
    return [
        "pos_x", "pos_y", "pos_z",
        "vel_x", "vel_y", "vel_z",
        "acc_x", "acc_y", "acc_z",
        "ang_x", "ang_y", "ang_z",
        "roll", "pitch", "yaw",
        "ang_acc_x", "ang_acc_y", "ang_acc_z",
        "steering_angle", "throttle", "pbk_con", "steering_speed",
        "CmpRD_L1", "CmpRD_L2", "CmpRD_R1", "CmpRD_R2",
    ]


def build_standalone_context():
    tracker = StateTracker()
    ui = StandaloneSimulatorAdapter(tracker)
    carsim = FakeCarsim(tracker)
    main_module = SimpleNamespace(
        vehicleInfoDic={
            "baseline_sedan": "Vehicle:<demo>baseline_sedan",
            "baseline_suv": "Vehicle:<demo>baseline_suv",
        },
        vehicleImagePath={},
        springInfoDic={
            "baseline_front_spring": "",
            "baseline_rear_spring": "",
            "sport_spring": "",
            "comfort_spring": "",
        },
        AuxMInfoDic={
            "baseline_front_bar": "",
            "baseline_rear_bar": "",
            "sport_bar": "",
            "comfort_bar": "",
        },
        MxTotInfoDic={},
        carsim=carsim,
    )
    ctx = SimpleNamespace(
        ui=ui,
        main_module=main_module,
        services={},
        mod=lambda attr_name, default=None: getattr(main_module, attr_name, default),
        require=lambda attr_name: getattr(main_module, attr_name),
        register_service=lambda name, service: ctx.services.__setitem__(name, service),
        service=lambda name: ctx.services.get(name),
        is_recording=lambda: any([
            ui.is_recording_imu,
            ui.is_recording_carsim,
            ui.is_recording_moog,
            ui.is_recording_disusx,
            ui.is_recording_visual_compensator,
        ]),
        state_tracker=tracker,
        state=tracker.state,
    )
    return ctx
