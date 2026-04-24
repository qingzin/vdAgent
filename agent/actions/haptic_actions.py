"""
触感力反馈相关 action

- tune_haptic_feedback   查询或设置触感增益参数
"""


HAPTIC_SPECS = [
    # (param_name, lo, hi, label, ui_attr, ui_spin_attr)
    ('friction',   -10, 10, '摩擦增益',         'gain_fri',      'gain_fri_spinbox'),
    ('damping',    -10, 10, '阻尼增益',         'gain_dam',      'gain_dam_spinbox'),
    ('feedback',   -10, 10, '回正增益',         'gain_feedback', 'gain_feedback_spinbox'),
    ('saturation', -10, 10, '限位增益',         'gain_sa',       'gain_sa_spinbox'),
    ('overall',     -1, 10, '手感轻重',         'gain_all',      'gain_all_spinbox'),
    ('steer_rate',   0, 100, '力矩转角曲线转速', 'sw_rate',       'sw_rate_spinbox'),
]


def register(registry, ctx):

    def tune_haptic_feedback(mode: str = "get", friction=None, damping=None, feedback=None,
                             saturation=None, overall=None, steer_rate=None) -> str:
        ui = ctx.ui
        mode = (mode or "get").lower().strip()
        if mode == "get":
            parts = []
            for key, _lo, _hi, label, attr, _spin in HAPTIC_SPECS:
                val = getattr(ui, attr, None)
                if val is not None:
                    parts.append(f"{label}({key})={val}")
            return "当前触感参数: " + "; ".join(parts) if parts else "触感参数未初始化"

        if mode != "set":
            return "mode 仅支持 get 或 set。"

        params = {'friction': friction, 'damping': damping, 'feedback': feedback,
                  'saturation': saturation, 'overall': overall, 'steer_rate': steer_rate}
        changes, errors = [], []

        for key, lo, hi, label, attr, spin_attr in HAPTIC_SPECS:
            val = params.get(key)
            if val is None:
                continue
            if val < lo or val > hi:
                errors.append(f"{label}={val} 超出范围 [{lo}, {hi}]")
                continue
            setattr(ui, attr, val)
            if hasattr(ui, spin_attr):
                getattr(ui, spin_attr).setValue(val)
            changes.append(f"{label}={val}")

        if errors and not changes:
            return "参数越界: " + "; ".join(errors)
        if not changes:
            return "未指定任何参数。"

        if hasattr(ui, 'save_haptic_gain'):
            ui.save_haptic_gain()

        result = f"已更新触感参数: {', '.join(changes)}"
        if errors:
            result += f"。以下参数被跳过: {'; '.join(errors)}"
        return result

    registry.register(
        name="tune_haptic_feedback",
        description="查询或设置转向力反馈触感参数。mode=get 时返回当前配置；"
                    "mode=set 时按需更新摩擦增益、阻尼增益、回正增益、限位增益、"
                    "手感轻重和力矩转角曲线转速。",
        params_schema={
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["get", "set"],
                         "description": "get 查询当前参数; set 更新参数"},
                "friction":   {"type": "number", "description": "摩擦增益, -10~10"},
                "damping":    {"type": "number", "description": "阻尼增益, -10~10"},
                "feedback":   {"type": "number", "description": "回正增益, -10~10"},
                "saturation": {"type": "number", "description": "限位增益, -10~10"},
                "overall":    {"type": "number", "description": "手感轻重, -1~10"},
                "steer_rate": {"type": "number", "description": "力矩转角曲线转速, 0~100"},
            },
            "required": []
        },
        callback=tune_haptic_feedback,
    )
