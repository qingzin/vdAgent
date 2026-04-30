"""场景设置 action — 通过 SceneService 操作。"""

from ._helpers import fuzzy_resolve


def register(registry, ctx):
    svc = ctx.service('scene')

    def prepare_test_scene(condition_name: str = None,
                           map_name: str = None,
                           start_point_name: str = None,
                           confirm: bool = True) -> str:
        msgs = []

        if condition_name is not None:
            resolved = svc.set_condition(condition_name)
            if resolved is None:
                names = svc.list_conditions()
                r, err = fuzzy_resolve(condition_name, names)
                if err:
                    return err + f" 可用工况: {names}"
                svc.set_condition(r)
                msgs.append(f"工况切换为: {r}")
            else:
                msgs.append(f"工况切换为: {resolved}")

        if map_name is not None:
            resolved = svc.set_map(map_name)
            if resolved is None:
                names = svc.list_maps()
                r, err = fuzzy_resolve(map_name, names)
                if err:
                    return err + f" 可用地图: {names}"
                svc.set_map(r)
                msgs.append(f"地图切换为: {svc.get_map()}")
            else:
                msgs.append(f"地图切换为: {resolved}")

        if start_point_name is not None:
            resolved = svc.set_start_point(start_point_name)
            if resolved is None:
                names = svc.list_start_points()
                r, err = fuzzy_resolve(start_point_name, names)
                if err:
                    return err + f" 可用起点: {names}"
                svc.set_start_point(r)
                msgs.append(f"起点切换为: {svc.get_start_point()}")
            else:
                msgs.append(f"起点切换为: {resolved}")

        if not msgs:
            return "请至少指定 condition_name、map_name 或 start_point_name 中的一项。"

        if confirm:
            try:
                svc.confirm_scene()
                msgs.append("场景已确认并下发到平台")
            except Exception as e:
                msgs.append(f"场景确认失败: {e}")
        else:
            msgs.append("当前仅更新选择,尚未确认生效")

        return "；".join(msgs)

    registry.register(
        name="prepare_test_scene",
        description="准备试验场景。可统一设置工况、地图和起点,默认自动确认生效。",
        params_schema={
            "type": "object",
            "properties": {
                "condition_name": {"type": "string"},
                "map_name": {"type": "string"},
                "start_point_name": {"type": "string"},
                "confirm": {"type": "boolean", "description": "是否立即确认生效,默认 true"},
            },
            "required": []
        },
        callback=prepare_test_scene,
        category="scene",
        risk_level="medium",
        exposed=True,
    )

    def get_current_scene() -> str:
        parts = []
        m = svc.get_map()
        if m: parts.append(f"地图: {m}")
        sp = svc.get_start_point()
        if sp: parts.append(f"起点: {sp}")
        c = svc.get_condition()
        if c: parts.append(f"工况: {c}")
        return "; ".join(parts) if parts else "场景信息不可用。"

    registry.register(
        name="get_current_scene",
        description="查询当前场景设置(地图、起点、工况)。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=get_current_scene,
        category="query",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )

    def set_road_segment(segment_name: str = None, query: bool = False) -> str:
        if query or segment_name is None:
            current = svc.get_road_segment()
            names = svc.list_road_segments()
            return f"当前路段: {current}; 可用路段: {names}"

        resolved = svc.set_road_segment(segment_name)
        if resolved is None:
            names = svc.list_road_segments()
            r, err = fuzzy_resolve(segment_name, names)
            if err:
                return f"未找到路段: {segment_name}, 可用: {names}"
            svc.set_road_segment(r)
            return f"已切换路段: {r},自动记录坐标已更新。"
        return f"已切换路段: {resolved},自动记录坐标已更新。"

    registry.register(
        name="set_road_segment",
        description="设置或查询自动记录路段。",
        params_schema={
            "type": "object",
            "properties": {
                "segment_name": {"type": "string"},
                "query": {"type": "boolean"},
            },
            "required": []
        },
        callback=set_road_segment,
        category="scene",
        risk_level="medium",
        exposed=True,
    )
