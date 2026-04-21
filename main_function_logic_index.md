# `main.py` 功能逻辑函数清单

基于 [main.py](/D:/codex/codex-IM/vdAgent/main.py) 手工整理。

说明：
- 这里主要列出“承载业务/功能逻辑”的函数。
- 纯 UI 搭建函数，如 `init_ui`、`create_*_tab`、纯弹窗构造函数，默认不作为核心功能逻辑列入。
- 行号用于快速跳转，后续如果 `main.py` 有较大改动，建议同步更新本文件。

## 1. 记录与数据归档

- [update_indicator](/D:/codex/codex-IM/vdAgent/main.py:493)
  录制状态指示灯更新。
- [start_record](/D:/codex/codex-IM/vdAgent/main.py:503)
  启动主记录流程，创建 IMU / CarSim / MOOG / 视觉补偿等 CSV 文件并切换状态。
- [start_record_disusx](/D:/codex/codex-IM/vdAgent/main.py:631)
  启动 DisusX 电控输入/输出数据记录。
- [select_save_folder](/D:/codex/codex-IM/vdAgent/main.py:657)
  选择记录结果保存目录。
- [finish_record](/D:/codex/codex-IM/vdAgent/main.py:668)
  结束记录，触发异步保存、参数导出、评价流程。
- [save_data_async](/D:/codex/codex-IM/vdAgent/main.py:709)
  异步保存本轮记录数据。
- [create_evaluation_dialog](/D:/codex/codex-IM/vdAgent/main.py:782)
  记录结束后弹出评价信息填写框。
- [on_evaluation_dialog_closed](/D:/codex/codex-IM/vdAgent/main.py:890)
  评价窗口关闭后的状态恢复。
- [save_parameters_async](/D:/codex/codex-IM/vdAgent/main.py:898)
  导出 CarSim 参数文件。
- [save_record_data](/D:/codex/codex-IM/vdAgent/main.py:916)
  校验评价信息、复制数据目录并写入数据库。
- [finish_record_disusx](/D:/codex/codex-IM/vdAgent/main.py:1016)
  落盘 DisusX 记录数据。

## 2. UDP 数据接收与实时数据入库

- [receive_electrical_control_i_data](/D:/codex/codex-IM/vdAgent/main.py:1040)
  接收电控输入数据并在记录时缓存。
- [receive_electrical_control_o_data](/D:/codex/codex-IM/vdAgent/main.py:1069)
  接收电控输出数据并在记录时缓存。
- [receive_rfpro_coordinates_data](/D:/codex/codex-IM/vdAgent/main.py:1096)
  接收 RFPRO 坐标数据。
- [receive_imu_data](/D:/codex/codex-IM/vdAgent/main.py:1166)
  接收 IMU 数据并更新缓存/记录。
- [receive_carsim_data](/D:/codex/codex-IM/vdAgent/main.py:1261)
  接收 CarSim 数据并更新缓存/记录。
- [receive_moog_data](/D:/codex/codex-IM/vdAgent/main.py:1385)
  接收运动平台 MOOG 数据并更新缓存/记录。
- [receive_compensator_data](/D:/codex/codex-IM/vdAgent/main.py:1474)
  接收视觉补偿相关数据。

## 3. 预设、采样率与 UI 状态持久化

- [preset_settings_dialog](/D:/codex/codex-IM/vdAgent/main.py:1603)
  打开预设设置界面。
- [cueing_change](/D:/codex/codex-IM/vdAgent/main.py:1645)
  触发 cueing 方案变更逻辑。
- [save_preset_settings](/D:/codex/codex-IM/vdAgent/main.py:1649)
  保存预设字段。
- [record_settings_dialog](/D:/codex/codex-IM/vdAgent/main.py:1692)
  打开记录设置界面。
- [open_settings_dialog](/D:/codex/codex-IM/vdAgent/main.py:1807)
  打开动态绘图相关设置。
- [save_settings](/D:/codex/codex-IM/vdAgent/main.py:1875)
  保存绘图/缓存相关设置。
- [save_sampling_rates](/D:/codex/codex-IM/vdAgent/main.py:1896)
  保存采样率配置。
- [load_sampling_rates](/D:/codex/codex-IM/vdAgent/main.py:1910)
  加载采样率配置。
- [load_ui_state](/D:/codex/codex-IM/vdAgent/main.py:1926)
  加载 UI 状态。
- [save_ui_state](/D:/codex/codex-IM/vdAgent/main.py:1946)
  保存 UI 状态。
- [on_tab_changed](/D:/codex/codex-IM/vdAgent/main.py:1887)
  页签切换时的状态处理。

## 4. 工作区变量管理

- [init_workspace_panel](/D:/codex/codex-IM/vdAgent/main.py:1955)
  初始化工作区变量面板。
- [handle_cell_double_clicked](/D:/codex/codex-IM/vdAgent/main.py:1985)
  双击变量单元格时进入编辑。
- [handle_cell_changed](/D:/codex/codex-IM/vdAgent/main.py:2001)
  处理变量值修改。
- [update_workspace_table](/D:/codex/codex-IM/vdAgent/main.py:2130)
  刷新工作区变量表。
- [create_variable](/D:/codex/codex-IM/vdAgent/main.py:2142)
  创建变量。
