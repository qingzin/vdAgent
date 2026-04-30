"""
车型与悬架调校相关 action — 通过 TuningService 操作。
"""

from ._helpers import require_not_recording, fuzzy_resolve


def register(registry, ctx):
    svc = ctx.service('tuning')

    # -- vehicle -------------------------------------------------------

    def select_vehicle(vehicle_name: str) -> str:
        guard = require_not_recording(ctx, "切换车型")
        if guard:
            return guard

        vehicle_dic = ctx.mod('vehicleInfoDic', {})
        resolved, err = fuzzy_resolve(vehicle_name, list(vehicle_dic.keys()))
        if err:
            return err + f" 可用车型示例: {list(vehicle_dic.keys())[:5]}"

        svc.select_vehicle(resolved)
        return f"已切换到车型: {resolved}"

    registry.register(
        name="select_vehicle",
        description="选择/切换车型,更改当前 CarSim 仿真使用的车辆模型。",
        params_schema={
            "type": "object",
            "properties": {
                "vehicle_name": {"type": "string", "description": "车型名称或部分关键词"}
            },
            "required": ["vehicle_name"]
        },
        callback=select_vehicle,
        category="vehicle",
        risk_level="medium",
        exposed=True,
    )

    # -- spring --------------------------------------------------------

    def set_spring(position: str, spring_name: str, side: str = "both") -> str:
        guard = require_not_recording(ctx, "修改弹簧")
        if guard:
            return guard

        position = position.lower().strip()
        side = (side or "both").lower().strip()
        if position not in ("front", "rear"):
            return "position 仅支持 front 或 rear。"
        if side not in ("left", "right", "both"):
            return "side 仅支持 left、right 或 both。"

        spring_dic = ctx.mod('springInfoDic', {})
        resolved, err = fuzzy_resolve(spring_name, list(spring_dic.keys()))
        numeric = None
        if err:
            try:
                numeric = float(spring_name)
            except ValueError:
                return err

        name = resolved if resolved else spring_name
        messages = []

        if side in ("left", "both"):
            setter = (svc.set_front_left_spring if position == "front"
                      else svc.set_rear_left_spring)
            result = setter(name)
            messages.append(result if result else f"弹簧 '{name}' 未找到。")

        if side in ("right", "both"):
            if numeric is not None:
                if side == "right":
                    return "右侧弹簧当前仅支持按名称切换,暂不支持直接输入数值刚度。"
                messages.append("右侧弹簧未更新: 仅支持按名称切换。")
            else:
                setter = (svc.set_front_right_spring if position == "front"
                          else svc.set_rear_right_spring)
                result = setter(name)
                messages.append(result if result else f"弹簧 '{name}' 未找到。")

        return "；".join(messages)

    registry.register(
        name="set_spring",
        description="统一设置弹簧。支持 position=front/rear, "
                    "side=left/right/both。可输入弹簧名称或刚度数值。",
        params_schema={
            "type": "object",
            "properties": {
                "position": {"type": "string", "enum": ["front", "rear"],
                             "description": "前轴或后轴"},
                "side": {"type": "string", "enum": ["left", "right", "both"],
                         "description": "左/右/双侧, 默认 both"},
                "spring_name": {"type": "string", "description": "弹簧名称或刚度数值"}
            },
            "required": ["position", "spring_name"]
        },
        callback=set_spring,
        category="tuning",
        risk_level="high",
        exposed=True,
    )

    # -- antiroll bar --------------------------------------------------

    def set_antiroll_bar(position: str, antiroll_name: str) -> str:
        guard = require_not_recording(ctx, f"修改{position}稳定杆")
        if guard:
            return guard

        is_front = position.lower().strip() == "front"
        all_names = {**ctx.mod('AuxMInfoDic', {}), **ctx.mod('MxTotInfoDic', {})}
        resolved, err = fuzzy_resolve(antiroll_name, list(all_names.keys()))
        if err:
            return f"{'前' if is_front else '后'}稳定杆: {err}"

        result = svc.set_antiroll_bar(is_front, resolved)
        return result if result else f"稳定杆 '{resolved}' 未找到。"

    registry.register(
        name="set_antiroll_bar",
        description="统一设置前/后防倾杆(稳定杆)或滚转刚度相关数据集。",
        params_schema={
            "type": "object",
            "properties": {
                "position": {"type": "string", "enum": ["front", "rear"],
                             "description": "前轴或后轴"},
                "antiroll_name": {"type": "string", "description": "稳定杆名称"}
            },
            "required": ["position", "antiroll_name"]
        },
        callback=set_antiroll_bar,
        category="tuning",
        risk_level="high",
        exposed=True,
    )

    # -- query ---------------------------------------------------------

    def get_current_setup() -> str:
        return svc.get_current_setup()

    registry.register(
        name="get_current_setup",
        description="查询并返回当前车型及其悬架配置(弹簧、稳定杆名称)。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=get_current_setup,
        category="query",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )
