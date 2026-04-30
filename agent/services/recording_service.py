"""数据记录 service。"""


from agent.services._base import BaseService

class RecordingService(BaseService):


    def is_recording(self) -> bool:
        return self._ctx.is_recording()

    def start(self) -> str:
        self._ui.start_record()
        return "已开始记录 IMU / CarSim / MOOG 数据。"

    def stop(self) -> str:
        self._ui.finish_record()
        return "已结束记录。稍后可能弹出评价信息对话框,请在 GUI 中填写。"

    def set_options(self, record_disusx=None, video_recording=None,
                    par_save=None, auto_record=None) -> dict:
        changes = {}
        ui = self._ui

        if record_disusx is not None:
            ui.record_disusx = bool(record_disusx)
            changes['disusx'] = bool(record_disusx)

        if video_recording is not None:
            ui.video_recording(bool(video_recording))
            changes['video'] = bool(video_recording)

        if par_save is not None:
            ui.is_par_save = bool(par_save)
            changes['par_save'] = bool(par_save)

        if auto_record is not None:
            val = 1 if auto_record else 0
            ui.auto_record = val
            changes['auto_record'] = bool(val)

        return changes

    def get_status(self) -> str:
        ui = self._ui
        is_rec = self.is_recording()
        parts = [f"当前记录状态: {'记录中' if is_rec else '未记录'}"]
        for label, attr in [
            ("Disus_C 电控记录", 'record_disusx'),
            ("视频录制", 'is_video_recording'),
            (".par 文件保存", 'is_par_save'),
        ]:
            val = getattr(ui, attr, None)
            if val is not None:
                parts.append(f"{label}: {'开' if val else '关'}")
        ar = getattr(ui, 'auto_record', 0)
        parts.append(f"自动记录: {'开启' if ar else '关闭'}")
        return "; ".join(parts)
