"""数据记录相关 action — 通过 RecordingService 操作。"""


def register(registry, ctx):
    svc = ctx.service('recording')

    def start_recording() -> str:
        if svc.is_recording():
            return "当前已经在记录中,无需重复开始。"
        try:
            return svc.start()
        except Exception as e:
            return f"开始记录失败: {e}"

    registry.register(
        name="start_recording",
        description="开始记录 IMU、CarSim、MOOG 等传感器数据到 CSV 文件。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=start_recording,
        category="recording",
        risk_level="medium",
        exposed=True,
    )

    def stop_recording() -> str:
        if not svc.is_recording():
            return "当前没有在记录,无需结束。"
        try:
            return svc.stop()
        except Exception as e:
            return f"结束记录失败: {e}"

    registry.register(
        name="stop_recording",
        description="结束当前记录,保存数据到 CSV。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=stop_recording,
        category="recording",
        risk_level="medium",
        exposed=True,
    )

    def prepare_recording_session(record_disusx=None, video_recording=None,
                                  par_save=None, auto_record=None) -> str:
        changes = svc.set_options(
            record_disusx=record_disusx,
            video_recording=video_recording,
            par_save=par_save,
            auto_record=auto_record,
        )
        if not changes:
            return ("未指定任何选项。可用参数: record_disusx, video_recording, "
                    "par_save, auto_record (均为布尔值)")
        desc = ", ".join(f"{k}={v}" for k, v in changes.items())
        return "已更新记录选项: " + desc

    registry.register(
        name="prepare_recording_session",
        description="准备一次记录会话。统一配置电控记录、视频录制等选项。",
        params_schema={
            "type": "object",
            "properties": {
                "record_disusx": {"type": "boolean"},
                "video_recording": {"type": "boolean"},
                "par_save": {"type": "boolean"},
                "auto_record": {"type": "boolean"},
            },
            "required": []
        },
        callback=prepare_recording_session,
        category="recording",
        risk_level="low",
        exposed=True,
    )

    def get_recording_status() -> str:
        return svc.get_status()

    registry.register(
        name="get_recording_status",
        description="查询当前数据记录状态。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=get_recording_status,
        category="query",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )
