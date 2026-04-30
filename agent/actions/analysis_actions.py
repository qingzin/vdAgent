"""
数据分析相关 action

- load_historical_record   加载指定文件夹的历史记录 CSV 数据并绘图
"""

import os


def register(registry, ctx):

    def load_historical_record(folder_path: str) -> str:
        """
        加载历史记录数据。folder_path 为包含 CarsimData.csv / MoogData.csv /
        IMUData.csv 的文件夹路径。
        """
        ui = ctx.ui
        if not folder_path or not os.path.isdir(folder_path):
            return f"文件夹路径无效或不存在: {folder_path}"

        carsim_file = os.path.join(folder_path, "CarsimData.csv")
        moog_file = os.path.join(folder_path, "MoogData.csv")
        imu_file = os.path.join(folder_path, "IMUData.csv")

        has_any = os.path.exists(carsim_file) or os.path.exists(moog_file) or os.path.exists(imu_file)
        if not has_any:
            return f"文件夹中未找到 CSV 数据文件 (CarsimData/MoogData/IMUData): {folder_path}"

        try:
            # 停止实时绘图并清空旧数据
            if hasattr(ui, 'run_button'):
                ui.run_button.setChecked(False)
            ui.plot_running = False
            ui.record_time_data_imu.clear()
            ui.record_time_data_carsim.clear()
            ui.record_time_data_moog.clear()
            for channel in ui.record_signal_data:
                for signal_type in ['input', 'moog', 'imu']:
                    ui.record_signal_data[channel][signal_type].clear()

            # 加载各数据源
            loaded = []
            if os.path.exists(carsim_file):
                ui.load_csv_data(carsim_file, 'input')
                loaded.append("CarsimData")
            if os.path.exists(moog_file):
                ui.load_csv_data(moog_file, 'moog')
                loaded.append("MoogData")
            if os.path.exists(imu_file):
                ui.load_csv_data(imu_file, 'imu')
                loaded.append("IMUData")

            # 绘图
            if loaded:
                ui.plot_loaded_data()
            return f"已加载历史记录: {', '.join(loaded)} ({folder_path})"
        except Exception as e:
            return f"加载历史记录失败: {e}"

    registry.register(
        name="load_historical_record",
        description="加载指定文件夹中的历史记录 CSV 数据并绘图。"
                    "适用于回放已完成的试验数据,CarsimData/MoogData/IMUData。",
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