- [edit_variable](/D:/codex/codex-IM/vdAgent/main.py:2153)
  编辑变量。
- [delete_variable](/D:/codex/codex-IM/vdAgent/main.py:2166)
  删除变量。
- [rename_variable](/D:/codex/codex-IM/vdAgent/main.py:2175)
  重命名变量。

## 5. 平台、相机、驾驶员与场景数据下发

- [sendData2PlatformControl](/D:/codex/codex-IM/vdAgent/main.py:2029)
  向运动平台发送控制指令。
- [sendDataStartPoint2](/D:/codex/codex-IM/vdAgent/main.py:2044)
  向平台发送起点坐标。
- [sendDataDriverData2](/D:/codex/codex-IM/vdAgent/main.py:2063)
  发送驾驶员操作数据。
- [sendDataPlatformOffset2](/D:/codex/codex-IM/vdAgent/main.py:2085)
  发送平台偏置数据。
- [sendData2Moog](/D:/codex/codex-IM/vdAgent/main.py:2102)
  向 MOOG 相关通道发送数据。
- [sendData2camera](/D:/codex/codex-IM/vdAgent/main.py:2117)
  向相机侧发送启停等控制数据。
- [apply_platform_offset](/D:/codex/codex-IM/vdAgent/main.py:3309)
  从界面输入读取偏置并应用到平台。
- [select_data_file](/D:/codex/codex-IM/vdAgent/main.py:3320)
  选择操作数据文件。
- [send_operation_data](/D:/codex/codex-IM/vdAgent/main.py:3336)
  按 CSV 驾驶操作回放发送控制数据。

## 6. 场景与工况

- [load_scenario_data](/D:/codex/codex-IM/vdAgent/main.py:3386)
  从 `scenarios.json` 加载地图与起点配置。
- [update_start_points](/D:/codex/codex-IM/vdAgent/main.py:3408)
  根据地图更新起点列表。
- [update_position_display](/D:/codex/codex-IM/vdAgent/main.py:3425)
  刷新当前起点坐标显示。
- [confirm_scenario_settings](/D:/codex/codex-IM/vdAgent/main.py:3434)
  确认场景设置并下发起点，同时触发 cueing 参数切换。
- [condition_choose](/D:/codex/codex-IM/vdAgent/main.py:4109)
  根据工况下拉框切换 CarSim 条目。

## 7. 仿真执行与结果处理

- [RunDspace](/D:/codex/codex-IM/vdAgent/main.py:3452)
  运行 CarSim/DSpace 流程，读取结果，比较指标并导出离线仿真 CSV。
- [OpenSimulink](/D:/codex/codex-IM/vdAgent/main.py:3585)
  打开 Simulink。
- [BuildDspace](/D:/codex/codex-IM/vdAgent/main.py:3588)
  编译 DSpace。
- [clear](/D:/codex/codex-IM/vdAgent/main.py:4387)
  清理离线仿真结果目录。
- [viewOfflineData](/D:/codex/codex-IM/vdAgent/main.py:4427)
  查看离线仿真数据对比结果。

## 8. 车型与虚拟调参

- [UpdateTuningParam](/D:/codex/codex-IM/vdAgent/main.py:4115)
  从当前 CarSim 数据集同步整车、弹簧、防倾杆等调参项到界面。
- [CurrentVehicleSpringPage](/D:/codex/codex-IM/vdAgent/main.py:4445)
  切换到当前车辆弹簧/悬架页面。
- [recordApplyTuningParam](/D:/codex/codex-IM/vdAgent/main.py:4466)
  记录当前调参方案。
- [Scheme_SetApplyTuningParam](/D:/codex/codex-IM/vdAgent/main.py:4565)
  将记录的方案应用到界面/当前状态。
- [selectScheme](/D:/codex/codex-IM/vdAgent/main.py:4573)
  选择方案。
- [resetApplyTuningParam](/D:/codex/codex-IM/vdAgent/main.py:4612)
  恢复默认调参状态。
- [ApplyTuningParam](/D:/codex/codex-IM/vdAgent/main.py:4619)
  将当前弹簧/防倾杆调参真正写回 CarSim。
- [add_subtract_button](/D:/codex/codex-IM/vdAgent/main.py:3268)
  通过增减按钮修改弹簧/防倾杆百分比。
- [onCarChange](/D:/codex/codex-IM/vdAgent/main.py:5523)
  切换车型。
- [onFrontSpringChange](/D:/codex/codex-IM/vdAgent/main.py:5536)
  切换前弹簧。
- [onFrontRightSpringChange](/D:/codex/codex-IM/vdAgent/main.py:5548)
  切换前右弹簧。
- [onRearSpringChange](/D:/codex/codex-IM/vdAgent/main.py:5561)
  切换后弹簧。
- [onRearRightSpringChange](/D:/codex/codex-IM/vdAgent/main.py:5573)
  切换后右弹簧。
- [onFrontAuxMChange](/D:/codex/codex-IM/vdAgent/main.py:5585)
  切换前防倾杆/滚转刚度相关数据集。
- [onRearAuxMChange](/D:/codex/codex-IM/vdAgent/main.py:5614)
  切换后防倾杆/滚转刚度相关数据集。
- [OnFrontSpringTextChanged](/D:/codex/codex-IM/vdAgent/main.py:5643)
  以数值方式修改前弹簧刚度。
- [OnRearSpringTextChanged](/D:/codex/codex-IM/vdAgent/main.py:5649)
  以数值方式修改后弹簧刚度。

## 9. 视觉补偿

- [ApplyVisualCompensation](/D:/codex/codex-IM/vdAgent/main.py:3874)
  应用视觉运动跟随补偿参数并保存配置。
- [ApplyVisualDelayCompensation](/D:/codex/codex-IM/vdAgent/main.py:3899)
  应用视觉延迟补偿参数并保存配置。

## 10. 绘图、报警与数据分析

- [toggle_alarm](/D:/codex/codex-IM/vdAgent/main.py:2392)
  开关报警逻辑。
- [change_scenario](/D:/codex/codex-IM/vdAgent/main.py:2407)
  切换报警工况。
- [open_custom_threshold_dialog](/D:/codex/codex-IM/vdAgent/main.py:2411)
  设置自定义报警阈值。
- [check_alarm](/D:/codex/codex-IM/vdAgent/main.py:2462)
  判断指定信号是否越过阈值。
- [run_jsmnq_plot](/D:/codex/codex-IM/vdAgent/main.py:2483)
  运行 jsmnq 绘图分析。
- [run_compare_csv](/D:/codex/codex-IM/vdAgent/main.py:2490)
  运行 CSV 对比分析。
- [open_axis_range_dialog](/D:/codex/codex-IM/vdAgent/main.py:2494)
  打开坐标轴范围设置。
- [apply_axis_range](/D:/codex/codex-IM/vdAgent/main.py:2525)
  应用绘图 X 轴范围。
- [get_unit](/D:/codex/codex-IM/vdAgent/main.py:4797)
  按通道名称返回单位。
- [toggle_plot_visibility](/D:/codex/codex-IM/vdAgent/main.py:4819)
  切换单个图表显示状态。
- [update_plot_layout](/D:/codex/codex-IM/vdAgent/main.py:4822)
  按当前启用通道重排图表布局。
- [update_plots](/D:/codex/codex-IM/vdAgent/main.py:4920)
  核心实时绘图刷新逻辑，同时包含报警检测。
- [clear_plots](/D:/codex/codex-IM/vdAgent/main.py:5085)
  清空实时绘图缓存并重置坐标轴。
- [toggle_plotting](/D:/codex/codex-IM/vdAgent/main.py:5124)
  切换绘图运行状态。
- [stop_plotting](/D:/codex/codex-IM/vdAgent/main.py:5197)
  停止实时绘图。
- [load_plot_state](/D:/codex/codex-IM/vdAgent/main.py:5313)
  加载图表显示状态。
- [save_plot_state](/D:/codex/codex-IM/vdAgent/main.py:5325)
  保存图表显示状态。
- [toggle_all_plots_on](/D:/codex/codex-IM/vdAgent/main.py:5357)
  一键打开全部图表。
- [toggle_all_plots_off](/D:/codex/codex-IM/vdAgent/main.py:5363)
  一键关闭全部图表。

## 11. 信号发送与 PVA 控制

- [handle_control_command_input](/D:/codex/codex-IM/vdAgent/main.py:2689)
  解析并下发平台控制码输入。
- [handle_signal_input](/D:/codex/codex-IM/vdAgent/main.py:2710)
  根据信号模式/算法切换信号配置面板逻辑。
- [update_signal_params](/D:/codex/codex-IM/vdAgent/main.py:2733)
  按信号数量和类型重建参数输入区。
- [update_time_value_combos](/D:/codex/codex-IM/vdAgent/main.py:2842)
  将工作区变量同步到自定义信号的时间/值下拉框。
- [clear_signal_param_widgets](/D:/codex/codex-IM/vdAgent/main.py:2880)
  清除信号参数输入组件。
- [send_signal](/D:/codex/codex-IM/vdAgent/main.py:5219)
  启动一次信号发送。
- [one_click_start](/D:/codex/codex-IM/vdAgent/main.py:5250)
  一键启动平台流程。
- [_one_click_step](/D:/codex/codex-IM/vdAgent/main.py:5260)
  一键启动流程中的分步执行。
- [one_click_stop](/D:/codex/codex-IM/vdAgent/main.py:5270)
  一键停机流程。
- [send_control_command](/D:/codex/codex-IM/vdAgent/main.py:5283)
  发送控制命令。
- [mode_changed](/D:/codex/codex-IM/vdAgent/main.py:5291)
  触感方案切换时更新显示。
- [apply_mode](/D:/codex/codex-IM/vdAgent/main.py:5301)
  应用当前体感方案。
- [toggle_all_signal](/D:/codex/codex-IM/vdAgent/main.py:5369)
  一键启停全部信号线程。
- [toggle_signal](/D:/codex/codex-IM/vdAgent/main.py:5383)
  启停单个信号线程。
- [stop_signal_thread](/D:/codex/codex-IM/vdAgent/main.py:5394)
  停止单个信号线程。
- [start_signal_thread](/D:/codex/codex-IM/vdAgent/main.py:5406)
  创建并启动单个信号线程。
