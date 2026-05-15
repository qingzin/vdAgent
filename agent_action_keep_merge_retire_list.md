# 当前 38 个 Action 治理清单

基于当前项目的底盘虚拟驾驶业务定位，对 `agent/README.md` 中登记的 38 个 action 做一次明确梳理。

治理原则：

- `保留`：已经是业务级入口，适合继续作为 Agent 直接可调用工具。
- `合并`：语义过细、同类动作拆得太散，应该收敛成更高阶业务工具。
- `下线`：过于底层、过于贴 UI、危险但低价值，或更适合作为内部实现而不是对 Agent 暴露。

## 1. 结论汇总

- 保留：9 个
- 合并：20 个
- 下线：9 个

建议收敛后的高阶工具方向：

- `set_spring`
- `set_antiroll_bar`
- `prepare_test_scene`
- `prepare_recording_session`
- `tune_haptic_feedback`
- `prepare_platform`
- `set_visual_profile`
- `prepare_evaluation_metadata`
- `manage_simulation_workspace`
- `analyze_offline_result`

## 2. 明确清单

| 当前 action | 当前模块 | 处理建议 | 合并后/保留后目标 | 原因 |
| --- | --- | --- | --- | --- |
| `select_vehicle` | tuning | 保留 | `select_vehicle` | 车型切换是明确业务动作，语义完整，保留价值高。 |
| `select_front_spring` | tuning | 合并 | `set_spring` | 前/后/左右弹簧不该拆成多个工具，应统一为一个弹簧配置工具。 |
| `select_rear_spring` | tuning | 合并 | `set_spring` | 同上，属于同一类悬架参数修改。 |
| `select_front_right_spring` | tuning | 合并 | `set_spring` | 同上，左右独立只是参数维度，不应单独占一个 tool。 |
| `select_rear_right_spring` | tuning | 合并 | `set_spring` | 同上。 |
| `select_front_antiroll` | tuning | 合并 | `set_antiroll_bar` | 前/后防倾杆应统一为一个稳定杆配置工具。 |
| `select_rear_antiroll` | tuning | 合并 | `set_antiroll_bar` | 同上。 |
| `refresh_tuning_params` | tuning | 下线 | 内部刷新逻辑 | 这是 UI/列表刷新，不是用户真正想完成的业务任务。 |
| `get_current_setup` | tuning | 保留 | `get_current_setup` | 查询当前车型与悬架配置是高频且高价值的业务入口。 |
| `run_carsim` | simulation | 保留 | `run_carsim` | 运行仿真是明确业务动作，直接保留。 |
| `open_simulink` | simulation | 合并 | `manage_simulation_workspace` | 打开 Simulink 更像仿真工作区准备动作，不宜单独暴露。 |
| `build_dspace` | simulation | 合并 | `manage_simulation_workspace` | 编译 DSpace 属于仿真环境准备的一部分。 |
| `clear_offline_data` | simulation | 下线 | 内部维护逻辑 | 危险且价值密度低，更适合作为内部清理能力。 |
| `view_offline_data` | simulation | 合并 | `analyze_offline_result` | “查看页面”不如直接收敛成“离线结果分析”业务工具。 |
| `start_recording` | recording | 保留 | `start_recording` | 开始记录是明确且高频的试验动作。 |
| `stop_recording` | recording | 保留 | `stop_recording` | 结束记录同样是高频业务动作，且常需要用户显式发起。 |
| `set_recording_options` | recording | 合并 | `prepare_recording_session` | 记录选项属于“试验准备”的一部分，不应独立成零散开关工具。 |
| `get_recording_status` | recording | 保留 | `get_recording_status` | 查询记录状态对试验前检查和异常排查都很有价值。 |
| `set_haptic_gains` | haptic | 合并 | `tune_haptic_feedback` | 触感参数设置应作为“手感调校”整体工具，而不是单纯参数写入。 |
| `get_haptic_gains` | haptic | 合并 | `tune_haptic_feedback` | 查询和设置应统一到同一个触感调校工具中。 |
| `platform_control` | platform | 下线 | 内部平台协议能力 | 0-6 原始指令太底层，Agent 不应直接暴露协议级操作。 |
| `one_click_platform_start` | platform | 保留 | `one_click_platform_start` | 一键启平台是明确的业务动作，且比底层 0-6 指令更安全。 |
| `one_click_platform_stop` | platform | 保留 | `one_click_platform_stop` | 同上，属于业务级安全封装。 |
| `set_platform_offset` | platform | 合并 | `prepare_platform` | 偏置设置应纳入平台准备工具，不必单独暴露。 |
| `select_map_and_start_point` | scene | 合并 | `prepare_test_scene` | 地图/起点选择只是场景准备的一部分。 |
| `confirm_scene` | scene | 合并 | `prepare_test_scene` | “选择 + 确认 + 下发”应一次完成，不应拆成两步 tool。 |
| `set_condition` | scene | 合并 | `prepare_test_scene` | 工况设置应与地图、起点、cueing 一起治理。 |
| `get_current_scene` | scene | 保留 | `get_current_scene` | 查询当前地图/起点/工况是有价值的场景状态查询。 |
| `set_visual_compensation` | visual | 合并 | `set_visual_profile` | 视觉跟随补偿应作为视觉配置的一部分统一治理。 |
| `set_visual_delay_compensation` | visual | 合并 | `set_visual_profile` | 延迟补偿与视觉补偿高度相关，适合并入同一视觉配置工具。 |
| `control_plotting` | plot | 下线 | 内部可视化控制 | run/pause/clear 是 UI 操作，不是底盘业务任务。 |
| `set_all_plots` | plot | 下线 | 内部可视化控制 | 全开/全关图表只是查看体验，不应占用 Agent 工具位。 |
| `set_plot_visibility` | plot | 下线 | 内部可视化控制 | 单通道图表显隐过于贴 UI。 |
| `set_plot_time_range` | plot | 下线 | 内部可视化控制 | 时间轴调整属于图表查看行为，不是核心业务能力。 |
| `set_alarm` | plot | 下线 | 后续并入监测能力 | 当前只是 UI 阈值开关，后续应升级为试验监测能力，而不是保留现态工具。 |
| `set_preset` | misc | 合并 | `prepare_evaluation_metadata` | 预定义字段本质上是评价记录元数据准备。 |
| `get_preset` | misc | 合并 | `prepare_evaluation_metadata` | 查询和设置预定义字段应统一处理。 |
| `toggle_all_signals` | misc | 下线 | 内部信号控制 | PVA 信号总开关太偏内部调试，不适合作为通用 Agent tool。 |

