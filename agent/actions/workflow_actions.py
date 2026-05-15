"""Agent workflow template and sim-test report actions."""


def register(registry, ctx):
    workflow = ctx.service("workflow_template")
    report = ctx.service("sim_test_report")

    def list_workflow_templates() -> str:
        templates = workflow.list_templates()
        if not templates:
            return "未找到 workflow 模板。请在 agent_data/workflow_templates 下添加 JSON 模板。"
        lines = ["可用一键实验模板:"]
        for item in templates:
            status = "有效" if item.get("valid") else "无效"
            lines.append(
                f"- {item.get('id')}: {item.get('name')} [{status}] "
                f"配置数={item.get('configurations', '-')}, 工况={item.get('procedures', [])} "
                f"{item.get('description', '')}"
            )
        return "\n".join(lines)

    registry.register(
        name="list_workflow_templates",
        description="列出可用的一键实验流程模板。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=list_workflow_templates,
        category="workflow",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )

    def preview_workflow_template(template_id: str) -> str:
        return workflow.preview(template_id)

    registry.register(
        name="preview_workflow_template",
        description="预览一键实验流程模板的执行内容、风险和输出位置。",
        params_schema={
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "模板 ID"}
            },
            "required": ["template_id"],
        },
        callback=preview_workflow_template,
        category="workflow",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )

    def run_workflow_template(template_id: str) -> str:
        return workflow.execute(template_id)

    registry.register(
        name="run_workflow_template",
        description="按 JSON 模板一键完成车辆配置、批量 CarSim 仿真、后处理和报告生成。",
        params_schema={
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "模板 ID"}
            },
            "required": ["template_id"],
        },
        callback=run_workflow_template,
        category="workflow",
        risk_level="high",
        exposed=True,
        side_effects=True,
        summary_callback=workflow.format_confirmation_summary,
    )

    def generate_sim_test_report(result_folder: str) -> str:
        return report.generate_report(result_folder)

    registry.register(
        name="generate_sim_test_report",
        description="针对已有 sim_test_report 结果文件夹计算指标并生成 Word 报告。",
        params_schema={
            "type": "object",
            "properties": {
                "result_folder": {"type": "string", "description": "包含车型子文件夹和 CSV 的结果目录"}
            },
            "required": ["result_folder"],
        },
        callback=generate_sim_test_report,
        category="analysis",
        risk_level="medium",
        exposed=True,
        side_effects=True,
    )