- [reset_signal_button](/D:/codex/codex-IM/vdAgent/main.py:5494)
  重置单个信号按钮状态。
- [get_index_from_signal_type](/D:/codex/codex-IM/vdAgent/main.py:5500)
  将信号类型映射到下发索引。
- [electrol_recording](/D:/codex/codex-IM/vdAgent/main.py:5131)
  切换电控记录开关。
- [rename_folder_name](/D:/codex/codex-IM/vdAgent/main.py:5134)
  切换录制目录重命名选项。
- [par_recording](/D:/codex/codex-IM/vdAgent/main.py:5137)
  切换参数文件导出开关。
- [auto_recording](/D:/codex/codex-IM/vdAgent/main.py:5140)
  切换自动记录模式。
- [video_recording](/D:/codex/codex-IM/vdAgent/main.py:5149)
  切换视频录制模式并同步到相机侧。

## 12. 触感反馈

- [save_haptic_settings](/D:/codex/codex-IM/vdAgent/main.py:5785)
  保存当前触感增益设置。
- [get_f_data](/D:/codex/codex-IM/vdAgent/main.py:5798)
  根据车速、横向加速度、方向盘状态计算反馈力矩。
- [update_haptic_plots](/D:/codex/codex-IM/vdAgent/main.py:5814)
  更新方向盘角度、力矩和力矩-转角关系图。
- [save_haptic_gain](/D:/codex/codex-IM/vdAgent/main.py:5871)
  落盘触感配置。
- [load_haptic_gain](/D:/codex/codex-IM/vdAgent/main.py:5883)
  加载触感配置。
- [sendData2CarSim](/D:/codex/codex-IM/vdAgent/main.py:5897)
  向 CarSim 发送触感/反馈相关数据。

## 13. 记录回放与离线绘制

- [load_record](/D:/codex/codex-IM/vdAgent/main.py:5911)
  选择一组记录文件并加载离线回放数据。
- [load_csv_data](/D:/codex/codex-IM/vdAgent/main.py:5967)
  读取单个 CSV 到记录缓存。
- [plot_loaded_data](/D:/codex/codex-IM/vdAgent/main.py:6056)
  绘制已加载的离线记录数据。

## 14. 线程/生命周期相关

- [closeEvent](/D:/codex/codex-IM/vdAgent/main.py:5330)
  关闭窗口时保存状态并做退出清理。
- [SendWarningMessage](/D:/codex/codex-IM/vdAgent/main.py:4463)
  统一弹出/显示警告消息。

## 15. 相关辅助类

- [VariableEditor.__init__](/D:/codex/codex-IM/vdAgent/main.py:6095)
  变量编辑弹窗初始化。
- [VariableEditor.init_ui](/D:/codex/codex-IM/vdAgent/main.py:6102)
  变量编辑弹窗界面搭建。
- [VariableEditor.confirm_edit](/D:/codex/codex-IM/vdAgent/main.py:6121)
  校验并提交变量编辑结果。
- [SignalSenderThread.__init__](/D:/codex/codex-IM/vdAgent/main.py:6151)
  信号发送线程初始化。
- [SignalSenderThread.run](/D:/codex/codex-IM/vdAgent/main.py:6170)
  信号发送线程主循环。
- [SignalSenderThread.sendPlotData](/D:/codex/codex-IM/vdAgent/main.py:6181)
  线程内按时间序列发送绘图/控制数据。
- [SignalSenderThread.stop](/D:/codex/codex-IM/vdAgent/main.py:6194)
  停止信号发送线程。

## 16. 本次未重点列入的纯 UI/结构函数

以下函数更偏界面搭建或容器初始化，这次没有作为“核心功能逻辑”展开：

- `init_ui`
- `create_analysis_tab`
- `create_database_tab`
- `create_motion_display_tab`
- `create_signal_input_tab`
- `create_feeling_mode_tab`
- `create_virtual_tuning_tab`
- `create_visual_compensation_tab`
- `create_delay_tab`
- `create_haptic_adjustment_tab`
- `toggle_sidebar`

## 17. 函数调用链与依赖关系

本节按业务链路整理“入口函数 -> 下游函数/外部依赖 -> 主要状态/产物”。

### 17.1 启动初始化链路

- [SimulatorUI.__init__](/D:/codex/codex-IM/vdAgent/main.py:184)
  -> [load_ui_state](/D:/codex/codex-IM/vdAgent/main.py:1926)
  -> [init_workspace_panel](/D:/codex/codex-IM/vdAgent/main.py:1955)
  -> [init_ui](/D:/codex/codex-IM/vdAgent/main.py:1501)
  -> [load_plot_state](/D:/codex/codex-IM/vdAgent/main.py:5313)
  -> [load_sampling_rates](/D:/codex/codex-IM/vdAgent/main.py:1910)
  -> [load_haptic_gain](/D:/codex/codex-IM/vdAgent/main.py:5883)
  初始化窗口、状态配置、工作区、图表状态、采样率和触感参数。