## 3. 合并后的建议工具清单

### 3.1 保留的 9 个直接工具

- `select_vehicle`
- `get_current_setup`
- `run_carsim`
- `start_recording`
- `stop_recording`
- `get_recording_status`
- `one_click_platform_start`
- `one_click_platform_stop`
- `get_current_scene`

### 3.2 建议新增的 10 个高阶合并工具

- `set_spring`
  统一处理前/后/左/右弹簧的名称选择、数值设置和幅度调整。
- `set_antiroll_bar`
  统一处理前/后防倾杆或滚转刚度相关配置。
- `prepare_test_scene`
  一次完成工况、地图、起点选择以及场景确认下发。
- `prepare_recording_session`
  统一处理记录前的 DisusX、视频、par、自动记录等配置。
- `tune_haptic_feedback`
  统一处理触感参数查询与修改。
- `prepare_platform`
  统一处理平台偏置、预备状态和关联配置。
- `set_visual_profile`
  统一处理视觉跟随补偿和视觉延迟补偿。
- `prepare_evaluation_metadata`
  统一处理评价记录的默认字段设置与查询。
- `manage_simulation_workspace`
  统一处理 Simulink 打开、DSpace 编译等仿真环境准备动作。
- `analyze_offline_result`
  从“打开页面”升级为“分析离线结果/对比方案”的业务工具。

## 4. 下线建议的判断依据

以下几类 action 建议优先下线出 Agent 暴露面：

- 纯 UI 控件型：如图表显隐、时间轴调整、刷新列表。
- 原始协议型：如平台 `0-6` 指令。
- 高风险低价值型：如直接清空离线仿真缓存。
- 内部调试型：如信号总开关。

## 5. 建议的下一步落地顺序

1. 给这 38 个 action 增加治理元数据：`status=keep/merge/retire`。
2. 先把 `set_spring`、`set_antiroll_bar`、`prepare_test_scene`、`prepare_recording_session` 四个高频合并工具做出来。
3. 在 registry 层隐藏 `下线` 工具，不再对 LLM 暴露。
4. 在 README 和 Agent 提示词里，把“38 个 action”更新为“少量高阶业务工具”。

