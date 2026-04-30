"""数据分析 action — 通过 AnalysisService 操作。"""

import os


def register(registry, ctx):
    svc = ctx.service('analysis')

    def load_historical_record(folder_path: str) -> str:
        if not folder_path or not os.path.isdir(folder_path):
            return f"文件夹路径无效或不存在: {folder_path}"

        has_any = any(
            os.path.exists(os.path.join(folder_path, f))
            for f in ("CarsimData.csv", "MoogData.csv", "IMUData.csv")
        )
        if not has_any:
            return f"文件夹中未找到 CSV 数据文件: {folder_path}"

        try:
            loaded = svc.load_record(folder_path)
            if loaded:
                return f"已加载历史记录: {', '.join(loaded)} ({folder_path})"
            return f"未加载到任何数据: {folder_path}"
        except Exception as e:
            return f"加载历史记录失败: {e}"

    registry.register(
        name="load_historical_record",
        description="加载指定文件夹中的历史记录 CSV 数据并绘图。",
        params_schema={
            "type": "object",
            "properties": {
                "folder_path": {"type": "string", "description": "记录文件夹路径"}
            },
            "required": ["folder_path"]
        },
        callback=load_historical_record,
        category="analysis",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )
