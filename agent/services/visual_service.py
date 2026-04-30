"""视觉补偿 service。"""

VC_FIELDS = [
    ('x_offset', 'xOffsetEditText'), ('y_offset', 'yOffsetEditText'),
    ('z_offset', 'zOffsetEditText'), ('roll_offset', 'rollOffsetEditText'),
    ('pitch_offset', 'pitchOffsetEditText'), ('yaw_offset', 'yawOffsetEditText'),
    ('x_gain', 'xGainEditText'), ('y_gain', 'yGainEditText'),
    ('z_gain', 'zGainEditText'), ('roll_gain', 'rollGainEditText'),
    ('pitch_gain', 'pitchGainEditText'), ('yaw_gain', 'yawGainEditText'),
]

VDC_FIELDS = [
    ('sample_time', 'sampleTimeEditText'), ('delay_time', 'delayTimeEditText'),
    ('freq', 'freqEditText'), ('pos_acc', 'posAccEditText'),
    ('neg_acc', 'negAccEditText'),
]


class VisualService:
    def __init__(self, ctx):
        self._ctx = ctx

    @property
    def _ui(self):
        return self._ctx.ui

    def set_profile(self, **kwargs) -> dict:
        """设置视觉补偿参数。返回 {vc: {...}, vdc: {...}}。"""
        ui = self._ui
        vc_changes = {}
        vdc_changes = {}

        for key, attr in VC_FIELDS:
            val = kwargs.get(key)
            if val is None:
                continue
            if hasattr(ui, attr):
                getattr(ui, attr).setText(str(val))
                vc_changes[key] = val

        for key, attr in VDC_FIELDS:
            val = kwargs.get(key)
            if val is None:
                continue
            if hasattr(ui, attr):
                getattr(ui, attr).setText(str(val))
                vdc_changes[key] = val

        if vc_changes:
            ui.ApplyVisualCompensation()
        if vdc_changes:
            ui.ApplyVisualDelayCompensation()

        return {"vc": vc_changes, "vdc": vdc_changes}
