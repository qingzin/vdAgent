"""视觉补偿 action — 通过 VisualService 操作。"""


def register(registry, ctx):
    svc = ctx.service('visual')

    def set_visual_profile(**kwargs) -> str:
        result = svc.set_profile(**kwargs)
        vc = result["vc"]
        vdc = result["vdc"]
        if not vc and not vdc:
            return "未指定任何参数。"

        messages = []
        if vc:
            messages.append(f"已应用视觉运动跟随补偿: {', '.join(f'{k}={v}' for k, v in vc.items())}")
        if vdc:
            messages.append(f"已应用视觉延迟补偿: {', '.join(f'{k}={v}' for k, v in vdc.items())}")
        return "；".join(messages)

    registry.register(
        name="set_visual_profile",
        description="统一设置视觉运动跟随补偿与视觉延迟补偿。",
        params_schema={
            "type": "object",
            "properties": {
                "x_offset": {"type": "number"}, "y_offset": {"type": "number"},
                "z_offset": {"type": "number"}, "roll_offset": {"type": "number"},
                "pitch_offset": {"type": "number"}, "yaw_offset": {"type": "number"},
                "x_gain": {"type": "number"}, "y_gain": {"type": "number"},
                "z_gain": {"type": "number"}, "roll_gain": {"type": "number"},
                "pitch_gain": {"type": "number"}, "yaw_gain": {"type": "number"},
                "sample_time": {"type": "number"}, "delay_time": {"type": "number"},
                "freq": {"type": "number"}, "pos_acc": {"type": "number"},
                "neg_acc": {"type": "number"},
            },
            "required": []
        },
        callback=set_visual_profile,
        category="visual",
        risk_level="medium",
        exposed=True,
    )
