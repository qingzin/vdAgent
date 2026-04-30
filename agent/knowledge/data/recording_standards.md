---
category: recording
tags: [数据记录, CSV, IMU, 传感器, 试验规范]
title: 驾驶模拟器数据记录规范
created: 2026-04-29
updated: 2026-04-29
source: human
---

# 驾驶模拟器数据记录规范

## 数据通道说明

### Carsim 数据（仿真端）
记录 CarSim 车辆模型的仿真计算结果，包括车身姿态、运动状态、驾驶员输入等。
- 关键通道：Roll/Pitch/Yaw、Vx/Vy/Vz、Ax/Ay/Az、方向盘转角/转速、油门开度
- 文件名：CarsimData.csv
- 用途：提供"输入信号"参考，即仿真器期望车辆达到的运动状态

### MOOG 数据（平台端）
记录 MOOG 运动平台的执行反馈，即平台实际输出的运动状态。
- 关键通道：平台 X/Y/Z 位置、Roll/Pitch/Yaw 姿态角、Vx/Vy/Vz 速度、Ax/Ay/Az 加速度
- 文件名：MoogData.csv
- 用途：评估平台跟踪精度，对比 Carsim 期望值与平台实际执行值

### IMU 数据（驾驶舱端）
记录安装在驾驶舱或驾驶员身上的惯性测量单元数据。
- 关键通道：Roll/Pitch/Yaw 姿态角、角速度、线加速度
- 文件名：IMUData.csv
- 用途：评估驾驶员实际感受到的运动，是主观评价的客观参考

## 记录操作流程

1. **准备场景**：确认工况、地图、起点无误，调用 `confirm_scenario_settings` 生效。
2. **配置记录选项**：通过 `prepare_recording_session` 设置 disusx/video/par/auto_record 开关。
3. **开始记录**：确认配置后执行 `start_recording`，确保三类传感器均启动。
4. **执行驾驶**：驾驶员完成指定工况的驾驶任务。
5. **结束记录**：执行 `stop_recording`，数据自动保存到指定路径。
6. **补充元数据**：在弹出的评价信息对话框中填写车型、调校件、评价人、工况等信息。

## 注意事项
- **记录中禁止修改车辆或场景**：修改会污染数据，导致前后不一致。
- 记录前检查数据保存路径是否有足够磁盘空间。
- 大规模对比试验建议统一使用 `auto_record` 模式以提高效率。
- CSV 文件路径默认格式：`E:\01_TestData\01_DCH_Data\DCH\<日期>\<试验名>\`