- [init_ui](/D:/codex/codex-IM/vdAgent/main.py:1501)
  -> `create_*_tab`
  -> [create_virtual_tuning_tab](/D:/codex/codex-IM/vdAgent/main.py:2928)
  -> [create_motion_display_tab](/D:/codex/codex-IM/vdAgent/main.py:2189)
  -> [create_signal_input_tab](/D:/codex/codex-IM/vdAgent/main.py:2538)
  -> [create_haptic_adjustment_tab](/D:/codex/codex-IM/vdAgent/main.py:5664)
  -> [create_visual_compensation_tab](/D:/codex/codex-IM/vdAgent/main.py:3591)
  构建主要功能页签，并通过按钮/信号连接后续功能入口。

外部依赖：
- `win32com.client.Dispatch("CarSim.Application")` 初始化全局 `carsim`。
- `udp_config.json` 提供本机绑定 IP。
- 多个 UDP socket 在模块加载阶段绑定端口。

### 17.2 数据记录链路

- [start_record](/D:/codex/codex-IM/vdAgent/main.py:503)
  -> [update_indicator](/D:/codex/codex-IM/vdAgent/main.py:493)
  -> [start_record_disusx](/D:/codex/codex-IM/vdAgent/main.py:631)
  -> [sendData2camera](/D:/codex/codex-IM/vdAgent/main.py:2117)
  启动记录，创建保存目录和 CSV writer，切换 `is_recording_*` 状态，并通知相机开始。
- [finish_record](/D:/codex/codex-IM/vdAgent/main.py:668)
  -> [update_indicator](/D:/codex/codex-IM/vdAgent/main.py:493)
  -> [save_data_async](/D:/codex/codex-IM/vdAgent/main.py:709)
  -> [create_evaluation_dialog](/D:/codex/codex-IM/vdAgent/main.py:782)
  -> [sendData2camera](/D:/codex/codex-IM/vdAgent/main.py:2117)
  -> [save_parameters_async](/D:/codex/codex-IM/vdAgent/main.py:898)
  结束记录，关闭状态、异步落盘、可选导出参数文件，并进入评价归档。
- [save_data_async](/D:/codex/codex-IM/vdAgent/main.py:709)
  -> [finish_record_disusx](/D:/codex/codex-IM/vdAgent/main.py:1016)
  -> 清空 `recordIMUDataList` / `recordCarsimDataList` / `recordMoogDataList` 等缓存。
- [save_record_data](/D:/codex/codex-IM/vdAgent/main.py:916)
  -> `shutil.copytree`
  -> `mysql_utils.MySQLDatabase().connect()`
  -> `insert_test_data`
  -> `disconnect`
  将记录目录复制到网络数据库目录，并把元数据写入 MySQL。

主要状态/产物：
- `self.save_path`
- `IMUData.csv`
- `CarsimData.csv`
- `MoogData.csv`
- `VisualCompensator.csv`
- `Disus_C_i.csv`
- `Disus_C_o.csv`
- 数据库中的评价记录。

### 17.3 UDP 接收与缓存链路

- [receive_imu_data](/D:/codex/codex-IM/vdAgent/main.py:1166)
  -> `udp.recvfrom`
  -> 更新 `time_data_imu` / `signal_data[*]['imu']`
  -> 记录时写入 `recordIMUDataList`。
- [receive_carsim_data](/D:/codex/codex-IM/vdAgent/main.py:1261)
  -> `udp2.recvfrom`
  -> 更新 `time_data_carsim` / `signal_data[*]['input']`
  -> 记录时写入 `recordCarsimDataList`。
- [receive_moog_data](/D:/codex/codex-IM/vdAgent/main.py:1385)
  -> `udp3.recvfrom`
  -> 更新 `time_data_moog` / `signal_data[*]['moog']`
  -> 记录时写入 `recordMoogDataList`。
- [receive_electrical_control_i_data](/D:/codex/codex-IM/vdAgent/main.py:1040)
  -> `udp_electrical_control_i.recvfrom`
  -> 记录时写入 `recordDisusxIDataList`。
- [receive_electrical_control_o_data](/D:/codex/codex-IM/vdAgent/main.py:1069)
  -> `udp_electrical_control_o.recvfrom`
  -> 记录时写入 `recordDisusxODataList`。
- [receive_rfpro_coordinates_data](/D:/codex/codex-IM/vdAgent/main.py:1096)
  -> `udp_rfpro_coordinates.recvfrom`
  -> 更新 RFPRO 坐标相关状态。
- [receive_compensator_data](/D:/codex/codex-IM/vdAgent/main.py:1474)
  -> `udpVisualDelayCompensationReceive.recvfrom`
  -> 更新视觉补偿数据缓存。

下游使用：
- [update_plots](/D:/codex/codex-IM/vdAgent/main.py:4920) 消费 `time_data_*` 和 `signal_data`。
- [save_data_async](/D:/codex/codex-IM/vdAgent/main.py:709) 消费 `record*DataList` 并写入 CSV。
- [get_f_data](/D:/codex/codex-IM/vdAgent/main.py:5798) 消费 CarSim 输入信号计算触感力矩。

### 17.4 平台控制与数据下发链路

- [handle_control_command_input](/D:/codex/codex-IM/vdAgent/main.py:2689)
  -> [sendData2PlatformControl](/D:/codex/codex-IM/vdAgent/main.py:2029)
  用户输入 0-6 控制码后发送到平台。
