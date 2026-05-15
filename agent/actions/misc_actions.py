"""杂项 action — 通过 MetadataService 操作。"""


def _read_platform_offset(ui) -> str:
    vals = []
    for label, attr in [("X", "offset_x"), ("Y", "offset_y"), ("Z", "offset_z")]:
        widget = getattr(ui, attr, None)
        if widget is None or not hasattr(widget, "text"):
            continue
        vals.append(f"{label}={widget.text()}")
    return ", ".join(vals) if vals else "不可用"


def _read_haptic_status(ctx) -> str:
    svc = ctx.service('haptic')
    if svc is None:
        return "不可用"
    labels = {
        "friction": "摩擦",
        "damping": "阻尼",
        "feedback": "回正",
        "saturation": "限位",
        "overall": "手感轻重",
        "steer_rate": "转速",
    }
    values = svc.get_all()
    parts = [
        f"{labels.get(k, k)}={v}"
        for k, v in values.items()
        if v is not None
    ]
    return ", ".join(parts) if parts else "不可用"


def register(registry, ctx):
    svc = ctx.service('metadata')

    def prepare_evaluation_metadata(mode: str = "set", car_model: str = None,
                                    tuning_parts: str = None, evaluator: str = None,
                                    condition: str = None) -> str:
        mode = (mode or "set").lower().strip()
        if mode == "get":
            data = svc.get_all()
            parts = [f"{k}={v or '(未设置)'}" for k, v in data.items()]
            return "当前预定义: " + ", ".join(parts)

        if mode != "set":
            return "mode 仅支持 get 或 set。"

        changed = svc.set_fields(
            car_model=car_model, tuning_parts=tuning_parts,
            evaluator=evaluator, condition=condition,
        )
        if not changed:
            return "未指定任何参数。可用: car_model, tuning_parts, evaluator, condition"
        return "已更新预定义: " + ", ".join(f"{k}='{v}'" for k, v in changed.items())

    registry.register(
        name="prepare_evaluation_metadata",
        description="设置或查询评价记录对话框的预定义元数据。",
        params_schema={
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["get", "set"]},
                "car_model": {"type": "string"},
                "tuning_parts": {"type": "string"},
                "evaluator": {"type": "string"},
                "condition": {"type": "string"},
            },
            "required": []
        },
        callback=prepare_evaluation_metadata,
        category="misc",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )

    def get_system_status() -> str:
        ui = ctx.ui
        parts = []

        tuning = ctx.service('tuning')
        if tuning is not None:
            parts.append(tuning.get_current_setup())
        else:
            parts.append(f"当前车型: {getattr(ui, 'carName', '未知')}")

        scene = ctx.service('scene')
        if scene is not None:
            scene_parts = []
            m = scene.get_map()
            if m:
                scene_parts.append(f"地图: {m}")
            sp = scene.get_start_point()
            if sp:
                scene_parts.append(f"起点: {sp}")
            c = scene.get_condition()
            if c:
                scene_parts.append(f"工况: {c}")
            parts.append("当前场景: " + ("; ".join(scene_parts) if scene_parts else "不可用"))

        recording = ctx.service('recording')
        if recording is not None:
            parts.append(recording.get_status())

        parts.append("触感参数: " + _read_haptic_status(ctx))
        parts.append("平台位置偏置: " + _read_platform_offset(ui))
        parts.append(f"方案计数: 第{getattr(ui, 'run_scheme', 0)}组")
        parts.append(f"报警监控: {'开启' if getattr(ui, 'alarm_enabled', False) else '关闭'}")
        return "\n".join(f"- {p}" for p in parts if p)

    registry.register(
        name="get_system_status",
        description="查询当前系统状态,包括车型悬架、场景、记录、触感、平台偏置、方案计数和报警状态。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=get_system_status,
        category="query",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )
