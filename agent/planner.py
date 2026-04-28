"""
Rule-based chassis planning and tuning suggestions.
"""

from hashlib import sha1


def _text(*parts) -> str:
    return " ".join(str(p or "") for p in parts).lower()


def _stable_plan_id(kind: str, goal: str = None, condition_name: str = None) -> str:
    raw = "|".join([str(kind or ""), str(goal or ""), str(condition_name or "")])
    return f"plan_{sha1(raw.encode('utf-8')).hexdigest()[:12]}"


def _base_response(kind: str, goal: str = None, complaint: str = None,
                   condition_name: str = None) -> dict:
    return {
        "kind": kind,
        "plan_id": _stable_plan_id(kind, goal or complaint, condition_name),
        "goal": goal,
        "complaint": complaint,
        "condition_name": condition_name,
        "steps": [],
        "recommended_steps": [],
        "parameter_direction": [],
        "risks": [],
        "validation_metrics": [],
        "required_confirmation": [],
        "recent_experiences": [],
    }


def _infer_action_name(description: str) -> str:
    text = str(description or "")
    action_names = [
        "get_current_setup",
        "prepare_test_scene",
        "prepare_recording_session",
        "start_recording",
        "stop_recording",
        "set_antiroll_bar",
        "set_spring",
        "tune_haptic_feedback",
        "run_carsim",
        "analyze_offline_result",
        "plan_chassis_task",
        "suggest_chassis_tuning",
    ]
    for action_name in action_names:
        if action_name in text:
            return action_name
    return "review_with_engineer"


def _ensure_plan_schema(result: dict) -> dict:
    """Attach the stable structured plan schema while keeping legacy fields."""
    if not isinstance(result, dict):
        return result
    kind = result.get("kind")
    goal = result.get("goal") or result.get("complaint")
    condition_name = result.get("condition_name")
    result.setdefault("plan_id", _stable_plan_id(kind, goal, condition_name))
    result.setdefault("goal", goal)
    result.setdefault("condition_name", condition_name)
    result.setdefault("validation_metrics", [])
    if not result.get("required_confirmation"):
        result["required_confirmation"] = [
            "Confirm any side-effect or high-risk action before execution."
        ]
    if not result.get("steps"):
        steps = []
        for index, description in enumerate(result.get("recommended_steps", []), start=1):
            action_name = _infer_action_name(description)
            steps.append({
                "step_id": f"{result['plan_id']}_step_{index}",
                "action_name": action_name,
                "description": str(description),
                "params_needed": [],
                "risk_level": "high" if action_name.startswith(("set_", "tune_", "prepare_", "start_", "stop_", "run_")) else "low",
                "preconditions": [],
                "validation": list(result.get("validation_metrics", [])),
            })
        result["steps"] = steps
    return result


def format_chassis_plan(result: dict) -> str:
    """Render planner output as user-facing Chinese Markdown."""
    title = "底盘任务规划" if result.get("kind") == "chassis_task_plan" else "底盘调校建议"
    lines = [f"## {title}"]
    if result.get("goal"):
        lines.append(f"- 目标: {result['goal']}")
    if result.get("complaint"):
        lines.append(f"- 现象/抱怨: {result['complaint']}")
    if result.get("condition_name"):
        lines.append(f"- 工况: {result['condition_name']}")

    sections = [
        ("建议步骤", "recommended_steps"),
        ("参数方向", "parameter_direction"),
        ("风险提示", "risks"),
        ("验证指标", "validation_metrics"),
    ]
    for heading, key in sections:
        values = [str(item) for item in result.get(key, []) if item]
        if not values:
            continue
        lines.append(f"\n### {heading}")
        lines.extend(f"{index}. {item}" for index, item in enumerate(values, start=1))
    experiences = _format_recent_experiences(result.get("recent_experiences", []))
    if experiences:
        lines.append("\n### 近期经验参考")
        lines.extend(f"{index}. {item}" for index, item in enumerate(experiences, start=1))
    return "\n".join(lines)


def _format_recent_experiences(experiences) -> list:
    """Convert recent experience seeds into short user-facing notes."""
    notes = []
    for item in experiences or []:
        if not isinstance(item, dict):
            continue
        action_name = item.get("action_name") or "unknown_action"
        result = str(item.get("result") or "").strip()
        lesson = str(item.get("lesson") or "").strip()
        condition = item.get("condition_name")
        summary_parts = [f"历史动作 {action_name}"]
        if condition:
            summary_parts.append(f"工况 {condition}")
        if result:
            summary_parts.append(f"结果: {result[:120]}")
        elif lesson:
            summary_parts.append(f"经验: {lesson[:120]}")
        notes.append("；".join(summary_parts))
    return notes[:3]