- [one_click_start](/D:/codex/codex-IM/vdAgent/main.py:5250)
  -> [send_control_command](/D:/codex/codex-IM/vdAgent/main.py:5283)
  -> [_one_click_step](/D:/codex/codex-IM/vdAgent/main.py:5260)
  -> `QTimer.singleShot`
  按 Reset -> Consent -> Engage 的节奏一键启动。
- [one_click_stop](/D:/codex/codex-IM/vdAgent/main.py:5270)
  -> [send_control_command](/D:/codex/codex-IM/vdAgent/main.py:5283)
  -> `QTimer.singleShot`
  按 Disengage -> Off 的节奏一键停机。
- [apply_platform_offset](/D:/codex/codex-IM/vdAgent/main.py:3309)
  -> [sendDataPlatformOffset2](/D:/codex/codex-IM/vdAgent/main.py:2085)
  将界面偏置值发送给平台。
- [confirm_scenario_settings](/D:/codex/codex-IM/vdAgent/main.py:3434)
  -> [sendDataStartPoint2](/D:/codex/codex-IM/vdAgent/main.py:2044)
  -> `cueing_change1.modify_cueing_parameters`
  下发起点坐标并按起点切换 cueing 参数。
- [send_operation_data](/D:/codex/codex-IM/vdAgent/main.py:3336)
  -> [sendDataDriverData2](/D:/codex/codex-IM/vdAgent/main.py:2063)
  -> `udpSendDriverData.sendto`
  从 CSV 回放驾驶员输入数据。

外部依赖：
- `QUdpSocket.writeDatagram`
- `QHostAddress("10.10.20.221")`
- `QHostAddress("10.10.20.214")`
- `udpSendDriverData`

### 17.5 场景与工况链路

- [load_scenario_data](/D:/codex/codex-IM/vdAgent/main.py:3386)
  -> 读取 `scenarios.json`
  -> 返回地图/起点配置。
- [update_start_points](/D:/codex/codex-IM/vdAgent/main.py:3408)
  -> [update_position_display](/D:/codex/codex-IM/vdAgent/main.py:3425)
  根据当前地图刷新起点下拉框和坐标显示。
- [confirm_scenario_settings](/D:/codex/codex-IM/vdAgent/main.py:3434)
  -> [sendDataStartPoint2](/D:/codex/codex-IM/vdAgent/main.py:2044)
  -> `cueing_change1.modify_cueing_parameters`
  使场景选择真正生效。
- [condition_choose](/D:/codex/codex-IM/vdAgent/main.py:4109)
  -> `carsim.GoHome`
  -> `carsim.BlueLink('#BlueLink28', ...)`
  将工况选择写入 CarSim。

主要状态：
- `self.scenario_data`
- `self.current_condition`
- `self.condition_info`
- `map_combo` / `start_point_combo` / `condition_combo`

### 17.6 CarSim 仿真执行链路

- [RunDspace](/D:/codex/codex-IM/vdAgent/main.py:3452)
  -> `carsim.RunButtonClick(1)`
  -> 读取 `C:\test\LastRun.csv`
  -> 计算 `AVy` 最优方案
  -> 导出到 `E:\01_TestData\01_DCH_Data\DCH\离线仿真`
  -> [_show_corner_message](/D:/codex/codex-IM/vdAgent/main.py:436)
  执行仿真并沉淀离线对比数据。
- [OpenSimulink](/D:/codex/codex-IM/vdAgent/main.py:3585)
  -> `carsim.RunButtonClick(2)`
  打开 Simulink。
- [BuildDspace](/D:/codex/codex-IM/vdAgent/main.py:3588)
  -> `carsim.RunButtonClick(3)`
  编译 DSpace。
- [clear](/D:/codex/codex-IM/vdAgent/main.py:4387)
  -> 清理离线仿真目录。
- [viewOfflineData](/D:/codex/codex-IM/vdAgent/main.py:4427)
  -> [run_compare_csv](/D:/codex/codex-IM/vdAgent/main.py:2490)
  查看/对比离线结果。

### 17.7 车型与调参链路

- [UpdateTuningParam](/D:/codex/codex-IM/vdAgent/main.py:4115)
  -> `carsim.GoHome`
  -> `carsim.GetBlueLink`
  -> [CurrentVehicleSpringPage](/D:/codex/codex-IM/vdAgent/main.py:4445)
  -> 创建/刷新车型、弹簧、防倾杆控件与状态。
- [onCarChange](/D:/codex/codex-IM/vdAgent/main.py:5523)
  -> `carsim.BlueLink('#BlueLink2', 'Vehicle: Assembly', ...)`
  -> [UpdateTuningParam](/D:/codex/codex-IM/vdAgent/main.py:4115)
  切换车辆并刷新全部调参项。
- [onFrontSpringChange](/D:/codex/codex-IM/vdAgent/main.py:5536)
  -> [CurrentVehicleSpringPage](/D:/codex/codex-IM/vdAgent/main.py:4445)
  -> `carsim.BlueLink('#BlueLink0', 'Suspension: Spring', ...)`
  切换前弹簧。
- [onFrontRightSpringChange](/D:/codex/codex-IM/vdAgent/main.py:5548)
  -> [CurrentVehicleSpringPage](/D:/codex/codex-IM/vdAgent/main.py:4445)
  -> `carsim.BlueLink('#BlueLink3', 'Suspension: Spring', ...)`
  切换前右弹簧。
