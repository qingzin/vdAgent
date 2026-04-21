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

