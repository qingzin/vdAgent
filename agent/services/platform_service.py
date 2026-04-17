"""
运动平台控制 Service

职责: 封装"发送平台控制指令"这一业务能力。
不涉及 UI, 不涉及 carsim。只发 UDP。
"""

import struct
from PyQt5.QtNetwork import QHostAddress


class PlatformService:
    COMMAND_NAMES = {
        0: "Off(关闭)", 1: "Disengage(脱开)", 2: "Consent(同意)",
        3: "ReadyForTraining(准备训练)", 4: "Engage(接合)",
        5: "Hold(保持)", 6: "Reset(重置)",
    }

    def __init__(self, udp_socket, target_host="10.10.20.221", target_port=3366):
        self.udp_socket = udp_socket
        self.target_host = target_host
        self.target_port = target_port

    def send_command(self, command: int) -> dict:
        """
        发送平台控制指令。

        Returns:
            {"command": int, "name": str}

        Raises:
            ValueError: 指令越界
        """
        if command not in self.COMMAND_NAMES:
            raise ValueError(f"无效指令 {command}, 有效范围 0-6")

        data = struct.pack('i', command)
        self.udp_socket.writeDatagram(
            data, QHostAddress(self.target_host), self.target_port
        )
        return {"command": command, "name": self.COMMAND_NAMES[command]}