- [onRearSpringChange](/D:/codex/codex-IM/vdAgent/main.py:5561)
  -> [CurrentVehicleSpringPage](/D:/codex/codex-IM/vdAgent/main.py:4445)
  -> `carsim.BlueLink('#BlueLink0', 'Suspension: Spring', ...)`
  切换后弹簧。
- [onRearRightSpringChange](/D:/codex/codex-IM/vdAgent/main.py:5573)
  -> [CurrentVehicleSpringPage](/D:/codex/codex-IM/vdAgent/main.py:4445)
  -> `carsim.BlueLink('#BlueLink3', 'Suspension: Spring', ...)`
  切换后右弹簧。
- [onFrontAuxMChange](/D:/codex/codex-IM/vdAgent/main.py:5585)
  -> [CurrentVehicleSpringPage](/D:/codex/codex-IM/vdAgent/main.py:4445)
  -> `carsim.BlueLink('#BlueLink2', ...)`
  -> 可选 `carsim.Yellow('DAUX', ...)`
  切换前防倾杆/滚转刚度。
- [onRearAuxMChange](/D:/codex/codex-IM/vdAgent/main.py:5614)
  -> [CurrentVehicleSpringPage](/D:/codex/codex-IM/vdAgent/main.py:4445)
  -> `carsim.BlueLink('#BlueLink2', ...)`
  -> 可选 `carsim.Yellow('DAUX', ...)`
  切换后防倾杆/滚转刚度。
- [ApplyTuningParam](/D:/codex/codex-IM/vdAgent/main.py:4619)
  -> [CurrentVehicleSpringPage](/D:/codex/codex-IM/vdAgent/main.py:4445)
  -> `carsim.Yellow`
  -> `carsim.SetTable`
  -> `carsim.GoHome`
  将当前弹簧/防倾杆数值或曲线写回 CarSim。

主要状态：
- `frontSpringName` / `rearSpringName`
- `frontRightSpringName` / `rearRightSpringName`
- `frontAuxMName` / `rearAuxMName`
- `frontSpringMode` / `rearSpringMode`
- `frontAuxRollMomentMode` / `rearAuxRollMomentMode`

### 17.8 绘图与报警链路

- [create_motion_display_tab](/D:/codex/codex-IM/vdAgent/main.py:2189)
  -> [get_unit](/D:/codex/codex-IM/vdAgent/main.py:4797)
  -> [load_plot_state](/D:/codex/codex-IM/vdAgent/main.py:5313)
  -> [update_plot_layout](/D:/codex/codex-IM/vdAgent/main.py:4822)
  初始化实时图表、曲线、报警控件和显示状态。
- [toggle_plot_visibility](/D:/codex/codex-IM/vdAgent/main.py:4819)
  -> [update_plot_layout](/D:/codex/codex-IM/vdAgent/main.py:4822)
  控制图表显示/隐藏。
- [update_plots](/D:/codex/codex-IM/vdAgent/main.py:4920)
  -> [check_alarm](/D:/codex/codex-IM/vdAgent/main.py:2462)
  -> [update_haptic_plots](/D:/codex/codex-IM/vdAgent/main.py:5814)
  消费实时数据缓存刷新曲线，并在报警开启时检查阈值。
- [clear_plots](/D:/codex/codex-IM/vdAgent/main.py:5085)
  -> 清空 `time_data_*` / `signal_data`
  -> 重置曲线和坐标轴。
- [toggle_all_plots_on](/D:/codex/codex-IM/vdAgent/main.py:5357)
  -> [update_plot_layout](/D:/codex/codex-IM/vdAgent/main.py:4822)
  一键显示全部图。
- [toggle_all_plots_off](/D:/codex/codex-IM/vdAgent/main.py:5363)
  -> [update_plot_layout](/D:/codex/codex-IM/vdAgent/main.py:4822)
  一键隐藏全部图。
- [run_compare_csv](/D:/codex/codex-IM/vdAgent/main.py:2490)
  -> `CompareCsv.CSVPlotter`
  打开 CSV 对比分析窗口。
- [load_record](/D:/codex/codex-IM/vdAgent/main.py:5911)
  -> [load_csv_data](/D:/codex/codex-IM/vdAgent/main.py:5967)
  -> [plot_loaded_data](/D:/codex/codex-IM/vdAgent/main.py:6056)
  读取历史记录并绘制离线曲线。

### 17.9 信号发送链路

- [create_signal_input_tab](/D:/codex/codex-IM/vdAgent/main.py:2538)
  -> [handle_signal_input](/D:/codex/codex-IM/vdAgent/main.py:2710)
  -> [update_signal_params](/D:/codex/codex-IM/vdAgent/main.py:2733)
  初始化 PVA/信号配置界面。
- [handle_signal_input](/D:/codex/codex-IM/vdAgent/main.py:2710)
  -> [update_signal_params](/D:/codex/codex-IM/vdAgent/main.py:2733)
  -> [update_time_value_combos](/D:/codex/codex-IM/vdAgent/main.py:2842)
  -> [clear_signal_param_widgets](/D:/codex/codex-IM/vdAgent/main.py:2880)
  根据算法、信号类型、信号数量重建输入区。
