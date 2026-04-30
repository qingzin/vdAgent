"""触感力反馈 service。"""

HAPTIC_SPECS = [
    ('friction',   -10, 10, '摩擦增益',         'gain_fri',      'gain_fri_spinbox'),
    ('damping',    -10, 10, '阻尼增益',         'gain_dam',      'gain_dam_spinbox'),
    ('feedback',   -10, 10, '回正增益',         'gain_feedback', 'gain_feedback_spinbox'),
    ('saturation', -10, 10, '限位增益',         'gain_sa',       'gain_sa_spinbox'),
    ('overall',     -1, 10, '手感轻重',         'gain_all',      'gain_all_spinbox'),
    ('steer_rate',   0, 100, '力矩转角曲线转速', 'sw_rate',       'sw_rate_spinbox'),
]


class HapticService:
    def __init__(self, ctx):
        self._ctx = ctx

    @property
    def _ui(self):
        return self._ctx.ui

    def get_all(self) -> dict:
        result = {}
        for key, _lo, _hi, _label, attr, _spin in HAPTIC_SPECS:
            result[key] = getattr(self._ui, attr, None)
        return result

    def set_params(self, **kwargs) -> dict:
        """设置触感参数。返回 {changed: {...}, errors: [...]}。"""
        ui = self._ui
        changed = {}
        errors = []

        for key, lo, hi, label, attr, spin_attr in HAPTIC_SPECS:
            val = kwargs.get(key)
            if val is None:
                continue
            if val < lo or val > hi:
                errors.append(f"{label}={val} 超出范围 [{lo}, {hi}]")
                continue
            setattr(ui, attr, val)
            if hasattr(ui, spin_attr):
                getattr(ui, spin_attr).setValue(val)
            changed[label] = val

        if changed and hasattr(ui, 'save_haptic_gain'):
            ui.save_haptic_gain()

        return {"changed": changed, "errors": errors}
