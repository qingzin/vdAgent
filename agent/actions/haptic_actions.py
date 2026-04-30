"""触感力反馈 action — 通过 HapticService 操作。"""


def register(registry, ctx):
    svc = ctx.service('haptic')

    def tune_haptic_feedback(mode: str = "get", friction=None, damping=None,
                             feedback=None, saturation=None, overall=None,
                             steer_rate=None) -> str:
        mode = (mode or "get").lower().strip()
        if mode == "get":
            params = svc.get_all()
            parts = [f"摩擦增益(friction)={params.get('friction')}",
                     f"阻尼增益(damping)={params.get('damping')}",
                     f"回正增益(feedback)={params.get('feedback')}",
                     f"限位增益(saturation)={params.get('saturation')}",
                     f"手感轻重(overall)={params.get('overall')}",
                     f"转速(steer_rate)={params.get('steer_rate')}"]
            return "当前触感参数: " + "; ".join(parts)

        if mode != "set":
            return "mode 仅支持 get 或 set。"

        result = svc.set_params(
            friction=friction, damping=damping, feedback=feedback,
            saturation=saturation, overall=overall, steer_rate=steer_rate,
        )
        changed = result["changed"]
        errors = result["errors"]

        if errors and not changed:
            return "参数越界: " + "; ".join(errors)
        if not changed:
            return "未指定任何参数。"

        msg = f"已更新触感参数: {', '.join(f'{k}={v}' for k, v in changed.items())}"
        if errors:
            msg += f"。以下参数被跳过: {'; '.join(errors)}"
        return msg

    registry.register(
        name="tune_haptic_feedback",
        description="查询或设置转向力反馈触感参数。",
        params_schema={
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["get", "set"]},
                "friction": {"type": "number", "description": "摩擦增益, -10~10"},
                "damping": {"type": "number", "description": "阻尼增益, -10~10"},
                "feedback": {"type": "number", "description": "回正增益, -10~10"},
                "saturation": {"type": "number", "description": "限位增益, -10~10"},
                "overall": {"type": "number", "description": "手感轻重, -1~10"},
                "steer_rate": {"type": "number", "description": "力矩转角曲线转速, 0~100"},
            },
            "required": []
        },
        callback=tune_haptic_feedback,
        category="haptic",
        risk_level="medium",
        exposed=True,
    )
