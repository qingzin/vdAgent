"""
数据记录相关 action

- start_recording         开始记录 IMU/CarSim/MOOG 数据
- stop_recording          结束记录
- set_recording_options   配置记录开关(disusx / video / par / auto_record)
- get_recording_status    查询当前记录状态
"""


def register(registry, ctx):

    # ---------- 开始记录 ----------
    def start_recording() -> str:
        ui = ctx.ui
        if ctx.is_recording():
            return "当前已经在记录中,无需重复开始。"
        try:
            ui.start_record()
            return "已开始记录 IMU / CarSim / MOOG 数据。"
        except Exception as e:
            return f"开始记录失败: {e}"

    registry.register(
        name="start_recording",
        description="开始记录 IMU、CarSim、MOOG 等传感器数据到 CSV 文件。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=start_recording,
    )

    # ---------- 结束记录 ----------
    def stop_recording() -> str:
        ui = ctx.ui
        if not ctx.is_recording():
            return "当前没有在记录,无需结束。"
        try:
            ui.finish_record()
            return "已结束记录。稍后可能弹出评价信息对话框,请在 GUI 中填写。"
        except Exception as e:
            return f"结束记录失败: {e}"

    registry.register(
        name="stop_recording",
        description="结束当前记录,保存数据到 CSV。"
                    "非 auto_record 模式下会弹出评价信息对话框。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=stop_recording,
    )

    # ---------- 记录选项 ----------
    def set_recording_options(record_disusx=None, video_recording=None,
                              par_save=None, auto_record=None) -> str:
        ui = ctx.ui
        changes = []

        if record_disusx is not None:
            ui.record_disusx = bool(record_disusx)
            changes.append(f"Disus_C 电控记录={bool(record_disusx)}")

        if video_recording is not None:
            try:
                ui.video_recording(bool(video_recording))
                changes.append(f"视频录制={bool(video_recording)}")
            except Exception as e:
                changes.append(f"视频录制设置失败: {e}")

        if par_save is not None:
            ui.is_par_save = bool(par_save)
            changes.append(f"保存 par 文件={bool(par_save)}")

        if auto_record is not None:
            # auto_record 是 int, 0 关闭非 0 开启。此处统一为 0 或 1。
            val = 1 if auto_record else 0
            ui.auto_record = val
            changes.append(f"自动记录={'开启' if val else '关闭'}")

        if not changes:
            return ("未指定任何选项。可用参数: record_disusx, video_recording, "
                    "par_save, auto_record (均为布尔值)")
        return "已更新记录选项: " + ", ".join(changes)

    registry.register(
        name="set_recording_options",
        description="配置数据记录的附加选项,未指定的参数保持不变。包括:"
                    "电控数据记录开关(record_disusx)、视频录制开关(video_recording)、"
                    ".par 参数文件保存开关(par_save)、自动记录模式(auto_record,"
                    "开启后根据 GPS 坐标自动开始/结束记录)。",
        params_schema={
            "type": "object",
            "properties": {
                "record_disusx":    {"type": "boolean", "description": "Disus_C 电控记录"},
                "video_recording":  {"type": "boolean", "description": "视频录制"},
                "par_save":         {"type": "boolean", "description": ".par 文件保存"},
                "auto_record":      {"type": "boolean", "description": "自动记录"},
            },
            "required": []
        },
        callback=set_recording_options,
    )

    # ---------- 查询记录状态 ----------
    def get_recording_status() -> str:
        ui = ctx.ui
        is_rec = ctx.is_recording()
        parts = [f"当前记录状态: {'记录中' if is_rec else '未记录'}"]
        for label, attr in [
            ("Disus_C 电控记录", 'record_disusx'),
            ("视频录制",         'is_video_recording'),
            (".par 文件保存",    'is_par_save'),
        ]:
            val = getattr(ui, attr, None)
            if val is not None:
                parts.append(f"{label}: {'开' if val else '关'}")
        ar = getattr(ui, 'auto_record', 0)
        parts.append(f"自动记录: {'开启' if ar else '关闭'}")
        return "; ".join(parts)

    registry.register(
        name="get_recording_status",
        description="查询当前数据记录状态(是否正在记录、各类开关的启停情况)。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=get_recording_status,
    )
