"""
视觉补偿相关 action

- set_visual_profile             统一设置视觉运动跟随与视觉延迟补偿
"""


VC_FIELDS = [
    # (param_name,   ui_attr,             label,   default_fallback)
    ('x_offset',     'xOffsetEditText',     'x偏置',    '0'),
    ('y_offset',     'yOffsetEditText',     'y偏置',    '0'),
    ('z_offset',     'zOffsetEditText',     'z偏置',    '0'),
    ('roll_offset',  'rollOffsetEditText',  'roll偏置', '0'),
    ('pitch_offset', 'pitchOffsetEditText', 'pitch偏置','0'),
    ('yaw_offset',   'yawOffsetEditText',   'yaw偏置',  '0'),
    ('x_gain',       'xGainEditText',       'x增益',    '1'),
    ('y_gain',       'yGainEditText',       'y增益',    '1'),
    ('z_gain',       'zGainEditText',       'z增益',    '1'),
    ('roll_gain',    'rollGainEditText',    'roll增益', '1'),
    ('pitch_gain',   'pitchGainEditText',   'pitch增益','1'),
    ('yaw_gain',     'yawGainEditText',     'yaw增益',  '1'),
]


VDC_FIELDS = [
    ('sample_time', 'sampleTimeEditText', '采样时间',        '0.001'),
    ('delay_time',  'delayTimeEditText',  '延迟时间 (ms)',    '60'),
    ('freq',        'freqEditText',       '机动频率',         '1.5'),
    ('pos_acc',     'posAccEditText',     '正向最大加速度',    '3'),
    ('neg_acc',     'negAccEditText',     '负向最大加速度',    '3'),
]


def register(registry, ctx):

    # --------- 视觉运动跟随补偿 ---------
    def set_visual_profile(**kwargs) -> str:
        ui = ctx.ui
        vc_changes = []
        for key, attr, label, _default in VC_FIELDS:
            if kwargs.get(key) is None:
                continue
            val = float(kwargs[key])
            if hasattr(ui, attr):
                getattr(ui, attr).setText(str(val))
                vc_changes.append(f"{label}({key})={val}")

        vdc_changes = []
        for key, attr, label, _default in VDC_FIELDS:
            if kwargs.get(key) is None:
                continue
            val = float(kwargs[key])
            if hasattr(ui, attr):
                getattr(ui, attr).setText(str(val))
                vdc_changes.append(f"{label}({key})={val}")

        if not vc_changes and not vdc_changes:
            return "未指定任何参数。"

        messages = []
        try:
            if vc_changes:
                ui.ApplyVisualCompensation()
                messages.append(f"已应用视觉运动跟随补偿: {', '.join(vc_changes)}")
            if vdc_changes:
                ui.ApplyVisualDelayCompensation()
                messages.append(f"已应用视觉延迟补偿: {', '.join(vdc_changes)}")
            return "；".join(messages)
        except Exception as e:
            return f"应用失败: {e}"

    registry.register(
        name="set_visual_profile",
        description="统一设置视觉运动跟随补偿与视觉延迟补偿。"
                    "未指定的参数保持当前值,可一次同时更新两类视觉参数。",
        params_schema={
            "type": "object",
            "properties": {
                "x_offset":     {"type": "number", "description": "X 方向偏置"},
                "y_offset":     {"type": "number", "description": "Y 方向偏置"},
                "z_offset":     {"type": "number", "description": "Z 方向偏置"},
                "roll_offset":  {"type": "number", "description": "Roll 偏置"},
                "pitch_offset": {"type": "number", "description": "Pitch 偏置"},
                "yaw_offset":   {"type": "number", "description": "Yaw 偏置"},
                "x_gain":       {"type": "number", "description": "X 方向增益"},
                "y_gain":       {"type": "number", "description": "Y 方向增益"},
                "z_gain":       {"type": "number", "description": "Z 方向增益"},
                "roll_gain":    {"type": "number", "description": "Roll 增益"},
                "pitch_gain":   {"type": "number", "description": "Pitch 增益"},
                "yaw_gain":     {"type": "number", "description": "Yaw 增益"},
                "sample_time": {"type": "number", "description": "采样时间 (秒)"},
                "delay_time":  {"type": "number", "description": "延迟时间 (毫秒)"},
                "freq":        {"type": "number", "description": "机动频率"},
                "pos_acc":     {"type": "number", "description": "正向最大加速度"},
                "neg_acc":     {"type": "number", "description": "负向最大加速度"},
            },
            "required": []
        },
        callback=set_visual_profile,
    )
