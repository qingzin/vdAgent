"""数据分析 service — 历史记录加载与回放。"""

import os


from agent.services._base import BaseService

class AnalysisService(BaseService):


    def load_record(self, folder_path: str) -> list:
        """加载历史记录 CSV 数据并绘图。返回已加载的数据源列表。"""
        ui = self._ui

        ui.plot_running = False
        if hasattr(ui, 'run_button'):
            ui.run_button.setChecked(False)

        # 清空旧数据
        ui.record_time_data_imu.clear()
        ui.record_time_data_carsim.clear()
        ui.record_time_data_moog.clear()
        for channel in ui.record_signal_data:
            for signal_type in ['input', 'moog', 'imu']:
                ui.record_signal_data[channel][signal_type].clear()

        loaded = []
        for fname, sig_type in [
            ("CarsimData.csv", 'input'),
            ("MoogData.csv", 'moog'),
            ("IMUData.csv", 'imu'),
        ]:
            path = os.path.join(folder_path, fname)
            if os.path.exists(path):
                ui.load_csv_data(path, sig_type)
                loaded.append(fname.replace('.csv', ''))

        if loaded:
            ui.plot_loaded_data()
        return loaded