def plan_chassis_task(goal: str, complaint: str = None,
                      condition_name: str = None) -> dict:
    """
    Build a conservative workflow plan before touching chassis parameters.
    """
    query = _text(goal, complaint, condition_name)
    result = _base_response("chassis_task_plan", goal, complaint, condition_name)

    if any(k in query for k in ["准备", "工况", "记录", "record", "采集"]):
        result["recommended_steps"].extend([
            "确认目标工况、地图和起点，先调用 prepare_test_scene 完成场景生效。",
            "调用 prepare_recording_session 检查记录选项，再 start_recording 开始采集。",
            "完成驾驶或仿真后 stop_recording，并补充评价元数据。",
        ])
        result["parameter_direction"].append("本任务优先准备场景和记录链路，不建议直接修改弹簧或稳定杆。")
        result["risks"].append("记录中修改车辆或场景会污染数据，应在记录前完成配置。")
        result["validation_metrics"].extend(["记录文件是否生成", "IMU/CarSim/MOOG 通道是否连续", "工况名称和起点是否正确"])
        return _ensure_plan_schema(result)

    if any(k in query for k in ["修改悬架", "仿真验证", "验证", "run_carsim", "悬架并仿真"]):
        result["recommended_steps"].extend([
            "先 get_current_setup 记录基线配置。",
            "根据目标只改变一个变量，例如先调整前/后稳定杆或前/后弹簧之一。",
            "调用 run_carsim 完成离线仿真，再 analyze_offline_result 对比基线。",
            "若指标改善且主观风险可接受，再进入下一轮小步迭代。",
        ])
        result["parameter_direction"].extend([
            "操稳问题优先小幅调整稳定杆分配，舒适性问题优先小幅调整弹簧刚度。",
            "避免一次同时修改前后弹簧和稳定杆，否则难以归因。",
        ])
        result["risks"].append("直接大幅提高刚度可能改善响应但恶化舒适性和轮胎贴地性。")
        result["validation_metrics"].extend(["横摆角速度峰值/相位", "侧倾角峰值", "横向加速度 RMS", "垂向加速度 RMS"])
        return _ensure_plan_schema(result)

    if any(k in query for k in ["侧倾", "单移线", "double lane", "lane change"]):
        result["recommended_steps"].extend([
            "先确认单移线工况并获取当前悬架配置。",
            "优先输出调校建议，再由工程师确认是否调用 set_antiroll_bar 或 set_spring。",
            "每次只改一个轴的稳定杆/弹簧，随后 run_carsim 验证。",
        ])
        result["parameter_direction"].extend([
            "侧倾大通常可考虑提高总滚转刚度，优先评估前/后稳定杆小幅加硬。",
            "若伴随转向不足，避免只加硬前稳定杆；可评估后稳定杆相对加硬。",
        ])
        result["risks"].append("提高滚转刚度可能增加单轮冲击、降低极限附着余量。")
        result["validation_metrics"].extend(["侧倾角峰值", "横摆响应", "转向盘角输入", "主观侧倾评分"])
        return _ensure_plan_schema(result)

    if any(k in query for k in ["中心区", "方向盘", "重", "手感"]):
        result["recommended_steps"].extend([
            "先查询 tune_haptic_feedback(mode=get) 和当前中心区工况。",
            "优先给出触感建议，确认后再小步调整摩擦/阻尼/回正增益。",
            "在中心区或小转角工况重复验证，不直接修改悬架硬件参数。",
        ])
        result["parameter_direction"].extend([
            "中心区重通常先评估降低摩擦增益或整体手感增益。",
            "若回正过强，再评估小幅降低回正增益。",
        ])
        result["risks"].append("过度降低摩擦/阻尼可能导致中心虚位感或振荡。")
        result["validation_metrics"].extend(["中心区转向力矩", "方向盘角速度", "回正超调", "主观中心区评分"])
        return _ensure_plan_schema(result)

    if any(k in query for k in ["起伏", "舒适", "垂向", "bump", "ride"]):
        result["recommended_steps"].extend([
            "确认起伏/舒适性工况并记录基线垂向响应。",
            "先建议弹簧/阻尼方向，确认后再小步修改悬架参数。",
            "每轮修改后用同一速度和同一路面重复验证。",
        ])
        result["parameter_direction"].extend([
            "垂向冲击偏大时，优先评估降低相关轴弹簧刚度或避免稳定杆过硬。",
            "若车身余振明显，应结合阻尼方案评估，当前工具仅覆盖弹簧/稳定杆。",
        ])
        result["risks"].append("降低刚度可能改善冲击但增加俯仰/侧倾和操稳响应滞后。")
        result["validation_metrics"].extend(["垂向加速度峰值/RMS", "俯仰角速度", "悬架行程", "舒适性主观评分"])
        return _ensure_plan_schema(result)

    result["recommended_steps"].extend([
        "先澄清目标、工况、当前配置和评价指标。",
        "优先调用 plan_chassis_task 或 suggest_chassis_tuning 形成方案，再确认具体动作。",
        "执行时保持单变量、小步迭代，并记录每轮结果。",
    ])
    result["parameter_direction"].append("信息不足时不直接修改硬件参数。")
    result["risks"].append("目标不清会导致参数修改不可追溯，且难以判断改善来源。")
    result["validation_metrics"].extend(["目标工况", "基线配置", "主观评价", "关键客观指标"])
    return _ensure_plan_schema(result)


