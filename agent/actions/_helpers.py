"""
Actions 共享辅助函数
"""


def require_not_recording(ctx, action_name: str):
    """记录中拒绝执行可能破坏状态的操作。返回错误字符串或 None。"""
    if ctx.is_recording():
        return (f"当前正在记录数据,无法执行【{action_name}】。"
                f"请先结束记录再执行此操作。")
    return None


def fuzzy_resolve(target, available):
    """
    精确匹配 + 子串模糊匹配。
    Returns: (resolved_name, error_message)
    """
    if target in available:
        return target, None
    matches = [n for n in available if target in n]
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        return None, f"找到多个匹配: {matches}, 请指定更精确的名称。"
    return None, f"未找到 '{target}'"