- [toggle_all_signal](/D:/codex/codex-IM/vdAgent/main.py:5369)
  -> [toggle_signal](/D:/codex/codex-IM/vdAgent/main.py:5383)
  批量启动或停止所有信号。
- [toggle_signal](/D:/codex/codex-IM/vdAgent/main.py:5383)
  -> [start_signal_thread](/D:/codex/codex-IM/vdAgent/main.py:5406)
  或 -> [stop_signal_thread](/D:/codex/codex-IM/vdAgent/main.py:5394)
  控制单个信号。
- [start_signal_thread](/D:/codex/codex-IM/vdAgent/main.py:5406)
  -> [get_index_from_signal_type](/D:/codex/codex-IM/vdAgent/main.py:5500)
  -> [SignalSenderThread.__init__](/D:/codex/codex-IM/vdAgent/main.py:6151)
  -> [SignalSenderThread.run](/D:/codex/codex-IM/vdAgent/main.py:6170)
  创建发送线程并开始周期发送。
- [stop_signal_thread](/D:/codex/codex-IM/vdAgent/main.py:5394)
  -> [sendData2Moog](/D:/codex/codex-IM/vdAgent/main.py:2102)
  -> [SignalSenderThread.stop](/D:/codex/codex-IM/vdAgent/main.py:6194)
  停止发送并清零对应平台通道。

主要状态：
- `signal_param_widgets`
- `signal_threads`
- `workspace_variables`
- `signal_data`

### 17.10 触感反馈链路

- [create_haptic_adjustment_tab](/D:/codex/codex-IM/vdAgent/main.py:5664)
  -> [load_haptic_gain](/D:/codex/codex-IM/vdAgent/main.py:5883)
  初始化触感参数和触感图表。
- [save_haptic_settings](/D:/codex/codex-IM/vdAgent/main.py:5785)
  -> [save_haptic_gain](/D:/codex/codex-IM/vdAgent/main.py:5871)
  将界面增益写入内存和 `haptic_config.json`。
- [get_f_data](/D:/codex/codex-IM/vdAgent/main.py:5798)
  -> `factor`
  -> `fcn_friction`
  -> `fcn_damping`
  -> `fcn_feedback`
  -> `fcn_saturation`
  -> 可选 [sendData2CarSim](/D:/codex/codex-IM/vdAgent/main.py:5897)
  根据实时信号计算方向盘力矩。
- [update_haptic_plots](/D:/codex/codex-IM/vdAgent/main.py:5814)
  -> 消费 `time_data_carsim` / `signal_data` / `f_data`
  更新方向盘角度、力矩、力矩-转角图。

外部依赖：
- `feedback.factor`
- `feedback.fcn_friction`
- `feedback.fcn_damping`
- `feedback.fcn_feedback`
- `feedback.fcn_saturation`
- `haptic_config.json`

### 17.11 视觉补偿链路

- [create_visual_compensation_tab](/D:/codex/codex-IM/vdAgent/main.py:3591)
  -> 读取 `visualCompensationConfig.json`
  -> 读取 `visualDelayCompensationConfig.json`
  初始化视觉补偿和视觉延迟补偿参数。
- [ApplyVisualCompensation](/D:/codex/codex-IM/vdAgent/main.py:3874)
  -> 打包 12 个补偿参数
  -> 保存 `visualCompensationConfig.json`
  当前 UDP 下发代码处于注释状态。
- [ApplyVisualDelayCompensation](/D:/codex/codex-IM/vdAgent/main.py:3899)
  -> 打包 5 个延迟补偿参数
  -> 保存 `visualDelayCompensationConfig.json`
  当前 UDP 下发代码处于注释状态。

### 17.12 关闭清理链路

- [closeEvent](/D:/codex/codex-IM/vdAgent/main.py:5330)
  -> [save_ui_state](/D:/codex/codex-IM/vdAgent/main.py:1946)
  -> [save_sampling_rates](/D:/codex/codex-IM/vdAgent/main.py:1896)
  -> [save_haptic_gain](/D:/codex/codex-IM/vdAgent/main.py:5871)
  关闭窗口时保存主要用户配置。

### 17.13 关键外部依赖速查

- `carsim`
  车型/弹簧/防倾杆读取与写入、仿真运行、Simulink 打开、DSpace 编译、参数导出。
- `udp` / `udp2` / `udp3`
  分别承载 IMU、CarSim、MOOG 等实时数据接收。
- `udp_electrical_control_i` / `udp_electrical_control_o`
  电控输入/输出记录通道。
- `udp_rfpro_coordinates`
  RFPRO 坐标接收。
- `udpVisualDelayCompensationReceive`
  视觉补偿回传接收。
- `udpSendDriverData`
  驾驶员操作数据回放发送。
- `self.udp_socket`
  平台控制、起点、偏置、相机、MOOG、CarSim 等多类数据下发。
- `mysql_utils.MySQLDatabase`
  评价记录入库。
- `CompareCsv.CSVPlotter`
  离线 CSV 对比窗口。
- `cueing_change` / `cueing_change1`
  体感 cueing 参数配置和切换。
- `SignalSenderThread`
  PVA/自定义信号的异步发送线程。