def suggest_chassis_tuning(complaint: str, objective: str = None,
                           condition_name: str = None) -> dict:
    """
    Give conservative first-pass chassis or haptic tuning advice.
    """
    query = _text(complaint, objective, condition_name)
    result = _base_response("chassis_tuning_suggestion", objective, complaint, condition_name)

    if any(k in query for k in ["侧倾", "单移线", "lane"]):
        result["recommended_steps"].extend([
            "先复跑或确认单移线基线，记录侧倾角、横摆响应和主观侧倾评分。",
            "从稳定杆分配开始小步调整，必要时再评估弹簧刚度。",
            "每次修改后 run_carsim 并对比同一工况指标。",
        ])
        result["parameter_direction"].extend([
            "侧倾大且响应慢：考虑前后稳定杆整体小幅加硬。",
            "侧倾大且转向不足：避免只加硬前稳定杆，可评估后稳定杆相对加硬。",
            "侧倾大且车尾活跃：优先谨慎提高前稳定杆或降低后轴滚转刚度。",
        ])
        result["risks"].extend(["稳定杆过硬会牺牲不平路舒适性。", "后轴过硬可能增加甩尾风险。"])
        result["validation_metrics"].extend(["侧倾角峰值", "横摆角速度峰值", "横向加速度 RMS", "主观稳定性评分"])
        return _ensure_plan_schema(result)

    if any(k in query for k in ["中心区", "方向盘", "重", "手感"]):
        result["recommended_steps"].extend([
            "先用 tune_haptic_feedback(mode=get) 读取当前触感参数。",
            "优先小步调整触感参数，而不是修改悬架硬件。",
            "在中心区工况重复验证转向力和回正表现。",
        ])
        result["parameter_direction"].extend([
            "中心区偏重：优先小幅降低 friction 或 overall。",
            "回正力偏大：小幅降低 feedback。",
            "阻尼拖滞明显：小幅降低 damping，并观察振荡风险。",
        ])
        result["risks"].append("手感调轻过多会让中心区变虚，甚至掩盖真实路感。")
        result["validation_metrics"].extend(["方向盘中心区力矩", "小角度回正时间", "方向盘振荡", "主观手感评分"])
        return _ensure_plan_schema(result)

    if any(k in query for k in ["起伏", "舒适", "垂向", "bump", "ride"]):
        result["recommended_steps"].extend([
            "先固定车速和路面，记录垂向加速度与悬架行程基线。",
            "优先小步调整弹簧刚度方向，必要时评估稳定杆对单轮起伏的耦合影响。",
            "复验舒适性同时检查操稳副作用。",
        ])
        result["parameter_direction"].extend([
            "垂向冲击大：考虑相关轴弹簧刚度小幅降低。",
            "左右耦合冲击明显：检查稳定杆是否过硬。",
            "余振大：需要阻尼方案配合，当前先记录为后续知识样本。",
        ])
        result["risks"].append("舒适性改善可能带来更大侧倾/俯仰，需要同步检查操稳指标。")
        result["validation_metrics"].extend(["垂向加速度峰值/RMS", "悬架行程余量", "俯仰角速度", "舒适性评分"])
        return _ensure_plan_schema(result)

    result["recommended_steps"].extend([
        "补充抱怨现象、目标工况、车速和当前配置。",
        "先建立基线记录，再进行单变量调校。",
    ])
    result["parameter_direction"].append("信息不足时只提供诊断路径，不建议直接给具体硬件参数。")
    result["risks"].append("缺少工况和指标会导致建议不可验证。")
    result["validation_metrics"].extend(["基线数据", "目标工况", "主观评分", "客观指标"])
    return _ensure_plan_schema(result)
