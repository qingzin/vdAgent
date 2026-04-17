import glob
import sys
import time
import struct
from collections import deque
import numpy as np
import pandas as pd
from PyQt5.QtGui import QImage, QPixmap, QIntValidator
from qtpy import QtGui
# from absl.logging import exception
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QFormLayout, QDockWidget,
    QHBoxLayout, QTabWidget, QLabel, QComboBox, QPushButton, QCheckBox,
    QLineEdit, QGroupBox, QRadioButton, QButtonGroup, QGridLayout, QFrame,
    QTableWidget, QTableWidgetItem, QInputDialog, QMessageBox,
    QDialog, QTextEdit, QMenu, QWidgetAction, QFileDialog, QSpinBox, QProgressDialog, QDoubleSpinBox, QListWidget,
    QListWidgetItem, QAbstractSpinBox, QDialogButtonBox, QDateEdit)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QMutex, QDate, QCoreApplication
from PyQt5.QtNetwork import QUdpSocket, QHostAddress
from PyQt5.QtGui import QDoubleValidator ,QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pyqtgraph as pg
import json
from pathlib import Path
import win32com.client
import os
import re
import random

import cueing_change
import cueing_change1
from CustomWidget import HoverButton, ButtonDropdown, CustomGroupPushButton, CustomCarPushButton
import socket
import csv
import shutil
import datetime
import threading
import copy
import subprocess
from getpass import getpass
# from function import wavelet_denoising
from scipy.constants import value
#from jsmnq_plot import jsmnq_plot
import CompareCsv
import mysql_utils, database_tab
from window_obj_center_process import CenterWidget
from window_obj_dil import BumpWidget
from pro_compare import pro_compare
from feedback import fcn_friction, fcn_damping, factor, fcn_feedback, fcn_saturation
from ProcessStatusMonitor import RemoteWorker, ProcessMonitor
# from signal_management_tab import create_signal_management_tab
# from ProcessStatus import create_Status_Control_tab
import math
#from mysql_utils import MySQLDatabase
#import CarsimDelegate as carsim
# import alert
carsim = win32com.client.Dispatch("CarSim.Application")
carsim.GoHome()
# carsim.Minimize()
# carsim.UnlockAll()
databasePath = carsim.GetDatabaseFolder()
vehicleInfo = carsim.GetDatasetList('Vehicle: Assembly')
vehicleNames = {}
vehiclePath = databasePath + 'Vehicles\\Assembly'
vehicleImagePath = {}
vehicleInfoDic = {}
for info in vehicleInfo:
    pattern = r"(.*):<(.*?)>(.*)"
    match = re.search(pattern, info)
    id = match.group(1)
    group = match.group(2)
    name = match.group(3)
    vehiclePic = vehiclePath + '\\' + id + '.PNG'
    vehicleInfoDic[name] = info
    if os.path.exists(vehiclePic):
        vehicleImagePath[name] = vehiclePic
    else:
        vehicleImagePath[name] = ''
    if group not in vehicleNames:
        vehicleNames[group] = []
        vehicleNames[group].append(name)
    else:
        vehicleNames[group].append(name)

springInfo = carsim.GetDatasetList('Suspension: Spring')
springNames = {}
springPath = databasePath + 'Suspensions\\Springs'
springInfoDic = {}
for info in springInfo:
    pattern = r"(.*):<(.*?)>(.*)"
    match = re.search(pattern, info)
    id = match.group(1)
    group = match.group(2)
    name = match.group(3)
    springInfoDic[name] = info
    if group not in springNames:
        springNames[group] = []
        springNames[group].append(name)
    else:
        springNames[group].append(name)

AuxMInfo = carsim.GetDatasetList('Suspension: Auxiliary Roll Moment')
AuxMNames = {}
AuxMPath = databasePath + 'Suspensions\\Aux_Roll'
AuxMInfoDic = {}
for info in AuxMInfo:
    pattern = r"(.*):<(.*?)>(.*)"
    match = re.search(pattern, info)
    id = match.group(1)
    group = match.group(2)
    name = match.group(3)
    AuxMInfoDic[name] = info
    if group not in AuxMNames:
        AuxMNames[group] = []
        AuxMNames[group].append(name)
    else:
        AuxMNames[group].append(name)

MxTotInfo = carsim.GetDatasetList('Suspension: Measured Total Roll Stiffness')
MxTotNames = {}
MxTotPath = databasePath + 'Suspensions\\Aux_Roll'
MxTotInfoDic = {}
for info in MxTotInfo:
    pattern = r"(.*):<(.*?)>(.*)"
    match = re.search(pattern, info)
    id = match.group(1)
    group = match.group(2)
    name = match.group(3)
    MxTotInfoDic[name] = info
    if group not in MxTotNames:
        MxTotNames[group] = []
        MxTotNames[group].append(name)
    else:
        MxTotNames[group].append(name)
with open("udp_config.json", "r") as f:
    udp_config = json.load(f)
    ip_address = udp_config.get("ip_address", 1)
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# udp.bind(('10.10.20.231', 9527))
udp.bind((ip_address, 9528))

udp2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# udp2.bind(('10.10.20.231', 9888))
udp2.bind((ip_address, 9888))

udp3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp3.bind((ip_address, 8848))
# udp3.bind((ip_address, 1715))
# udp3.bind((ip_address, 1703))


udp4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp4.bind((ip_address, 9998))

udp_electrical_control_i = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_electrical_control_i.bind((ip_address, 7354))
udp_electrical_control_i.settimeout(60000)

udp_electrical_control_o = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_electrical_control_o.bind((ip_address, 48967))

udp_rfpro_coordinates = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_rfpro_coordinates.bind((ip_address, 6828))

udpVisualDelayCompensation = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpVisualDelayCompensation.bind((ip_address, 9999))

udpVisualDelayCompensationReceive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpVisualDelayCompensationReceive.bind((ip_address, 10001))

udpSendDriverData = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpSendDriverData.bind((ip_address, 10002))

def SvnTest01():
    pass

def SvnTest02():
    pass

class SimulatorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lastCarsimTime = 0
        self.lastIMUTime = 0
        self.lastMoogTime = 0
        self.lastUpdateTime = 0
        self.lastElectrolTime = 0
        self.isPloting = False
        self.signal_steer_angle = 0
        # 接收simulink电控数据
        self.record_disusx = False
        self.record_disusc = False
        self.auto_record = 0
        self.current_condition=''
        self.setWindowTitle('驾驶模拟器控制面板')
        self.resize(1400, 800)  # 设置初始大小
        self.setMinimumSize(1200, 800)  # 设置最小大小
        # self.setMaximumSize(2500, 1500)  # 设置最大大小
        # 启用全屏按钮
        self.setWindowFlags(
            self.windowFlags() | Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowFullscreenButtonHint)
        # 添加一个变量来保存按钮的状态
        self.signal_button_state = False  # 默认状态为关闭
        self.is_running = False  # 添加一个标志来控制线程的运行状态

        self.is_video_recording = False
        # 初始化数据存储
        self.data_buffer_size = 12000  # 12秒的1000Hz数据
        self.time_data_imu = deque()
        self.time_data_imu_all = deque()
        self.time_data_carsim = deque()
        self.time_data_carsim_all = deque()
        self.time_data_moog = deque()
        self.time_data_moog_all = deque()

        self.f_data = deque()  # 力反馈数据
        self.last_1s = 0

        self.is_par_save = False
        self.is_rename_folder_name = False

        # self.start_record_input_index = 0
        # self.finish_record_input_index = 0
        # self.start_record_moog_index = 0
        # self.finish_record_moog_index = 0
        # self.start_record_imu_index = 0
        # self.finish_record_imu_index = 0

        self.x_start_record_coordinate = 10000.0
        self.y_start_record_coordinate = 10000.0
        self.velocity_autorecord = 10000.0
        self.x_finish_record_coordinate = 20000.0
        self.y_finish_record_coordinate = 20000.0
        self._in_start_zone = False
        self._in_end_zone = False
        self.signal_rfpro_x_coordinate = 0.0
        self.signal_rfpro_y_coordinate = 0.0
        self.vx = 0.0

        self.recordIMUDataList = {}
        self.recordCarsimDataList = {}
        self.recordMoogDataList = {}
        self.recordVisualCompensatorDataList = {}
        self.recordDisusxIDataList = {}
        self.recordDisusxODataList = {}

        self.signal_data_all = {}
        self.config_file = Path('config.json')

        self.gain_fri = 1
        self.gain_dam = 1
        self.gain_feedback = 1
        self.gain_sa = 1
        self.gain_all = 1
        self.sw_rate = 10
        # 初始化状态存储
        self.ui_state = self.load_ui_state()

        self.signal_threads = {}  # 存储每个信号的线程
        # 为每个信号创建数据缓冲区
        self.signal_data = {}
        signal_names = ['pos_x', 'pos_y', 'pos_z',
                        'vel_x', 'vel_y', 'vel_z',
                        'acc_x', 'acc_y', 'acc_z',
                        'ang_x', 'ang_y', 'ang_z',
                        'roll', 'pitch', 'yaw',
                        'ang_acc_x', 'ang_acc_y', 'ang_acc_z',
                        'steering_angle', 'throttle', 'pbk_con', 'steering_speed',
                        'CmpRD_L1','CmpRD_L2','CmpRD_R1','CmpRD_R2'
                        ]

        for name in signal_names:
            self.signal_data[name] = {
                # 'input': deque(maxlen=self.data_buffer_size),
                # 'moog': deque(maxlen=self.data_buffer_size),
                # 'imu': deque(maxlen=self.data_buffer_size)
                'input': deque(),
                'moog': deque(),
                'imu': deque()
            }
            self.signal_data_all[name] = {
                # 'input': deque(maxlen=self.data_buffer_size),
                # 'moog': deque(maxlen=self.data_buffer_size),
                # 'imu': deque(maxlen=self.data_buffer_size)
                'input': deque(),
                'moog': deque(),
                'imu': deque()
            }
        # 新增变量用于存储从 CSV 文件中读取的记录数据
        self.record_time_data_imu = deque()
        self.record_time_data_carsim = deque()
        self.record_time_data_moog = deque()
        self.record_signal_data = {
            name: {'input': deque(), 'moog': deque(), 'imu': deque()}
            for name in ['pos_x', 'pos_y', 'pos_z', 'vel_x', 'vel_y', 'vel_z',
                         'acc_x', 'acc_y', 'acc_z', 'ang_x', 'ang_y', 'ang_z',
                         'roll', 'pitch', 'yaw', 'ang_acc_x', 'ang_acc_y', 'ang_acc_z',
                         'steering_angle', 'throttle', 'pbk_con', 'steering_speed',
                         'CmpRD_L1','CmpRD_L2','CmpRD_R1','CmpRD_R2']
        }
        # 初始化工作区变量存储
        self.workspace_variables = {}  # 确保这里被初始化

        # 绘图控制
        self.plot_running = True
        self.start_time = time.perf_counter()
        self.start_time1 = time.time()
        self.record_start_time = time.perf_counter()
        self.record_start_time_last = time.perf_counter()
        self.record_finish_time_last = time.perf_counter()
        self.value_labels = {}  # 用于存储文本标签
        # 初始化UDP Socket
        self.udp_socket = QUdpSocket(self)
        # self.udp_socket.bind(QHostAddress.LocalHost, 3394)
        # self.udp_socket.readyRead.connect(self.process_pending_datagrams)
        # 初始化IMU和Carsim数据接收线程
        self.imu_thread = None
        self.carsim_thread = None
        self.moog_thread = None
        self.is_recording_imu = False
        self.is_recording_carsim = False
        self.is_recording_moog = False
        self.is_recording_disusx = False
        self.is_recording_visual_compensator = False
        self.csv_file_imu = None
        self.csv_writer_imu = None
        self.csv_file_carsim = None
        self.csv_file_visual_compensator = None
        self.csv_writer_carsim = None
        self.csv_file_moog = None
        self.csv_writer_moog = None
        self.csv_writer_visual_compensator = None
        self.csv_file_disusx_i = None
        self.csv_writer_disusx_i = None
        self.csv_file_disusx_o = None
        self.csv_writer_disusx_o = None
        self.plot_sample_imu = 1
        self.plot_sample_carsim = 1
        self.plot_sample_moog = 1
        self.plot_buffer_imu = 100
        self.plot_buffer_carsim = 100
        self.plot_buffer_moog = 100
        self.plot_delete_step = 50

        #线控转向数据
        self.TR_TRFinal = 0.0
        self.AngReq_Angle_write = 0.0

        self.default_save_path = r"E:\01_TestData\01_DCH_Data\DCH"
        self.current_save_path = self.default_save_path
        # self.alert = alert.VehicleMonitor()

        self.carsim_db_path = ""
        # 初始化工作区面板
        self.init_workspace_panel()  # 确保在初始化UI之前调用

        # 报警系统变量
        self.alarm_enabled = False
        self.current_scenario = "单移线"  # 默认工况
        self.custom_thresholds = {}  # 存储自定义阈值

        # 定义工况阈值
        self.scenario_thresholds = {
            "单移线": {'vel_x': (80, 100), 'steering_angle': (-20, 20), 'steering_speed': (-45, 45)},
            "转弯": {'vel_x': (80, 100), 'steering_angle': (-20, 20), 'steering_speed': (-30, 30)},
            "中心区": {'vel_x': (80, 100), 'steering_angle': (-20, 20), 'steering_speed': (40, 60)},
            "一阶起伏": {'vel_x': (80, 100), 'steering_angle': (-3, 3), 'steering_speed': (-3, 3)},
            "自定义": {}  # 由用户设置
        }

        # 报警标记
        self.alarm_indicators = {}

        #字段初始化
        self.default_evaluator = ""
        self.default_evaluation_count = ""
        self.default_condition_version = ""
        self.default_feeling_version = ""

        # 初始化UI
        self.init_ui()

        # 加载图表状态
        self.load_plot_state()
        self.load_sampling_rates()
        self.load_haptic_gain()
        # load_carsimdatabase(self)
        # 设置更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_plots)
        self.update_timer.start(50)

        # 新增变量用于平滑纵坐标范围
        self.y_range_cache = {}  # 存储每个图表的纵坐标范围
        self.y_range_smoothing_factor = 0.01  # 滑动平均的平滑系数

        # 新增变量用于记录信号变化时间和超时机制
        self.last_signal_change_time = {}  # 记录每个信号通道的上次变化时间
        self.y_range_timeout = 10.0  # 纵坐标范围缩小超时时间（秒）

        self.signal_thread = None  # 用于存储信号发送线程
        self.receive_electrical_thread_running = False  # 是否接收电控的收发信号
        self.sendData = [0] * 32
        self.sendData_platform = [0]
        self.sendData_camera = [0] * 2
        self.sendData_CarSim = [0.0] * 1
        self.sendData_startPoint = [0.0] * 5
        self.sendData_platformOffset = [0.0] * 3
        self.sendData_DriverData = [0.0] * 8
        self.count = 0
        self.imu_thread = threading.Thread(target=self.receive_imu_data)
        self.imu_thread.start()
        self.carsim_thread = threading.Thread(target=self.receive_carsim_data)
        self.carsim_thread.start()
        self.moog_thread = threading.Thread(target=self.receive_moog_data)
        self.moog_thread.start()
        self.electrical_control_i_thread = threading.Thread(target=self.receive_electrical_control_i_data)
        self.electrical_control_o_thread = threading.Thread(target=self.receive_electrical_control_o_data)
        # rpfro坐标
        self.rfpro_coordinates_thread = threading.Thread(target=self.receive_rfpro_coordinates_data)
        self.rfpro_coordinates_thread.start()
        # if self.record_disusx:
        self.electrical_control_i_thread.start()
        self.electrical_control_o_thread.start()
        self.visual_compensator_thread = threading.Thread(target=self.receive_compensator_data)
        self.visual_compensator_thread.start()
        # self.receive_data_thread = threading.Thread(target=self.receive_all_data)
        # self.receive_data_thread.start()
        # self.record_indicator = QLabel()
        # self.record_indicator.setFixedSize(20, 20)
        self.update_indicator(False)  # 初始状态为熄灭

    def _show_corner_message(self, message: str, seconds: int = 5):
        try:
            # 找到主窗口
            window = self.window()
            if window is None:
                return

            # 创建临时消息标签
            message_label = QLabel(message, window)
            message_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(0, 128, 0, 180);
                    color: white;
                    padding: 8px 24px;
                    border-radius: 4px;
                    font-size: 15px;
                    border: 1px solid rgba(0, 100, 0, 200);
                    max-width: 600px;
                    min-width: 250px;
                    qproperty-alignment: AlignCenter;
                }
            """)
            message_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            message_label.setWordWrap(False)  # 不允许换行，保持单行显示
            message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)  # 允许选择文本
            message_label.adjustSize()  # 自动调整大小以适应内容

            # 设置位置在中间偏上
            window_width = window.width()
            window_height = window.height()
            label_width = message_label.sizeHint().width()
            label_height = message_label.sizeHint().height()

            # 确保标签不会超出窗口边界
            max_width = min(600, window_width - 40)  # 最大宽度限制
            message_label.setMaximumWidth(max_width)

            # 重新计算宽度（因为设置了最大宽度）
            label_width = message_label.sizeHint().width()
            x_pos = (window_width - label_width) // 2  # 水平居中
            y_pos = window_height // 4  # 窗口高度的1/4位置，偏上

            message_label.move(x_pos, y_pos)
            message_label.show()
            message_label.raise_()

            # 创建定时器自动隐藏
            timer = QTimer(message_label)
            timer.setInterval(seconds * 1000)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: message_label.hide())
            timer.start()

        except Exception:
            # 兜底：静默
            pass

    def update_indicator(self, recording):
        color = "green" if recording else (0, 255, 0)
        self.record_indicator.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 10px;
                border: 1px solid black;
            }}
        """)

    def start_record(self):
        """开始记录IMU和Carsim和MOOG数据"""
        self.update_indicator(True)
        self.side_start_record_button.setStyleSheet("background-color:green;color:white;")
        timestamp = time.perf_counter() * 1000  # 转换为毫秒
        milliseconds = int(timestamp)  # 转为整数
        self.record_start_time = milliseconds
        self.record_start_time_last = time.perf_counter()
        now_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.now_time = now_time
        # 虚拟调教参数
        #frontSpring_percentage_text = "_FS%+.1f%%" % self.frontSpring_percentage
        #rearSpring_percentage_text = "_RS%+.1f%%" % self.rearSpring_percentage
        #frontAuxRollMoment_percentage_text = "_FM%+.1f%%" % self.frontAuxRollMoment_percentage
        #rearAuxRollMoment_percentage_text = "_RM%+.1f%%" % self.rearAuxRollMoment_percentage
        #self.suspension_label_text = frontSpring_percentage_text + rearSpring_percentage_text + frontAuxRollMoment_percentage_text + rearAuxRollMoment_percentage_text
        if self.is_rename_folder_name:
            desktop_path = self.current_save_path
            #self.save_path = desktop_path + '\\DCH_' + now_time + self.suspension_label_text
        elif self.auto_record != 0:
            desktop_path = self.current_save_path
            self.save_path = desktop_path + '\\DCH_' + now_time + self.preset_condition
        else:
            desktop_path = self.current_save_path
            self.save_path = desktop_path + '\\DCH_' + now_time
        if not self.is_recording_imu:
            self.is_recording_imu = True
            full_path = self.save_path + '\\' + 'IMUData.csv'
            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path)  # 创建保存路径
            self.csv_file_imu = open(full_path, "w", newline='')
            self.csv_writer_imu = csv.writer(self.csv_file_imu)
            self.csv_writer_imu.writerow([
                "TimeStep", "sampleTimeFine", "utcTime", "Roll", "Pitch",
                "Yaw", "q0", "q1",
                "q2", "q3", "RateOfTurnX", "RateOfTurnY",
                "RateOfTurnZ", "FreeAccX", "FreeAccY", "FreeAccZ", "AccelerationX", "AccelerationY",
                "AccelerationZ"])

            print("开始记录IMU数据...")

        if not self.is_recording_carsim:
            self.is_recording_carsim = True

            desktop_path = self.current_save_path
            full_path2 = self.save_path + '\\' + 'CarsimData.csv'
            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path)  # 创建保存路径
            self.csv_file_carsim = open(full_path2, "w", newline='')
            self.csv_writer_carsim = csv.writer(self.csv_file_carsim)
            self.csv_writer_carsim.writerow([
                "TimeStep", "Ax", "Ay", "Az",
                "Avx", "Avy", "Avz",
                "Roll", "Pitch", "Yaw", "AAx",
                "AAy", "AAz", "Vx",
                "steering_angle", "Throttle", "Pbk_con", "steering_speed", "steer_L1", 'T_Stamp', 'Xo', 'Yo', 'Vx',
                'Vy', 'Beta', 'Steer_SW',
                'M_SW', 'Ay', 'Yaw', 'AVz', 'Hcg_TM', 'LxcgTM', 'Clutch', 'Gears', 'FBK_PDL', 'RideCtrl_FrcRq_FL',
                'RideCtrl_FrcRq_FR', 'RideCtrl_FrcRq_RL', 'RideCtrl_FrcRq_RR',
                'FLWhlH', 'FRWhlH', 'RLWhlH', 'RRWhlH', 'Fx_L1', 'Fx_L2', 'Fx_R1', 'Fx_R2', 'Fy_L1', 'Fy_L2', 'Fy_R1',
                'Fy_R2', 'Fd_L1', 'Fd_L2', 'Fd_R1', 'Fd_R2',
                'Fz_L1', 'Fz_L2', 'Fz_R1', 'Fz_R2', 'Avy_L1', 'Avy_L2', 'Avy_R1', 'Avy_R2', 'VxCenL1', 'VxCenL2',
                'VxCenR1', 'VxCenR2','CmpRD_L1','CmpRD_L2','CmpRD_R1','CmpRD_R2', 'CmpD_L1', 'CmpD_L2', 'CmpD_R1', 'CmpD_R2', 'Jnc_L1', 'Jnc_R1', 'Jnc_L2', 'Jnc_R2', 'Steer_L2', 'Steer_R2', 'CmpS_L1', 'CmpS_L2'])
            # self.csv_writer_carsim.writerow([
            #     "TimeStep", "Ax", "Ay", "Az",
            #     "Avx", "Avy", "Avz",
            #     "Roll", "Pitch", "Yaw", "AAx",
            #     "AAy", "AAz", "Vx",
            #     "steering_angle", "TR_TRFinal", "AngReq_Angle_write", "steering_speed", "steer_L1", 'T_Stamp', 'Xo', 'Yo', 'Vx',
            #     'Vy', 'Beta', 'Steer_SW',
            #     'M_SW', 'Ay', 'Yaw', 'AVz', 'Hcg_TM', 'LxcgTM', 'Clutch', 'Gears', 'FBK_PDL', 'RideCtrl_FrcRq_FL',
            #     'RideCtrl_FrcRq_FR', 'RideCtrl_FrcRq_RL', 'RideCtrl_FrcRq_RR',
            #     'FLWhlH', 'FRWhlH', 'RLWhlH', 'RRWhlH', 'Fx_L1', 'Fx_L2', 'Fx_R1', 'Fx_R2', 'Fy_L1', 'Fy_L2', 'Fy_R1',
            #     'Fy_R2', 'Fd_L1', 'Fd_L2', 'Fd_R1', 'Fd_R2',
            #     'Fz_L1', 'Fz_L2', 'Fz_R1', 'Fz_R2', 'Avy_L1', 'Avy_L2', 'Avy_R1', 'Avy_R2', 'VxCenL1', 'VxCenL2',
            #     'VxCenR1', 'VxCenR2'])

            print("开始记录Carsim数据...")

        if not self.is_recording_moog:
            self.is_recording_moog = True

            desktop_path = self.current_save_path
            full_path2 = self.save_path + '\\' + 'MoogData.csv'
            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path)  # 创建保存路径
            self.csv_file_moog = open(full_path2, "w", newline='')
            self.csv_writer_moog = csv.writer(self.csv_file_moog)
            self.csv_writer_moog.writerow([
                "TimeStep", "X", "Y", "Z", "Roll", "Pitch", "Yaw",
                "Vx", "Vy", "Vz", "Avx", "Avy", "Avz",
                "Ax", "Ay", "Az", "AAx", "AAy", "AAz",
                "Acu1_pos", "Acu2_pos", "Acu3_pos", "Acu4_pos", "Acu5_pos", "Acu6_pos",
                "Acu1_vel", "Acu2_vel", "Acu3_vel", "Acu4_vel", "Acu5_vel", "Acu6_vel",
                "Acu1_acc", "Acu2_acc", "Acu3_acc", "Acu4_acc", "Acu5_acc", "Acu6_acc",
                "ActualLPRollPos", "ActualLPPitchPos", "ActualLPRollVel", "ActualLPPitchVel",
                "ActualLPRollAcc", "ActualLPPitchAcc"
            ])

            print("开始记录Moog数据...")

        if self.record_disusx:
            self.start_record_disusx()

        if not self.is_recording_visual_compensator:
            self.is_recording_visual_compensator = True

            desktop_path = self.current_save_path
            full_path2 = self.save_path + '\\' + 'VisualCompensator.csv'
            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path)  # 创建保存路径
            self.csv_file_visual_compensator = open(full_path2, "w", newline='')
            self.csv_writer_visual_compensator = csv.writer(self.csv_file_visual_compensator)
            self.csv_writer_visual_compensator.writerow([
                "TimeStep", "x", "x_pre", "ax", "y", "y_pre", "ay", "yaw", "yaw_pre", "aaz"])

            print("开始记录视觉延迟补偿数据...")


        # self.start_record_input_index = len(self.time_data_carsim_all)
        # self.start_record_moog_index = len(self.time_data_moog_all)
        # self.start_record_imu_index = len(self.time_data_imu_all)
        self.lastCarsimTime = time.perf_counter() - self.start_time
        self.lastMoogTime = time.perf_counter() - self.start_time
        self.lastIMUTime = time.perf_counter() - self.start_time
        self.lastElectrolTime = time.perf_counter() - self.start_time
        self.sendData2camera(1, 1)

    def start_record_disusx(self):
        now_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if not self.is_recording_disusx:
            self.is_recording_disusx = True

            desktop_path = self.current_save_path
            full_path2 = self.save_path + '\\' + 'Disus_C_i.csv'
            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path)  # 创建保存路径
            self.csv_file_disusx_i = open(full_path2, "w", newline='')
            self.csv_writer_disusx_i = csv.writer(self.csv_file_disusx_i)
            self.csv_writer_disusx_i.writerow([
                "TimeStep", "IMP_FD_L1", "IMP_FD_R1", "IMP_FD_L2", "IMP_FD_R2"
            ])
            full_path3 = self.save_path + '\\' + 'Disus_C_o.csv'
            self.csv_file_disusx_o = open(full_path3, "w", newline='')
            self.csv_writer_disusx_o = csv.writer(self.csv_file_disusx_o)
            self.csv_writer_disusx_o.writerow([
                "TimeStep", "Vx", "Vx_L1", "Vx_R1", "Vx_L2", "Vx_R2", "Pbk_Con", "Steer_SW", "StrAV_SW",
                "M_D3f", "Vx", "Ax", "Ay", "Az", "AVx", "AVy", "AVz",
                "Jnc_L1", "Jnc_R1", "Jnc_L2", "Jnc_R2", "CmpRD_L1", "CmpRD_L2", "CmpRD_R1", "CmpRD_R2",
                "Z_L1", "Z_R1", "Vx", "Vx", "Pitch", "Roll", "Zcg_SM"
            ])

            print("开始记录Disus_X数据...")

    def select_save_folder(self):
        folder_path = QFileDialog.getExistingDirectory(
            None,
            "选择保存数据的文件夹",
            self.current_save_path,
            QFileDialog.ShowDirsOnly
        )
        if folder_path:
            self.current_save_path = folder_path
            print(self.current_save_path)

    def finish_record(self):
        self.update_indicator(False)
        self.side_start_record_button.setStyleSheet("background-color:white;color:black;")
        """结束记录IMU和Carsim和MOOG数据"""

        # 检查是否已有对话框打开
        if hasattr(self, 'evaluation_dialog') and self.evaluation_dialog and self.evaluation_dialog.isVisible():
            # 如果已有对话框，将其置顶并激活
            self.evaluation_dialog.raise_()
            self.evaluation_dialog.activateWindow()
            return

        self.record_finish_time_last = time.perf_counter()

        if not (self.is_recording_imu or self.is_recording_carsim or self.is_recording_moog):
            return

        self.is_recording_imu = False
        self.is_recording_carsim = False
        self.is_recording_moog = False
        self.is_recording_visual_compensator = False
        self.is_recording_disusx = False



        # 异步保存数据，避免阻塞界面
        self.save_data_async()

        # 创建非模态对话框
        if self.auto_record == 0:
            # 禁用结束记录按钮，防止重复点击
            self.side_start_record_button.setEnabled(False)
            self.create_evaluation_dialog()

        # 发送信号到相机
        self.sendData2camera(1, 0)

        # 保存参数文件（如果是并行保存）
        if self.is_par_save:
            self.save_parameters_async()

    def save_data_async(self):
        """异步保存数据，避免阻塞界面"""
        # 使用线程或定时器来异步保存数据
        from threading import Thread

        def save_data_thread():
            # 保存IMU数据
            imuLength = len(self.recordIMUDataList)
            count = 0
            if self.csv_writer_imu:
                for t, data in self.recordIMUDataList.items():
                    self.csv_writer_imu.writerow([t] + data)
            if self.csv_file_imu:
                self.csv_file_imu.close()
                self.csv_file_imu = None
                self.csv_writer_imu = None
            print("结束记录IMU数据...")

            # 保存Carsim数据
            carsimLength = len(self.recordCarsimDataList)
            count = 0
            if self.csv_writer_carsim:
                for t, data in self.recordCarsimDataList.items():
                    if count % 5 == 0:
                        self.csv_writer_carsim.writerow([t] + data)
                    count = count + 1
            if self.csv_file_carsim:
                self.csv_file_carsim.close()
                self.csv_file_carsim = None
                self.csv_writer_carsim = None
            print("结束记录Carsim数据...")

            # 保存MOOG数据
            moogLength = len(self.recordMoogDataList)
            count = 0
            if self.csv_writer_moog:
                for t, data in self.recordMoogDataList.items():
                    if count % 5 == 0:
                        self.csv_writer_moog.writerow([t] + data)
                    count = count + 1
            if self.csv_file_moog:
                self.csv_file_moog.close()
                self.csv_file_moog = None
                self.csv_writer_moog = None
            print("结束记录moog数据...")

            # 保存其他数据
            if self.record_disusx:
                self.finish_record_disusx()

            if self.csv_writer_visual_compensator:
                for t, data in self.recordVisualCompensatorDataList.items():
                    self.csv_writer_visual_compensator.writerow([t] + data)
            if self.csv_file_visual_compensator:
                self.csv_file_visual_compensator.close()
                self.csv_file_visual_compensator = None
                self.csv_writer_visual_compensator = None

            # 清空数据列表
            self.recordIMUDataList.clear()
            self.recordCarsimDataList.clear()
            self.recordMoogDataList.clear()
            self.recordVisualCompensatorDataList.clear()
            self.recordDisusxIDataList.clear()
            self.recordDisusxODataList.clear()

            print("所有数据保存完成")

        # 启动线程保存数据
        thread = Thread(target=save_data_thread)
        thread.daemon = True
        thread.start()

    def create_evaluation_dialog(self):
        """创建非模态的评价信息对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("记录评价信息")
        dialog.setMinimumWidth(400)
        dialog.setModal(False)  # 设置为非模态，不阻塞主界面

        # 存储对话框引用
        self.evaluation_dialog = dialog

        # 连接对话框关闭事件
        dialog.finished.connect(self.on_evaluation_dialog_closed)

        # 创建布局
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # 评价日期（默认当前时间）
        date_str = self.now_time.split('_')[0]
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate(year, month, day))
        form_layout.addRow("评价日期:", self.date_edit)

        # 车型（优先使用预定义值，否则使用当前车型）
        if self.preset_car_model:
            car_model_default = self.preset_car_model
        else:
            car_model_default = self.carName
        self.car_model_edit = QLineEdit(car_model_default)
        form_layout.addRow("车型:", self.car_model_edit)

        # 调校件（优先使用预定义值，否则根据参数计算默认值）
        if self.preset_tuning_parts:
            tuning_default = self.preset_tuning_parts
        else:
            tuning_parts = []
            # # 检查每个调校参数，如果不为0则添加到列表中
            # if self.frontSpring_percentage != 0:
            #     frontSpring_text = f"FS{self.frontSpring_percentage:+.1f}".replace('.0', '')
            #     tuning_parts.append(frontSpring_text)
            #
            # if self.rearSpring_percentage != 0:
            #     rearSpring_text = f"RS{self.rearSpring_percentage:+.1f}".replace('.0', '')
            #     tuning_parts.append(rearSpring_text)
            #
            # if self.frontAuxRollMoment_percentage != 0:
            #     frontAux_text = f"FM{self.frontAuxRollMoment_percentage:+.1f}".replace('.0', '')
            #     tuning_parts.append(frontAux_text)
            #
            # if self.rearAuxRollMoment_percentage != 0:
            #     rearAux_text = f"RM{self.rearAuxRollMoment_percentage:+.1f}".replace('.0', '')
            #     tuning_parts.append(rearAux_text)

            # 如果没有调校件，显示ORI
            tuning_default = "_".join(tuning_parts) if tuning_parts else "ORI"

        self.tuning_edit = QLineEdit(tuning_default)
        form_layout.addRow("调校件:", self.tuning_edit)

        # 评价人（优先使用预定义值，否则使用默认值）
        if self.preset_evaluator:
            evaluator_default = self.preset_evaluator
        else:
            evaluator_default = self.default_evaluator
        self.evaluator_edit = QLineEdit(evaluator_default)
        form_layout.addRow("评价人:", self.evaluator_edit)

        # 第几次评价（使用默认值）
        self.evaluation_count_edit = QLineEdit(self.default_evaluation_count)
        self.evaluation_count_edit.setValidator(QIntValidator(1, 100))
        form_layout.addRow("第几次评价:", self.evaluation_count_edit)

        # 工况（改为文本框输入，优先使用预定义值）
        condition_default = self.preset_condition if self.preset_condition else ""
        self.condition_edit = QLineEdit(condition_default)
        form_layout.addRow("工况:", self.condition_edit)

        # 工况版本（使用默认值）
        self.condition_version_edit = QLineEdit(self.default_condition_version)
        form_layout.addRow("工况版本:", self.condition_version_edit)

        # 体感版本（使用默认值）
        self.feeling_version_edit = QLineEdit(self.default_feeling_version)
        form_layout.addRow("体感版本:", self.feeling_version_edit)

        layout.addLayout(form_layout)

        # 确定和取消按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)

        # 连接按钮信号 - 使用lambda函数传递对话框引用
        ok_button.clicked.connect(lambda: self.save_record_data(dialog))
        cancel_button.clicked.connect(dialog.close)

        # 显示对话框（非模态）
        dialog.show()

    def on_evaluation_dialog_closed(self, result):
        """当评价对话框关闭时调用的函数"""
        # 重新启用结束记录按钮
        self.side_start_record_button.setEnabled(True)

        # 清除对话框引用
        self.evaluation_dialog = None

    def save_parameters_async(self):
        """异步保存参数文件"""
        from threading import Thread

        def save_parameters_thread():
            carsim.GoHome()
            lib, dt, cat, _ = carsim.GetBlueLink('#BlueLink2')
            carsim.Gotolibrary(lib, dt, cat)
            carsim.ExportParsfile(self.save_path + '\\' + dt, 1)
            carsim.GoHome()
            print("参数文件保存完成")

        # 启动线程保存参数
        thread = Thread(target=save_parameters_thread)
        thread.daemon = True
        thread.start()

    # 在save_record_data函数中添加验证和保存默认值
    def save_record_data(self, dialog):
        # 验证必填字段
        if not self.evaluator_edit.text().strip():
            QMessageBox.warning(dialog, "警告", "评价人不能为空!")
            return

        if not self.evaluation_count_edit.text().strip():
            QMessageBox.warning(dialog, "警告", "第几次评价不能为空!")
            return

        if not self.condition_version_edit.text().strip():
            QMessageBox.warning(dialog, "警告", "工况版本不能为空!")
            return

        if not self.feeling_version_edit.text().strip():
            QMessageBox.warning(dialog, "警告", "体感版本不能为空!")
            return

        # 如果是第一次填写或默认值为空，则保存当前值作为默认值
        self.default_evaluator = self.evaluator_edit.text().strip()
        self.default_evaluation_count = self.evaluation_count_edit.text().strip()
        self.default_condition_version = self.condition_version_edit.text().strip()
        self.default_feeling_version = self.feeling_version_edit.text().strip()

        # 获取评价人、第几次评价和工况
        car_name = self.carName.split(',')[0].strip()
        evaluator = self.evaluator_edit.text().strip()

        evaluation_count = self.evaluation_count_edit.text().strip()
        working_condition = self.condition_edit.text().strip()
        evaluation_date = self.date_edit.date().toString("yyyy-MM-dd")
        # 构建目标路径
        base_dir = r"\\10.10.10.99\database"
        target_dir = os.path.join(base_dir, evaluation_date,evaluator,car_name, working_condition)

        # 获取原始文件夹名称
        original_folder_name = os.path.basename(self.save_path)

        # 完整目标路径
        full_target_path = os.path.join(target_dir, original_folder_name)

        try:
            # 创建目标目录（如果不存在）
            os.makedirs(target_dir, exist_ok=True)

            # 复制文件夹
            if os.path.exists(self.save_path):
                # 如果目标路径已存在，先删除
                if os.path.exists(full_target_path):
                    shutil.rmtree(full_target_path)

                # 复制文件夹
                shutil.copytree(self.save_path, full_target_path)
                print(f"文件夹已从 {self.save_path} 复制到 {full_target_path}")
            else:
                QMessageBox.warning(dialog, "警告", "原始数据文件夹不存在!")
                return
        except Exception as e:
            QMessageBox.warning(dialog, "错误", f"复制文件夹时出错: {str(e)}")
            return

        # 收集所有数据
        tuning_parts_list = []
        if self.tuning_edit.text() != "ORI":
            # 将下划线分隔的字符串转换为列表
            tuning_parts_list = self.tuning_edit.text().split('_')
        else:
            tuning_parts_list = ['ORI']

        record_data = {
            'evaluation_date': self.date_edit.date().toString("yyyy-MM-dd"),
            'car_model': self.car_model_edit.text(),
            'tuning_parts': tuning_parts_list,  # 列表形式
            'evaluator': evaluator,
            'evaluation_count': int(evaluation_count),
            'working_condition': working_condition,
            'condition_version': self.condition_version_edit.text(),
            'feeling_version': self.feeling_version_edit.text(),
            'data_location': full_target_path  # 更新为新的存放位置
        }

        # 连接到数据库并插入数据
        db = mysql_utils.MySQLDatabase()
        try:
            flag = db.connect()
        except Exception as e:
            QMessageBox.information(self,'警告',f'数据库连接失败{str(e)}')
            return
        if flag:
            if db.insert_test_data(record_data):
                # 接受对话框
                dialog.accept()
                # 提示用户保存成功
                QMessageBox.information(self, "成功", "评价记录已保存!")
            else:
                QMessageBox.warning(dialog, "错误", "保存到数据库失败!")
            db.disconnect()
        else:
            QMessageBox.warning(dialog, "错误", "无法连接到数据库!")

    def finish_record_disusx(self):
        count = 0
        if self.csv_writer_disusx_i:
            for t, data in self.recordDisusxIDataList.items():
                if count % 5 == 0:
                    self.csv_writer_disusx_i.writerow([t] + data)

                count = count + 1
        if self.csv_file_disusx_i:
            self.csv_file_disusx_i.close()
            self.csv_file_disusx_i = None
            self.csv_writer_disusx_i = None

        count = 0
        if self.csv_writer_disusx_o:
            for t, data in self.recordDisusxODataList.items():
                if count % 5 == 0:
                    self.csv_writer_disusx_o.writerow([t] + data)
                count = count + 1
        if self.csv_file_disusx_o:
            self.csv_file_disusx_o.close()
            self.csv_file_disusx_o = None
            self.csv_writer_disusx_o = None

    def receive_electrical_control_i_data(self):
        try:
            while True:
                rec_msg = udp_electrical_control_i.recvfrom(4096)
                res = rec_msg[0]
                try:
                    data_list = struct.unpack('4d', res)
                    timestamp = time.perf_counter() * 1000  # 转换为毫秒
                    record_current_time = int(timestamp) - self.record_start_time  # 转为整数
                    current_time = time.perf_counter() - self.start_time
                    if current_time <= self.lastElectrolTime:
                        current_time = self.lastElectrolTime + 0.000000000000001
                    self.lastElectrolTime = current_time
                    self.TR_TRFinal = data_list[2]
                    self.AngReq_Angle_write = data_list[3]
                    if self.csv_writer_disusx_i and self.is_recording_disusx:
                        self.recordDisusxIDataList[current_time] = list(data_list)


                except AttributeError as e:
                    print(e)
        except socket.timeout:
            print("未接收指令超时，停止程序")
            udp_electrical_control_i.close()
            if self.csv_file_disusx_i:
                self.csv_file_disusx_i.close()
                print("CSV文件已关闭")
            sys.exit()

    def receive_electrical_control_o_data(self):
        try:
            while True:
                rec_msg = udp_electrical_control_o.recvfrom(4096)
                res = rec_msg[0]
                try:
                    data_list = struct.unpack('31d', res)
                    timestamp = time.perf_counter() * 1000  # 转换为毫秒
                    record_current_time = int(timestamp) - self.record_start_time  # 转为整数
                    current_time = time.perf_counter() - self.start_time
                    if current_time <= self.lastElectrolTime:
                        current_time = self.lastElectrolTime + 0.000000000000001
                    self.lastElectrolTime = current_time

                    if self.csv_writer_disusx_o and self.is_recording_disusx:
                        self.recordDisusxODataList[current_time] = list(data_list)

                except AttributeError as e:
                    print(e)
        except socket.timeout:
            print("未接收指令超时，停止程序")
            udp_electrical_control_o.close()
            if self.csv_file_disusx_o:
                self.csv_file_disusx_o.close()
                print("CSV文件已关闭")
            sys.exit()

    def receive_rfpro_coordinates_data(self):
        try:
            while True:
                rec_msg = udp_rfpro_coordinates.recvfrom(4096)
                res = rec_msg[0]
                try:
                    data_list = struct.unpack('2d', res)
                    self.signal_rfpro_x_coordinate = data_list[0]
                    self.signal_rfpro_y_coordinate = data_list[1]

                    if self.auto_record != 0:
                        start_x_coords = self.x_start_record_coordinate
                        start_y_coords = self.y_start_record_coordinate
                        finish_x_coords = self.x_finish_record_coordinate
                        finish_y_coords = self.y_finish_record_coordinate

                        # 计算与所有起点的距离
                        start_distances = []
                        for i, (start_x, start_y) in enumerate(zip(start_x_coords, start_y_coords)):
                            start_distance_x = abs(self.signal_rfpro_x_coordinate - start_x)
                            start_distance_y = abs(self.signal_rfpro_y_coordinate - start_y)
                            start_distances.append((i, start_distance_x, start_distance_y))

                        # 计算与所有终点的距离
                        end_distances = []
                        for i, (finish_x, finish_y) in enumerate(zip(finish_x_coords, finish_y_coords)):
                            end_distance_x = abs(self.signal_rfpro_x_coordinate - finish_x)
                            end_distance_y = abs(self.signal_rfpro_y_coordinate - finish_y)
                            end_distances.append((i, end_distance_x, end_distance_y))

                        # 检查是否进入起点区域
                        in_any_start_zone = False
                        for i, start_dist_x, start_dist_y in start_distances:
                            if start_dist_x <= 0.5 and start_dist_y <= 5 and self.vx >= self.velocity_autorecord:
                                if not self._in_start_zone or self._current_start_zone != i:
                                    self._in_start_zone = True
                                    self._current_start_zone = i  # 记录当前进入的起点区域索引
                                    self.preset_condition = self.preset_condition_all[i]
                                    self.start_record()
                                    print(f"进入起点区域 {i + 1} (坐标: {start_x_coords[i]}, {start_y_coords[i]})")
                                in_any_start_zone = True
                                break  # 如果进入多个起点区域，只记录第一个

                        if not in_any_start_zone:
                            self._in_start_zone = False
                            self._current_start_zone = None

                        # 检查是否进入终点区域
                        in_any_end_zone = False

                        for i, end_dist_x, end_dist_y in end_distances:
                            if end_dist_x <= 0.5 and end_dist_y <= 5:
                                if not self._in_end_zone or self._current_end_zone != i:
                                    self._in_end_zone = True
                                    self._current_end_zone = i  # 记录当前进入的终点区域索引
                                    print(f"进入终点区域 {i + 1} (坐标: {finish_x_coords[i]}, {finish_y_coords[i]})")
                                    self.finish_record()
                                in_any_end_zone = True
                                break

                        if not in_any_end_zone:
                            self._in_end_zone = False
                            self._current_end_zone = None
                except AttributeError as e:
                    print(e)
        except socket.timeout:
            print("未接收指令超时，停止程序")
            udp_rfpro_coordinates.close()
            sys.exit()

    def receive_imu_data(self):
        """接收IMU数据"""
        try:
            while True:
                rec_msg = udp.recvfrom(4096)
                res = rec_msg[0]
                try:
                    current_time = time.perf_counter() - self.start_time
                    self.time_data_imu.append(current_time)
                    # self.time_data_imu_all.append(current_time)
                    timestamp = time.perf_counter() * 1000  # 转换为毫秒
                    record_current_time = int(timestamp) - self.record_start_time  # 转为整数
                    data_list = struct.unpack('18d', res)
                    cur = time.time()
                    error = cur - data_list[1]
                    data_list = list(data_list)
                    data_list[1] = data_list[1] - self.start_time1
                    # self.signal_data['roll']['imu'].append((data_list[2]-180 if data_list[2]>0 else data_list[2]+180))
                    # self.signal_data_all['roll']['imu'].append((data_list[2]-180 if data_list[2]>0 else data_list[2]+180))
                    self.signal_data['roll']['imu'].append(data_list[2] * (-1))
                    # self.signal_data_all['roll']['imu'].append(data_list[2] * (-1))
                    self.signal_data['pitch']['imu'].append(data_list[3])
                    # self.signal_data_all['pitch']['imu'].append(data_list[3])
                    self.signal_data['yaw']['imu'].append(data_list[4] * (-1))
                    # self.signal_data_all['yaw']['imu'].append(data_list[4] * (-1))

                    self.signal_data['ang_x']['imu'].append(data_list[9] * 57.3 * -1)
                    # self.signal_data_all['ang_x']['imu'].append(data_list[9]*57.3 * -1)
                    self.signal_data['ang_y']['imu'].append(data_list[10] * 57.3)
                    # self.signal_data_all['ang_y']['imu'].append(data_list[10]*57.3)
                    self.signal_data['ang_z']['imu'].append(data_list[11] * 57.3 * -1)
                    # self.signal_data_all['ang_z']['imu'].append(data_list[11]*57.3 * -1)

                    self.signal_data['acc_x']['imu'].append(data_list[12] * (-1))
                    # self.signal_data_all['acc_x']['imu'].append(data_list[12] * (-1))
                    self.signal_data['acc_y']['imu'].append(data_list[13])
                    # self.signal_data_all['acc_y']['imu'].append(data_list[13])
                    self.signal_data['acc_z']['imu'].append(data_list[14] * (-1))
                    # self.signal_data_all['acc_z']['imu'].append(data_list[14] * (-1))

                    # self.signal_data['pos_x']['imu'].append(0)
                    # self.signal_data_all['pos_x']['imu'].append(0)
                    # self.signal_data['pos_y']['imu'].append(0)
                    # self.signal_data_all['pos_y']['imu'].append(0)
                    # self.signal_data['pos_z']['imu'].append(0)
                    # self.signal_data_all['pos_z']['imu'].append(0)
                    #
                    # self.signal_data['vel_x']['imu'].append(0)
                    # self.signal_data_all['vel_x']['imu'].append(0)
                    # self.signal_data['vel_y']['imu'].append(0)
                    # self.signal_data_all['vel_y']['imu'].append(0)
                    # self.signal_data['vel_z']['imu'].append(0)
                    # self.signal_data_all['vel_z']['imu'].append(0)
                    #
                    # self.signal_data['ang_acc_x']['imu'].append(0)
                    # self.signal_data_all['ang_acc_x']['imu'].append(0)
                    # self.signal_data['ang_acc_y']['imu'].append(0)
                    # self.signal_data_all['ang_acc_y']['imu'].append(0)
                    # self.signal_data['ang_acc_z']['imu'].append(0)
                    # self.signal_data_all['ang_acc_z']['imu'].append(0)
                    if self.csv_writer_imu and self.is_recording_imu:
                        # self.csv_writer_imu.writerow([current_time] + list(data_list))
                        if current_time <= self.lastIMUTime:
                            current_time = self.lastIMUTime + 0.000000000000001
                        self.lastIMUTime = current_time
                        self.recordIMUDataList[current_time] = list(data_list)

                    num_deletions_imu = max(
                        (len(self.time_data_imu) - (
                                self.plot_buffer_imu + self.plot_delete_step)) // self.plot_delete_step,
                        0)
                    while num_deletions_imu > 0:
                        # print(len(self.time_data_imu))
                        for _ in range(self.plot_delete_step):
                            if self.time_data_imu:  # 确保队列不为空
                                self.time_data_imu.popleft()
                        for channel in self.signal_data:
                            for signal in ['imu']:
                                for _ in range(self.plot_delete_step):
                                    if self.signal_data[channel][signal]:  # 确保队列不为空
                                        self.signal_data[channel][signal].popleft()
                        num_deletions_imu = max(
                            (len(self.time_data_imu) - self.plot_buffer_imu) // self.plot_delete_step, 0)
                except AttributeError as e:
                    print(e)


        except socket.timeout:
            print("未接收指令超时，停止程序")
            udp.close()
            if self.csv_file_imu:
                self.csv_file_imu.close()
                print("CSV文件已关闭")
            sys.exit()

    def receive_carsim_data(self):
        """接收Carsim数据"""
        try:
            while True:
                rec_msg = udp2.recvfrom(4096)
                res = rec_msg[0]
                dataLen = len(res)

                # udp2.sendto(res, ('10.10.20.225', 9899))
                try:
                    data_list = struct.unpack('83d', res)
                    data_list = list(data_list)
                    timestamp = time.perf_counter() * 1000  # 转换为毫秒
                    record_current_time = int(timestamp) - self.record_start_time  # 转为整数
                    # current_time = time.perf_counter() - self.start_time
                    # current_time = time.time() - self.start_time1
                    current_time = time.perf_counter() - self.start_time
                    if current_time <= self.lastCarsimTime:
                        # print('imu时间重复')
                        current_time = self.lastCarsimTime + 0.000000000000001
                        # self.lastIMUTime = current_time
                    self.lastCarsimTime = current_time
                    self.time_data_carsim.append(current_time)
                    # self.time_data_carsim_all.append(current_time)

                    self.signal_data['roll']['input'].append(data_list[6])
                    # self.signal_data_all['roll']['input'].append(data_list[6] * (-1))
                    self.signal_data['pitch']['input'].append(data_list[7] * (-1))
                    # self.signal_data_all['pitch']['input'].append(data_list[7] * (-1))
                    self.signal_data['yaw']['input'].append(
                        (data_list[8] % 360 if data_list[8] > 0 else data_list[8] % (-360)) * (-1))
                    # self.signal_data_all['yaw']['input'].append((data_list[8]%360 if data_list[8]>0 else data_list[8]%(-360)) * (-1))

                    self.signal_data['ang_x']['input'].append(data_list[3] )
                    # self.signal_data_all['ang_x']['input'].append(data_list[3] * (-1))
                    self.signal_data['ang_y']['input'].append(data_list[4] * (-1))
                    # self.signal_data_all['ang_y']['input'].append(data_list[4] * (-1))
                    self.signal_data['ang_z']['input'].append(data_list[5] * (-1))
                    # self.signal_data_all['ang_z']['input'].append(data_list[5] * (-1))

                    self.signal_data['acc_x']['input'].append(data_list[0] * 9.81)
                    # self.signal_data_all['acc_x']['input'].append(data_list[0]*9.81)
                    self.signal_data['acc_y']['input'].append(data_list[1] * (-1) * 9.81)
                    # self.signal_data_all['acc_y']['input'].append(data_list[1] * (-1)*9.81)
                    self.signal_data['acc_z']['input'].append(data_list[2] * (-1) * 9.81)
                    # self.signal_data_all['acc_z']['input'].append(data_list[2] * (-1)*9.81)

                    self.signal_data['pos_x']['input'].append(0)
                    # self.signal_data_all['pos_x']['input'].append(0)
                    self.signal_data['pos_y']['input'].append(0)
                    # self.signal_data_all['pos_y']['input'].append(0)
                    self.signal_data['pos_z']['input'].append(0)
                    # self.signal_data_all['pos_z']['input'].append(0)

                    self.signal_data['vel_x']['input'].append(data_list[12])
                    # self.signal_data_all['vel_x']['input'].append(data_list[12])
                    vx = data_list[12]
                    self.signal_data['vel_y']['input'].append(data_list[17])
                    #print(data_list[17])
                    # self.signal_data_all['vel_y']['input'].append(0)
                    self.signal_data['vel_z']['input'].append(0)
                    # self.signal_data_all['vel_z']['input'].append(0)

                    self.signal_data['ang_acc_x']['input'].append(data_list[9] * 57.3)
                    # self.signal_data_all['ang_acc_x']['input'].append(data_list[9]*57.3)
                    self.signal_data['ang_acc_y']['input'].append(data_list[10] * 57.3 * (-1))
                    # self.signal_data_all['ang_acc_y']['input'].append(data_list[10]*57.3 * (-1))
                    self.signal_data['ang_acc_z']['input'].append(data_list[11] * 57.3 * (-1))
                    # self.signal_data_all['ang_acc_z']['input'].append(data_list[11]*57.3 * (-1))

                    # 添加新的信号数据
                    self.signal_data['steering_angle']['input'].append(data_list[13])
                    # self.signal_data_all['steering_angle']['input'].append(data_list[13])
                    sw = data_list[13]
                    self.signal_steer_angle = data_list[13]
                    self.signal_data['throttle']['input'].append(data_list[14])

                    self.signal_data['pbk_con']['input'].append(data_list[15])

                    self.signal_data['steering_speed']['input'].append(data_list[16]*57.3)
                    self.signal_data['CmpRD_L1']['input'].append(data_list[66] / 1000.0)
                    self.signal_data['CmpRD_L2']['input'].append(data_list[67] / 1000.0)
                    self.signal_data['CmpRD_R1']['input'].append(data_list[68] / 1000.0)
                    self.signal_data['CmpRD_R2']['input'].append(data_list[69] / 1000.0)
                    # self.signal_data_all['steering_speed']['input'].append(data_list[16])
                    sw_speed = data_list[16]
                    # self.alert.alert(vx,sw,sw_speed,self.condition_combo.currentText())
                    # self.get_f_data()
                    self.f_data.append(0)
                    self.vx = data_list[12]
                    channels = list(self.signal_data.keys())
                    # data_list[14] = self.TR_TRFinal
                    # data_list[15] = self.AngReq_Angle_write
                    data_list[19] = self.signal_rfpro_x_coordinate
                    data_list[20] = self.signal_rfpro_y_coordinate
                    if self.csv_writer_carsim and self.is_recording_carsim:
                        # self.csv_writer_carsim.writerow([record_current_time] + list(data_list))
                        self.recordCarsimDataList[data_list[82]] = list(data_list[:-1])

                    num_deletions_carsim = max((len(self.time_data_carsim) - (
                            self.plot_buffer_carsim + self.plot_delete_step)) // self.plot_delete_step, 0)
                    while num_deletions_carsim > 0:
                        # print(len(self.time_data_carsim))
                        for _ in range(self.plot_delete_step):
                            if self.time_data_carsim:  # 确保队列不为空
                                self.time_data_carsim.popleft()
                                self.f_data.popleft()
                        for channel in self.signal_data:
                            for signal in ['input']:
                                for _ in range(self.plot_delete_step):
                                    if self.signal_data[channel][signal]:  # 确保队列不为空
                                        self.signal_data[channel][signal].popleft()
                        num_deletions_carsim = max(
                            (len(self.time_data_carsim) - self.plot_buffer_carsim) // self.plot_delete_step, 0)
                except AttributeError as e:
                    print(e)
        except socket.timeout:
            print("未接收指令超时，停止程序")
            udp2.close()
            if self.csv_file_carsim:
                self.csv_file_carsim.close()
                print("CSV文件已关闭")
            sys.exit()

    def receive_moog_data(self):
        """接收moog数据"""
        try:
            while True:
                rec_msg = udp3.recvfrom(4096)
                res = rec_msg[0]
                try:
                    data_list = struct.unpack('12i42fd', res)
                    timestamp = time.perf_counter() * 1000  # 转换为毫秒
                    record_current_time = int(timestamp) - self.record_start_time  # 转为整数
                    current_time = time.perf_counter() - self.start_time
                    if current_time <= self.lastMoogTime:
                        # print('imu时间重复')
                        current_time = self.lastMoogTime + 0.000000000000001
                        # self.lastIMUTime = current_time
                    self.lastMoogTime = current_time
                    self.time_data_moog.append(current_time)
                    # self.time_data_moog_all.append(current_time)
                    self.signal_data['roll']['moog'].append(data_list[15] * 57.3)
                    # self.signal_data_all['roll']['moog'].append(data_list[15]*57.3)
                    self.signal_data['pitch']['moog'].append(data_list[16] * 57.3)
                    # self.signal_data_all['pitch']['moog'].append(data_list[16]*57.3)
                    self.signal_data['yaw']['moog'].append(data_list[17] * 57.3)
                    # self.signal_data_all['yaw']['moog'].append(data_list[17]*57.3)

                    self.signal_data['ang_x']['moog'].append(data_list[21] * 57.3)
                    # self.signal_data_all['ang_x']['moog'].append(data_list[21]*57.3)
                    self.signal_data['ang_y']['moog'].append(data_list[22] * 57.3)
                    # self.signal_data_all['ang_y']['moog'].append(data_list[22]*57.3)
                    self.signal_data['ang_z']['moog'].append(data_list[23] * 57.3)
                    # self.signal_data_all['ang_z']['moog'].append(data_list[23]*57.3)

                    self.signal_data['acc_x']['moog'].append(data_list[24])
                    # self.signal_data_all['acc_x']['moog'].append(data_list[24])
                    self.signal_data['acc_y']['moog'].append(data_list[25])
                    # self.signal_data_all['acc_y']['moog'].append(data_list[25])
                    self.signal_data['acc_z']['moog'].append(data_list[26])
                    # self.signal_data_all['acc_z']['moog'].append(data_list[26])

                    self.signal_data['pos_x']['moog'].append(data_list[12])
                    # self.signal_data_all['pos_x']['moog'].append(data_list[12])
                    self.signal_data['pos_y']['moog'].append(data_list[13])
                    # self.signal_data_all['pos_y']['moog'].append(data_list[13])
                    self.signal_data['pos_z']['moog'].append(data_list[14] * (-1))
                    # self.s                    # self.signal_data_all['ang_acc_z']['moog'].append(data_list[29]*57.3)ignal_data_all['pos_z']['moog'].append(data_list[14] * (-1))

                    self.signal_data['vel_x']['moog'].append(data_list[18])
                    # self.signal_data_all['vel_x']['moog'].append(data_list[18])
                    self.signal_data['vel_y']['moog'].append(data_list[19])
                    # self.signal_data_all['vel_y']['moog'].append(data_list[19])
                    self.signal_data['vel_z']['moog'].append(data_list[20])
                    # self.signal_data_all['vel_z']['moog'].append(data_list[20])

                    self.signal_data['ang_acc_x']['moog'].append(data_list[27] * 57.3)
                    # self.signal_data_all['ang_acc_x']['moog'].append(data_list[27]*57.3)
                    self.signal_data['ang_acc_y']['moog'].append(data_list[28] * 57.3)
                    # self.signal_data_all['ang_acc_y']['moog'].append(data_list[28]*57.3)
                    self.signal_data['ang_acc_z']['moog'].append(data_list[29] * 57.3)

                    # channels = list(self.signal_data.keys())

                    if self.csv_writer_moog and self.is_recording_moog:
                        # self.csv_writer_moog.writerow([record_current_time] + list(data_list[12:30]))
                        self.recordMoogDataList[data_list[54]] = list(data_list[12:54])

                    num_deletions_moog = max((len(self.time_data_moog) - (
                            self.plot_buffer_moog + self.plot_delete_step)) // self.plot_delete_step, 0)
                    while num_deletions_moog > 0:
                        # print(len(self.time_data_moog))
                        for _ in range(self.plot_delete_step):
                            if self.time_data_moog:  # 确保队列不为空
                                self.time_data_moog.popleft()
                        for channel in self.signal_data:
                            for signal in ['moog']:
                                for _ in range(self.plot_delete_step):
                                    if self.signal_data[channel][signal]:  # 确保队列不为空
                                        self.signal_data[channel][signal].popleft()
                        num_deletions_moog = max(
                            (len(self.time_data_moog) - self.plot_buffer_moog) // self.plot_delete_step, 0)
                except AttributeError as e:
                    print(e)
        except socket.timeout:
            print("未接收指令超时，停止程序")
            udp3.close()
            if self.csv_file_moog:
                self.csv_file_moog.close()
                print("CSV文件已关闭")
            sys.exit()

    def receive_compensator_data(self):
        """接收moog数据"""
        try:
            while True:
                rec_msg = udpVisualDelayCompensationReceive.recvfrom(4096)
                res = rec_msg[0]
                try:
                    data_list = struct.unpack('9d', res)
                    timestamp = time.perf_counter() * 1000  # 转换为毫秒
                    record_current_time = int(timestamp) - self.record_start_time  # 转为整数
                    current_time = time.perf_counter() - self.start_time

                    # channels = list(self.signal_data.keys())

                    if self.csv_writer_visual_compensator and self.is_recording_visual_compensator:
                        # self.csv_writer_moog.writerow([record_current_time] + list(data_list[12:30]))
                        self.recordVisualCompensatorDataList[current_time] = list(data_list)
                except AttributeError as e:
                    print(e)
        except socket.timeout:
            print("未接收指令超时，停止程序")
            udp3.close()
            if self.csv_file_moog:
                self.csv_file_moog.close()
                print("CSV文件已关闭")
            sys.exit()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # 创建选项卡
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_virtual_tuning_tab(), "启动")
        self.tabs.addTab(self.create_motion_display_tab(), "运动数据显示")
        self.tabs.addTab(self.create_signal_input_tab(), "信号输入配置")

        # tabs.addTab(self.create_feeling_mode_tab(), "体感方案设置")
        self.tabs.addTab(self.create_haptic_adjustment_tab(), "触感调节")
        # tabs.addTab(create_signal_management_tab(self),"信号管理")
        # tabs.addTab(create_Status_Control_tab(self), "进程管理")

        self.tabs.addTab(self.create_visual_compensation_tab(), "视觉补偿")
        # tabs.addTab(self.create_delay_tab(),"延迟")
        self.tabs.addTab(self.create_analysis_tab(), "数据处理")

        self.tabs.addTab(self.create_database_tab(), "数据库")
        # 连接选项卡切换信号
        self.tabs.currentChanged.connect(self.on_tab_changed)

        layout.addWidget(self.tabs)

        # 创建右侧可停靠侧边栏
        self.dock = QDockWidget("Sidebar", self)
        self.dock.setFeatures(QDockWidget.DockWidgetClosable |
                              QDockWidget.DockWidgetMovable |
                              QDockWidget.DockWidgetFloatable)

        # 侧边栏内容
        sidebar_content = QWidget()
        layout = QVBoxLayout()
        # 按钮高度
        button_height = 80
        # 添加“一键启动”按钮
        one_click_start_button = QPushButton("一键启动")
        one_click_start_button.clicked.connect(self.one_click_start)
        one_click_start_button.setFixedHeight(button_height)
        layout.addWidget(one_click_start_button)

        # 添加“一键关闭”按钮
        one_click_stop_button = QPushButton("一键关闭")
        one_click_stop_button.clicked.connect(self.one_click_stop)
        one_click_stop_button.setFixedHeight(button_height)
        layout.addWidget(one_click_stop_button)
        # 确认按钮
        confirm_button = QPushButton("确认场景设置")
        confirm_button.clicked.connect(self.confirm_scenario_settings)
        confirm_button.setFixedHeight(button_height)
        layout.addWidget(confirm_button)

        self.side_start_record_button = QPushButton("开始记录")
        self.side_start_record_button.clicked.connect(self.start_record)
        self.side_start_record_button.setFixedHeight(button_height)
        finish_record_button = QPushButton("结束记录")
        finish_record_button.clicked.connect(self.finish_record)
        finish_record_button.setFixedHeight(button_height)
        layout.addWidget(self.side_start_record_button)
        layout.addWidget(finish_record_button)

        record_settings_button = QPushButton("记录设置")
        record_settings_button.clicked.connect(self.record_settings_dialog)
        record_settings_button.setFixedHeight(button_height)
        layout.addWidget(record_settings_button)

        # 新增：预定义设置按钮
        # 预定义变量
        self.preset_car_model = ""
        self.preset_tuning_parts = ""
        self.preset_evaluator = ""
        self.preset_condition = ""
        self.run_scheme = 0
        self.avy = 100
        self.best = 0
        preset_button = QPushButton("预定义设置")
        preset_button.clicked.connect(self.preset_settings_dialog)
        preset_button.setFixedHeight(button_height)
        layout.addWidget(preset_button)

        cueing_button = QPushButton("体感方案修改")
        cueing_button.clicked.connect(self.cueing_change)
        cueing_button.setFixedHeight(button_height)
        layout.addWidget(cueing_button)

        layout.addStretch()
        sidebar_content.setLayout(layout)

        self.dock.setWidget(sidebar_content)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)

        # 添加一个按钮来控制侧边栏显示/隐藏
        self.toggle_button = QPushButton("Toggle Sidebar", self)
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        self.statusBar().addPermanentWidget(self.toggle_button)

        self.setWindowTitle("Collapsible Sidebar Example")
        self.resize(1200, 600)

    def preset_settings_dialog(self):
        """预定义设置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("预定义设置")
        dialog.setMinimumWidth(400)

        # 创建布局
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # 车型预定义
        self.preset_car_model_edit = QLineEdit(self.preset_car_model)
        form_layout.addRow("车型预定义:", self.preset_car_model_edit)

        # 调校件预定义
        self.preset_tuning_edit = QLineEdit(self.preset_tuning_parts)
        form_layout.addRow("调校件预定义:", self.preset_tuning_edit)

        # 评价人预定义
        self.preset_evaluator_edit = QLineEdit(self.preset_evaluator)
        form_layout.addRow("评价人预定义:", self.preset_evaluator_edit)

        # 工况预定义（改为文本框输入）
        self.preset_condition_edit = QLineEdit(self.preset_condition)
        form_layout.addRow("工况预定义:", self.preset_condition_edit)

        layout.addLayout(form_layout)

        # 按钮布局
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(lambda: self.save_preset_settings(dialog))
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(dialog.reject)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.exec_()

    def cueing_change(self):
        dialog = cueing_change.CueingDialog()
        dialog.exec_()

    def save_preset_settings(self, dialog):
        """保存预定义设置"""
        self.preset_car_model = self.preset_car_model_edit.text().strip()
        self.preset_tuning_parts = self.preset_tuning_edit.text().strip()
        self.preset_evaluator = self.preset_evaluator_edit.text().strip()
        self.preset_condition = self.preset_condition_edit.text().strip()

        # 可选：保存到配置文件
        # self.save_preset_to_config()

        dialog.accept()
        QMessageBox.information(self, "成功", "预定义设置已保存！")

    def toggle_sidebar(self):
        self.dock.setVisible(not self.dock.isVisible())

    def create_analysis_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        # widget.setLayout(layout) # 这行写一遍就行，建议放在 addWidget 之后

        # 创建选项卡
        self.sub_tabs = QTabWidget()
        self.sub_tabs.addTab(pro_compare(), "复现方案对比")
        self.sub_tabs.currentChanged.connect(self.on_tab_changed)

        # 子页1：一阶起伏
        self.tab_bump = BumpWidget()
        self.sub_tabs.addTab(self.tab_bump, "一阶起伏")

        self.tab_center = CenterWidget()
        self.sub_tabs.addTab(self.tab_center, "中心区")

        layout.addWidget(self.sub_tabs)  # 这里之前是 tabs，会报错
        widget.setLayout(layout)

        self.analysis_page_widget = widget

        return widget

    def create_database_tab(self):
        return database_tab.create_database_tab()

    def record_settings_dialog(self):
        self.dialog = QDialog(self)
        self.dialog.setWindowTitle("记录设置")
        layout = QVBoxLayout()

        # 数据频率
        self.record_hz_combo = QComboBox()
        # self.record_hz_combo.addItem("1000HZ")
        self.record_hz_combo.addItem("400HZ")
        layout.addWidget(self.record_hz_combo)
        # # 自动记录
        # self.auto_record_button = QCheckBox("自动开始记录", self)
        # self.auto_record_button.setChecked(self.auto_record)
        # self.auto_record_button.stateChanged.connect(self.auto_recording)
        # layout.addWidget(self.auto_record_button)
        #
        # # 路段选择下拉框
        # self.road_segment_combo = QComboBox(self)
        #
        # # Store the current index before loading new items
        # current_index = self.road_segment_combo.currentIndex()
        #
        # try:
        #     # 读取JSON文件
        #     with open('road_segments.json', 'r', encoding='utf-8') as f:
        #         road_data = json.load(f)
        #         segments = road_data.get('segments', [])
        #
        #         # 添加路段选项到下拉框
        #         for segment in segments:
        #             self.road_segment_combo.addItem(segment['name'], userData=segment)
        #
        #         # 如果没有数据，添加默认选项
        #         if not segments:
        #             self.road_segment_combo.addItem("无可用路段")
        #
        #         # Restore the previous selection if it exists
        #         if hasattr(self, 'last_road_segment_index'):
        #             if self.last_road_segment_index < self.road_segment_combo.count():
        #                 self.road_segment_combo.setCurrentIndex(self.last_road_segment_index)
        #                 self.update_coordinates(self.last_road_segment_index)
        #         else:
        #             self.update_coordinates(0)
        #
        # except Exception as e:
        #     print(f"读取路段数据失败: {e}")
        #     self.road_segment_combo.addItem("加载路段失败")
        #
        # self.road_segment_combo.currentIndexChanged.connect(self.update_coordinates)
        # if self.auto_record == 2:
        #     print("选择路段")
        #     layout.addWidget(QLabel("选择路段:"))
        #     layout.addWidget(self.road_segment_combo)

        # 视频录制设置
        self.video_recording_button = QCheckBox("视频录制", self)
        self.video_recording_button.setChecked(self.is_video_recording)
        self.video_recording_button.stateChanged.connect(self.video_recording)
        layout.addWidget(self.video_recording_button)

        # 电控记录
        self.disusx_recording_button = QCheckBox("Disus_C记录", self)
        self.disusx_recording_button.setChecked(self.record_disusx)
        self.disusx_recording_button.stateChanged.connect(self.electrol_recording)
        layout.addWidget(self.disusx_recording_button)

        #车辆模型保存
        self.par_save_button = QCheckBox('.par',self)
        self.par_save_button.setChecked(self.is_par_save)
        self.par_save_button.stateChanged.connect(self.par_recording)
        layout.addWidget(self.par_save_button)

        # self.disusc_recording_button = QCheckBox("Disus_C记录", self)
        # self.disusc_recording_button.setChecked(self.record_disusc)
        # self.disusc_recording_button.stateChanged.connect(self.electrol_recording)
        # layout.addWidget(self.disusc_recording_button)
        select_save_path_button = QPushButton("数据保存路径")
        select_save_path_button.clicked.connect(lambda: self.select_save_folder())
        layout.addWidget(select_save_path_button)
        # 添加确认按钮
        confirm_button = QPushButton("确认")
        confirm_button.clicked.connect(self.dialog.close)
        layout.addWidget(confirm_button)

        self.dialog.setLayout(layout)
        self.dialog.exec_()

        # Store the current selection when dialog closes
        self.last_road_segment_index = self.road_segment_combo.currentIndex()

    # 当下拉框选项改变时，更新坐标变量
    def update_coordinates(self, index):
        print(index)
        segment_data = self.road_segment_combo.itemData(index)
        if segment_data:
            self.x_start_record_coordinate = segment_data['start_point']['x']
            self.y_start_record_coordinate = segment_data['start_point']['y']
            self.velocity_autorecord = segment_data['start_velocity']
            self.x_finish_record_coordinate = segment_data['end_point']['x']
            self.y_finish_record_coordinate = segment_data['end_point']['y']
            self.preset_condition_all = segment_data['record_name']
            print(f"坐标已更新: 起点({self.x_start_record_coordinate}, {self.y_start_record_coordinate}) "
                  f"终点({self.x_finish_record_coordinate}, {self.y_finish_record_coordinate})"
                  f"开始记录速度({self.velocity_autorecord})")

    # def on_enter_start_zone(self):
    #     # self.start_record_button.animateClick()
    #     self.start_record()
    #     print("进入起点区域")

    # def on_enter_end_zone(self):
    # self.finish_record_button.animateClick()
    # self.finish_record()
    # print("进入终点区域")

    def open_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("设置")
        layout = QVBoxLayout()

        # 添加 IMU 采样率设置
        imu_label = QLabel("IMU 采样率:")
        imu_spinbox = QSpinBox()
        imu_spinbox.setRange(1, 1000)  # 设置范围为 1 到 1000
        imu_spinbox.setValue(self.plot_sample_imu)
        layout.addWidget(imu_label)
        layout.addWidget(imu_spinbox)

        # 添加 Carsim 采样率设置
        carsim_label = QLabel("Carsim 采样率:")
        carsim_spinbox = QSpinBox()
        carsim_spinbox.setRange(1, 1000)  # 设置范围为 1 到 1000
        carsim_spinbox.setValue(self.plot_sample_carsim)
        layout.addWidget(carsim_label)
        layout.addWidget(carsim_spinbox)

        # 添加 Moog 采样率设置
        moog_label = QLabel("Moog 采样率:")
        moog_spinbox = QSpinBox()
        moog_spinbox.setRange(1, 1000)  # 设置范围为 1 到 1000
        moog_spinbox.setValue(self.plot_sample_moog)
        layout.addWidget(moog_label)
        layout.addWidget(moog_spinbox)
        # 添加 IMU 数据缓冲区大小设置
        imu_buffer_label = QLabel("IMU 数据缓冲区大小:")
        imu_buffer_spinbox = QSpinBox()
        imu_buffer_spinbox.setRange(1, 100000)  # 设置范围为 1 到 100000
        imu_buffer_spinbox.setValue(self.plot_buffer_imu)
        layout.addWidget(imu_buffer_label)
        layout.addWidget(imu_buffer_spinbox)
        # 添加 Carsim 数据缓冲区大小设置
        carsim_buffer_label = QLabel("Carsim 数据缓冲区大小:")
        carsim_buffer_spinbox = QSpinBox()
        carsim_buffer_spinbox.setRange(1, 100000)
        carsim_buffer_spinbox.setValue(self.plot_buffer_carsim)
        layout.addWidget(carsim_buffer_label)
        layout.addWidget(carsim_buffer_spinbox)
        # 添加 Moog 数据缓冲区大小设置
        moog_buffer_label = QLabel("Moog 数据缓冲区大小:")
        moog_buffer_spinbox = QSpinBox()
        moog_buffer_spinbox.setRange(1, 100000)
        moog_buffer_spinbox.setValue(self.plot_buffer_moog)
        layout.addWidget(moog_buffer_label)
        layout.addWidget(moog_buffer_spinbox)
        # 添加删除步长设置
        delete_step_label = QLabel("删除步长:")
        delete_step_spinbox = QSpinBox()
        delete_step_spinbox.setRange(1, 10000)
        delete_step_spinbox.setValue(self.plot_delete_step)
        layout.addWidget(delete_step_label)
        layout.addWidget(delete_step_spinbox)

        # 添加确认按钮
        confirm_button = QPushButton("确认")
        confirm_button.clicked.connect(
            lambda: self.save_settings(imu_spinbox.value(), carsim_spinbox.value(), moog_spinbox.value(),
                                       imu_buffer_spinbox.value(), carsim_buffer_spinbox.value(),
                                       moog_buffer_spinbox.value(), delete_step_spinbox.value(), dialog))
        layout.addWidget(confirm_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def save_settings(self, imu_sample, carsim_sample, moog_sample, imu_buffer, carsim_buffer, moog_buffer, delete_step,
                      dialog):
        self.plot_sample_imu = imu_sample  # 采样率
        self.plot_sample_carsim = carsim_sample
        self.plot_sample_moog = moog_sample
        self.plot_buffer_imu = imu_buffer  # 缓冲区大小
        self.plot_buffer_carsim = carsim_buffer
        self.plot_buffer_moog = moog_buffer
        self.plot_delete_step = delete_step  # 删除步长
        dialog.close()
        self.save_sampling_rates()  # 保存到配置文件

    def on_tab_changed(self, index):
        """选项卡切换时恢复按钮状态"""
        if index == 0:  # 假设信号输入配置是第一个选项卡
            self.signal_toggle_button.setChecked(self.signal_button_state)
            if self.signal_button_state:
                self.signal_toggle_button.setText("全部停止")
            else:
                self.signal_toggle_button.setText("全部启动")

    def save_sampling_rates(self):
        """保存采样率设置到配置文件"""
        config = {
            "plot_sample_imu": self.plot_sample_imu,
            "plot_sample_carsim": self.plot_sample_carsim,
            "plot_sample_moog": self.plot_sample_moog,
            "plot_buffer_imu": self.plot_buffer_imu,
            "plot_buffer_carsim": self.plot_buffer_carsim,
            "plot_buffer_moog": self.plot_buffer_moog,
            "plot_delete_step": self.plot_delete_step
        }
        with open("sampling_config.json", "w") as f:
            json.dump(config, f)

    def load_sampling_rates(self):
        """从配置文件加载采样率设置"""
        if os.path.exists("sampling_config.json"):
            try:
                with open("sampling_config.json", "r") as f:
                    config = json.load(f)
                    self.plot_sample_imu = config.get("plot_sample_imu", 1)
                    self.plot_sample_carsim = config.get("plot_sample_carsim", 1)
                    self.plot_sample_moog = config.get("plot_sample_moog", 1)
                    self.plot_buffer_imu = config.get("plot_buffer_imu", 10000)
                    self.plot_buffer_carsim = config.get("plot_buffer_carsim", 10000)
                    self.plot_buffer_moog = config.get("plot_buffer_moog", 10000)
                    self.plot_delete_step = config.get("plot_delete_step", 1000)
            except Exception as e:
                print(f"加载采样率配置时出错: {e}")

    def load_ui_state(self):
        default_state = {
            'plot_states': {},
            'algorithm': "MOOG洗出算法",
            'feeling_mode': "舒适方案",
            'workspace_variables': {}  # 新增：保存工作区变量
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    # 加载工作区变量
                    if 'workspace_variables' in state:
                        self.workspace_variables = state['workspace_variables']
                    return state
            except Exception as e:
                print(f"加载配置文件出错: {e}")
                return default_state

    def save_ui_state(self):
        state = {
            'plot_states': {plot_name: switch.isChecked() for plot_name, switch in self.plot_switches.items()},
            'algorithm': self.algo_combo.currentText(),
            #'feeling_mode': self.mode_combo.currentText()
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False)

    def init_workspace_panel(self):
        """初始化工作区面板"""
        self.workspace_panel = QGroupBox("工作区")
        layout = QVBoxLayout()

        # 变量表格
        self.workspace_table = QTableWidget()
        self.workspace_table.setColumnCount(2)
        self.workspace_table.setHorizontalHeaderLabels(["变量名", "值"])
        self.workspace_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)  # 允许双击编辑
        self.workspace_table.cellDoubleClicked.connect(self.handle_cell_double_clicked)  # 连接单元格双击事件
        self.workspace_table.cellChanged.connect(self.handle_cell_changed)  # 连接单元格编辑完成事件
        layout.addWidget(self.workspace_table)

        # 操作按钮（只保留“创建变量”和“删除变量”按钮）
        button_layout = QHBoxLayout()
        self.create_var_button = QPushButton("创建变量")
        self.create_var_button.clicked.connect(self.create_variable)
        button_layout.addWidget(self.create_var_button)

        self.delete_var_button = QPushButton("删除变量")
        self.delete_var_button.clicked.connect(self.delete_variable)
        button_layout.addWidget(self.delete_var_button)

        layout.addLayout(button_layout)
        self.workspace_panel.setLayout(layout)

        # 默认隐藏工作区面板
        self.workspace_panel.setVisible(False)

    def handle_cell_double_clicked(self, row, column):
        """处理单元格双击事件"""
        if column == 1:  # 双击的是变量值单元格
            var_name_item = self.workspace_table.item(row, 0)
            if var_name_item is None:
                return

            var_name = var_name_item.text().strip()
            var_value = self.workspace_variables.get(var_name)

            # 弹出变量编辑窗口
            editor = VariableEditor(var_name, var_value, self)
            if editor.exec_() == QDialog.Accepted:
                self.workspace_variables[var_name] = editor.var_value
                self.update_workspace_table()

    def handle_cell_changed(self, row, column):
        """处理单元格编辑完成事件"""
        if column == 0:  # 编辑的是变量名单元格
            try:
                var_name_item = self.workspace_table.item(row, 0)  # 变量名
                if var_name_item is None:
                    return

                new_var_name = var_name_item.text().strip()
                if not new_var_name:
                    QMessageBox.warning(self, "错误", "变量名不能为空！")
                    return

                # 获取旧的变量名
                old_var_name = list(self.workspace_variables.keys())[row]

                if old_var_name != new_var_name:  # 如果变量名被修改
                    if new_var_name in self.workspace_variables:  # 检查变量名是否已存在
                        QMessageBox.warning(self, "错误", "变量名已存在！")
                        var_name_item.setText(old_var_name)  # 恢复旧的变量名
                        return

                    # 更新变量名
                    var_value = self.workspace_variables.pop(old_var_name)
                    self.workspace_variables[new_var_name] = var_value
            except Exception as e:
                QMessageBox.warning(self, "错误", f"修改变量名失败: {e}")

    def sendData2PlatformControl(self, index, value):
        try:
            self.sendData_platform[index] = value

            data = struct.pack('i', *self.sendData_platform)
            # 发送二进制数据
            self.udp_socket.writeDatagram(
                data,
                QHostAddress("10.10.20.221"),
                3366  # 发送端口
            )
            print(self.sendData_platform)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"发送数据失败: {e}")

    def sendDataStartPoint2(self, value_x, value_y, value_yaw, value_z, value_height):
        try:
            self.sendData_startPoint[0] = value_x
            self.sendData_startPoint[1] = value_y
            self.sendData_startPoint[2] = value_yaw
            self.sendData_startPoint[3] = value_z
            self.sendData_startPoint[4] = value_height

            data = struct.pack('5f', *self.sendData_startPoint)
            # 发送二进制数据
            self.udp_socket.writeDatagram(
                data,
                QHostAddress("10.10.20.221"),
                3366  # 发送端口
            )
            print(self.sendData_startPoint)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"发送数据失败: {e}")

    def sendDataDriverData2(self, time_step, steering, throttle, pbk_con, clutch, gears, fbk_pdl, steerRate):
        try:
            self.sendData_DriverData[0] = time_step
            self.sendData_DriverData[1] = steering
            self.sendData_DriverData[2] = throttle
            self.sendData_DriverData[4] = pbk_con
            self.sendData_DriverData[5] = clutch
            self.sendData_DriverData[6] = gears
            self.sendData_DriverData[3] = fbk_pdl
            self.sendData_DriverData[7] = steerRate

            data = struct.pack('8d', *self.sendData_DriverData)
            # 发送二进制数据
            self.udp_socket.writeDatagram(
                data,
                QHostAddress("10.10.20.221"),
                10003  # 发送端口
            )
            # print(self.sendData_DriverData)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"发送数据失败: {e}")

    def sendDataPlatformOffset2(self, value_x, value_y, value_z):
        try:
            self.sendData_platformOffset[0] = value_x
            self.sendData_platformOffset[1] = value_y
            self.sendData_platformOffset[2] = value_z

            data = struct.pack('3f', *self.sendData_platformOffset)
            # 发送二进制数据
            self.udp_socket.writeDatagram(
                data,
                QHostAddress("10.10.20.221"),
                3366  # 发送端口
            )
            print(self.sendData_platformOffset)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"发送数据失败: {e}")

    def sendData2Moog(self, index, value):
        try:
            self.sendData[index] = value
            data = struct.pack('2i30f', *self.sendData)
            # data = struct.pack('i', *self.sendData)
            # 发送二进制数据
            self.udp_socket.writeDatagram(
                data,
                QHostAddress("127.0.0.1"),
                12346  # 发送端口
            )
            # print(self.sendData)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"发送数据失败: {e}")

    def sendData2camera(self, index, value):
        try:
            self.sendData_camera[index] = value
            data = struct.pack('2i', *self.sendData_camera)
            self.udp_socket.writeDatagram(
                data,
                QHostAddress("10.10.20.214"),
                4511
            )
            print(self.sendData_camera)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"发送数据失败: {e}")

    def update_workspace_table(self):
        """更新工作区表格"""
        self.workspace_table.blockSignals(True)  # 阻止信号触发
        self.workspace_table.setRowCount(len(self.workspace_variables))
        for row, (var_name, var_value) in enumerate(self.workspace_variables.items()):
            self.workspace_table.setItem(row, 0, QTableWidgetItem(var_name))
            if isinstance(var_value, np.ndarray):  # 如果是 numpy 数组
                self.workspace_table.setItem(row, 1, QTableWidgetItem(str(var_value.tolist())))
            else:  # 如果是标量
                self.workspace_table.setItem(row, 1, QTableWidgetItem(str(var_value)))
        self.workspace_table.blockSignals(False)  # 恢复信号触发

    def create_variable(self):
        """创建变量"""
        var_name, ok = QInputDialog.getText(self, "创建变量", "请输入变量名:")
        if ok and var_name:
            # 弹出变量编辑窗口
            editor = VariableEditor(var_name, 0, self)  # 默认值为 0
            if editor.exec_() == QDialog.Accepted:
                self.workspace_variables[var_name] = editor.var_value
                self.update_workspace_table()
        self.update_time_value_combos()  # 更新“时间”和“值”选择栏的选项

    def edit_variable(self):
        """编辑变量"""
        selected_row = self.workspace_table.currentRow()
        if selected_row >= 0:
            var_name = self.workspace_table.item(selected_row, 0).text()
            var_value = self.workspace_variables[var_name]

            # 弹出变量编辑窗口
            editor = VariableEditor(var_name, var_value, self)
            if editor.exec_() == QDialog.Accepted:
                self.workspace_variables[var_name] = editor.var_value
                self.update_workspace_table()

    def delete_variable(self):
        """删除变量"""
        selected_row = self.workspace_table.currentRow()
        if selected_row >= 0:
            var_name = self.workspace_table.item(selected_row, 0).text()
            del self.workspace_variables[var_name]
            self.update_workspace_table()
        self.update_time_value_combos()  # 更新“时间”和“值”选择栏的选项

    def rename_variable(self):
        """重命名变量"""
        selected_row = self.workspace_table.currentRow()
        if selected_row >= 0:
            old_name = self.workspace_table.item(selected_row, 0).text()
            new_name, ok = QInputDialog.getText(self, "重命名变量", f"重命名变量 {old_name}:", text=old_name)
            if ok and new_name:
                if new_name in self.workspace_variables:
                    QMessageBox.warning(self, "错误", "变量名已存在！")
                else:
                    self.workspace_variables[new_name] = self.workspace_variables.pop(old_name)
                    self.update_workspace_table()
        self.update_time_value_combos()  # 更新“时间”和“值”选择栏的选项

    def create_motion_display_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # 添加控制按钮
        control_layout = QHBoxLayout()
        self.run_button = QPushButton("运行")
        self.run_button.setCheckable(True)
        self.run_button.setChecked(True)
        self.run_button.clicked.connect(self.toggle_plotting)

        self.stop_button = QPushButton("暂停")
        self.stop_button.clicked.connect(self.stop_plotting)

        self.clear_button = QPushButton("清空")
        self.clear_button.clicked.connect(self.clear_plots)

        # 新增全开和全关按钮
        self.all_on_button = QPushButton("全开")
        self.all_on_button.clicked.connect(self.toggle_all_plots_on)
        self.all_off_button = QPushButton("全关")
        self.all_off_button.clicked.connect(self.toggle_all_plots_off)

        self.start_record_button = QPushButton("开始记录")
        self.start_record_button.clicked.connect(self.start_record)
        self.finish_record_button = QPushButton("结束记录")
        self.finish_record_button.clicked.connect(self.finish_record)

        self.record_settings_button = QPushButton("记录设置")
        self.record_settings_button.clicked.connect(self.record_settings_dialog)
        # 在控制按钮布局中添加“设置”按钮
        self.settings_button = QPushButton("动态绘图设置")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        self.axis_range_button = QPushButton("时间范围")
        self.axis_range_button.clicked.connect(self.open_axis_range_dialog)

        self.record_indicator = QLabel()
        self.record_indicator.setFixedSize(20, 20)

        # self.plot_lastrecord_button = QPushButton("显示记录")
        # self.plot_lastrecord_button.clicked.connect(self.plot_lastrecord)
        self.load_record_button = QPushButton("读取记录")
        self.load_record_button.clicked.connect(self.load_record)
        self.jsmnq_plot_button = QPushButton("jsmnq_plot")
        self.jsmnq_plot_button.clicked.connect(self.run_jsmnq_plot)
        self.compare_csv_plot_button = QPushButton("csv数据对比")
        self.compare_csv_plot_button.clicked.connect(self.run_compare_csv)
        # === 新增报警控制部分 ===
        self.alarm_toggle = QPushButton("报警开关")
        self.alarm_toggle.setCheckable(True)
        self.alarm_toggle.setChecked(False)
        self.alarm_toggle.clicked.connect(self.toggle_alarm)

        self.scenario_combo = QComboBox()
        self.scenario_combo.addItems(["单移线", "转弯", "中心区", "一阶起伏", "自定义"])
        self.scenario_combo.currentIndexChanged.connect(self.change_scenario)

        self.custom_threshold_button = QPushButton("设置阈值")
        self.custom_threshold_button.clicked.connect(self.open_custom_threshold_dialog)

        control_layout.addWidget(self.run_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.clear_button)
        control_layout.addWidget(self.all_on_button)  # 添加全开按钮
        control_layout.addWidget(self.all_off_button)  # 添加全关按钮
        control_layout.addWidget(self.axis_range_button)
        control_layout.addWidget(self.start_record_button)
        control_layout.addWidget(self.finish_record_button)
        control_layout.addWidget(self.record_indicator)
        control_layout.addWidget(self.record_settings_button)
        control_layout.addWidget(self.settings_button)
        # control_layout.addWidget(self.plot_lastrecord_button)
        control_layout.addWidget(self.load_record_button)

        control_layout.addWidget(self.jsmnq_plot_button)
        control_layout.addWidget(self.compare_csv_plot_button)
        control_layout.addWidget(QLabel("报警:"))
        control_layout.addWidget(self.alarm_toggle)
        control_layout.addWidget(QLabel("工况:"))
        control_layout.addWidget(self.scenario_combo)
        control_layout.addWidget(self.custom_threshold_button)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        # 添加显示控制开关
        switch_layout = QHBoxLayout()
        self.plot_switches = {}
        plot_configs = {
            'pos_x': '位移X', 'pos_y': '位移Y', 'pos_z': '位移Z',
            'vel_x': '速度X', 'vel_y': '速度Y', 'vel_z': '速度Z',
            'acc_x': '加速度X', 'acc_y': '加速度Y', 'acc_z': '加速度Z',
            'ang_x': '角速度X', 'ang_y': '角速度Y', 'ang_z': '角速度Z',
            'roll': 'Roll', 'pitch': 'Pitch', 'yaw': 'Yaw',
            'ang_acc_x': '角加速度X', 'ang_acc_y': '角加速度Y', 'ang_acc_z': '角加速度Z',
            'steering_angle': '方向盘转角',  # 新增
            'throttle': '油门开度',  # 新增
            'pbk_con': '制动主缸压力',  # 新增
            'steering_speed': '方向盘转速',  # 新增
            'CmpRD_L1': '运行速度L1',
            'CmpRD_L2': '运行速度L2',
            'CmpRD_R1': '运行速度R1',
            'CmpRD_R2': '运行速度R2',
        }

        for key, title in plot_configs.items():
            switch = QPushButton(title)
            switch.setCheckable(True)
            switch.setChecked(True)  # 默认设置为选中状态
            switch.clicked.connect(lambda checked, k=key: self.toggle_plot_visibility(k))
            self.plot_switches[key] = switch
            switch_layout.addWidget(switch)

        layout.addLayout(switch_layout)

        # 创建图表容器
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_widget.setLayout(self.grid_layout)
        layout.addWidget(self.grid_widget)

        # 初始化图表
        self.plots = {}
        self.curves = {}
        self.plot_widgets = {}  # 存储图表和对应的GroupBox

        # 创建所有图表
        for name, title in plot_configs.items():
            group = QGroupBox(title)
            group_layout = QVBoxLayout()

            plot = pg.PlotWidget()
            plot.setBackground('w')
            plot.showGrid(x=True, y=True)

            plot.setLabel('bottom', '时间 (s)', color='k')
            # 标题显示数值
            # if title == '方向盘转角':
            #     plot.setTitle(f'方向盘转角：{self.signal_steer_angle:+.1f}度', color='k')
            #     plot.setLabel('left', 'Steer_SW(deg)', color='k')
            # else:
            plot.setTitle(title, color='k')
            plot.setLabel('left', self.get_unit(name), color='k')
            plot.setXRange(0, 10)
            plot.getAxis('left').setTextPen('k')
            plot.getAxis('bottom').setTextPen('k')
            plot.getAxis('left').setPen('k')
            plot.getAxis('bottom').setPen('k')

            if name.startswith('pos') or name.startswith('vel') or name.startswith('acc') or name.startswith(
                    'ang') or name.startswith('roll') or name.startswith('pitch') or name.startswith('yaw'):
                # 添加图例
                legend = plot.addLegend()
                legend.setBrush((255, 255, 255, 150))  # 设置图例背景为半透明白色
                legend.setLabelTextSize('8pt')  # 设置图例字体大小为8pt

                # 延迟设置图例位置
                # QTimer.singleShot(100, lambda p=plot, l=legend: l.setPos(p.width() - l.size().width() - 10, 10))
                legend.anchor = (0, 0)  # 右上角

            # 为需要报警的图表添加报警标记
            if name in ['vel_x', 'steering_angle', 'steering_speed']:
                # 创建报警指示器 - 使用中央位置
                alarm_indicator = pg.TextItem(text='', color=(255, 0, 0),
                                              anchor=(0.5, 0.5))  # 锚点设置为中央
                # 设置大字体和粗体
                font = QtGui.QFont()
                font.setPointSize(24)  # 增大字体
                font.setBold(True)
                alarm_indicator.setFont(font)

                # 设置高Z值确保在最上层
                alarm_indicator.setZValue(100)

                # 添加到图表
                plot.addItem(alarm_indicator)
                self.alarm_indicators[name] = alarm_indicator

                # 初始位置设为图表中心
                alarm_indicator.setPos(0, 0)

            # 为每个图表创建3个曲线，并设置图例名称
            self.curves[name] = {
                'input': plot.plot(pen=pg.mkPen(color=(0, 0, 255), width=1.5), name='CARSIM'),  # 红色，宽度为2
                'moog': plot.plot(pen=pg.mkPen(color=(0, 255, 0), width=1.5), name='MOOG'),  # 绿色，宽度为2
                'imu': plot.plot(pen=pg.mkPen(color=(255, 0, 0), width=1.5), name='IMU')  # 蓝色，宽度为2
            }

            self.plots[name] = plot

            group_layout.addWidget(plot)
            group.setLayout(group_layout)
            self.plot_widgets[name] = group
        # 加载图表状态
        self.load_plot_state()

        # 初始化显示图表布局
        self.update_plot_layout()

        tab.setLayout(layout)
        return tab

    # === 新增报警相关方法 ===
    def toggle_alarm(self, checked):
        """切换报警开关状态"""
        self.alarm_enabled = checked
        self.alarm_toggle.setText("报警开启" if checked else "报警关闭")

        # 当关闭报警时清除所有报警指示器
        if not checked:
            for name in ['vel_x', 'steering_angle', 'steering_speed']:
                if name in self.alarm_indicators:
                    self.alarm_indicators[name].setText('')

        # 当开启报警时，强制更新一次图表
        if checked:
            self.update_plots()

    def change_scenario(self, index):
        """切换当前工况"""
        self.current_scenario = self.scenario_combo.currentText()

    def open_custom_threshold_dialog(self):
        """打开自定义阈值设置对话框"""
        dialog = QDialog()
        dialog.setWindowTitle("自定义阈值设置")
        layout = QFormLayout()

        # 为需要报警的信号创建输入框
        self.custom_inputs = {}
        for signal in ['vel_x', 'steering_angle', 'steering_speed']:
            min_label = QLabel(f"{signal} 最小值:")
            min_input = QLineEdit()
            min_input.setPlaceholderText("最小值")

            max_label = QLabel(f"{signal} 最大值:")
            max_input = QLineEdit()
            max_input.setPlaceholderText("最大值")

            # 加载当前值（如果有）
            if signal in self.custom_thresholds:
                min_input.setText(str(self.custom_thresholds[signal][0]))
                max_input.setText(str(self.custom_thresholds[signal][1]))

            layout.addRow(min_label, min_input)
            layout.addRow(max_label, max_input)

            self.custom_inputs[signal] = (min_input, max_input)

        # 确定和取消按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)

        layout.addRow(btn_box)
        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            # 保存自定义阈值
            self.custom_thresholds = {}
            for signal, (min_input, max_input) in self.custom_inputs.items():
                try:
                    min_val = float(min_input.text()) if min_input.text() else None
                    max_val = float(max_input.text()) if max_input.text() else None

                    if min_val is not None and max_val is not None:
                        self.custom_thresholds[signal] = (min_val, max_val)
                except ValueError:
                    QMessageBox.warning(self, "输入错误", f"{signal} 的阈值必须是数字")

            # 更新工况阈值
            self.scenario_thresholds["自定义"] = self.custom_thresholds

    def check_alarm(self, channel, value):
        """检查值是否超出阈值并返回报警状态"""
        if not self.alarm_enabled:
            return False

        # 获取当前阈值
        thresholds = self.scenario_thresholds.get(self.current_scenario, {})

        if channel not in thresholds:
            return False

        min_val, max_val = thresholds[channel]

        # 特殊处理中心区的方向盘转速
        if self.current_scenario == "中心区" and channel == "steering_speed":
            abs_value = abs(value)
            return abs_value < min_val or abs_value > max_val

        # 其他情况的标准检查
        return value < min_val or value > max_val

    def run_jsmnq_plot(self):
        # try:
        pass
        #jsmnq_plot()
        # except Exception as e:
        #     QMessageBox.warning(self, "错误", f"运行 jsmnq_plot.py 失败: {e}")

    def run_compare_csv(self):
        self.second_window = CompareCsv.CSVPlotter()
        self.second_window.show()

    def open_axis_range_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("坐标区域设置")
        layout = QVBoxLayout()

        # 添加 X 轴范围设置
        x_range_label = QLabel("X 轴范围 (秒):")
        x_range_min_input = QLineEdit()
        x_range_min_input.setPlaceholderText("最小值")
        x_range_max_input = QLineEdit()
        x_range_max_input.setPlaceholderText("最大值")
        x_range_layout = QHBoxLayout()
        x_range_layout.addWidget(x_range_min_input)
        x_range_layout.addWidget(x_range_max_input)
        layout.addWidget(x_range_label)
        layout.addWidget(x_range_min_input)
        layout.addWidget(x_range_max_input)

        # 添加确认按钮
        confirm_button = QPushButton("确认")
        confirm_button.clicked.connect(
            lambda: self.apply_axis_range(
                x_range_min_input.text(), x_range_max_input.text(),
                dialog
            )
        )
        layout.addWidget(confirm_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def apply_axis_range(self, x_min, x_max, dialog):
        try:
            # 将输入的字符串转换为浮点数
            x_min = float(x_min)
            x_max = float(x_max)
            # 遍历所有图窗，设置X轴和Y轴范围
            for plot in self.plots.values():
                plot.setXRange(x_min, x_max)

            dialog.close()  # 关闭对话框
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的数字！")

    def create_signal_input_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # 创建一个水平布局，用于放置算法选择、Control Command 输入和“一键启动”按钮
        top_layout = QHBoxLayout()

        # 算法选择区域
        algo_group = QGroupBox("算法选择")
        algo_group.setFixedHeight(150)  # 设置固定高度为100
        algo_layout = QVBoxLayout()  # 使用垂直布局
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["MOOG洗出算法", "PVA控制", "自研洗出算法"])
        saved_algo = self.ui_state.get('algorithm', "MOOG洗出算法")
        index = self.algo_combo.findText(saved_algo)
        if index >= 0:
            self.algo_combo.setCurrentIndex(index)
        algo_layout.addWidget(self.algo_combo)
        algo_group.setLayout(algo_layout)

        # 添加算法选择组框到水平布局
        top_layout.addWidget(algo_group)

        # 添加 Control Command 组框
        control_command_group = QGroupBox("Control Command")
        control_command_group.setFixedHeight(150)  # 设置固定高度为100
        control_command_layout = QVBoxLayout()

        # 添加输入框
        self.control_command_input = QLineEdit()
        self.control_command_input.setPlaceholderText("输入控制命令值")
        self.control_command_input.returnPressed.connect(self.handle_control_command_input)
        self.control_command_0_button = QPushButton("0-Off")
        self.control_command_1_button = QPushButton("1-Disengage")
        self.control_command_2_button = QPushButton("2-Consent")
        self.control_command_3_button = QPushButton("3-ReadyForTraining")
        self.control_command_4_button = QPushButton("4-Engage")
        self.control_command_5_button = QPushButton("5-Hold")
        self.control_command_6_button = QPushButton("6-Reset")
        self.control_command_0_button.clicked.connect(lambda: self.sendData2PlatformControl(0, 0))
        self.control_command_1_button.clicked.connect(lambda: self.sendData2PlatformControl(0, 1))
        self.control_command_2_button.clicked.connect(lambda: self.sendData2PlatformControl(0, 2))
        self.control_command_3_button.clicked.connect(lambda: self.sendData2PlatformControl(0, 3))
        self.control_command_4_button.clicked.connect(lambda: self.sendData2PlatformControl(0, 4))
        self.control_command_5_button.clicked.connect(lambda: self.sendData2PlatformControl(0, 5))
        self.control_command_6_button.clicked.connect(lambda: self.sendData2PlatformControl(0, 6))
        # 设置默认值为0
        self.control_command_input.setText("0")  # 设置默认值为0

        control_command_layout.addWidget(self.control_command_input)

        # 添加提示信息
        # control_command_label = QLabel("0-Off，1-Disengage，2-Consent，3-ReadyForTraining，4-Engage，5-Hold，6-Reset")
        control_command_button_layout = QHBoxLayout()
        control_command_button_layout.addWidget(self.control_command_0_button)
        control_command_button_layout.addWidget(self.control_command_1_button)
        control_command_button_layout.addWidget(self.control_command_2_button)
        control_command_button_layout.addWidget(self.control_command_3_button)
        control_command_button_layout.addWidget(self.control_command_4_button)
        control_command_button_layout.addWidget(self.control_command_5_button)
        control_command_button_layout.addWidget(self.control_command_6_button)

        control_command_layout.addLayout(control_command_button_layout)

        control_command_group.setLayout(control_command_layout)

        # 添加 Control Command 组框到水平布局
        top_layout.addWidget(control_command_group)

        # 添加“一键启动”按钮
        self.one_click_start_button = QPushButton("一键启动")
        self.one_click_start_button.clicked.connect(self.one_click_start)
        top_layout.addWidget(self.one_click_start_button)

        # 添加“一键关闭”按钮
        self.one_click_stop_button = QPushButton("一键关闭")
        self.one_click_stop_button.clicked.connect(self.one_click_stop)
        top_layout.addWidget(self.one_click_stop_button)

        # 将水平布局添加到主布局
        layout.addLayout(top_layout)

        # 信号类型选择和绘图窗口
        signal_plot_layout = QHBoxLayout()

        # 信号类型选择
        self.signal_group = QGroupBox("信号类型")
        signal_layout = QVBoxLayout()
        self.signal_combo = QComboBox()
        self.signal_combo.addItems(["函数信号", "自定义信号"])
        signal_layout.addWidget(self.signal_combo)

        # 添加信号个数选择栏
        self.quantity_combo = QComboBox()
        self.quantity_combo.addItems(["1", "2", "3", "4", "5", "6"])
        self.quantity_combo.setVisible(False)  # 默认隐藏
        signal_layout.addWidget(self.quantity_combo)

        self.signal_group.setLayout(signal_layout)
        signal_plot_layout.addWidget(self.signal_group)

        # 将信号类型和绘图窗口添加到主布局
        layout.addLayout(signal_plot_layout)

        # 创建一个垂直布局，用于放置“工作区”和“信号参数”
        workspace_param_layout = QVBoxLayout()

        # 添加“工作区”面板
        workspace_param_layout.addWidget(self.workspace_panel)

        # 信号参数配置区域
        self.param_group = QGroupBox("信号参数")
        self.param_button_layout = QVBoxLayout()
        self.param_layout = QHBoxLayout()
        self.param_button_layout.addLayout(self.param_layout)
        self.param_group.setLayout(self.param_button_layout)
        self.signal_param_widgets = []  # 存储参数窗口
        workspace_param_layout.addWidget(self.param_group)

        # 设置“工作区”和“信号参数”的拉伸比例
        workspace_param_layout.setStretch(0, 2)  # 工作区占 2 份
        workspace_param_layout.setStretch(1, 1)  # 信号参数占 1 份

        # 将“工作区”和“信号参数”布局添加到主布局
        layout.addLayout(workspace_param_layout)

        # 将发送信号按钮改为开关按钮
        self.signal_toggle_button = QPushButton("全部启动")
        self.signal_toggle_button.setCheckable(True)  # 设置为可切换的按钮
        self.signal_toggle_button.setChecked(False)  # 初始状态为关闭
        self.signal_toggle_button.clicked.connect(self.toggle_all_signal)
        # self.param_button_layout.addWidget(self.signal_toggle_button)

        # 设置初始可见性
        self.signal_group.setVisible(True)
        self.param_group.setVisible(True)

        # 连接信号槽
        self.algo_combo.currentTextChanged.connect(lambda x: self.handle_signal_input("algo", x))
        self.signal_combo.currentTextChanged.connect(lambda x: self.handle_signal_input("signal", x))
        self.quantity_combo.currentTextChanged.connect(lambda x: self.handle_signal_input("quantity", x))

        # 初始化界面状态
        self.handle_signal_input("algo", saved_algo)
        if saved_algo == "PVA控制":
            self.signal_combo.setCurrentText("函数信号")  # 将默认信号类型改为“函数信号”
            self.handle_signal_input("signal", "函数信号")

        tab.setLayout(layout)
        return tab

    def handle_control_command_input(self):
        """处理 Control Command 输入框的回车事件"""
        try:
            value = int(self.control_command_input.text())
            if 0 <= value <= 6:
                # 将整数打包为二进制数据
                # data = struct.pack('!i', value)

                # 发送二进制数据
                # self.udp_socket.writeDatagram(
                #     data,
                #     QHostAddress("127.0.0.1"),
                #     12346  # 发送端口
                # )
                self.sendData2PlatformControl(0, value)
                # print(f"Control Command 值已发送: {value}")
            else:
                QMessageBox.warning(self, "错误", "请输入 0 到 6 之间的整数")
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的整数")

    def handle_signal_input(self, input_type, value=None):
        if input_type == "algo":
            self.signal_group.setVisible(value == "PVA控制")
            self.param_group.setVisible(value == "PVA控制")
            if value != "PVA控制":
                self.workspace_panel.setVisible(False)
            if value == "MOOG洗出算法":
                self.operation_record_group.setVisible(True)

        elif input_type == "signal":
            is_function_signal = value == "函数信号"
            is_custom_signal = value == "自定义信号"  # 新增：检查是否为自定义信号
            self.quantity_combo.setVisible(is_function_signal or is_custom_signal)  # 函数信号或自定义信号时显示信号个数选择栏
            self.workspace_panel.setVisible(is_custom_signal)  # 自定义信号时显示工作区面板
            if is_function_signal or is_custom_signal:
                self.update_signal_params(int(self.quantity_combo.currentText()))
                self.update_time_value_combos()  # 更新“时间”和“值”选择栏的选项
            else:
                self.clear_signal_param_widgets()
        elif input_type == "quantity":
            if self.signal_combo.currentText() == "函数信号" or self.signal_combo.currentText() == "自定义信号":
                self.update_signal_params(int(value))

    def update_signal_params(self, num_signals):
        self.clear_signal_param_widgets()  # 清空现有的参数窗口

        # 根据信号类型决定显示哪些参数
        signal_type = self.signal_combo.currentText()

        if signal_type == "自定义信号":
            # 自定义信号时，增加“时间”和“值”选择栏
            for i in range(num_signals):
                group = QGroupBox(f"信号 {i + 1}")
                layout = QGridLayout()

                # 添加类型选择下拉栏
                type_combo = QComboBox()
                type_combo.addItems([
                    "加速度x", "加速度y", "加速度z", "角加速度x", "角加速度y", "角加速度z",
                    "位移x", "位移y", "位移z", "角度x(Roll)", "角度y(Pitch)", "角度z(Yaw)",
                    "速度x", "速度y", "速度z", "角速度x", "角速度y", "角速度z"
                ])
                layout.addWidget(type_combo, 0, 0, 1, 2)

                # 添加“时间”选择栏
                time_label = QLabel("时间:")
                time_combo = QComboBox()  # 初始化 time_combo
                time_combo.setObjectName("time_combo")
                self.update_time_value_combos()  # 更新“时间”和“值”选择栏的选项
                layout.addWidget(time_label, 1, 0)
                layout.addWidget(time_combo, 1, 1)

                # 添加“值”选择栏
                value_label = QLabel("值:")
                value_combo = QComboBox()  # 初始化 value_combo
                value_combo.setObjectName("value_combo")
                self.update_time_value_combos()  # 更新“时间”和“值”选择栏的选项
                layout.addWidget(value_label, 2, 0)
                layout.addWidget(value_combo, 2, 1)

                # 添加“gain”输入框
                gain_label = QLabel("增益 (gain):")
                gain_input = QLineEdit()
                gain_input.setPlaceholderText("输入增益值")
                gain_input.setText("1")  # 默认值为1
                layout.addWidget(gain_label, 3, 0)
                layout.addWidget(gain_input, 3, 1)

                # 启动按钮
                start_button = QPushButton('启动信号')
                start_button.setCheckable(True)
                start_button.setChecked(False)

                # start_button.clicked.connect(self.toggle_signal)
                start_button.clicked.connect(lambda checked, idx=i: self.toggle_signal(idx))
                layout.addWidget(start_button)

                group.setLayout(layout)
                self.param_layout.addWidget(group)
                self.signal_param_widgets.append(group)
                self.param_button_layout.addWidget(self.signal_toggle_button)
                self.update_time_value_combos()  # 更新“时间”和“值”选择栏的选项
        elif signal_type == "函数信号":
            # 函数信号时，保留原有的参数输入框
            params = [
                ("振幅", "输入振幅", "0.1"),
                ("周期", "输入周期", "1"),
                ("偏置", "输入偏置", "0"),
                ("过渡时间", "输入相位", "0")
            ]

            for i in range(num_signals):
                group = QGroupBox(f"信号 {i + 1}")
                layout = QGridLayout()

                # 添加类型选择下拉栏
                type_combo = QComboBox()
                type_combo.addItems([
                    "加速度x", "加速度y", "加速度z", "角加速度x", "角加速度y", "角加速度z",
                    "位移x", "位移y", "位移z", "角度x(Roll)", "角度y(Pitch)", "角度z(Yaw)",
                    "速度x", "速度y", "速度z", "角速度x", "角速度y", "角速度z"
                ])
                layout.addWidget(type_combo, 0, 0, 1, 2)

                # 添加波形选择下拉栏
                waveform_combo = QComboBox()
                waveform_combo.addItems(["Sine", "Square", "Sawtooth", "Value"])
                waveform_combo.setObjectName("waveform_combo")
                layout.addWidget(waveform_combo, 1, 0, 1, 2)

                # 添加原有的参数输入框（带默认值）
                self.signal_input_fields = []  # 保存输入框引用
                for j, (label_text, placeholder, default_value) in enumerate(params):
                    layout.addWidget(QLabel(label_text), j + 2, 0)
                    input_field = QLineEdit()
                    input_field.setPlaceholderText(placeholder)
                    input_field.setText(default_value)  # 设置默认值
                    self.signal_input_fields.append(input_field)
                    layout.addWidget(input_field, j + 2, 1)

                # 添加启动按钮
                start_button = QPushButton('启动信号')
                start_button.setCheckable(True)
                start_button.setChecked(False)
                start_button.clicked.connect(lambda checked, idx=i: self.toggle_signal(idx))
                layout.addWidget(start_button, len(params) + 2, 0, 1, 2)

                group.setLayout(layout)
                self.param_layout.addWidget(group)
                self.param_button_layout.addWidget(self.signal_toggle_button)
                self.signal_param_widgets.append(group)

    def update_time_value_combos(self):
        # """更新‘时间’和‘值’选择栏的选项"""
        # # 清空现有的选项
        # if hasattr(self, 'time_combo'):
        #     self.time_combo.clear()
        # if hasattr(self, 'value_combo'):
        #     self.value_combo.clear()
        #
        # # 从工作区变量中获取变量名
        # variable_names = list(self.workspace_variables.keys())
        #
        # # 添加变量名到选择栏
        # for var_name in variable_names:
        #     if hasattr(self, 'time_combo'):
        #         self.time_combo.addItem(var_name)
        #     if hasattr(self, 'value_combo'):
        #         self.value_combo.addItem(var_name)

        """更新‘时间’和‘值’选择栏的选项"""
        # 遍历所有信号参数窗口
        for signal_widget in self.signal_param_widgets:
            # 查找“时间”和“值”下拉栏
            time_combo = signal_widget.findChild(QComboBox, "time_combo")
            value_combo = signal_widget.findChild(QComboBox, "value_combo")

            if time_combo is not None and value_combo is not None:
                # 清空现有的选项
                time_combo.clear()
                value_combo.clear()

                # 从工作区变量中获取变量名
                variable_names = list(self.workspace_variables.keys())

                # 添加变量名到选择栏
                for var_name in variable_names:
                    time_combo.addItem(var_name)
                    value_combo.addItem(var_name)

    def clear_signal_param_widgets(self):
        """清空信号参数窗口"""
        for widget in self.signal_param_widgets:
            widget.setParent(None)  # 从布局中移除窗口
            widget.deleteLater()  # 销毁窗口
        self.signal_param_widgets.clear()  # 清空存储的窗口

    def create_feeling_mode_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        mode_group = QGroupBox("体感方案选择")
        mode_layout = QVBoxLayout()

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["舒适方案", "赛道方案", "极限方案", "自定义方案"])

        # 设置保存的体感方案
        saved_mode = self.ui_state.get('feeling_mode', "舒适方案")
        index = self.mode_combo.findText(saved_mode)
        if index >= 0:
            self.mode_combo.setCurrentIndex(index)

        self.mode_combo.currentIndexChanged.connect(self.mode_changed)
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)

        # 方案参数显示区域
        self.param_display = QGroupBox("方案参数")
        param_layout = QVBoxLayout()
        self.param_label = QLabel()
        param_layout.addWidget(self.param_label)
        self.param_display.setLayout(param_layout)

        layout.addWidget(mode_group)
        layout.addWidget(self.param_display)

        # 应用按钮
        apply_button = QPushButton("应用方案")
        apply_button.clicked.connect(self.apply_mode)
        layout.addWidget(apply_button)

        # 初始化显示参数
        self.mode_changed()

        tab.setLayout(layout)
        return tab

    def create_virtual_tuning_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)  # 主水平布局

        # 左侧大区域（垂直布局，包含虚拟调校和场景设置）
        left_side_layout = QVBoxLayout()

        # 1. 虚拟调校设置GroupBox
        tuning_group = QGroupBox("虚拟调校设置")
        tuning_layout = QHBoxLayout()  # 水平布局，内部左右两部分

        # 左侧区域 - 车型选择和图片
        left_tuning_layout = QVBoxLayout()

        # 车型选择按钮
        self.car_menu = QMenu()
        self.select_car_button = QPushButton("选择车型")
        self.select_car_button.setMenu(self.car_menu)

        for groupName in vehicleNames.keys():
            custom_button = CustomGroupPushButton(groupName)
            widget_action = QWidgetAction(self.car_menu)
            widget_action.setDefaultWidget(custom_button)
            self.car_menu.addAction(widget_action)
            subMenu = QMenu()
            carNames = vehicleNames[groupName]
            for carName in carNames:
                subButton = CustomCarPushButton(carName, hasMenu=False, topWidget=self.select_car_button)
                subButton.clicked.connect(self.onCarChange)
                subWidgetAction = QWidgetAction(subMenu)
                subWidgetAction.setDefaultWidget(subButton)
                subMenu.addAction(subWidgetAction)
            custom_button.setMenu(subMenu)

        left_tuning_layout.addWidget(self.select_car_button, alignment=Qt.AlignTop)
        # 车辆图片
        self.carImage = QLabel()
        self.carImage.setScaledContents(True)
        self.carImage.setMaximumSize(200, 120)

        # 初始化车辆信息
        carInfo = carsim.GetBlueLink('#BlueLink2')
        print(carInfo)
        carName = carInfo[1]
        carImagePath = vehicleImagePath[carName]
        image = QImage(carImagePath)
        pixmap = QPixmap.fromImage(image).scaled(200, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.carImage.setPixmap(pixmap)
        self.select_car_button.setText(carName)
        self.carName = carName
        left_tuning_layout.addWidget(self.carImage, alignment=Qt.AlignTop)
        left_tuning_layout.addStretch(1)

        # 右侧区域 - 控制按钮和参数设置
        right_tuning_layout = QVBoxLayout()

        # 顶部按钮行
        button_row = QHBoxLayout()
        self.runButton = QPushButton("运行")
        self.runButton.clicked.connect(self.RunDspace)
        button_row.addWidget(self.runButton)

        self.openButton = QPushButton("打开simulink")
        self.openButton.clicked.connect(self.OpenSimulink)
        button_row.addWidget(self.openButton)

        self.buildButton = QPushButton("编译")
        self.buildButton.clicked.connect(self.BuildDspace)
        button_row.addWidget(self.buildButton)

        right_tuning_layout.addLayout(button_row)


        # 参数设置表单
        self.form_layout = QFormLayout()
        self.form_layout_1 = QFormLayout()

        self.UpdateTuningParam()

        self.form_layout_2 = QHBoxLayout()
        self.form_layout_2.addLayout(self.form_layout)
        self.form_layout_2.addLayout(self.form_layout_1)
        right_tuning_layout.addLayout(self.form_layout_2)

        button_container = QHBoxLayout()
        button_container.addStretch(1)  # 将按钮推到右侧

        # rename_button = QCheckBox("文件夹命名%%", self)
        # rename_button.setChecked(self.is_rename_folder_name)
        # rename_button.stateChanged.connect(self.rename_folder_name)
        # button_container.addWidget(rename_button)
        #
        # # 方案记录
        # self.recordApplyButton = QPushButton("方案")
        # self.recordApplyButton.clicked.connect(self.recordApplyTuningParam)
        #
        # # 重置
        # self.resetApplyButton = QPushButton("重置")
        # self.resetApplyButton.clicked.connect(self.resetApplyTuningParam)
        #
        # # 应用按钮
        # self.tuningApplyButton = QPushButton("应用")
        # self.tuningApplyButton.clicked.connect(self.ApplyTuningParam)
        # button_container.addWidget(self.recordApplyButton)
        # button_container.addWidget(self.resetApplyButton)
        # button_container.addWidget(self.tuningApplyButton)
        self.condition_combo = QComboBox(self)
        with open('condition.json', 'r', encoding='utf-8') as f:
            condition = json.load(f)
            self.condition_info = condition
            segments = list(condition.keys())

            # 添加工况选项到下拉框
            for segment in segments:
                self.condition_combo.addItem(segment)
        self.condition_combo.currentIndexChanged.connect(self.condition_choose)
        button_container.addWidget(self.condition_combo)
        self.clearButton = QPushButton("清除缓存")
        self.clearButton.clicked.connect(self.clear)

        self.viewOfflineDataBtn = QPushButton("数据查看")
        self.viewOfflineDataBtn.clicked.connect(self.viewOfflineData)

        self.UpdateTuningParamButton = QPushButton("重新读取样件列表")
        self.UpdateTuningParamButton.clicked.connect(self.UpdateTuningParam)
        button_container.addWidget(self.clearButton)
        button_container.addWidget(self.viewOfflineDataBtn)
        button_container.addWidget(self.UpdateTuningParamButton)
        # 将按钮容器添加到主布局
        right_tuning_layout.addLayout(button_container)

        # 将左右布局添加到调校组
        tuning_layout.addLayout(left_tuning_layout, stretch=1)
        tuning_layout.addLayout(right_tuning_layout, stretch=2)
        tuning_group.setLayout(tuning_layout)

        # 2. 场景设置GroupBox（新增部分）
        scenario_group = QGroupBox("场景设置")
        scenario_layout = QVBoxLayout()
        # 从JSON加载场景数据
        self.scenario_data = self.load_scenario_data()
        # 地图选择下拉框
        map_layout = QHBoxLayout()
        map_label = QLabel("地图:")
        self.map_combo = QComboBox()
        # 从JSON数据填充地图下拉框
        for map_info in self.scenario_data["maps"]:
            self.map_combo.addItem(map_info["name"], userData=map_info)

        # 当地图选择变化时更新起点列表
        self.map_combo.currentIndexChanged.connect(self.update_start_points)

        map_layout.addWidget(map_label)
        map_layout.addWidget(self.map_combo)
        map_layout.addStretch(1)

        # 起点选择下拉框
        # 起点选择下拉框
        start_point_layout = QHBoxLayout()
        start_point_label = QLabel("起点:")
        self.start_point_combo = QComboBox()
        start_point_layout.addWidget(start_point_label)
        start_point_layout.addWidget(self.start_point_combo)
        start_point_layout.addStretch(1)

        # 坐标显示
        position_layout = QHBoxLayout()
        position_label = QLabel("坐标:")
        self.position_display = QLabel("x: -, y: -, yaw: -, z: -, height: -")
        position_layout.addWidget(position_label)
        position_layout.addWidget(self.position_display)
        position_layout.addStretch(1)
        #self.xy_coordinate_value_label = QLabel("x：%+.1f, y:%+.1f" % (self.signal_rfpro_x_coordinate ,self.signal_rfpro_y_coordinate))


        # 初始化起点列表（默认选择第一个地图的起点）
        self.update_start_points()

        # 确认按钮
        confirm_button = QPushButton("确认场景设置")
        confirm_button.clicked.connect(self.confirm_scenario_settings)

        #自动记录

        self.auto_record_button = QCheckBox("自动开始记录", self)
        self.auto_record_button.setChecked(self.auto_record)
        self.auto_record_button.stateChanged.connect(self.auto_recording)
        # 路段选择下拉框
        road_segment_combo_layout = QHBoxLayout()
        self.road_segment_combo = QComboBox(self)

        # Store the current index before loading new items
        current_index = self.road_segment_combo.currentIndex()

        try:
            # 读取JSON文件
            with open('road_segments.json', 'r', encoding='utf-8') as f:
                road_data = json.load(f)
                segments = road_data.get('segments', [])

                # 添加路段选项到下拉框
                for segment in segments:
                    self.road_segment_combo.addItem(segment['name'], userData=segment)

                # 如果没有数据，添加默认选项
                if not segments:
                    self.road_segment_combo.addItem("无可用路段")

                # Restore the previous selection if it exists
                if hasattr(self, 'last_road_segment_index'):
                    if self.last_road_segment_index < self.road_segment_combo.count():
                        self.road_segment_combo.setCurrentIndex(self.last_road_segment_index)
                        self.update_coordinates(self.last_road_segment_index)
                else:
                    self.update_coordinates(0)

        except Exception as e:
            print(f"读取路段数据失败: {e}")
            self.road_segment_combo.addItem("加载路段失败")

        self.road_segment_combo.currentIndexChanged.connect(self.update_coordinates)
        # if self.auto_record == 2:
        #     print("选择路段")
            # auto_record_layout.addWidget(QLabel("选择路段:"))
            # auto_record_layout.addWidget(self.road_segment_combo)


        # 添加到场景布局
        scenario_layout.addLayout(map_layout)
        scenario_layout.addLayout(start_point_layout)
        scenario_layout.addLayout(position_layout)
        # scenario_layout.addLayout(auto_record_layout)
        #scenario_layout.addWidget(self.xy_coordinate_value_label)
        # 添加一键启动关闭按钮
        platform_control_layout = QHBoxLayout()
        platform_control_layout.addStretch(1)
        platform_control_layout.addWidget(confirm_button)


        scenario_layout.addLayout(platform_control_layout)
        scenario_layout.addWidget(self.auto_record_button)
        scenario_layout.addWidget(QLabel("选择路段:"))
        road_segment_combo_layout.addWidget(self.road_segment_combo)
        road_segment_combo_layout.addStretch(1)
        scenario_layout.addLayout(road_segment_combo_layout)
        scenario_layout.addStretch(1)

        scenario_group.setLayout(scenario_layout)

        # 3. 新增工具GroupBox
        tools_group = QGroupBox("工具")
        tools_layout = QVBoxLayout()

        # 平台位置偏置
        offset_group = QGroupBox("平台位置偏置")
        offset_layout = QFormLayout()

        # XYZ偏移输入框
        self.offset_x = QLineEdit("0.0")
        self.offset_y = QLineEdit("0.0")
        self.offset_z = QLineEdit("0.0")

        # 设置输入验证（只允许数字和小数点）
        double_validator = QDoubleValidator()
        self.offset_x.setValidator(double_validator)
        self.offset_y.setValidator(double_validator)
        self.offset_z.setValidator(double_validator)

        offset_layout.addRow("X(m):", self.offset_x)
        offset_layout.addRow("Y(m):", self.offset_y)
        offset_layout.addRow("Z(m):", self.offset_z)

        # 确认按钮
        self.offset_confirm_btn = QPushButton("确认")
        self.offset_confirm_btn.clicked.connect(self.apply_platform_offset)
        offset_layout.addRow(self.offset_confirm_btn)

        offset_group.setLayout(offset_layout)
        tools_layout.addWidget(offset_group)

        # 操作数据发送
        data_send_group = QGroupBox("操作数据发送")
        data_send_layout = QHBoxLayout()

        # 文件选择按钮
        self.select_data_btn = QPushButton("选择数据文件")
        self.select_data_btn.clicked.connect(self.select_data_file)

        # 发送按钮
        self.send_data_btn = QPushButton("发送数据")
        self.send_data_btn.clicked.connect(self.send_operation_data)
        self.send_data_btn.setEnabled(False)  # 初始禁用，选择了文件后才启用

        # 文件路径显示
        self.data_file_label = QLabel("未选择文件")
        self.data_file_label.setWordWrap(True)

        # 添加到布局
        data_send_layout.addWidget(self.select_data_btn)
        data_send_layout.addWidget(self.send_data_btn)
        data_send_layout.addWidget(self.data_file_label)

        # 方向盘监测+力矩断线按钮
        self.steer_angle_value_label = QLabel("方向盘转角：%+.1f" % self.signal_steer_angle)
        self.steer_angle_torque_layout = QHBoxLayout()
        self.steer_angle_torque_layout.addWidget(self.steer_angle_value_label)
        self.steer_angle_torque_layout.addStretch(1)
        # 方向盘监测+力矩断线+发送数据 布局
        data_send_layout_0 = QVBoxLayout()
        data_send_layout_0.addLayout(self.steer_angle_torque_layout)
        data_send_layout_0.addLayout(data_send_layout)
        data_send_group.setLayout(data_send_layout_0)
        tools_layout.addWidget(data_send_group)

        tools_group.setLayout(tools_layout)

        # 将两个GroupBox添加到左侧垂直布局
        left_side_layout.addWidget(tuning_group, stretch=1)  # 调校设置占1份
        left_side_layout.addWidget(scenario_group, stretch=1)  # 场景设置占1份
        left_side_layout.addWidget(tools_group, stretch=1)  # 工具区域占1份

        # 右侧区域 - 系统监控GroupBox
        monitor_group = QGroupBox("系统监控")
        monitor_layout = QVBoxLayout()

        # monitor_layout.addWidget(self.monitor_tabs)
        # 嵌入 ProcessMonitor
        self.process_monitor = ProcessMonitor(parent=self)  # 实例化
        monitor_layout.addWidget(self.process_monitor)  # 添加到布局
        monitor_group.setLayout(monitor_layout)

        # 设置主布局比例
        main_layout.addLayout(left_side_layout, stretch=1)  # 左侧区域占2份
        main_layout.addWidget(monitor_group, stretch=1)  # 右侧监控区域占1份

        # 更新调校参数
        #self.UpdateTuningParam()

        return tab

    def add_subtract_button(self, sig):
        if sig == "spring_front_add":
            self.frontSpring_percentage += 5
            self.frontSpringEditText.setValue(
                (self.frontSpring_percentage * 0.01 + 1) * self.frontSpringRateValue_record)
            self.frontSpringEditLabel_percent.setText("%+.1f%%" % self.frontSpring_percentage)
        if sig == "spring_front_subtract":
            self.frontSpring_percentage -= 5
            self.frontSpringEditText.setValue(
                (self.frontSpring_percentage * 0.01 + 1) * self.frontSpringRateValue_record)
            self.frontSpringEditLabel_percent.setText("%+.1f%%" % self.frontSpring_percentage)
        if sig == "spring_rear_add":
            self.rearSpring_percentage += 5
            self.rearSpringEditText.setValue((self.rearSpring_percentage * 0.01 + 1) * self.rearSpringRateValue_record)
            self.rearSpringEditLabel_percent.setText("%+.1f%%" % self.rearSpring_percentage)
        if sig == "spring_rear_subtract":
            self.rearSpring_percentage -= 5
            self.rearSpringEditText.setValue((self.rearSpring_percentage * 0.01 + 1) * self.rearSpringRateValue_record)
            self.rearSpringEditLabel_percent.setText("%+.1f%%" % self.rearSpring_percentage)
        if sig == "Aux_front_add":
            self.frontAuxRollMoment_percentage += 5
            self.frontAuxRollMomentEditText.setValue(
                (self.frontAuxRollMoment_percentage * 0.01 + 1) * self.frontAuxRollMomentValue_record)
            self.frontAuxRollMomentEditLabel_percent.setText("%+.1f%%" % self.frontAuxRollMoment_percentage)
        if sig == "Aux_front_subtract":
            self.frontAuxRollMoment_percentage -= 5
            self.frontAuxRollMomentEditText.setValue(
                (self.frontAuxRollMoment_percentage * 0.01 + 1) * self.frontAuxRollMomentValue_record)
            self.frontAuxRollMomentEditLabel_percent.setText("%+.1f%%" % self.frontAuxRollMoment_percentage)
        if sig == "Aux_rear_add":
            self.rearAuxRollMoment_percentage += 5
            self.rearAuxRollMomentEditText.setValue(
                (self.rearAuxRollMoment_percentage * 0.01 + 1) * self.rearAuxRollMomentValue_record)
            self.rearAuxRollMomentEditLabel_percent.setText("%+.1f%%" % self.rearAuxRollMoment_percentage)
        if sig == "Aux_rear_subtract":
            self.rearAuxRollMoment_percentage -= 5
            self.rearAuxRollMomentEditText.setValue(
                (self.rearAuxRollMoment_percentage * 0.01 + 1) * self.rearAuxRollMomentValue_record)
            self.rearAuxRollMomentEditLabel_percent.setText("%+.1f%%" % self.rearAuxRollMoment_percentage)

    # 新增的工具相关方法
    def apply_platform_offset(self):
        """应用平台位置偏移"""
        try:
            x = float(self.offset_x.text())
            y = float(self.offset_y.text())
            z = float(self.offset_z.text())
            # print(f"应用平台偏移 - X: {x}, Y: {y}, Z: {z}")
            self.sendDataPlatformOffset2(x, y, z)
        except ValueError:
            print("错误：请输入有效的数字")

    def select_data_file(self):
        """选择数据文件"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            None,
            "选择操作数据文件",
            "",
            "CSV文件 (*.csv);;所有文件 (*)"
        )

        if file_path:
            self.data_file_path = file_path
            self.data_file_label.setText(os.path.basename(file_path))
            self.send_data_btn.setEnabled(True)
            print(f"已选择数据文件: {file_path}")

    def send_operation_data(self):
        """发送操作数据"""
        if not hasattr(self, 'data_file_path'):
            print("请先选择数据文件")
            return

        # 读取CSV文件
        with open(self.data_file_path, 'r') as csvfile:
            csv_reader = csv.DictReader(csvfile)

            # 检查必需的列是否存在
            required_columns = {'TimeStep', 'steering_angle', 'Throttle', 'Pbk_con'}
            if not required_columns.issubset(csv_reader.fieldnames):
                missing = required_columns - set(csv_reader.fieldnames)
                print(f"CSV文件缺少必要的列: {missing}")
                return
            count = 0
            recordStartTime = 0
            # 遍历每一行数据并打包
            for row in csv_reader:
                # 提取四个信号值
                if count == 0:
                    recordStartTime = float(row['TimeStep'])
                count = count + 1
                time_step = float(row['TimeStep']) - recordStartTime
                steering = float(row['steering_angle'])
                throttle = float(row['Throttle'])
                fbk_pdl = float(row['FBK_PDL'])
                pbk_con = float(row['Pbk_con'])
                clutch = float(row['Clutch'])
                gears = float(row['Gears'])
                steerRate = float(row['steering_speed'])

                # 使用struct.pack打包数据
                # 'f'表示4字节float，打包4个float共16字节
                # packed_data = struct.pack('8f', time_step, steering, throttle, pbk_con, clutch, gears, fbk_pdl, steerRate)
                # udpSendDriverData.sendto(packed_data, ("10.10.20.221", 10003))
                self.sendDataDriverData2(time_step, steering, throttle, pbk_con, clutch, gears, fbk_pdl, steerRate)
                # 这里添加实际发送数据的代码
                # 例如: self.serial_port.write(packed_data)

                # print(f"打包数据: TimeStep={time_step}, steering={steering}, "
                #       f"throttle={throttle}, pbk_con={pbk_con}")
                # print(f"十六进制: {packed_data.hex()}")

        print("数据发送完成")
        command = 1
        commandData = struct.pack('f', command)
        udpSendDriverData.sendto(commandData, ("10.10.20.221", 10003))

    def load_scenario_data(self):
        """从JSON文件加载场景数据"""
        try:
            with open('scenarios.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 验证JSON数据结构
                if "maps" not in data:
                    raise ValueError("JSON文件缺少'maps'字段")
                for map_item in data["maps"]:
                    if "name" not in map_item or "start_points" not in map_item:
                        raise ValueError("地图配置缺少必要字段")
                    for point in map_item["start_points"]:
                        if "name" not in point or "x" not in point or "y" not in point:
                            raise ValueError("起点配置缺少必要字段")
                return data
        except FileNotFoundError:
            print("警告：未找到scenarios.json文件，使用空配置")
            return {"maps": []}
        except Exception as e:
            print(f"加载场景数据出错: {e}")
            return {"maps": []}

    def update_start_points(self):
        """根据选择的地图更新起点下拉框"""
        self.start_point_combo.clear()
        current_map = self.map_combo.currentData()

        if current_map and "start_points" in current_map:
            for point in current_map["start_points"]:
                self.start_point_combo.addItem(
                    point["name"],
                    userData={"x": point["x"], "y": point["y"], "yaw": point["yaw"], "z": point["z"],
                              "height": point["height"]}
                )

        # 当起点变化时更新坐标显示
        self.start_point_combo.currentIndexChanged.connect(self.update_position_display)
        self.update_position_display()

    def update_position_display(self):
        """更新坐标显示标签"""
        point_data = self.start_point_combo.currentData()
        if point_data:
            self.position_display.setText(
                f"x: {point_data['x']}, y: {point_data['y']}, yaw: {point_data['yaw']}, z: {point_data['z']}, height: {point_data['height']}")
        else:
            self.position_display.setText("x: -, y: -")

    def confirm_scenario_settings(self):
        """确认场景设置按钮点击事件"""
        selected_map = self.map_combo.currentText()
        selected_point = self.start_point_combo.currentText()
        point_data = self.start_point_combo.currentData()

        if point_data:
            # print(f"场景设置已确认 - 地图: {selected_map}, 起点: {selected_point}")
            # print(f"起点坐标: x={point_data['x']}, y={point_data['y']}")
            self.sendDataStartPoint2(point_data['x'], point_data['y'], point_data['yaw'], point_data['z'],
                                     point_data['height'])
        else:
            print("请先选择地图和起点")
        if self.current_condition != selected_point:
            success,message =cueing_change1.modify_cueing_parameters(selected_point)
            QMessageBox.information(self,str(success),message)
        self.current_condition = selected_point

    def RunDspace(self):
        def get_newest_file(root_path):
            if not os.path.exists(root_path) or not os.path.isdir(root_path):
                print(f"指定的路径 {root_path} 不存在或不是一个目录")
                return None

            # 使用os.scandir遍历目录，查找最后修改的子目录，假设最后一个目录是最新创建的
            file_folders = [f for f in os.scandir(root_path) if f.is_dir()]
            if not file_folders:
                print("目录内没有子文件夹")
                return None
            # 根据名称排序（实际上无法准确判断时间，这里仅按名称排列）
            newest_subfolder = max(file_folders, key=lambda x: os.path.getmtime(x))

            newest_file_path = newest_subfolder.path
            resultPath = newest_file_path.replace("\\", "/")
            strings = '/LastRun.csv'
            resultPath = resultPath + strings
            return resultPath

        def find_latest_csv_in_latest_folder(base_path):
            """
            在指定路径的最新文件夹中查找最新的CSV文件
            """
            try:
                # 检查基础路径是否存在
                if not os.path.exists(base_path):
                    print(f"❌ 路径不存在: {base_path}")
                    return None

                # 获取所有子文件夹（只获取文件夹，排除文件）
                subfolders = [f for f in os.listdir(base_path)
                              if os.path.isdir(os.path.join(base_path, f))]

                if not subfolders:
                    print(f"⚠️  在 {base_path} 中没有找到子文件夹")
                    return None

                # 按修改时间排序，获取最新的文件夹
                subfolders.sort(key=lambda x: os.path.getmtime(os.path.join(base_path, x)),
                                reverse=True)

                latest_folder = os.path.join(base_path, subfolders[0])
                print(f"📁 最新的文件夹: {latest_folder}")

                # 在新文件夹中查找CSV文件
                csv_files = glob.glob(os.path.join(latest_folder, "*.csv"))

                if not csv_files:
                    print(f"⚠️  在 {latest_folder} 中没有找到CSV文件")
                    return None

                # 按修改时间排序，获取最新的CSV文件
                csv_files.sort(key=os.path.getmtime, reverse=True)
                latest_csv = csv_files[0]

                print(f"✅ 找到最新的CSV文件: {latest_csv}")
                print(f"📅 修改时间: {os.path.getmtime(latest_csv)}")

                return latest_csv

            except Exception as e:
                print(f"❌ 发生错误: {e}")
                return None


        def extract_last_number(text):
            """提取字符串中的最后一组数字（包括小数），如果没有则返回None"""
            if not text:
                return None
            # 修改正则表达式以匹配数字（包括小数）
            numbers = re.findall(r'\d+\.?\d*', text)
            return numbers[-1] if numbers else None

        def format_suspension_data(front_spring, rear_spring, front_aux, rear_aux):
            """
            格式化悬挂数据为指定格式

            参数:
                front_spring: 前弹簧名称
                rear_spring: 后弹簧名称
                front_aux: 前稳定杆名称
                rear_aux: 后稳定杆名称

            返回:
                格式化后的字符串，格式为: 前弹簧-后弹簧-前稳定杆-后稳定杆
            """

            # 处理弹簧数据
            def process_spring(value):
                num = extract_last_number(value)
                return "ori" if num is None else num

            # 处理稳定杆数据
            def process_aux(value):
                num = extract_last_number(value)
                return "0" if num is None else num

            # 提取各部分数据
            front_spring_val = process_spring(front_spring)
            rear_spring_val = process_spring(rear_spring)
            front_aux_val = process_aux(front_aux)
            rear_aux_val = process_aux(rear_aux)

            # 组合成最终格式
            return f"{front_spring_val}-{rear_spring_val}-{front_aux_val}-{rear_aux_val}"

        waiting_box = QProgressDialog("运行中,请稍等...",None,0,0)
        waiting_box.setCancelButton(None)
        waiting_box.show()
        QCoreApplication.processEvents()

        #carsim.Run('','')
        carsim.RunButtonClick(1)
        self.run_scheme = self.run_scheme+1
        self.result_path = 'C:\\Users\\Public\\Documents\\CarSim2020.0_DataNI\\Results'
        #result_path = get_newest_file(self.result_path)
        #result_path = find_latest_csv_in_latest_folder(self.result_path)
        tempFilePath = 'C:\\test\\LastRun.csv'
        with open(tempFilePath,'r',encoding='utf-8') as f:
            df = pd.read_csv(f)
            avy = df['AVy'].abs().max()
            if avy<self.avy:
                self.avy = avy
                self.best = self.run_scheme

        df_name = f'方案{self.run_scheme}'+' '+format_suspension_data(self.frontSpringName,self.rearSpringName,self.frontAuxMName,self.rearAuxMName)
        df.to_csv(r'E:\01_TestData\01_DCH_Data\DCH\离线仿真'+'\\'+df_name+'.csv')
        # shutil.copyfile(result_path,r'E:\01_TestData\01_DCH_Data\DCH\离线仿真'+'\\'+df_name+'.csv')
        # QMessageBox.information(self, "成功", f"已完成{self.run_scheme}组方案运行")
        waiting_box.close()
        self._show_corner_message(f"已完成{self.run_scheme}组方案运行")

    def OpenSimulink(self):
        carsim.RunButtonClick(2)

    def BuildDspace(self):
        carsim.RunButtonClick(3)

    def create_visual_compensation_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        mode_group = QGroupBox("视觉运动跟随补偿设置")

        mode_group2 = QGroupBox("视觉延迟补偿设置")
        mode_layout = QVBoxLayout()

        mode_group.setLayout(mode_layout)
        mode_group2.setLayout(mode_layout)

        with open('./visualCompensationConfig.json', 'r') as f:
            visualCompensationConfig = json.load(f)
            print(visualCompensationConfig)

        self.xOffsetTextLabel = QLabel("x偏置")
        self.xOffsetTextLabel.setParent(mode_group)
        self.xOffsetTextLabel.setGeometry(50, 100, 150, 30)
        self.xOffsetTextLabel.raise_()
        self.xOffsetEditText = QLineEdit()
        self.xOffsetEditText.setParent(mode_group)
        self.xOffsetEditText.setGeometry(130, 100, 200, 30)
        self.xOffsetEditText.raise_()
        self.xOffsetEditText.setText(str(visualCompensationConfig['xOffset']))

        self.yOffsetTextLabel = QLabel("y偏置")
        self.yOffsetTextLabel.setParent(mode_group)
        self.yOffsetTextLabel.setGeometry(50, 150, 150, 30)
        self.yOffsetTextLabel.raise_()
        self.yOffsetEditText = QLineEdit()
        self.yOffsetEditText.setParent(mode_group)
        self.yOffsetEditText.setGeometry(130, 150, 200, 30)
        self.yOffsetEditText.raise_()
        self.yOffsetEditText.setText(str(visualCompensationConfig['yOffset']))

        self.zOffsetTextLabel = QLabel("z偏置")
        self.zOffsetTextLabel.setParent(mode_group)
        self.zOffsetTextLabel.setGeometry(50, 200, 150, 30)
        self.zOffsetTextLabel.raise_()
        self.zOffsetEditText = QLineEdit()
        self.zOffsetEditText.setParent(mode_group)
        self.zOffsetEditText.setGeometry(130, 200, 200, 30)
        self.zOffsetEditText.raise_()
        self.zOffsetEditText.setText(str(visualCompensationConfig['zOffset']))

        self.rollOffsetTextLabel = QLabel("roll偏置")
        self.rollOffsetTextLabel.setParent(mode_group)
        self.rollOffsetTextLabel.setGeometry(50, 250, 150, 30)
        self.rollOffsetTextLabel.raise_()
        self.rollOffsetEditText = QLineEdit()
        self.rollOffsetEditText.setParent(mode_group)
        self.rollOffsetEditText.setGeometry(130, 250, 200, 30)
        self.rollOffsetEditText.raise_()
        self.rollOffsetEditText.setText(str(visualCompensationConfig['rollOffset']))

        self.pitchOffsetTextLabel = QLabel("pitch偏置")
        self.pitchOffsetTextLabel.setParent(mode_group)
        self.pitchOffsetTextLabel.setGeometry(50, 300, 150, 30)
        self.pitchOffsetTextLabel.raise_()
        self.pitchOffsetEditText = QLineEdit()
        self.pitchOffsetEditText.setParent(mode_group)
        self.pitchOffsetEditText.setGeometry(130, 300, 200, 30)
        self.pitchOffsetEditText.raise_()
        self.pitchOffsetEditText.setText(str(visualCompensationConfig['pitchOffset']))

        self.yawOffsetTextLabel = QLabel("yaw偏置")
        self.yawOffsetTextLabel.setParent(mode_group)
        self.yawOffsetTextLabel.setGeometry(50, 350, 150, 30)
        self.yawOffsetTextLabel.raise_()
        self.yawOffsetEditText = QLineEdit()
        self.yawOffsetEditText.setParent(mode_group)
        self.yawOffsetEditText.setGeometry(130, 350, 200, 30)
        self.yawOffsetEditText.raise_()
        self.yawOffsetEditText.setText(str(visualCompensationConfig['yawOffset']))

        self.xGainTextLabel = QLabel("x增益")
        self.xGainTextLabel.setParent(mode_group)
        self.xGainTextLabel.setGeometry(400, 100, 150, 30)
        self.xGainTextLabel.raise_()
        self.xGainEditText = QLineEdit()
        self.xGainEditText.setParent(mode_group)
        self.xGainEditText.setGeometry(480, 100, 200, 30)
        self.xGainEditText.raise_()
        self.xGainEditText.setText(str(visualCompensationConfig['xGain']))

        self.yGainTextLabel = QLabel("y增益")
        self.yGainTextLabel.setParent(mode_group)
        self.yGainTextLabel.setGeometry(400, 150, 150, 30)
        self.yGainTextLabel.raise_()
        self.yGainEditText = QLineEdit()
        self.yGainEditText.setParent(mode_group)
        self.yGainEditText.setGeometry(480, 150, 200, 30)
        self.yGainEditText.raise_()
        self.yGainEditText.setText(str(visualCompensationConfig['yGain']))

        self.zGainTextLabel = QLabel("z增益")
        self.zGainTextLabel.setParent(mode_group)
        self.zGainTextLabel.setGeometry(400, 200, 150, 30)
        self.zGainTextLabel.raise_()
        self.zGainEditText = QLineEdit()
        self.zGainEditText.setParent(mode_group)
        self.zGainEditText.setGeometry(480, 200, 200, 30)
        self.zGainEditText.raise_()
        self.zGainEditText.setText(str(visualCompensationConfig['zGain']))

        self.rollGainTextLabel = QLabel("roll增益")
        self.rollGainTextLabel.setParent(mode_group)
        self.rollGainTextLabel.setGeometry(400, 250, 150, 30)
        self.rollGainTextLabel.raise_()
        self.rollGainEditText = QLineEdit()
        self.rollGainEditText.setParent(mode_group)
        self.rollGainEditText.setGeometry(480, 250, 200, 30)
        self.rollGainEditText.raise_()
        self.rollGainEditText.setText(str(visualCompensationConfig['rollGain']))

        self.pitchGainTextLabel = QLabel("pitch增益")
        self.pitchGainTextLabel.setParent(mode_group)
        self.pitchGainTextLabel.setGeometry(400, 300, 150, 30)
        self.pitchGainTextLabel.raise_()
        self.pitchGainEditText = QLineEdit()
        self.pitchGainEditText.setParent(mode_group)
        self.pitchGainEditText.setGeometry(480, 300, 200, 30)
        self.pitchGainEditText.raise_()
        self.pitchGainEditText.setText(str(visualCompensationConfig['pitchGain']))

        self.yawGainTextLabel = QLabel("yaw增益")
        self.yawGainTextLabel.setParent(mode_group)
        self.yawGainTextLabel.setGeometry(400, 350, 150, 30)
        self.yawGainTextLabel.raise_()
        self.yawGainEditText = QLineEdit()
        self.yawGainEditText.setParent(mode_group)
        self.yawGainEditText.setGeometry(480, 350, 200, 30)
        self.yawGainEditText.raise_()
        self.yawGainEditText.setText(str(visualCompensationConfig['yawGain']))

        self.visualCompensationApplyButton = QPushButton("应用", mode_group)
        self.visualCompensationApplyButton.setGeometry(50, 400, 300, 30)
        self.visualCompensationApplyButton.raise_()
        self.visualCompensationApplyButton.clicked.connect(self.ApplyVisualCompensation)
        self.ApplyVisualCompensation()

        self.delayTimeTextLabel = QLabel("延迟时间")
        self.delayTimeTextLabel.setParent(mode_group2)
        self.delayTimeTextLabel.setGeometry(50, 100, 150, 30)
        self.delayTimeTextLabel.raise_()
        self.delayTimeEditText = QLineEdit()
        self.delayTimeEditText.setParent(mode_group2)
        self.delayTimeEditText.setGeometry(130, 100, 200, 30)
        self.delayTimeEditText.raise_()
        self.delayTimeEditText.setText('60')

        self.sampleTimeTextLabel = QLabel("采样时间")
        self.sampleTimeTextLabel.setParent(mode_group2)
        self.sampleTimeTextLabel.setGeometry(50, 150, 150, 30)
        self.sampleTimeTextLabel.raise_()
        self.sampleTimeEditText = QLineEdit()
        self.sampleTimeEditText.setParent(mode_group2)
        self.sampleTimeEditText.setGeometry(130, 150, 200, 30)
        self.sampleTimeEditText.raise_()
        self.sampleTimeEditText.setText('0.001')

        self.freqTextLabel = QLabel("机动频率")
        self.freqTextLabel.setParent(mode_group2)
        self.freqTextLabel.setGeometry(50, 200, 150, 30)
        self.freqTextLabel.raise_()
        self.freqEditText = QLineEdit()
        self.freqEditText.setParent(mode_group2)
        self.freqEditText.setGeometry(130, 200, 200, 30)
        self.freqEditText.raise_()
        self.freqEditText.setText('1.5')

        self.posAccTextLabel = QLabel("正向最大加速度")
        self.posAccTextLabel.setParent(mode_group2)
        self.posAccTextLabel.setGeometry(0, 250, 150, 30)
        self.posAccTextLabel.raise_()
        self.posAccEditText = QLineEdit()
        self.posAccEditText.setParent(mode_group2)
        self.posAccEditText.setGeometry(130, 250, 200, 30)
        self.posAccEditText.raise_()
        self.posAccEditText.setText('3')

        self.negAccTextLabel = QLabel("负向最大加速度")
        self.negAccTextLabel.setParent(mode_group2)
        self.negAccTextLabel.setGeometry(0, 300, 150, 30)
        self.negAccTextLabel.raise_()
        self.negAccEditText = QLineEdit()
        self.negAccEditText.setParent(mode_group2)
        self.negAccEditText.setGeometry(130, 300, 200, 30)
        self.negAccEditText.raise_()
        self.negAccEditText.setText('3')

        self.visualDelayCompensationApplyButton = QPushButton("应用", mode_group2)
        self.visualDelayCompensationApplyButton.setGeometry(50, 400, 300, 30)
        self.visualDelayCompensationApplyButton.raise_()
        self.visualDelayCompensationApplyButton.clicked.connect(self.ApplyVisualDelayCompensation)
        self.ApplyVisualDelayCompensation()

        layout.addWidget(mode_group)
        layout.addWidget(mode_group2)

        tab.setLayout(layout)
        return tab

    def create_delay_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout()
        layout = QVBoxLayout()
        tab.setLayout(main_layout)

        # 创建实时绘图组
        plot_group = QGroupBox("实时数据显示")
        plot_layout = QVBoxLayout()

        # 创建绘图控件
        self.cal_delay = pg.PlotWidget()  # DSPACE计算延迟曲线
        self.cal_delay.setBackground('w')  # 白色背景
        self.cal_delay.showGrid(x=True, y=True)  # 显示网格
        self.cal_delay.setLabel('left', '延迟(ns)', color='k')  # Y轴标签
        self.cal_delay.setLabel('bottom', '时间/s', color='k')  # X轴标签
        self.cal_delay.setTitle('DSPACE计算延迟', color='k')  # 标题

        self.rf_delay = pg.PlotWidget()  # RFPRO延迟曲线
        self.rf_delay.setBackground('w')
        self.rf_delay.showGrid(x=True, y=True)
        self.rf_delay.setLabel('left', '延迟(μs)', color='k')
        self.rf_delay.setLabel('bottom', '时间/s', color='k')
        self.rf_delay.setTitle('DSPACE-RFPRO延迟', color='k')

        self.mo_delay = pg.PlotWidget()  # MOOG延迟曲线
        self.mo_delay.setBackground('w')
        self.mo_delay.showGrid(x=True, y=True)
        self.mo_delay.setLabel('left', '延迟(μs)', color='k')
        self.mo_delay.setLabel('bottom', '时间/s', color='k')
        self.mo_delay.setTitle('DSPACE-MOOG延迟', color='k')

        self.sw_delay = pg.PlotWidget()  # 方向盘延迟曲线
        self.sw_delay.setBackground('w')
        self.sw_delay.showGrid(x=True, y=True)
        self.sw_delay.setLabel('left', '延迟(μs)', color='k')
        self.sw_delay.setLabel('bottom', '时间/s', color='k')
        self.sw_delay.setTitle('DSPACE-方向盘延迟', color='k')

        # 创建曲线
        self.cal_curve = self.cal_delay.plot(pen=pg.mkPen(color=(0, 0, 255), width=1.5))  # 蓝色曲线
        self.rf_curve = self.rf_delay.plot(pen=pg.mkPen(color=(255, 0, 0), width=1.5))  # 红色曲线
        self.mo_f_curve = self.mo_delay.plot(pen=pg.mkPen(color=(0, 255, 0), width=1.5))  # 绿色曲线
        self.sw_delay_curve = self.sw_delay.plot(pen=pg.mkPen(color=(255, 255, 0), width=1.5))  # 黄色曲线

        # 生成初始数据
        # 1秒内有400个时间点，间隔为0.0025秒
        x = [0.0025 * i for i in range(400)]  # 时间点

        # DSPACE计算延迟曲线数据（30ns附近波动）
        y_cal = [30 + random.uniform(-5, 5) for _ in range(400)]
        self.cal_curve.setData(x, y_cal)

        # RFPRO延迟曲线数据（200μs附近波动）
        y_rf = [200 + random.uniform(-25, 25) for _ in range(400)]
        self.rf_curve.setData(x, y_rf)

        # MOOG延迟曲线数据（500μs附近波动）
        y_mo = [500 + random.uniform(-25, 25) for _ in range(400)]
        self.mo_f_curve.setData(x, y_mo)

        # 方向盘延迟曲线数据（400μs附近波动）
        y_sw = [400 + random.uniform(-25, 25) for _ in range(400)]
        self.sw_delay_curve.setData(x, y_sw)

        # 将绘图控件添加到布局
        plot_layout.addWidget(self.cal_delay)
        plot_layout.addWidget(self.rf_delay)
        plot_layout.addWidget(self.mo_delay)
        plot_layout.addWidget(self.sw_delay)

        layout.setContentsMargins(100, 100, 100, 100)
        plot_layout.setContentsMargins(0, 50, 100, 50)

        main_layout.addLayout(layout)
        main_layout.addLayout(plot_layout)
        tab.setLayout(main_layout)

        return tab

    def ApplyVisualCompensation(self):
        xOffset = float(self.xOffsetEditText.text())
        yOffset = float(self.yOffsetEditText.text())
        zOffset = float(self.zOffsetEditText.text())
        rollOffset = float(self.rollOffsetEditText.text())
        pitchOffset = float(self.pitchOffsetEditText.text())
        yawOffset = float(self.yawOffsetEditText.text())
        xGain = float(self.xGainEditText.text())
        yGain = float(self.yGainEditText.text())
        zGain = float(self.zGainEditText.text())
        rollGain = float(self.rollGainEditText.text())
        pitchGain = float(self.pitchGainEditText.text())
        yawGain = float(self.yawGainEditText.text())
        send_data = [xOffset, yOffset, zOffset, rollOffset, pitchOffset, yawOffset, xGain, yGain, zGain, rollGain,
                     pitchGain, yawGain]
        send_data = struct.pack('12f', *send_data)
        # udp4.sendto(send_data, ('10.10.20.221', 9999))
        save_data = {'xOffset': xOffset, 'yOffset': yOffset, 'zOffset': zOffset, 'rollOffset': rollOffset,
                     'pitchOffset': pitchOffset,
                     'yawOffset': yawOffset, 'xGain': xGain, 'yGain': yGain, 'zGain': zGain, 'rollGain': rollGain,
                     'pitchGain': pitchGain, 'yawGain': yawGain}
        save_data_json = json.dumps(save_data)
        with open('./visualCompensationConfig.json', 'w') as f:
            f.write(save_data_json)

    def ApplyVisualDelayCompensation(self):
        sampleTime = float(self.sampleTimeEditText.text())
        delayTime = float(self.delayTimeEditText.text())
        freq = float(self.freqEditText.text())
        posAcc = float(self.posAccEditText.text())
        negAcc = float(self.negAccEditText.text())
        send_data = [sampleTime, delayTime, freq, posAcc, negAcc]
        send_data = struct.pack('5f', *send_data)
        # udpVisualDelayCompensation.sendto(send_data, ('10.10.20.221', 12345))
        save_data = {'sampleTime': sampleTime, 'delayTime': delayTime, 'freq': freq, 'posAcc': posAcc, 'negAcc': negAcc}
        save_data_json = json.dumps(save_data)
        with open('./visualDelayCompensationConfig.json', 'w') as f:
            f.write(save_data_json)

    # def UpdateTuningParam(self):
    #     self.CurrentVehicleSpringPage(1)
    #     currentSpringLibrary_FR, currentSpringDataset_FR, currentSpringCat_FR, _ = carsim.GetBlueLink('#BlueLink3')
    #     if currentSpringDataset_FR == None:
    #         self.is_leftright_front = False
    #     else:
    #         self.is_leftright_front = True
    #     if carsim.GetRing('*OPT_SPR') == '0' and carsim.GetRing('#RingCtrl1') == '1':
    #         # 判断曲线
    #         self.frontSpringMode = 1
    #         # 输入框设置
    #         self.frontSpringEditLabel.setText("前轮弹簧刚度：")
    #         #self.frontSpringEditText.setEnabled(True)
    #         self.frontSpringRateValue = carsim.GetYellow('*KSPRING_L')
    #         #self.frontSpringEditText.setValue(float(self.frontSpringRateValue))
    #         # 记录初始值
    #         self.frontSpringRateValue_record = float(self.frontSpringRateValue)
    #         self.front_fs_record = 0.0
    #         self.front_fs1_record = 0.0
    #         self.front_right_fs_record = 0.0
    #         self.front_right_fs1_record = 0.0
    #     elif carsim.GetRing('*OPT_SPR') == '0' and (
    #             carsim.GetRing('#RingCtrl1') == '2' or carsim.GetRing('#RingCtrl2') == '3'):
    #         self.frontSpringMode = 2
    #         self.frontSpringEditLabel.setText("前轮弹簧刚度：")
    #         self.frontSpringRateValue = 1.0
    #         #self.frontSpringEditText.setValue(float(self.frontSpringRateValue))
    #         # 记录初始值
    #         self.frontSpringRateValue_record = self.frontSpringRateValue
    #         currentSpringLibrary, currentSpringDataset, currentSpringCat, _ = carsim.GetBlueLink('#BlueLink0')
    #         carsim.Gotolibrary(currentSpringLibrary, currentSpringDataset, currentSpringCat)
    #         self.front_fs_record = list(carsim.GetTable('FS_COMP'))
    #         self.front_fs1_record = list(carsim.GetTable('FS_EXT'))
    #         if self.is_leftright_front:
    #             carsim.GoHome()
    #             self.CurrentVehicleSpringPage(1)
    #             carsim.Gotolibrary(currentSpringLibrary_FR, currentSpringDataset_FR, currentSpringCat_FR)
    #             self.front_right_fs_record = list(carsim.GetTable('FS_COMP'))
    #             self.front_right_fs1_record = list(carsim.GetTable('FS_EXT'))
    #             #print("右前弹簧")
    #         else:
    #             self.front_right_fs_record = 0.0
    #             self.front_right_fs1_record = 0.0
    #     else:
    #         self.frontSpringEditText.setEnabled(False)
    #         self.frontSpringRateValue = 0.0
    #         self.frontSpringEditText.setValue(0.0)  # 使用 setValue
    #     # print(f"*OPT_SPR: {carsim.GetRing('*OPT_SPR')}")
    #     carsim.GoHome()
    #
    #     # 后轮弹簧刚度
    #     self.CurrentVehicleSpringPage(2)
    #     currentSpringLibrary_RR, currentSpringDataset_RR, currentSpringCat_RR, _ = carsim.GetBlueLink('#BlueLink3')
    #     if currentSpringDataset_RR == None:
    #         self.is_leftright_rear = False
    #     else:
    #         self.is_leftright_rear = True
    #     if carsim.GetRing('*OPT_SPR') == '0' and carsim.GetRing('#RingCtrl1') == '1':
    #         self.rearSpringMode = 1
    #         self.rearSpringEditLabel.setText("后轮弹簧刚度：")
    #         #self.rearSpringEditText.setEnabled(True)
    #         self.rearSpringRateValue = carsim.GetYellow('*KSPRING_L')
    #         #self.rearSpringEditText.setValue(float(self.rearSpringRateValue))
    #         # 记录初始值
    #         self.rearSpringRateValue_record = float(self.rearSpringRateValue)
    #         self.rear_fs_record = 0.0
    #         self.rear_fs1_record = 0.0
    #         self.rear_right_fs_record = 0.0
    #         self.rear_right_fs1_record = 0.0
    #     elif carsim.GetRing('*OPT_SPR') == '0' and (
    #             carsim.GetRing('#RingCtrl1') == '2' or carsim.GetRing('#RingCtrl2') == '3'):
    #         self.rearSpringMode = 2
    #         self.rearSpringEditLabel.setText("后轮弹簧刚度：")
    #         self.rearSpringRateValue = 1.0
    #         #self.rearSpringEditText.setValue(float(self.rearSpringRateValue))
    #         # 记录初始值
    #         self.rearSpringRateValue_record = self.rearSpringRateValue
    #         currentSpringLibrary, currentSpringDataset, currentSpringCat, _ = carsim.GetBlueLink('#BlueLink0')
    #         carsim.Gotolibrary(currentSpringLibrary, currentSpringDataset, currentSpringCat)
    #         self.rear_fs_record = list(carsim.GetTable('FS_COMP'))
    #         self.rear_fs1_record = list(carsim.GetTable('FS_EXT'))
    #         if self.is_leftright_rear:
    #             carsim.GoHome()
    #             self.CurrentVehicleSpringPage(2)
    #             carsim.Gotolibrary(currentSpringLibrary_RR, currentSpringDataset_RR, currentSpringCat_RR)
    #             self.rear_right_fs_record = list(carsim.GetTable('FS_COMP'))
    #             self.rear_right_fs1_record = list(carsim.GetTable('FS_EXT'))
    #             print("右后弹簧")
    #         else:
    #             self.rear_right_fs_record = 0.0
    #             self.rear_right_fs1_record = 0.0
    #
    #     else:
    #         self.rearSpringEditText.setEnabled(False)
    #         self.rearSpringRateValue = 0
    #         self.rearSpringEditText.setValue(0.0)  # 使用 setValue
    #
    #     carsim.GoHome()
    #
    #     # 前轮稳定杆刚度
    #     self.CurrentVehicleSpringPage(1)
    #     ARMLibrary, ARMDataset, ARMCat, _ = carsim.GetBlueLink('#BlueLink2')
    #     carsim.Gotolibrary(ARMLibrary, ARMDataset, ARMCat)
    #     ringName = carsim.GetRing('#RingCtrl0')
    #     if ringName == 'CONSTANT' or ringName == 'COEFFICIENT':
    #         self.frontAuxRollMomentMode = 1
    #         self.frontAuxRollMomentEditLabel.setText("前轮稳定杆刚度：")
    #         #self.frontAuxRollMomentEditText.setEnabled(True)
    #         self.frontAuxRollMomentValue = carsim.GetYellow('*SCALAR')
    #         #self.frontAuxRollMomentEditText.setValue(float(self.frontAuxRollMomentValue))
    #         # 记录初始值
    #         self.frontAuxRollMomentValue_record = float(self.frontAuxRollMomentValue)
    #         self.front_m_record = 0.0
    #     elif ringName == None:
    #         self.frontAuxRollMomentMode = 3
    #         self.frontAuxRollMomentEditLabel.setText("前轮稳定杆刚度：")
    #         self.frontAuxRollMomentValue = 1.0
    #         #self.frontAuxRollMomentEditText.setValue(float(self.frontAuxRollMomentValue))
    #         # 记录初始值
    #         self.frontAuxRollMomentValue_record = self.frontAuxRollMomentValue
    #         self.front_m_record = list(carsim.GetTable('MX_TOTAL_TABLE'))
    #     else:
    #         self.frontAuxRollMomentMode = 2
    #         self.frontAuxRollMomentEditLabel.setText("前轮稳定杆刚度：")
    #         self.frontAuxRollMomentValue = 1.0
    #         #self.frontAuxRollMomentEditText.setValue(float(self.frontAuxRollMomentValue))
    #         # 记录初始值
    #         self.frontAuxRollMomentValue_record = self.frontAuxRollMomentValue
    #         self.front_m_record = list(carsim.GetTable('MX_AUX'))
    #
    #     # else:
    #     #     self.frontAuxRollMomentEditText.setEnabled(False)
    #     #     self.frontAuxRollMomentValue = 0
    #     #     self.frontAuxRollMomentEditText.setValue(0.0)  # 使用 setValue
    #
    #     carsim.GoHome()
    #
    #     # 后轮稳定杆刚度
    #     self.CurrentVehicleSpringPage(2)
    #     ARMLibrary, ARMDataset, ARMCat, _ = carsim.GetBlueLink('#BlueLink2')
    #     carsim.Gotolibrary(ARMLibrary, ARMDataset, ARMCat)
    #     ringName = carsim.GetRing('#RingCtrl0')
    #     print(ringName)
    #     if ringName == 'CONSTANT' or ringName == 'COEFFICIENT':
    #         self.rearAuxRollMomentMode = 1
    #         self.rearAuxRollMomentEditLabel.setText("后轮稳定杆刚度：")
    #         #self.rearAuxRollMomentEditText.setEnabled(True)
    #         self.rearAuxRollMomentValue = carsim.GetYellow('*SCALAR')
    #         #self.rearAuxRollMomentEditText.setValue(float(self.rearAuxRollMomentValue))
    #         # 记录初始值
    #         self.rearAuxRollMomentValue_record = float(self.rearAuxRollMomentValue)
    #         self.rear_m_record = 0.0
    #     elif ringName == None:
    #         self.rearAuxRollMomentMode = 3
    #         self.rearAuxRollMomentEditLabel.setText("后轮稳定杆刚度：")
    #         self.rearAuxRollMomentValue = 1.0
    #         #self.rearAuxRollMomentEditText.setValue(float(self.rearAuxRollMomentValue))
    #         # 记录初始值
    #         self.rearAuxRollMomentValue_record = self.rearAuxRollMomentValue
    #         self.rear_m_record = list(carsim.GetTable('MX_TOTAL_TABLE'))
    #     else:
    #         self.rearAuxRollMomentMode = 2
    #         self.rearAuxRollMomentEditLabel.setText("后轮稳定杆刚度(增益)：")
    #         self.rearAuxRollMomentValue = 1.0
    #         self.rearAuxRollMomentEditText.setValue(float(self.rearAuxRollMomentValue))
    #         # 记录初始值
    #         self.rearAuxRollMomentValue_record = self.rearAuxRollMomentValue
    #         self.rear_m_record = list(carsim.GetTable('MX_AUX'))
    #     # else:
    #     #     self.rearAuxRollMomentEditText.setEnabled(False)
    #     #     self.rearAuxRollMomentValue = 0
    #     #     self.rearAuxRollMomentEditText.setValue(0.0)  # 使用 setValue
    #
    #     carsim.GoHome()
    #     data = {
    #         "FrontSpringValue": self.frontSpringRateValue_record,
    #         "FrontSpringFsCurve": self.front_fs_record,
    #         "FrontSpringFs1Curve": self.front_fs1_record,
    #         "FrontRightSpringFsCurve": self.front_right_fs_record,
    #         "FrontRightSpringFs1Curve": self.front_right_fs1_record,
    #         "RearSpringValue": self.rearSpringRateValue_record,
    #         "RearSpringFsCurve": self.rear_fs1_record,
    #         "RearSpringFs1Curve": self.rear_fs1_record,
    #         "RearRightSpringFsCurve": self.rear_right_fs_record,
    #         "RearRightSpringFs1Curve": self.rear_right_fs1_record,
    #         "FrontAuxValue": self.frontAuxRollMomentValue_record,
    #         "FrontAuxCurve": self.front_m_record,
    #         "RearAuxValue": self.rearAuxRollMomentValue_record,
    #         "RearAuxCurve": self.rear_m_record
    #     }
    #     # 保存到JSON文件
    #     with open("SpringAuxRollMoment.json", 'w') as f:
    #         json.dump(data, f, indent=4)  # indent参数使输出格式化更易读
    #
    #     print("数据已保存到 SpringAuxRollMoment.json")

    def condition_choose(self):
        if self.condition_combo.currentText()!='请选择工况':
            condition_info = self.condition_info.get(self.condition_combo.currentText())
            carsim.GoHome()
            carsim.BlueLink('#BlueLink28',condition_info[0],condition_info[1],condition_info[2])

    def UpdateTuningParam(self):
        # 初始化车辆信息
        carsim.GoHome()
        carInfo = carsim.GetBlueLink('#BlueLink2')
        carName = carInfo[1]
        carImagePath = vehicleImagePath[carName]
        image = QImage(carImagePath)
        pixmap = QPixmap.fromImage(image).scaled(200, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.carImage.setPixmap(pixmap)
        self.select_car_button.setText(carName)
        self.carName = carName

        self.form_layout.removeRow(0)
        self.form_layout.removeRow(0)
        self.form_layout.removeRow(0)
        self.form_layout.removeRow(0)

        # 初始化前轮弹簧信息

        # 前轮弹簧选择按钮
        self.frontSpringEditLabel = QLabel("前轮弹簧刚度：")
        self.CurrentVehicleSpringPage(1)
        self.frontSpring_menu = QMenu()
        self.select_frontSpring_button = QPushButton("选择车型")
        self.select_frontSpring_button.setMenu(self.frontSpring_menu)
        frontSpringInfo = carsim.GetBlueLink('#BlueLink0')
        frontSpringName = frontSpringInfo[1]
        frontSpringGroup = frontSpringInfo[2]
        # 初始化前轮弹簧信息
        self.select_frontSpring_button.setText(frontSpringName)
        self.frontSpringName = frontSpringName
        global springNames
        if (carsim.GetRing('*OPT_SPR') == '0' or carsim.GetRing('*OPT_SPR') == '1') and carsim.GetRing('#RingCtrl1') == '1':
            print(0)
            # 前轮弹簧刚度输入框
            self.frontSpringEditText = QDoubleSpinBox()
            self.frontSpringEditText.setButtonSymbols(QAbstractSpinBox.NoButtons)
            self.frontSpringEditText.setRange(-10000.0, 10000.0)
            #self.frontSpringEditText.editingFinished.connect(self.OnFrontSpringTextChanged)
            self.frontSpringEditButton = QPushButton("√")
            self.frontSpringEditButton.clicked.connect(self.OnFrontSpringTextChanged)
            self.frontSpringRateValue = carsim.GetYellow('*KSPRING_L')
            self.frontSpringEditText.setValue(float(self.frontSpringRateValue))
            self.frontSpringName = self.frontSpringRateValue
        else:
            for springName in springNames[frontSpringGroup]:
                button = CustomCarPushButton(springName, hasMenu=False, topWidget=self.select_frontSpring_button)
                button.clicked.connect(self.onFrontSpringChange)
                action = QWidgetAction(self.frontSpring_menu)
                action.setDefaultWidget(button)
                self.frontSpring_menu.addAction(action)
        # 判断是否分左右侧
        layoutleftrightspring = QHBoxLayout()
        currentSpringLibrary_FR, currentSpringDataset_FR, currentSpringCat_FR, _ = carsim.GetBlueLink('#BlueLink3')
        if currentSpringDataset_FR == None:
            if (carsim.GetRing('*OPT_SPR') == '0' or carsim.GetRing('*OPT_SPR') == '1') and carsim.GetRing('#RingCtrl1') == '1':
                layoutleftrightspring.addWidget(self.frontSpringEditText)
                layoutleftrightspring.addWidget(self.frontSpringEditButton)
            else:
                layoutleftrightspring.addWidget(self.select_frontSpring_button)
            self.is_leftright_front = False

        else:
            self.is_leftright_front = True
            #创建右侧按钮
            self.frontRightSpring_menu = QMenu()
            self.select_frontRightSpring_button = QPushButton("选择车型")
            self.select_frontRightSpring_button.setMenu(self.frontRightSpring_menu)
            frontRightSpringInfo = carsim.GetBlueLink('#BlueLink3')
            frontRightSpringName = frontRightSpringInfo[1]
            frontRightSpringGroup = frontRightSpringInfo[2]
            for springName in springNames[frontRightSpringGroup]:
                button = CustomCarPushButton(springName, hasMenu=False, topWidget=self.select_frontRightSpring_button)
                button.clicked.connect(self.onFrontRightSpringChange)
                action = QWidgetAction(self.frontRightSpring_menu)
                action.setDefaultWidget(button)
                self.frontRightSpring_menu.addAction(action)

            self.select_frontRightSpring_button.setText(frontRightSpringName)
            self.frontRightSpringName = frontRightSpringName
            layoutleftrightspring.addWidget(self.select_frontSpring_button)
            layoutleftrightspring.addWidget(self.select_frontRightSpring_button)
        self.form_layout.addRow(self.frontSpringEditLabel, layoutleftrightspring)
        # self.frontSpring_percentage = 0.0
        # self.frontSpringEditLabel_percent = QLabel("%+.1f%%" % self.frontSpring_percentage)
        # self.add_frontSpring = QPushButton("+5%")
        # self.add_frontSpring.clicked.connect(lambda: self.add_subtract_button("spring_front_add"))
        # self.subtract_frontSpring = QPushButton("-5%")
        # self.subtract_frontSpring.clicked.connect(lambda: self.add_subtract_button("spring_front_subtract"))
        # self.frontSpring_button_layout = QHBoxLayout()
        # self.frontSpring_button_layout.addWidget(self.subtract_frontSpring)
        # self.frontSpring_button_layout.addWidget(self.add_frontSpring)
        # self.form_layout_1.addRow(self.frontSpringEditLabel_percent, self.frontSpring_button_layout)


        # 后轮弹簧刚度
        self.rearSpringEditLabel = QLabel("后轮弹簧刚度：")

        # 后轮弹簧选择按钮
        self.rearSpring_menu = QMenu()
        self.select_rearSpring_button = QPushButton("选择车型")
        self.select_rearSpring_button.setMenu(self.rearSpring_menu)
        self.CurrentVehicleSpringPage(2)
        rearSpringInfo = carsim.GetBlueLink('#BlueLink0')
        rearSpringName = rearSpringInfo[1]
        rearSpringGroup = rearSpringInfo[2]
        # 初始化后轮弹簧信息
        self.select_rearSpring_button.setText(rearSpringName)
        self.rearSpringName = rearSpringName
        if (carsim.GetRing('*OPT_SPR') == '0' or carsim.GetRing('*OPT_SPR') == '1') and carsim.GetRing('#RingCtrl1') == '1':
            self.rearSpringEditText = QDoubleSpinBox()
            self.rearSpringEditText.setButtonSymbols(QAbstractSpinBox.NoButtons)
            self.rearSpringEditText.setRange(-10000.0, 10000.0)
            #self.rearSpringEditText.editingFinished.connect(self.OnRearSpringTextChanged)
            self.rearSpringEditButton = QPushButton("√")
            self.rearSpringEditButton.clicked.connect(self.OnRearSpringTextChanged)
            self.rearSpringRateValue = carsim.GetYellow('*KSPRING_L')
            self.rearSpringEditText.setValue(float(self.rearSpringRateValue))
            self.rearSpringName = self.rearSpringRateValue
        else:
            for springName in springNames[rearSpringGroup]:
                button = CustomCarPushButton(springName, hasMenu=False, topWidget=self.select_rearSpring_button)
                button.clicked.connect(self.onRearSpringChange)

                action = QWidgetAction(self.rearSpring_menu)
                action.setDefaultWidget(button)
                self.rearSpring_menu.addAction(action)

        # 判断是否分左右侧
        layoutleftrightspring = QHBoxLayout()
        currentSpringLibrary_FR, currentSpringDataset_FR, currentSpringCat_FR, _ = carsim.GetBlueLink('#BlueLink3')
        if currentSpringDataset_FR == None:
            if (carsim.GetRing('*OPT_SPR') == '0' or carsim.GetRing('*OPT_SPR') == '1') and carsim.GetRing('#RingCtrl1') == '1':
                layoutleftrightspring.addWidget(self.rearSpringEditText)
                layoutleftrightspring.addWidget(self.rearSpringEditButton)
            else:
                layoutleftrightspring.addWidget(self.select_rearSpring_button)
            self.is_leftright_rear = False
        else:
            self.is_leftright_rear = True
            # 创建右侧按钮
            self.rearRightSpring_menu = QMenu()
            self.select_rearRightSpring_button = QPushButton("选择车型")
            self.select_rearRightSpring_button.setMenu(self.rearRightSpring_menu)
            rearRightSpringInfo = carsim.GetBlueLink('#BlueLink3')
            rearRightSpringName = rearRightSpringInfo[1]
            rearRightSpringGroup = rearRightSpringInfo[2]
            for springName in springNames[rearRightSpringGroup]:
                button = CustomCarPushButton(springName, hasMenu=False, topWidget=self.select_rearRightSpring_button)
                button.clicked.connect(self.onRearRightSpringChange)

                action = QWidgetAction(self.rearRightSpring_menu)
                action.setDefaultWidget(button)
                self.rearRightSpring_menu.addAction(action)
            self.select_rearRightSpring_button.setText(rearRightSpringName)
            self.rearRightSpringName = rearRightSpringName

            layoutleftrightspring.addWidget(self.select_rearSpring_button)
            layoutleftrightspring.addWidget(self.select_rearRightSpring_button)
        self.form_layout.addRow(self.rearSpringEditLabel, layoutleftrightspring)
        self.rearSpring_percentage = 0.0
        self.rearSpringEditLabel_percent = QLabel("%+.1f%%" % self.rearSpring_percentage)
        self.add_rearSpring = QPushButton("+5%")
        self.add_rearSpring.clicked.connect(lambda: self.add_subtract_button("spring_rear_add"))
        self.subtract_rearSpring = QPushButton("-5%")
        self.subtract_rearSpring.clicked.connect(lambda: self.add_subtract_button("spring_rear_subtract"))
        # self.rearSpring_button_layout = QHBoxLayout()
        # self.rearSpring_button_layout.addWidget(self.subtract_rearSpring)
        # self.rearSpring_button_layout.addWidget(self.add_rearSpring)
        # self.form_layout_1.addRow(self.rearSpringEditLabel_percent, self.rearSpring_button_layout)

        # 前轮稳定杆刚度
        self.frontAuxRollMomentEditLabel = QLabel("前轮稳定杆刚度:")
        # self.frontAuxRollMomentEditText = QDoubleSpinBox()
        # self.frontAuxRollMomentEditText.setButtonSymbols(QAbstractSpinBox.NoButtons)
        # self.frontAuxRollMomentEditText.setRange(-10000.0, 10000.0)
        # self.frontAuxRollMomentEditText.valueChanged.connect(self.OnfrontAuxRollMomentTextChanged)
        # self.form_layout.addRow(self.frontAuxRollMomentEditLabel, self.frontAuxRollMomentEditText)
        # 前轮稳定杆选择按钮
        # 判断Library
        global AuxMNames
        global MxTotNames
        self.frontAuxM_menu = QMenu()
        self.select_frontAuxM_button = QPushButton("选择车型")
        self.select_frontAuxM_button.setMenu(self.frontAuxM_menu)
        self.CurrentVehicleSpringPage(1)
        frontAuxMInfo = carsim.GetBlueLink('#BlueLink2')
        frontAuxMName = frontAuxMInfo[1]
        frontAuxMGroup = frontAuxMInfo[2]
        currentLibrary, currentDataset, currentCat, _ = carsim.GetBlueLink('#BlueLink2')
        if currentLibrary == 'Suspension: Auxiliary Roll Moment':
            for AuxMName in AuxMNames[frontAuxMGroup]:
                button = CustomCarPushButton(AuxMName, hasMenu=False, topWidget=self.select_frontAuxM_button)
                button.clicked.connect(self.onFrontAuxMChange)
                action = QWidgetAction(self.frontAuxM_menu)
                action.setDefaultWidget(button)
                self.frontAuxM_menu.addAction(action)
        elif currentLibrary == 'Suspension: Measured Total Roll Stiffness':
            for MxTotMName in MxTotNames[frontAuxMGroup]:
                button = CustomCarPushButton(MxTotMName, hasMenu=False, topWidget=self.select_frontAuxM_button)
                button.clicked.connect(self.onFrontAuxMChange)
                action = QWidgetAction(self.frontAuxM_menu)
                action.setDefaultWidget(button)
                self.frontAuxM_menu.addAction(action)
        else:
            pass
        # 初始化前轮稳定杆信息
        self.select_frontAuxM_button.setText(frontAuxMName)
        self.frontAuxMName = frontAuxMName
        self.form_layout.addRow(self.frontAuxRollMomentEditLabel, self.select_frontAuxM_button)

        self.frontAuxRollMoment_percentage = 0.0
        self.frontAuxRollMomentEditLabel_percent = QLabel("%+.1f%%" % self.frontAuxRollMoment_percentage)
        self.add_frontAuxRollMoment = QPushButton("+5%")
        self.add_frontAuxRollMoment.clicked.connect(lambda: self.add_subtract_button("Aux_front_add"))
        self.subtract_frontAuxRollMoment = QPushButton("-5%")
        self.subtract_frontAuxRollMoment.clicked.connect(lambda: self.add_subtract_button("Aux_front_subtract"))
        # self.frontAuxRollMoment_layout = QHBoxLayout()
        # self.frontAuxRollMoment_layout.addWidget(self.subtract_frontAuxRollMoment)
        # self.frontAuxRollMoment_layout.addWidget(self.add_frontAuxRollMoment)
        # self.form_layout_1.addRow(self.frontAuxRollMomentEditLabel_percent, self.frontAuxRollMoment_layout)

        # 后轮稳定杆刚度
        self.rearAuxRollMomentEditLabel = QLabel("后轮稳定杆刚度:")
        # self.rearAuxRollMomentEditText = QDoubleSpinBox()
        # self.rearAuxRollMomentEditText.setButtonSymbols(QAbstractSpinBox.NoButtons)
        # self.rearAuxRollMomentEditText.setRange(-10000.0, 10000.0)
        # self.rearAuxRollMomentEditText.valueChanged.connect(self.OnRearAuxRollMomentTextChanged)
        # self.form_layout.addRow(self.rearAuxRollMomentEditLabel, self.rearAuxRollMomentEditText)
        # 后轮稳定杆选择按钮
        self.rearAuxM_menu = QMenu()
        self.select_rearAuxM_button = QPushButton("选择车型")
        self.select_rearAuxM_button.setMenu(self.rearAuxM_menu)
        self.CurrentVehicleSpringPage(2)
        rearAuxMInfo = carsim.GetBlueLink('#BlueLink2')
        rearAuxMName = rearAuxMInfo[1]
        rearAuxMGroup = rearAuxMInfo[2]
        currentLibrary, currentDataset, currentCat, _ = carsim.GetBlueLink('#BlueLink2')
        if currentLibrary == 'Suspension: Auxiliary Roll Moment':
            for AuxMName in AuxMNames[rearAuxMGroup]:
                button = CustomCarPushButton(AuxMName, hasMenu=False, topWidget=self.select_rearAuxM_button)
                button.clicked.connect(self.onRearAuxMChange)
                action = QWidgetAction(self.rearAuxM_menu)
                action.setDefaultWidget(button)
                self.rearAuxM_menu.addAction(action)
        elif currentLibrary == 'Suspension: Measured Total Roll Stiffness':
            for MxTotMName in MxTotNames[rearAuxMGroup]:
                button = CustomCarPushButton(MxTotMName, hasMenu=False, topWidget=self.select_rearAuxM_button)
                button.clicked.connect(self.onRearAuxMChange)
                action = QWidgetAction(self.rearAuxM_menu)
                action.setDefaultWidget(button)
                self.rearAuxM_menu.addAction(action)
        else:
            pass
        # 初始化后轮稳定杆信息

        self.select_rearAuxM_button.setText(rearAuxMName)
        self.rearAuxMName = rearAuxMName
        self.form_layout.addRow(self.rearAuxRollMomentEditLabel, self.select_rearAuxM_button)

        self.rearAuxRollMoment_percentage = 0.0
        self.rearAuxRollMomentEditLabel_percent = QLabel("%+.1f%%" % self.rearAuxRollMoment_percentage)
        self.add_rearAuxRollMoment = QPushButton("+5%")
        self.add_rearAuxRollMoment.clicked.connect(lambda: self.add_subtract_button("Aux_rear_add"))
        self.subtract_rearAuxRollMoment = QPushButton("-5%")
        self.subtract_rearAuxRollMoment.clicked.connect(lambda: self.add_subtract_button("Aux_rear_subtract"))
        # self.rearAuxRollMoment_layout = QHBoxLayout()
        # self.rearAuxRollMoment_layout.addWidget(self.subtract_rearAuxRollMoment)
        # self.rearAuxRollMoment_layout.addWidget(self.add_rearAuxRollMoment)
        # self.form_layout_1.addRow(self.rearAuxRollMomentEditLabel_percent, self.rearAuxRollMoment_layout)
        carsim.GoHome()

    def clear(self):
        """
        删除D:\离线数据目录下的所有文件和文件夹
        注意：这是一个危险操作，会永久删除数据，请谨慎使用
        """
        # 指定要清空的目录
        target_dir = r"E:\01_TestData\01_DCH_Data\DCH\离线仿真"
        self.run_scheme=0
        # 安全检查：确认目录存在
        if not os.path.exists(target_dir):
            print(f"警告：目录 {target_dir} 不存在")
            return False

        try:
            # 方法1：删除目录下所有文件，但保留目录本身
            print(f"开始清空目录: {target_dir}")

            # 遍历目录中的所有文件和文件夹
            for item in os.listdir(target_dir):
                item_path = os.path.join(target_dir, item)

                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        # 删除文件或链接
                        os.unlink(item_path)
                        print(f"已删除文件: {item_path}")
                    elif os.path.isdir(item_path):
                        # 删除文件夹及其内容
                        shutil.rmtree(item_path)
                        print(f"已删除文件夹: {item_path}")
                except Exception as e:
                    print(f"删除 {item_path} 时出错: {e}")
            QMessageBox.information(self, '成功', '清理缓存成功')
            print(f"目录 {target_dir} 已清空")
            return True

        except Exception as e:
            print(f"清空目录时发生错误: {e}")
            return False

    def viewOfflineData(self):
        """跳转查看离线数据"""

        if self.tab_bump:
            self.tabs.setCurrentWidget(self.analysis_page_widget)
            self.sub_tabs.setCurrentWidget(self.tab_bump)
            input_dir = r'E:\01_TestData\01_DCH_Data\DCH\离线仿真'
            self.tab_bump.source_pane.rb_offline.setChecked(True)
            self.tab_bump.source_pane.fm.set_base_path(input_dir)
            self.tab_bump.source_pane._set_all(True)
            if not self.tab_bump.btn_run.isEnabled():
                QMessageBox.information(self, 'False',f"[{self.task_name}] 请检查数据sheet")
                return
            self.tab_bump._run()

            self._show_corner_message(f"Avy最优方案：方案{self.best}")


    def CurrentVehicleSpringPage(self, loc):
        carsim.GoHome()
        currentVehicleLibrary, currentVehicleDataset, currentVehicleCat, _ = carsim.GetBlueLink(
            '#BlueLink2')
        carsim.Gotolibrary(currentVehicleLibrary, currentVehicleDataset, currentVehicleCat)
        if loc == 1:
            springLibrary, springDataset, springCat, _ = carsim.GetBlueLink('#BlueLink16')
            if springLibrary == None:
                self.SendWarningMessage('警告', '前轮弹簧有误，请检查模型是否为#BlueLink16!')
            else:
                carsim.Gotolibrary(springLibrary, springDataset, springCat)
        else:
            springLibrary, springDataset, springCat, _ = carsim.GetBlueLink('#BlueLink17')
            if springLibrary == None:
                self.SendWarningMessage('警告', '后轮弹簧有误，请检查模型是否为#BlueLink17!')
            else:
                carsim.Gotolibrary(springLibrary, springDataset, springCat)

    def SendWarningMessage(self, message):
        QMessageBox.warning(self, message)

    def recordApplyTuningParam(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("方案记录")

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 添加标题
        title_label = QLabel("请选择要应用的方案")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 添加分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # 示例方案数据
        schemes = [
            "方案1: -15% -10% 0% 0%",
            "方案2: -15% 0% 0% 0%",
            "方案3: -15% 10% 0% 0%",
        ]

        # 存储方案按钮的引用
        self.scheme_buttons = []
        self.selected_scheme = None
        # 定义四个变量来存储百分数
        self.param1 = 0
        self.param2 = 0
        self.param3 = 0
        self.param4 = 0

        # 为每个方案创建按钮
        button_height = 50
        num = 0
        for scheme in schemes:
            btn = QPushButton(scheme)
            btn.setProperty("scheme", scheme)  # 存储方案信息
            btn.clicked.connect(lambda checked, b=btn: self.selectScheme(b))
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                }
                QPushButton[selected="true"] {
                    background-color: #4CAF50;
                    color: white;
                    border: 1px solid #45a049;
                }
            """)
            btn.setFixedHeight(button_height)
            layout.addWidget(btn)
            self.scheme_buttons.append(btn)
            num = num + 1
        layout.addStretch()
        #设置窗口大小
        dialog.setFixedSize(300, (num+3) * (button_height))
        # 添加确定按钮（初始状态不可用）
        self.btn_ok = QPushButton("确定")
        self.btn_ok.clicked.connect(
            lambda: self.Scheme_SetApplyTuningParam(dialog, self.param1, self.param2, self.param3, self.param4))
        self.btn_ok.setEnabled(False)  # 初始状态不可用
        self.btn_ok.setFixedHeight(40)
        self.btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:enabled {
                background-color: #4CAF50;
            }
            QPushButton:enabled:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        layout.addWidget(self.btn_ok)

        dialog.setLayout(layout)
        dialog.exec_()

    def Scheme_SetApplyTuningParam(self, dialog, param1, param2, param3, param4):
        self.frontSpringEditText.setValue(self.frontSpringRateValue_record * (param1 + 100) / 100)
        self.rearSpringEditText.setValue(self.rearSpringRateValue_record * (param2 + 100) / 100)
        self.frontAuxRollMomentEditText.setValue(self.frontAuxRollMomentValue_record * (param3 + 100) / 100)
        self.rearAuxRollMomentEditText.setValue(self.rearAuxRollMomentValue_record * (param4 + 100) / 100)
        self.ApplyTuningParam()
        dialog.accept()

    def selectScheme(self, button):
        # 重置所有按钮的样式
        for btn in self.scheme_buttons:
            btn.setProperty("selected", "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # 设置当前选中的按钮样式
        button.setProperty("selected", "true")
        button.style().unpolish(button)
        button.style().polish(button)

        # 存储选中的方案
        scheme_text = button.property("scheme")
        self.selected_scheme = scheme_text

        # 解析方案中的四个百分数
        try:
            # 提取百分数字符串部分（例如："0% 0% 0% 0%"）
            percent_part = scheme_text.split(":")[1].strip()
            # 分割字符串并去除%符号，转换为整数
            percentages = percent_part.split()

            if len(percentages) == 4:
                self.param1 = int(percentages[0].replace('%', ''))
                self.param2 = int(percentages[1].replace('%', ''))
                self.param3 = int(percentages[2].replace('%', ''))
                self.param4 = int(percentages[3].replace('%', ''))

                # print(f"解析成功: param1={self.param1}%, param2={self.param2}%, "
                #      f"param3={self.param3}%, param4={self.param4}%")
            else:
                print("错误: 方案格式不正确")
        except Exception as e:
            print(f"解析方案时出错: {e}")

        # 启用确定按钮
        self.btn_ok.setEnabled(True)

    def resetApplyTuningParam(self):
        self.frontSpringEditText.setValue(self.frontSpringRateValue_record)
        self.rearSpringEditText.setValue(self.rearSpringRateValue_record)
        self.frontAuxRollMomentEditText.setValue(self.frontAuxRollMomentValue_record)
        self.rearAuxRollMomentEditText.setValue(self.rearAuxRollMomentValue_record)
        self.ApplyTuningParam()

    def ApplyTuningParam(self):
        self.progress = QProgressDialog("应用中...", "取消", 0, 100, self)
        self.progress.setWindowTitle("虚拟调校")
        self.progress.setWindowModality(Qt.WindowModal)  # 设置为模态对话框
        self.progress.setMinimumSize(400, 100)  # 设置最小大小
        self.progress.setCancelButton(None)  # 禁用取消按钮
        self.progress.show()
        self.progress.setValue(0)
        self.progress.setLabelText("开始")
        QApplication.processEvents()  # 强制刷新界面
        self.progress.setLabelText("前轮弹簧刚度...")
        self.progress.setValue(25)
        # 前轮弹簧刚度
        if self.frontSpringRateValue != self.frontSpringEditText.value() and self.frontSpringMode == 1:
            self.frontSpringRateValue = self.frontSpringEditText.value()
            self.CurrentVehicleSpringPage(1)
            carsim.Yellow('*KSPRING_L', self.frontSpringRateValue)
            carsim.GoHome()

        elif self.frontSpringRateValue != self.frontSpringEditText.value() and self.frontSpringMode == 2:
            self.frontSpringRateValue = self.frontSpringEditText.value()
            self.CurrentVehicleSpringPage(1)
            currentSpringLibrary, currentSpringDataset, currentSpringCat, _ = carsim.GetBlueLink('#BlueLink0')
            carsim.Gotolibrary(currentSpringLibrary, currentSpringDataset, currentSpringCat)
            s = self.frontSpringRateValue
            fs = copy.deepcopy(self.front_fs_record)
            fs1 = copy.deepcopy(self.front_fs1_record)
            for j in range(len(fs)):
                fs[j] = list(fs[j])
                fs[j][1] = fs[j][1] * float(s)
            for j in range(len(fs1)):
                fs1[j] = list(fs1[j])
                fs1[j][1] = fs1[j][1] * float(s)
            carsim.SetTable('FS_COMP', fs)
            carsim.SetTable('FS_EXT', fs1)
            carsim.GoHome()
            if self.is_leftright_front:
                self.CurrentVehicleSpringPage(1)
                currentSpringLibrary, currentSpringDataset, currentSpringCat, _ = carsim.GetBlueLink('#BlueLink3')
                carsim.Gotolibrary(currentSpringLibrary, currentSpringDataset, currentSpringCat)
                s = self.frontSpringRateValue
                fs = copy.deepcopy(self.front_right_fs_record)
                fs1 = copy.deepcopy(self.front_right_fs1_record)
                for j in range(len(fs)):
                    fs[j] = list(fs[j])
                    fs[j][1] = fs[j][1] * float(s)
                for j in range(len(fs1)):
                    fs1[j] = list(fs1[j])
                    fs1[j][1] = fs1[j][1] * float(s)
                carsim.SetTable('FS_COMP', fs)
                carsim.SetTable('FS_EXT', fs1)
                carsim.GoHome()
        self.frontSpring_percentage = (
                                                  self.frontSpringRateValue - self.frontSpringRateValue_record) / self.frontSpringRateValue_record * 100
        self.frontSpringEditLabel_percent.setText("%+.1f%%" % self.frontSpring_percentage)
        self.progress.setLabelText("后轮弹簧刚度...")
        self.progress.setValue(50)
        # 后轮弹簧刚度
        if self.rearSpringRateValue != self.rearSpringEditText.value() and self.rearSpringMode == 1:
            self.rearSpringRateValue = self.rearSpringEditText.value()
            self.CurrentVehicleSpringPage(2)
            carsim.Yellow('*KSPRING_L', self.rearSpringRateValue)
            carsim.GoHome()

        elif self.rearSpringRateValue != self.rearSpringEditText.value() and self.rearSpringMode == 2:
            self.rearSpringRateValue = self.rearSpringEditText.value()
            self.CurrentVehicleSpringPage(2)
            currentSpringLibrary, currentSpringDataset, currentSpringCat, _ = carsim.GetBlueLink('#BlueLink0')
            carsim.Gotolibrary(currentSpringLibrary, currentSpringDataset, currentSpringCat)
            s = self.rearSpringRateValue
            fs = copy.deepcopy(self.rear_fs_record)
            fs1 = copy.deepcopy(self.rear_fs1_record)
            for j in range(len(fs)):
                fs[j] = list(fs[j])
                fs[j][1] = fs[j][1] * float(s)
            for j in range(len(fs1)):
                fs1[j] = list(fs1[j])
                fs1[j][1] = fs1[j][1] * float(s)
            carsim.SetTable('FS_COMP', fs)
            carsim.SetTable('FS_EXT', fs1)
            carsim.GoHome()
            if self.is_leftright_rear:
                self.CurrentVehicleSpringPage(2)
                currentSpringLibrary, currentSpringDataset, currentSpringCat, _ = carsim.GetBlueLink('#BlueLink3')
                carsim.Gotolibrary(currentSpringLibrary, currentSpringDataset, currentSpringCat)
                s = self.rearSpringRateValue
                fs = copy.deepcopy(self.rear_fs_record)
                fs1 = copy.deepcopy(self.rear_fs1_record)
                for j in range(len(fs)):
                    fs[j] = list(fs[j])
                    fs[j][1] = fs[j][1] * float(s)
                for j in range(len(fs1)):
                    fs1[j] = list(fs1[j])
                    fs1[j][1] = fs1[j][1] * float(s)
                carsim.SetTable('FS_COMP', fs)
                carsim.SetTable('FS_EXT', fs1)
                carsim.GoHome()
        self.rearSpring_percentage = (
                                             self.rearSpringRateValue - self.rearSpringRateValue_record) / self.rearSpringRateValue_record * 100
        self.rearSpringEditLabel_percent.setText("%+.1f%%" % self.rearSpring_percentage)
        self.progress.setLabelText("前轮稳定杆刚度...")
        self.progress.setValue(75)
        # 前轮稳定杆刚度
        if self.frontAuxRollMomentValue != self.frontAuxRollMomentEditText.value() and self.frontAuxRollMomentMode == 1:
            self.frontAuxRollMomentValue = self.frontAuxRollMomentEditText.value()
            self.CurrentVehicleSpringPage(1)
            ARMLibrary, ARMDataset, ARMCat, _ = carsim.GetBlueLink('#BlueLink2')
            carsim.Gotolibrary(ARMLibrary, ARMDataset, ARMCat)
            carsim.Yellow('*SCALAR', self.frontAuxRollMomentValue)
            carsim.GoHome()
        elif self.frontAuxRollMomentValue != self.frontAuxRollMomentEditText.value() and self.frontAuxRollMomentMode == 2:
            self.frontAuxRollMomentValue = self.frontAuxRollMomentEditText.value()
            self.CurrentVehicleSpringPage(1)
            ARMLibrary, ARMDataset, ARMCat, _ = carsim.GetBlueLink('#BlueLink2')
            carsim.Gotolibrary(ARMLibrary, ARMDataset, ARMCat)
            s = self.frontAuxRollMomentValue
            m = copy.deepcopy(self.front_m_record)
            for j in range(len(m)):
                m[j] = list(m[j])
                m[j][1] = m[j][1] * float(s)
            carsim.SetTable('MX_AUX', m)
            carsim.GoHome()
        elif self.frontAuxRollMomentValue != self.frontAuxRollMomentEditText.value() and self.frontAuxRollMomentMode == 3:
            self.frontAuxRollMomentValue = self.frontAuxRollMomentEditText.value()
            self.CurrentVehicleSpringPage(1)
            ARMLibrary, ARMDataset, ARMCat, _ = carsim.GetBlueLink('#BlueLink2')
            carsim.Gotolibrary(ARMLibrary, ARMDataset, ARMCat)
            s = self.frontAuxRollMomentValue
            m = copy.deepcopy(self.front_m_record)
            for j in range(len(m)):
                m[j] = list(m[j])
                m[j][1] = m[j][1] * float(s)
            carsim.SetTable('MX_TOTAL_TABLE', m)
            carsim.GoHome()
        self.frontAuxRollMoment_percentage = (
                                                     self.frontAuxRollMomentValue - self.frontAuxRollMomentValue_record) / self.frontAuxRollMomentValue_record * 100
        self.frontAuxRollMomentEditLabel_percent.setText("%+.1f%%" % self.frontAuxRollMoment_percentage)
        self.progress.setLabelText("后轮稳定杆刚度...")
        self.progress.setValue(100)
        # 后轮稳定杆刚度

        if self.rearAuxRollMomentValue != self.rearAuxRollMomentEditText.value() and self.rearAuxRollMomentMode == 1:
            self.rearAuxRollMomentValue = self.rearAuxRollMomentEditText.value()
            self.CurrentVehicleSpringPage(2)
            ARMLibrary, ARMDataset, ARMCat, _ = carsim.GetBlueLink('#BlueLink2')
            carsim.Gotolibrary(ARMLibrary, ARMDataset, ARMCat)
            carsim.Yellow('*SCALAR', self.rearAuxRollMomentValue)
            carsim.GoHome()
        elif self.rearAuxRollMomentValue != self.rearAuxRollMomentEditText.value() and self.frontAuxRollMomentMode == 2:
            self.rearAuxRollMomentValue = self.rearAuxRollMomentEditText.value()
            self.CurrentVehicleSpringPage(2)
            ARMLibrary, ARMDataset, ARMCat, _ = carsim.GetBlueLink('#BlueLink2')
            carsim.Gotolibrary(ARMLibrary, ARMDataset, ARMCat)
            s = self.rearAuxRollMomentValue
            m = copy.deepcopy(self.rear_m_record)
            for j in range(len(m)):
                m[j] = list(m[j])
                m[j][1] = m[j][1] * float(s)
            carsim.SetTable('MX_AUX', m)
            carsim.GoHome()
        elif self.rearAuxRollMomentValue != self.rearAuxRollMomentEditText.value() and self.frontAuxRollMomentMode == 3:
            self.rearAuxRollMomentValue = self.rearAuxRollMomentEditText.value()
            self.CurrentVehicleSpringPage(2)
            ARMLibrary, ARMDataset, ARMCat, _ = carsim.GetBlueLink('#BlueLink2')
            carsim.Gotolibrary(ARMLibrary, ARMDataset, ARMCat)
            s = self.rearAuxRollMomentValue
            m = copy.deepcopy(self.rear_m_record)
            for j in range(len(m)):
                m[j] = list(m[j])
                m[j][1] = m[j][1] * float(s)
            carsim.SetTable('MX_TOTAL_TABLE', m)
            carsim.GoHome()
        self.rearAuxRollMoment_percentage = (
                                                    self.rearAuxRollMomentValue - self.rearAuxRollMomentValue_record) / self.rearAuxRollMomentValue_record * 100
        self.rearAuxRollMomentEditLabel_percent.setText("%+.1f%%" % self.rearAuxRollMoment_percentage)
        # 关闭进度条
        self.progress.close()

    def get_unit(self, name):
        if name.startswith('pos'):
            return 'm'
        elif name.startswith('vel'):
            return 'm/s'
        elif name.startswith('acc'):
            return 'm/s²'
        elif name.startswith('ang'):
            return 'deg/s'
        elif name.startswith('ang_acc'):
            return 'deg/s²'
        elif name.startswith('throttle'):
            return '-'
        elif name.startswith('pbk_con'):
            return 'MPa'
        elif name.startswith('steering_speed'):
            return 'deg/s'
        elif name.startswith('Cmp'):
            return 'm/s'
        else:
            return 'deg'

    def toggle_plot_visibility(self, plot_name):
        self.update_plot_layout()

    def update_plot_layout(self):
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        visible_plots = [name for name, switch in self.plot_switches.items()
                         if switch.isChecked()]

        n = len(visible_plots)
        if n == 1:
            cols = 1
            rows = 1
        elif n == 2:
            cols = 1
            rows = 2
        elif n == 3:
            cols = 1
            rows = 3
        elif n <= 4:
            cols = 2
            rows = 2
        else:
            cols = 3
            rows = (n + 2) // 3

        for i, plot_name in enumerate(visible_plots):
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(self.plot_widgets[plot_name], row, col)

        if n == 1:
            self.plot_widgets[visible_plots[0]].setMinimumSize(self.grid_widget.size())
        elif n == 2:
            for plot_name in visible_plots:
                self.plot_widgets[plot_name].setMinimumSize(self.grid_widget.width(), self.grid_widget.height() // 2)
        elif n == 3:
            for plot_name in visible_plots:
                self.plot_widgets[plot_name].setMinimumSize(self.grid_widget.width(), self.grid_widget.height() // 3)
        elif n <= 4:
            for plot_name in visible_plots:
                self.plot_widgets[plot_name].setMinimumSize(self.grid_widget.width() // 2,
                                                            self.grid_widget.height() // 2)
        else:
            for plot_name in visible_plots:
                self.plot_widgets[plot_name].setMinimumSize(0, 0)

    # def process_pending_datagrams(self):
    #     while self.udp_socket.hasPendingDatagrams():
    #         datagram, host, port = self.udp_socket.readDatagram(
    #             self.udp_socket.pendingDatagramSize()
    #         )
    #         try:
    #             import struct
    #             num_floats = len(datagram) // 4  # single类型，每个4字节
    #
    #             if num_floats >= 36:  # 确保数据包包含至少36个浮点数
    #                 # 使用反转后的字节数据解析浮点数
    #                 data = struct.unpack('!' + 'f' * num_floats, datagram)
    #                 current_time = time.perf_counter() - self.start_time
    #                 self.time_data_imu.append(current_time)
    #                 self.time_data_imu_all.append(current_time)
    #
    #                 # 数据分组：第13到第30个数据为moog数据
    #                 moog_data = data[12:30]  # 第13到第30个数据（Python索引从0开始）
    #
    #                 # 定义信号类型和通道
    #                 signals = ['input','moog','imu']
    #                 channels = list(self.signal_data.keys())
    #
    #                 # 将moog数据存储到对应的通道中
    #                 for i, channel in enumerate(channels):
    #                     value = moog_data[i]  # 每个通道对应一个moog数据
    #                     self.signal_data[channel]['moog'].append(value)
    #                     self.signal_data[channel]['input'].append(0)
    #                     self.signal_data[channel]['imu'].append(0)
    #                     self.signal_data_all[channel]['moog'].append(value)
    #                     self.signal_data_all[channel]['input'].append(0)
    #                     self.signal_data_all[channel]['imu'].append(0)
    #                 # print(f"接收到数据包: {len(data)} 个数据点")
    #         except Exception as e:
    #             print(f"数据处理错误: {e}")
    #             print(f"原始数据长度: {len(datagram)} 字节")
    #
    #     current_time = time.perf_counter() - self.start_time
    #     cutoff_time = current_time - 10
    #     num_deletions = max((len(self.time_data_imu) - 11000) // 1000,0)
    #
    #     while num_deletions > 0:
    #         print(len(self.time_data_imu))
    #         for _ in range(1000):
    #             if self.time_data_imu:  # 确保队列不为空
    #                 self.time_data_imu.popleft()
    #         for channel in self.signal_data:
    #             for signal in ['input', 'moog', 'imu']:
    #                 for _ in range(1000):
    #                     if self.signal_data[channel][signal]:  # 确保队列不为空
    #                         self.signal_data[channel][signal].popleft()
    #         num_deletions = max((len(self.time_data_imu) - 10000) // 1000, 0)

    def update_plots(self):
        if len(self.time_data_imu) == 0 and len(self.time_data_carsim) == 0 and len(self.time_data_moog) == 0:
            self.start_time = time.perf_counter()
            return
        current_time = time.perf_counter() - self.start_time
        if not self.plot_running:
            return
        # 固定横坐标范围，始终显示最近10秒的数据
        for plot in self.plots.values():
            plot.setXRange(current_time - 10, current_time)
            # if plot.getAxis("left").labelText == 'Steer_SW(deg)':
            #     plot.setTitle(f'方向盘转角：{self.signal_steer_angle:+.1f}度', color='k')

        time_array_imu = np.array(self.time_data_imu)
        time_array_carsim = np.array(self.time_data_carsim)
        time_array_moog = np.array(self.time_data_moog)

        # 更新纵坐标范围
        for channel, curves in self.curves.items():
            if self.plot_switches[channel].isChecked():
                data_input = np.array(self.signal_data[channel]['input'])
                data_moog = np.array(self.signal_data[channel]['moog'])
                data_imu = np.array(self.signal_data[channel]['imu'])

                # 计算当前数据的范围
                y_min = min(np.min(data_input if len(data_input) > 0 else [0]),
                            np.min(data_moog if len(data_moog) > 0 else [0]),
                            np.min(data_imu if len(data_imu) > 0 else [0]))
                y_max = max(np.max(data_input if len(data_input) > 0 else [0]),
                            np.max(data_moog if len(data_moog) > 0 else [0]),
                            np.max(data_imu if len(data_imu) > 0 else [0]))

                # # 如果数据范围无效，跳过
                # if np.isnan(y_min) or np.isnan(y_max):
                #     continue
                #
                # # 初始化纵坐标范围缓存和上次变化时间
                # if channel not in self.y_range_cache:
                #     self.y_range_cache[channel] = {'y_min': y_min, 'y_max': y_max}
                #     self.last_signal_change_time[channel] = time.perf_counter()  # 初始化上次变化时间
                # else:
                #     # 检查信号是否有变化
                #     if y_min != self.y_range_cache[channel]['y_min'] or y_max != self.y_range_cache[channel]['y_max']:
                #
                #
                #         # 只允许纵坐标范围增大，不允许缩小（除非超时）
                #         current_real_time = time.perf_counter()
                #         if current_real_time - self.last_signal_change_time[channel] > self.y_range_timeout:
                #             # 超时后允许纵坐标范围缩小
                #             self.y_range_cache[channel]['y_min'] = y_min
                #             self.y_range_cache[channel]['y_max'] = y_max
                #             self.last_signal_change_time[channel] = time.perf_counter()  # 更新上次变化时间
                #         else:
                #             # 只允许纵坐标范围增大
                #             self.y_range_cache[channel]['y_min'] = min(self.y_range_cache[channel]['y_min'], y_min)
                #             self.y_range_cache[channel]['y_max'] = max(self.y_range_cache[channel]['y_max'], y_max)
                #             self.last_signal_change_time[channel] = time.perf_counter()  # 更新上次变化时间

                # 使用滑动平均值平滑纵坐标范围
                # smoothed_y_min = (1 - self.y_range_smoothing_factor) * self.y_range_cache[channel][
                #    'y_min'] + self.y_range_smoothing_factor * y_min
                # smoothed_y_max = (1 - self.y_range_smoothing_factor) * self.y_range_cache[channel][
                #    'y_max'] + self.y_range_smoothing_factor * y_max

                # 增加缓冲区域
                # y_range_buffer = 0.1 * (smoothed_y_max - smoothed_y_min)
                # final_y_min = smoothed_y_min - y_range_buffer
                # final_y_max = smoothed_y_max + y_range_buffer
                y_range_buffer = 0.1 * (y_max - y_min)
                final_y_min = y_min - y_range_buffer
                final_y_max = y_max + y_range_buffer

                # 设置纵坐标范围
                try:
                    self.plots[channel].setYRange(final_y_min, final_y_max)
                except Exception as e:
                    continue

        # 更新曲线数据
        for channel, curves in self.curves.items():
            if self.plot_switches[channel].isChecked():
                for signal_type, curve in curves.items():
                    if signal_type == 'input':
                        plot_time_input = time_array_carsim[:min(len(time_array_carsim),
                                                                 len(np.array(self.signal_data[channel]['input'])))][
                                          ::self.plot_sample_carsim]
                        plot_data_input = np.array(self.signal_data[channel]['input'])[:min(len(time_array_carsim),
                                                                                            len(np.array(
                                                                                                self.signal_data[
                                                                                                    channel][
                                                                                                    'input'])))][
                                          ::self.plot_sample_carsim]
                        # plot_data = np.array(self.signal_data[channel][signal_type])[::self.plot_sample_carsim]
                        curve.setData(plot_time_input, plot_data_input)
                    elif signal_type == 'imu':
                        plot_time_imu = time_array_imu[
                                        :min(len(time_array_imu), len(np.array(self.signal_data[channel]['imu'])))][
                                        ::self.plot_sample_imu]
                        plot_data_imu = np.array(self.signal_data[channel]['imu'])[
                                        :min(len(time_array_imu), len(np.array(self.signal_data[channel]['imu'])))][
                                        ::self.plot_sample_imu]
                        # plot_data = np.array(self.signal_data[channel][signal_type])[::self.plot_sample_imu]
                        curve.setData(plot_time_imu, plot_data_imu)

                    else:
                        plot_time_moog = time_array_moog[
                                         :min(len(time_array_moog), len(np.array(self.signal_data[channel]['moog'])))][
                                         ::self.plot_sample_moog]
                        plot_data_moog = np.array(self.signal_data[channel]['moog'])[
                                         :min(len(time_array_moog), len(np.array(self.signal_data[channel]['moog'])))][
                                         ::self.plot_sample_moog]
                        # plot_data = np.array(self.signal_data[channel][signal_type])[::self.plot_sample_moog]
                        curve.setData(plot_time_moog, plot_data_moog)
                # === 报警检查 ===
                # 只在报警开启时检查
                alarm_status = {'vel_x': False, 'steering_angle': False, 'steering_speed': False}

                if self.alarm_enabled:
                    # 检查每个需要报警的信号
                    for channel in ['vel_x', 'steering_angle', 'steering_speed']:
                        if not self.plot_switches[channel].isChecked():
                            continue

                        # 检查三条曲线的最新值
                        for signal_type in ['input']:
                            data = self.signal_data[channel][signal_type]
                            if not data:
                                continue

                            latest_value = data[-1]

                            # 检查是否超出阈值
                            if self.check_alarm(channel, latest_value):
                                alarm_status[channel] = True
                                break

                    # 更新报警指示器
                for channel, status in alarm_status.items():
                    indicator = self.alarm_indicators.get(channel)
                    if indicator:
                        # 设置报警文本
                        if status:
                            indicator.setText('⚠️ 超出阈值!')
                        else:
                            indicator.setText('')

                        # 获取当前视图范围
                        view_range = self.plots[channel].viewRange()
                        if view_range:
                            # 计算图表中心位置
                            x_center = (view_range[0][0] + view_range[0][1]) / 2
                            y_center = (view_range[1][0] + view_range[1][1]) / 2

                            # 设置指示器位置在图表中心
                            indicator.setPos(x_center, y_center)


                        else:
                            # 如果无法获取视图范围，使用默认位置
                            indicator.setPos(0, 0)
                        indicator.setVisible(True)
        self.update_haptic_plots()
        self.steer_angle_value_label.setText("方向盘转角：%+.1f" % self.signal_steer_angle)
        #self.xy_coordinate_value_label.setText("x：%+.1f, y:%+.1f" % (self.signal_rfpro_x_coordinate ,self.signal_rfpro_y_coordinate))

    def clear_plots(self):
        # 重置时间
        self.start_time = time.perf_counter()
        self.start_time1 = time.time()
        # 清空所有数据
        self.time_data_imu.clear()
        self.time_data_carsim.clear()
        # self.time_data_imu_all.clear()
        # self.time_data_carsim_all.clear()
        self.time_data_moog.clear()
        # self.time_data_moog_all.clear()
        self.f_data.clear()
        for channel in self.signal_data.keys():
            for signal_type in ['input', 'moog', 'imu']:
                self.signal_data[channel][signal_type].clear()
                # self.signal_data_all[channel][signal_type].clear()
        self.signal_data['steering_angle']['input'].clear()

        self.signal_data['throttle']['input'].clear()

        self.signal_data['pbk_con']['input'].clear()

        self.signal_data['steering_speed']['input'].clear()

        # 重置纵坐标范围
        for channel, plot in self.plots.items():
            plot.setXRange(0, 10)  # 重置横坐标范围
            plot.setYRange(-1, 1)  # 重置纵坐标范围为默认值，可以根据需要调整
        self.sw_plot.setXRange(0, 10)
        self.f_plot.setXRange(0, 10)
        # 清空纵坐标范围缓存
        self.y_range_cache.clear()
        self.last_signal_change_time.clear()

        # 清空图表中的曲线
        for channel, curves in self.curves.items():
            for signal_type, curve in curves.items():
                curve.setData([], [])  # 清空曲线数据

    def toggle_plotting(self, checked):
        self.plot_running = checked
        self.is_running = checked  # 更新标志状态
        # if checked:
        #     # 如果有数据，从最后一个时间点继续
        #     self.start_time = time.perf_counter() - (self.time_data_carsim[-1] if self.time_data_carsim else 0)

    def electrol_recording(self, checked):
        self.record_disusx = checked

    def rename_folder_name(self,checked):
        self.is_rename_folder_name = checked
        print(self.is_rename_folder_name)
    def par_recording(self,checked):
        self.is_par_save = checked

    def auto_recording(self, checked):
        self.auto_record = checked
        if self.auto_record == 0:
            print("关闭自动记录")
        else:
            print("开启自动记录")
        #self.dialog.close()
        #self.record_settings_dialog()

    def video_recording(self, checked):
        self.is_video_recording = checked
        if checked:
            # 发送is_video_recording
            self.sendData2camera(0, 1)
        else:
            self.sendData2camera(0, 0)

    # def plot_lastrecord(self):
    #     self.run_button.setChecked(False)
    #     self.plot_running = False
    #     # 创建进度条对话框
    #     self.progress = QProgressDialog("显示记录中...", "取消", 0, 100, self)
    #     self.progress.setWindowTitle("显示记录")
    #     self.progress.setWindowModality(Qt.WindowModal)  # 设置为模态对话框
    #     self.progress.setMinimumSize(400, 100)  # 设置最小大小
    #     self.progress.setCancelButton(None)  # 禁用取消按钮
    #     self.progress.show()
    #
    #     self.progress.setValue(0)
    #     self.progress.setLabelText("更新中")
    #     QApplication.processEvents()  # 强制刷新界面
    #
    #     InputLength = self.finish_record_input_index - self.start_record_input_index
    #     MoogLength = self.finish_record_moog_index - self.start_record_moog_index
    #     ImuLength = self.finish_record_imu_index - self.start_record_imu_index
    #     AllLength = InputLength + MoogLength + ImuLength
    #     count = 0
    #     for channel, curves in self.curves.items():
    #             for signal_type, curve in curves.items():
    #                 if signal_type == 'input':
    #                     curve.setData(np.array(self.time_data_carsim_all)[self.start_record_input_index:self.finish_record_input_index], np.array(self.signal_data_all[channel][signal_type])[self.start_record_input_index:self.finish_record_input_index])
    #                 elif signal_type == 'imu':
    #                     curve.setData(np.array(self.time_data_imu_all)[self.start_record_imu_index:self.finish_record_imu_index], np.array(self.signal_data_all[channel][signal_type])[self.start_record_imu_index:self.finish_record_imu_index])
    #                 else:
    #                     curve.setData(np.array(self.time_data_moog_all)[self.start_record_moog_index:self.finish_record_moog_index], np.array(self.signal_data_all[channel][signal_type])[self.start_record_moog_index:self.finish_record_moog_index])
    #                 count += 1
    #                 self.progress.setValue(int(count/54 *100))
    #             y_min = min(np.min(np.array(self.signal_data_all[channel]['input'])[self.start_record_input_index:self.finish_record_input_index] if len(self.time_data_carsim_all)>0 else [0]),
    #                         np.min(np.array(self.signal_data_all[channel]['moog'])[self.start_record_moog_index:self.finish_record_moog_index] if len(self.time_data_moog_all)>0 else [0]),
    #                         np.min(np.array(self.signal_data_all[channel]['imu'])[self.start_record_imu_index:self.finish_record_imu_index] if len(self.time_data_imu_all)>0 else [0]))
    #             y_max = max(np.max(np.array(self.signal_data_all[channel]['input'])[self.start_record_input_index:self.finish_record_input_index] if len(self.time_data_carsim_all)>0 else [0]),
    #                         np.max(np.array(self.signal_data_all[channel]['moog'])[self.start_record_moog_index:self.finish_record_moog_index] if len(self.time_data_moog_all)>0 else [0]),
    #                         np.max(np.array(self.signal_data_all[channel]['imu'])[self.start_record_imu_index:self.finish_record_imu_index] if len(self.time_data_imu_all)>0 else [0]))
    #             self.plots[channel].setYRange(y_min, y_max)
    #     for plot in self.plots.values():
    #         plot.setXRange(self.record_start_time_last-self.start_time,self.record_finish_time_last-self.start_time)
    #     self.progress.close()
    def stop_plotting(self):
        self.run_button.setChecked(False)
        self.plot_running = False
        # for channel, curves in self.curves.items():
        #         for signal_type, curve in curves.items():
        #             if signal_type == 'input':
        #                 curve.setData(np.array(self.time_data_carsim_all)[:min(len(self.time_data_carsim_all),len(self.signal_data_all[channel][signal_type]))],
        #                               np.array(self.signal_data_all[channel][signal_type])[:min(len(self.time_data_carsim_all),len(self.signal_data_all[channel][signal_type]))])
        #             elif signal_type == 'imu':
        #                 curve.setData(np.array(self.time_data_imu_all)[:min(len(self.time_data_imu_all),len(self.signal_data_all[channel][signal_type]))],
        #                               np.array(self.signal_data_all[channel][signal_type])[:min(len(self.time_data_imu_all),len(self.signal_data_all[channel][signal_type]))])
        #             else:
        #                 curve.setData(np.array(self.time_data_moog_all)[:min(len(self.time_data_moog_all),len(self.signal_data_all[channel][signal_type]))],
        #                               np.array(self.signal_data_all[channel][signal_type])[:min(len(self.time_data_moog_all),len(self.signal_data_all[channel][signal_type]))])
        #         y_min = min(np.min(self.signal_data_all[channel]['input'] if len(self.signal_data_all[channel]['input'])>0 else [0]),
        #                     np.min(self.signal_data_all[channel]['moog'] if len(self.signal_data_all[channel]['moog'])>0 else [0]),
        #                     np.min(self.signal_data_all[channel]['imu'] if len(self.signal_data_all[channel]['imu'])>0 else [0]))
        #         y_max = max(np.max(self.signal_data_all[channel]['input'] if len(self.signal_data_all[channel]['input'])>0 else [0]),
        #                     np.max(self.signal_data_all[channel]['moog'] if len(self.signal_data_all[channel]['moog'])>0 else [0]),
        #                     np.max(self.signal_data_all[channel]['imu'] if len(self.signal_data_all[channel]['imu'])>0 else [0]))
        #         self.plots[channel].setYRange(y_min, y_max)

    def send_signal(self):
        try:
            algorithm = self.algo_group.checkedButton()
            if algorithm is None:
                print("请选择算法")
                return

            algorithm = algorithm.text()
            signal_type = self.signal_combo.currentText()

            # 获取参数值
            params = {}
            for name, input_field in self.param_inputs.items():
                text = input_field.text()
                if not text:
                    print(f"请输入{name}")
                    return
                try:
                    params[name] = float(text)
                except ValueError:
                    print(f"{name}必须是数字")
                    return

            # 构建要发送的数据
            data = f"{algorithm},{signal_type}"
            for param, value in params.items():
                data += f",{value}"

        except Exception as e:
            print(f"发送信号错误: {e}")

    def one_click_start(self):
        """实现一键启动的逻辑"""
        try:
            # 第一步：发送 Control Command = 6
            self.send_control_command(6)
            self.control_command_input.setText("6")  # 更新输入框的值
            QTimer.singleShot(200, lambda: self._one_click_step(2))  # 200ms后执行下一步
        except Exception as e:
            QMessageBox.warning(self, "错误", f"一键启动失败: {e}")

    def _one_click_step(self, value):
        """内部方法，用于分步执行一键启动的后续步骤"""
        try:
            self.send_control_command(value)
            self.control_command_input.setText(str(value))  # 更新输入框的值
            if value == 2:
                QTimer.singleShot(200, lambda: self._one_click_step(4))  # 200ms后执行下一步
        except Exception as e:
            QMessageBox.warning(self, "错误", f"一键启动失败: {e}")

    def one_click_stop(self):
        """实现一键关闭的逻辑"""
        try:
            # 第一步：发送 Control Command = 1
            # self.send_control_command(1)
            QTimer.singleShot(200, lambda: self.send_control_command(1))
            QTimer.singleShot(200, lambda: self.control_command_input.setText("1"))  # 更新输入框的值
            # 0.2秒后发送 Control Command = 0
            QTimer.singleShot(200, lambda: self.send_control_command(0))
            QTimer.singleShot(200, lambda: self.control_command_input.setText("0"))  # 更新输入框的值
        except Exception as e:
            QMessageBox.warning(self, "错误", f"一键关闭失败: {e}")

    def send_control_command(self, value):
        """发送 Control Command 值"""
        try:
            self.sendData2PlatformControl(0, value)
            print(f"Control Command 值已发送: {value}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"发送 Control Command 失败: {e}")

    def mode_changed(self):
        mode = self.mode_combo.currentText()
        params = {
            "舒适方案": "减震系数: 0.8\n响应速度: 中等\n最大加速度: 0.3g\n最大角速度: 15°/s",
            "赛道方案": "减震系数: 0.4\n响应速度: 快速\n最大加速度: 0.6g\n最大角速度: 30°/s",
            "极限方案": "减震系数: 0.2\n响应速度: 极快\n最大加速度: 0.9g\n最大角速度: 45°/s",
            "自定义方案": "参数配置中..."
        }
        self.param_label.setText(params.get(mode, "未知方案"))

    def apply_mode(self):
        try:
            mode = self.mode_combo.currentText()
            data = f"MODE_CHANGE,{mode}"
            # self.udp_socket.writeDatagram(
            #     data.encode(),
            #     QHostAddress("127.0.0.1"),
            #     12346
            # )
        except Exception as e:
            print(f"应用方案错误: {e}")

    def load_plot_state(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    if 'plot_states' in state:
                        for plot_name, checked in state['plot_states'].items():
                            if plot_name in self.plot_switches:
                                self.plot_switches[plot_name].setChecked(checked)
            except Exception as e:
                print(f"加载配置文件出错: {e}")

    def save_plot_state(self):
        state = {plot_name: switch.isChecked() for plot_name, switch in self.plot_switches.items()}
        with open(self.config_file, 'w') as f:
            json.dump(state, f)

    def closeEvent(self, event):
        # if self.frontSpring_percentage != 0 or self.rearSpring_percentage != 0 or self.frontAuxRollMoment_percentage != 0 or self.rearAuxRollMoment_percentage != 0:
        #     result = QMessageBox.warning(
        #         self,
        #         "警告",
        #         "未重置车辆参数,确定要退出吗？",
        #         QMessageBox.Yes | QMessageBox.Cancel
        #     )
        #     if result == QMessageBox.Yes:
        #         self.save_ui_state()
        #         self.save_sampling_rates()
        #         self.save_haptic_gain()
        #         save_carsimdatabase(self.carsim_db_path)
        #         # cmd = 'taskkill /im carsim.exe'
        #         # os.system(cmd)
        #         super().closeEvent(event)
        #     else:
        #         event.ignore()
        # else:
        self.save_ui_state()
        self.save_sampling_rates()
        self.save_haptic_gain()
        #save_carsimdatabase(self.carsim_db_path)
        # cmd = 'taskkill /im carsim.exe'
        # os.system(cmd)
        super().closeEvent(event)

    def toggle_all_plots_on(self):
        """将所有图表的开关设置为打开状态"""
        for switch in self.plot_switches.values():
            switch.setChecked(True)
        self.update_plot_layout()

    def toggle_all_plots_off(self):
        """将所有图表的开关设置为关闭状态"""
        for switch in self.plot_switches.values():
            switch.setChecked(False)
        self.update_plot_layout()

    def toggle_all_signal(self):
        quantity = int(self.quantity_combo.currentText())
        if self.signal_toggle_button.isChecked():
            self.signal_toggle_button.setText("全部停止")
            # 遍历所有信号参数窗口
            for i in range(0, quantity):
                self.signal_param_widgets[i].findChild(QPushButton).setChecked(True)
                self.toggle_signal(i)
        else:
            self.signal_toggle_button.setText("全部启动")
            for i in range(0, quantity):
                self.signal_param_widgets[i].findChild(QPushButton).setChecked(False)
                self.toggle_signal(i)

    def toggle_signal(self, signal_number):
        """切换信号发送状态"""
        if self.signal_param_widgets[signal_number].findChild(QPushButton).isChecked():
            self.signal_param_widgets[signal_number].findChild(QPushButton).setText("停止信号")

            self.start_signal_thread(signal_number)  # 启动信号发送线程

        else:
            self.signal_param_widgets[signal_number].findChild(QPushButton).setText("启动信号")
            self.stop_signal_thread(signal_number)  # 停止信号发送线程

    def stop_signal_thread(self, signal_number):
        """停止信号发送线程"""

        if signal_number in self.signal_threads and self.signal_threads[signal_number].isRunning():
            self.signal_threads[signal_number].stop()  # 停止线程
            self.signal_threads[signal_number].wait()  # 等待线程结束
            del self.signal_threads[signal_number]  # 从字典中移除线程
            signal_type = self.signal_param_widgets[signal_number].findChild(QComboBox).currentText()
            signal_index = self.get_index_from_signal_type(signal_type)
            # 停止信号时发送0
            self.sendData2Moog(signal_index, 0)

    def start_signal_thread(self, signal_number):
        """启动信号发送线程"""
        try:
            print(f"Starting signal thread for signal number: {signal_number}")
            signal_type = self.signal_combo.currentText()

            if signal_type == "自定义信号":
                # 自定义信号处理逻辑（保持不变）
                time_var_name = self.signal_param_widgets[signal_number].findChild(QComboBox,
                                                                                   "time_combo").currentText()
                value_var_name = self.signal_param_widgets[signal_number].findChild(QComboBox,
                                                                                    "value_combo").currentText()
                time_var = self.workspace_variables.get(time_var_name)
                value_var = self.workspace_variables.get(value_var_name)

                if time_var is None or value_var is None:
                    QMessageBox.warning(self, "错误", "未找到指定的时间或值变量！")
                    self.reset_signal_button(signal_number)
                    return

                time_var = np.array(time_var).flatten()
                value_var = np.array(value_var).flatten()

                if len(time_var) != len(value_var):
                    QMessageBox.warning(self, "错误", "时间变量和值变量的长度不一致！")
                    self.reset_signal_button(signal_number)
                    return

                gain = float(self.signal_param_widgets[signal_number].findChild(QLineEdit).text()) if \
                    self.signal_param_widgets[signal_number].findChild(QLineEdit) else 1.0

            elif signal_type == "函数信号":
                # 函数信号处理逻辑
                temp = self.signal_param_widgets[signal_number]
                waveform = self.signal_param_widgets[signal_number].findChild(QComboBox, "waveform_combo").currentText()

                # 获取参数值
                amplitude = float(self.signal_input_fields[0].text())  # 振幅
                period = float(self.signal_input_fields[1].text())  # 周期
                bias = float(self.signal_input_fields[2].text())  # 偏置
                phase = float(self.signal_input_fields[3].text())  # 过渡时间/相位

                # 生成时间序列（默认5秒，1000Hz采样率）
                time_var = np.arange(0, period, 0.001)

                # 根据波形类型生成信号
                if waveform == "Sine":
                    # 正弦波: A*sin(2πt/T + φ) + bias
                    value_var = amplitude * np.sin(2 * np.pi * time_var / period + phase) + bias
                elif waveform == "Square":
                    # 方波
                    value_var = amplitude * np.sign(np.sin(2 * np.pi * time_var / period + phase)) + bias
                elif waveform == "Sawtooth":
                    # 锯齿波
                    value_var = amplitude * (time_var % period) / period + bias
                elif waveform == "Value":
                    # 固定值
                    value_var = np.full_like(time_var, amplitude + bias)
                else:
                    value_var = time_var
                gain = 1.0  # 函数信号模式下gain固定为1.0

            # 获取信号类型和索引
            signal_type_combo = self.signal_param_widgets[signal_number].findChild(QComboBox)
            signal_type = signal_type_combo.currentText()
            signal_index = self.get_index_from_signal_type(signal_type)

            # print(f"Current signal index: {signal_index}")

            # 创建并启动信号发送线程
            self.signal_threads[signal_number] = SignalSenderThread(
                time_var,
                value_var,
                self.udp_socket,
                signal_index,
                gain,
                parent=self
            )
            self.signal_threads[signal_number].start()

        except ValueError as e:
            QMessageBox.warning(self, "错误", f"参数值无效: {e}")
            self.reset_signal_button(signal_number)
        except Exception as e:
            print(e)
            QMessageBox.warning(self, "错误", f"启动信号发送失败: {e}")
            self.reset_signal_button(signal_number)

    def reset_signal_button(self, signal_number):
        """重置信号按钮状态"""
        button = self.signal_param_widgets[signal_number].findChild(QPushButton)
        button.setText("启动信号")
        button.setChecked(False)

    def get_index_from_signal_type(self, signal_type):
        signal_type_mapping = {
            "加速度x": 2,
            "加速度y": 3,
            "加速度z": 4,
            "角加速度x": 5,
            "角加速度y": 6,
            "角加速度z": 7,
            "位移x": 8,
            "位移y": 9,
            "位移z": 10,
            "角度x(Roll)": 11,
            "角度y(Pitch)": 12,
            "角度z(Yaw)": 13,
            "速度x": 15,
            "速度y": 18,
            "速度z": 21,
            "角速度x": 24,
            "角速度y": 27,
            "角速度z": 30,
        }
        return signal_type_mapping.get(signal_type, 1)  # 默认返回1

    def onCarChange(self, text):
        if self.carName != self.select_car_button.text():
            self.carName = self.select_car_button.text()
            image = QImage(vehicleImagePath[self.carName])  # 替换为你的图像路径
            pixmap = QPixmap.fromImage(image)
            self.carImage.setPixmap(pixmap)
            vehicleInfo = vehicleInfoDic[self.carName]
            pattern = r"(.*):<(.*?)>(.*)"
            match = re.search(pattern, vehicleInfo)
            group = match.group(2)
            carsim.GoHome()
            carsim.BlueLink('#BlueLink2', 'Vehicle: Assembly', self.carName, group)
            self.UpdateTuningParam()
    def onFrontSpringChange(self, text):
        self.frontSpring_menu.close()
        if self.frontSpringName != self.select_frontSpring_button.text():
            self.frontSpringName = self.select_frontSpring_button.text()
            self.CurrentVehicleSpringPage(1)
            # springInfo = springInfoDic[self.frontSpringName]
            # pattern = r"(.*):<(.*?)>(.*)"
            # match = re.search(pattern, springInfo)
            # group = match.group(2)
            group = carsim.GetBlueLink('#BlueLink0')[2]
            carsim.BlueLink('#BlueLink0', 'Suspension: Spring', self.frontSpringName, group)
            carsim.GoHome()
    def onFrontRightSpringChange(self, text):
        self.frontRightSpring_menu.close()
        if self.frontRightSpringName != self.select_frontRightSpring_button.text():
            self.frontRightSpringName = self.select_frontRightSpring_button.text()
            self.CurrentVehicleSpringPage(1)
            # springInfo = springInfoDic[self.frontRightSpringName]
            # pattern = r"(.*):<(.*?)>(.*)"
            # match = re.search(pattern, springInfo)
            # group = match.group(2)
            group = carsim.GetBlueLink('#BlueLink3')[2]

            carsim.BlueLink('#BlueLink3', 'Suspension: Spring', self.frontRightSpringName, group)
            carsim.GoHome()
    def onRearSpringChange(self, text):
        self.rearSpring_menu.close()
        if self.rearSpringName != self.select_rearSpring_button.text():
            self.rearSpringName = self.select_rearSpring_button.text()
            self.CurrentVehicleSpringPage(2)
            # springInfo = springInfoDic[self.rearSpringName]
            # pattern = r"(.*):<(.*?)>(.*)"
            # match = re.search(pattern, springInfo)
            # group = match.group(2)
            group = carsim.GetBlueLink('#BlueLink0')[2]
            carsim.BlueLink('#BlueLink0', 'Suspension: Spring', self.rearSpringName, group)
            carsim.GoHome()
    def onRearRightSpringChange(self, text):
        self.rearRightSpring_menu.close()
        if self.rearRightSpringName != self.select_rearRightSpring_button.text():
            self.rearRightSpringName = self.select_rearRightSpring_button.text()
            self.CurrentVehicleSpringPage(2)
            # springInfo = springInfoDic[self.rearRightSpringName]
            # pattern = r"(.*):<(.*?)>(.*)"
            # match = re.search(pattern, springInfo)
            # group = match.group(2)
            group = carsim.GetBlueLink('#BlueLink3')[2]
            carsim.BlueLink('#BlueLink3', 'Suspension: Spring', self.rearRightSpringName, group)
            carsim.GoHome()
    def onFrontAuxMChange(self, text):
        self.frontAuxM_menu.close()
        if self.frontAuxMName != self.select_frontAuxM_button.text():
            self.frontAuxMName = self.select_frontAuxM_button.text()
            self.CurrentVehicleSpringPage(1)
            if carsim.GetBlueLink('#BlueLink2')[0] == 'Suspension: Auxiliary Roll Moment':
                # AuxMInfo = AuxMInfoDic[self.frontAuxMName]
                # pattern = r"(.*):<(.*?)>(.*)"
                # match = re.search(pattern, AuxMInfo)
                # group = match.group(2)
                group = carsim.GetBlueLink('#BlueLink2')[2]
                carsim.BlueLink('#BlueLink2', 'Suspension: Auxiliary Roll Moment', self.frontAuxMName, group)

                ARMLibrary, ARMDataset, ARMCat, _ = carsim.GetBlueLink('#BlueLink2')
                carsim.Gotolibrary(ARMLibrary, ARMDataset, ARMCat)
                ringName = carsim.GetRing('#RingCtrl0')
                if ringName == 'CONSTANT' or ringName == 'COEFFICIENT':
                    frontAuxRollMomentValue = float(carsim.GetYellow('*SCALAR'))
                    self.CurrentVehicleSpringPage(1)
                    carsim.Yellow('DAUX', frontAuxRollMomentValue*0.01)
            else:
                # MxTotInfo = MxTotInfoDic[self.frontAuxMName]
                # pattern = r"(.*):<(.*?)>(.*)"
                # match = re.search(pattern, MxTotInfo)
                # group = match.group(2)
                group = carsim.GetBlueLink('#BlueLink2')[2]
                carsim.BlueLink('#BlueLink2', 'Suspension: Measured Total Roll Stiffness', self.frontAuxMName, group)
            carsim.GoHome()

    def onRearAuxMChange(self, text):
        self.rearAuxM_menu.close()
        if self.rearAuxMName != self.select_rearAuxM_button.text():
            self.rearAuxMName = self.select_rearAuxM_button.text()
            self.CurrentVehicleSpringPage(2)
            if carsim.GetBlueLink('#BlueLink2')[0] == 'Suspension: Auxiliary Roll Moment':
                # AuxMInfo = AuxMInfoDic[self.rearAuxMName]
                # pattern = r"(.*):<(.*?)>(.*)"
                # match = re.search(pattern, AuxMInfo)
                # group = match.group(2)
                group = carsim.GetBlueLink('#BlueLink2')[2]
                carsim.BlueLink('#BlueLink2', 'Suspension: Auxiliary Roll Moment', self.rearAuxMName, group)
                ARMLibrary, ARMDataset, ARMCat, _ = carsim.GetBlueLink('#BlueLink2')
                carsim.Gotolibrary(ARMLibrary, ARMDataset, ARMCat)
                ringName = carsim.GetRing('#RingCtrl0')
                if ringName == 'CONSTANT' or ringName == 'COEFFICIENT':
                    rearAuxRollMomentValue = float(carsim.GetYellow('*SCALAR'))
                    self.CurrentVehicleSpringPage(2)
                    carsim.Yellow('DAUX', rearAuxRollMomentValue*0.01)
            else:
                global MxtotInfoDic
                # MxTotInfo = MxtotInfoDic[self.rearAuxMName]
                # pattern = r"(.*):<(.*?)>(.*)"
                # match = re.search(pattern, MxTotInfo)
                # group = match.group(2)
                group = carsim.GetBlueLink('#BlueLink2')[2]
                carsim.BlueLink('#BlueLink2', 'Suspension: Measured Total Roll Stiffness', self.rearAuxMName, group)
        carsim.GoHome()

    def OnFrontSpringTextChanged(self):
        self.CurrentVehicleSpringPage(1)
        carsim.Yellow('*KSPRING_L', self.frontSpringEditText.text())
        self.frontSpringName = self.frontSpringEditText.text()
        self._show_corner_message("前轴弹簧修改完成")

    def OnRearSpringTextChanged(self):
        self.CurrentVehicleSpringPage(1)
        carsim.Yellow('*KSPRING_L', self.rearSpringEditText.text())
        self.rearSpringName = self.rearSpringEditText.text()
        # QMessageBox.information(self,'true','修改完成')
        self._show_corner_message("后轴弹簧修改完成")


    def OnfrontAuxRollMomentTextChanged(self):
        pass

    def OnRearAuxRollMomentTextChanged(self):
        pass

    # 在SimulatorUI类中添加创建触感调节标签页的方法
    def create_haptic_adjustment_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout()
        layout = QVBoxLayout()
        self.load_haptic_gain()
        # 添加摩擦增益设置
        row1 = QHBoxLayout()
        self.gain_fri_label = QLabel("摩擦增益:")
        self.gain_fri_spinbox = QDoubleSpinBox()
        self.gain_fri_spinbox.setRange(-10, 10)  # 设置范围为 1 到 1000
        self.gain_fri_spinbox.setValue(self.gain_fri)
        row1.addWidget(self.gain_fri_label)
        row1.addWidget(self.gain_fri_spinbox)
        layout.addLayout(row1)

        # 添加摩擦增益设置
        row2 = QHBoxLayout()
        self.gain_dam_label = QLabel("阻尼增益:")
        self.gain_dam_spinbox = QDoubleSpinBox()
        self.gain_dam_spinbox.setRange(-10, 10)  # 设置范围为 1 到 1000
        self.gain_dam_spinbox.setValue(self.gain_dam)
        row2.addWidget(self.gain_dam_label)
        row2.addWidget(self.gain_dam_spinbox)
        layout.addLayout(row2)

        # 添加回正增益设置
        row3 = QHBoxLayout()
        self.gain_feedback_label = QLabel("回正增益:")
        self.gain_feedback_spinbox = QDoubleSpinBox()
        self.gain_feedback_spinbox.setRange(-10, 10)  # 设置范围为 1 到 1000
        self.gain_feedback_spinbox.setValue(self.gain_feedback)
        row3.addWidget(self.gain_feedback_label)
        row3.addWidget(self.gain_feedback_spinbox)
        layout.addLayout(row3)

        # 添加限位增益设置
        row4 = QHBoxLayout()
        self.gain_sa_label = QLabel("限位增益:")
        self.gain_sa_spinbox = QDoubleSpinBox()
        self.gain_sa_spinbox.setRange(-10, 10)  # 设置范围为 1 到 1000
        self.gain_sa_spinbox.setValue(self.gain_sa)
        row4.addWidget(self.gain_sa_label)
        row4.addWidget(self.gain_sa_spinbox)
        layout.addLayout(row4)

        # 添加手感轻重设置
        row5 = QHBoxLayout()
        self.gain_all_label = QLabel("手感轻重:")
        self.gain_all_spinbox = QDoubleSpinBox()
        self.gain_all_spinbox.setRange(-1, 10)  # 设置范围为 1 到 1000
        self.gain_all_spinbox.setValue(self.gain_all)
        row5.addWidget(self.gain_all_label)
        row5.addWidget(self.gain_all_spinbox)

        layout.addLayout(row5)
        # 添加转速设置
        row6 = QHBoxLayout()
        self.sw_rate_label = QLabel("力矩转角曲线自定义转速:")
        self.sw_rate_spinbox = QDoubleSpinBox()
        self.sw_rate_spinbox.setRange(0, 100)  # 设置范围为 1 到 1000
        self.sw_rate_spinbox.setValue(self.sw_rate)
        row6.addWidget(self.sw_rate_label)
        row6.addWidget(self.sw_rate_spinbox)
        layout.addLayout(row6)

        # 添加确认按钮
        confirm_button = QPushButton("确认")
        confirm_button.clicked.connect(
            lambda: self.save_haptic_settings(self.gain_fri_spinbox.value(), self.gain_dam_spinbox.value(),
                                              self.gain_feedback_spinbox.value(), self.gain_sa_spinbox.value(),
                                              self.gain_all_spinbox.value(), self.sw_rate_spinbox.value()))
        layout.addWidget(confirm_button)
        # 创建实时绘图组
        plot_group = QGroupBox("实时数据显示")
        plot_layout = QVBoxLayout()

        # 创建绘图控件
        self.sw_plot = pg.PlotWidget()  # 方向盘值曲线
        self.sw_plot.setBackground('w')  # 白色背景
        self.sw_plot.showGrid(x=True, y=True)  # 显示网格
        self.sw_plot.setLabel('left', '方向盘转角/deg', color='k')  # Y轴标签
        self.sw_plot.setLabel('bottom', '时间/s', color='k')  # X轴标签
        self.sw_plot.setTitle('方向盘转角', color='k')  # 标题

        self.f_plot = pg.PlotWidget()  # 力反馈值曲线
        self.f_plot.setBackground('w')
        self.f_plot.showGrid(x=True, y=True)
        self.f_plot.setLabel('left', '力矩/N·m', color='k')
        self.f_plot.setLabel('bottom', '时间/s', color='k')
        self.f_plot.setTitle('力矩', color='k')

        self.sw_f_plot = pg.PlotWidget()  # 力矩转角值曲线
        self.sw_f_plot.setBackground('w')
        self.sw_f_plot.showGrid(x=True, y=True)
        self.sw_f_plot.setLabel('left', '力矩/N·m', color='k')
        self.sw_f_plot.setLabel('bottom', '方向盘转角/deg', color='k')
        self.sw_f_plot.setTitle('力矩转角关系曲线', color='k')
        self.sw_f_plot.setXRange(-600, 600)
        # self.sw_f_plot.setYRange(-10,10)

        # 创建曲线
        self.sw_curve = self.sw_plot.plot(pen=pg.mkPen(color=(0, 0, 255), width=1.5))  # 蓝色曲线
        self.f_curve = self.f_plot.plot(pen=pg.mkPen(color=(255, 0, 0), width=1.5))  # 红色曲线
        self.sw_f_curve = self.sw_f_plot.plot(pen=pg.mkPen(color=(0, 255, 0), width=1.5))  # 绿色曲线

        # 将绘图控件添加到布局
        plot_layout.addWidget(self.sw_plot)
        plot_layout.addWidget(self.f_plot)
        plot_layout.addWidget(self.sw_f_plot)

        layout.setContentsMargins(100, 100, 100, 100)
        plot_layout.setContentsMargins(0, 0, 100, 0)
        # main_layout.addStretch(stretch=1)
        main_layout.addLayout(layout, stretch=1)

        main_layout.addLayout(plot_layout, stretch=2)
        # main_layout.addStretch(stretch=1)

        tab.setLayout(main_layout)
        return tab

    def save_haptic_settings(self, gain_fri, gain_dam, gain_feedback, gain_sa, gain_all, sw_rate):
        try:
            self.gain_fri = gain_fri
            self.gain_dam = gain_dam
            self.gain_feedback = gain_feedback
            self.gain_sa = gain_sa
            self.gain_all = gain_all
            self.sw_rate = sw_rate
            QMessageBox.information(self, "成功", "触感设置已成功应用")
            self.save_haptic_gain()  # 保存到配置文件
        except ValueError:
            QMessageBox.information(self, "错误", "请输入有效数值")

    def get_f_data(self):
        # 下列2个值从carsim获取
        v = self.signal_data['vel_x']['input'][-1]
        ay = self.signal_data['acc_y']['input'][-1]
        sw_rate = self.signal_data['steering_speed']['input'][-1]
        s = self.signal_data['steering_angle']['input'][-1]
        fac = factor(v)
        friction = fcn_friction(sw_rate, s) * self.gain_fri
        damping = fcn_damping(sw_rate, fac) * self.gain_dam
        feedback = fcn_feedback(s, ay, fac) * self.gain_feedback
        saturation = fcn_saturation(s, v) * self.gain_sa
        f = (friction + damping + feedback + saturation) * self.gain_all
        self.f_data.append(f)
        # self.sendData2CarSim(0,f)

    # 添加更新触感曲线的方法
    def update_haptic_plots(self):
        if not hasattr(self, 'gain_fri'):
            return  # 如果触感设置未初始化则跳过

        current_time = time.perf_counter() - self.start_time

        # self.haptic_time_data.append(current_time)

        min_len = min(len(np.array(self.time_data_carsim)), len(np.array(self.signal_data['steering_angle']['input'])),
                      len(np.array(self.f_data)))
        # 更新曲线
        # self.sw_curve.setData(np.array(self.time_data_carsim)[:min_len][::10], np.array(self.signal_data['steering_angle']['input'])[:min_len][::10])
        # self.f_curve.setData(np.array(self.time_data_carsim)[:min_len][::10], np.array(self.f_data)[:min_len][::10])

        # 自动调整坐标范围
        if len(self.time_data_imu) > 0:
            self.sw_plot.setXRange(current_time, current_time - 10)
            self.f_plot.setXRange(current_time, current_time - 10)
        self.sw_plot.setYRange(min(np.array(self.signal_data['steering_angle']['input'])) - 1 if len(
            self.signal_data['steering_angle']['input']) > 0 else -1,
                               max(np.array(self.signal_data['steering_angle']['input'])) + 1 if len(
                                   self.signal_data['steering_angle']['input']) > 0 else 1)
        self.f_plot.setYRange(min(np.array(self.f_data)) - 1 if len(self.f_data) > 0 else -1,
                              max(np.array(self.f_data)) + 1 if len(self.f_data) > 0 else 1)

        # 更新力矩转角曲线
        if int(current_time) > self.last_1s:
            self.sw_f_plot.clear()
            sw_values = list(range(-540, 541)) + list(range(539, -541, -1))
            f = [0] * len(sw_values)
            if len(self.time_data_carsim) > 0:
                v = self.signal_data['vel_x']['input'][-1]
                ay = self.signal_data['acc_y']['input'][-1]
            else:
                v = 0
                ay = 0
            fac = factor(v)
            for i, s in enumerate(sw_values):
                if i < 1080:
                    sw_rate = self.sw_rate
                else:
                    sw_rate = -self.sw_rate
                friction = fcn_friction(sw_rate, s) * self.gain_fri
                damping = fcn_damping(sw_rate, fac) * self.gain_dam
                feedback = fcn_feedback(s, ay, fac) * self.gain_feedback
                saturation = fcn_saturation(s, v) * self.gain_sa
                f[i] = (friction + damping + feedback + saturation) * self.gain_all

            self.last_1s = int(current_time)
            if self.last_1s % 3 == 0:
                self.sw_f_curve = self.sw_f_plot.plot(pen=pg.mkPen(color=(0, 255, 0), width=1.5))
            elif self.last_1s % 2 == 0:
                self.sw_f_curve = self.sw_f_plot.plot(pen=pg.mkPen(color=(0, 0, 255), width=1.5))
            else:
                self.sw_f_curve = self.sw_f_plot.plot(pen=pg.mkPen(color=(255, 0, 0), width=1.5))
            self.sw_f_curve.setData(sw_values + [-540], f + [f[0]])

    def save_haptic_gain(self):
        config = {
            "gain_fri": self.gain_fri,  # 摩擦增益
            "gain_dam": self.gain_dam,  # 阻尼增益
            "gain_feedback": self.gain_feedback,  # 回正增益
            "gain_sa": self.gain_sa,  # 限位增益
            "gain_all": self.gain_all,  # 手感轻重
            "sw_rate": self.sw_rate  # 转速定义
        }
        with open("haptic_config.json", "w") as f:
            json.dump(config, f)

    def load_haptic_gain(self):
        if os.path.exists("haptic_config.json"):
            try:
                with open("haptic_config.json", "r") as f:
                    config = json.load(f)
                    self.gain_fri = config.get("gain_fri", 1)
                    self.gain_dam = config.get("gain_dam", 1)
                    self.gain_feedback = config.get("gain_feedback", 1)
                    self.gain_sa = config.get("gain_sa", 1)
                    self.gain_all = config.get("gain_all", 1)
                    self.sw_rate = config.get("sw_rate", 1)
            except Exception as e:
                print(f"加载力反馈配置时出错: {e}")

    def sendData2CarSim(self, index, value):
        try:
            self.sendData_CarSim[index] = value
            data = struct.pack('f', *self.sendData_CarSim)
            self.udp_socket.writeDatagram(

                data,
                QHostAddress(ip_address),
                3394  # 发送端口
            )
            print(self.sendData_CarSim)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"发送数据失败: {e}")

    def load_record(self):
        self.run_button.setChecked(False)
        self.plot_running = False
        # 清空旧的记录数据
        self.record_time_data_imu.clear()
        self.record_time_data_carsim.clear()
        self.record_time_data_moog.clear()
        for channel in self.record_signal_data.keys():
            for signal_type in ['input', 'moog', 'imu']:
                self.record_signal_data[channel][signal_type].clear()

        # 弹出文件浏览窗口，选择文件夹
        folder_path = QFileDialog.getExistingDirectory(self, "选择记录文件夹",
                                                       os.path.expanduser(r"E:\01_TestData\01_DCH_Data\DCH"))

        if not folder_path:
            return  # 用户取消选择
        # 创建进度条对话框
        self.progress = QProgressDialog("读取记录数据中...", "取消", 0, 100, self)
        self.progress.setWindowTitle("读取记录")
        self.progress.setWindowModality(Qt.WindowModal)  # 设置为模态对话框
        self.progress.setMinimumSize(400, 100)  # 设置最小大小
        self.progress.setCancelButton(None)  # 禁用取消按钮
        self.progress.show()

        self.progress.setValue(0)
        self.progress.setLabelText("开始读取")
        QApplication.processEvents()  # 强制刷新界面

        # 读取 CarsimData.csv
        carsim_file = os.path.join(folder_path, "CarsimData.csv")
        if os.path.exists(carsim_file):
            self.progress.setLabelText("读取 Carsim 数据...")
            self.load_csv_data(carsim_file, 'input')
            self.progress.setValue(25)

        # 读取 MoogData.csv
        moog_file = os.path.join(folder_path, "MoogData.csv")
        if os.path.exists(moog_file):
            self.progress.setLabelText("读取 Moog 数据...")
            self.load_csv_data(moog_file, 'moog')
            self.progress.setValue(50)

        # 读取 IMUData.csv
        imu_file = os.path.join(folder_path, "IMUData.csv")
        if os.path.exists(imu_file):
            self.progress.setLabelText("读取 IMU 数据...")
            self.load_csv_data(imu_file, 'imu')

        self.progress.setLabelText("绘制数据...")
        self.progress.setValue(75)  # 绘制数据
        self.plot_loaded_data()
        self.progress.setValue(100)
        # 关闭进度条
        self.progress.close()

    def load_csv_data(self, file_path, signal_type):
        try:
            with open(file_path, 'r') as file:
                reader = csv.reader(file)
                next(reader)  # 跳过标题行
                for row in reader:
                    time_step = float(row[0])  # 第一列是时间
                    data = [float(x) for x in row[1:]]  # 其余列是数据
                    # 根据 signal_type 将数据存储到对应的队列中
                    if signal_type == 'input':
                        # self.progress.setValue(int(count / row_count * 30))  # 更新进度
                        # count = count + 1
                        self.record_time_data_carsim.append(time_step)
                        # self.record_signal_data['pos_x']['input'].append(data[0])  # X
                        # self.record_signal_data['pos_y']['input'].append(data[1])  # Y
                        # self.record_signal_data['pos_z']['input'].append(data[2])  # Z
                        self.record_signal_data['roll']['input'].append(data[6])  # Roll
                        self.record_signal_data['pitch']['input'].append(data[7] * (-1))  # Pitch
                        self.record_signal_data['yaw']['input'].append(
                            -(data[8] % 360 if data[8] > 0 else data[8] % (-360)))  # Yaw
                        self.record_signal_data['vel_x']['input'].append(data[12])  # Vx
                        # self.record_signal_data['vel_y']['input'].append(data[7])  # Vy
                        # self.record_signal_data['vel_z']['input'].append(data[8])  # Vz
                        self.record_signal_data['ang_x']['input'].append(data[3])  # Avx
                        self.record_signal_data['ang_y']['input'].append(data[4] * (-1))  # Avy
                        self.record_signal_data['ang_z']['input'].append(data[5] * (-1))  # Avz
                        self.record_signal_data['acc_x']['input'].append(data[0] * 9.81)  # Ax
                        self.record_signal_data['acc_y']['input'].append(data[1] * 9.81 * (-1))  # Ay
                        self.record_signal_data['acc_z']['input'].append(data[2] * 9.81 * (-1))  # Az
                        self.record_signal_data['ang_acc_x']['input'].append(data[9] * 57.3)  # AAx
                        self.record_signal_data['ang_acc_y']['input'].append(-data[10] * 57.3)  # AAy
                        self.record_signal_data['ang_acc_z']['input'].append(-data[11] * 57.3)  # AAz
                        if len(data) > 13:
                            self.record_signal_data['steering_angle']['input'].append(data[13])  # 方向盘转角
                            self.record_signal_data['throttle']['input'].append(data[14])  # 油门开度
                            self.record_signal_data['pbk_con']['input'].append(data[15])  # Pbk_Con
                            self.record_signal_data['steering_speed']['input'].append(data[16])  # 方向盘转速
                        # 其他信号数据...
                    elif signal_type == 'moog':
                        # self.progress.setValue(int(count / row_count * 30 + 30))  # 更新进度
                        # count = count + 1
                        self.record_time_data_moog.append(time_step)
                        self.record_signal_data['pos_x']['moog'].append(data[0])  # X
                        self.record_signal_data['pos_y']['moog'].append(data[1])  # Y
                        self.record_signal_data['pos_z']['moog'].append(-data[2])  # Z
                        self.record_signal_data['roll']['moog'].append(data[3] * 57.3)  # Roll
                        self.record_signal_data['pitch']['moog'].append(data[4] * 57.3)  # Pitch
                        self.record_signal_data['yaw']['moog'].append(data[5] * 57.3)  # Yaw
                        self.record_signal_data['vel_x']['moog'].append(data[6])  # Vx
                        self.record_signal_data['vel_y']['moog'].append(data[7])  # Vy
                        self.record_signal_data['vel_z']['moog'].append(data[8])  # Vz
                        self.record_signal_data['ang_x']['moog'].append(data[9] * 57.3)  # Avx
                        self.record_signal_data['ang_y']['moog'].append(data[10] * 57.3)  # Avy
                        self.record_signal_data['ang_z']['moog'].append(data[11] * 57.3)  # Avz
                        self.record_signal_data['acc_x']['moog'].append(data[12])  # Ax
                        self.record_signal_data['acc_y']['moog'].append(data[13])  # Ay
                        self.record_signal_data['acc_z']['moog'].append(data[14])  # Az
                        self.record_signal_data['ang_acc_x']['moog'].append(data[15] * 57.3)  # AAx
                        self.record_signal_data['ang_acc_y']['moog'].append(data[16] * 57.3)  # AAy
                        self.record_signal_data['ang_acc_z']['moog'].append(data[17] * 57.3)  # AAz
                        # 其他信号数据...
                    elif signal_type == 'imu':
                        # self.progress.setValue(int(count / row_count * 30 + 60))  # 更新进度
                        # count = count + 1
                        self.record_time_data_imu.append(time_step)
                        # self.record_signal_data['pos_x']['imu'].append(data[0])  # X
                        # self.record_signal_data['pos_y']['imu'].append(data[1])  # Y
                        # self.record_signal_data['pos_z']['imu'].append(data[2])  # Z
                        # self.record_signal_data['roll']['imu'].append((data[2]-180 if data[2]>0 else data[2]+180))  # Roll
                        self.record_signal_data['roll']['imu'].append(data[2] * (-1))
                        self.record_signal_data['pitch']['imu'].append(data[3])  # Pitch
                        self.record_signal_data['yaw']['imu'].append(data[4] * (-1))  # Yaw
                        # self.record_signal_data['vel_x']['imu'].append(data[6])  # Vx
                        # self.record_signal_data['vel_y']['imu'].append(data[7])  # Vy
                        # self.record_signal_data['vel_z']['imu'].append(data[8])  # Vz
                        self.record_signal_data['ang_x']['imu'].append(data[9] * 57.3 * (-1))  # Avx
                        self.record_signal_data['ang_y']['imu'].append(data[10] * 57.3)  # Avy
                        self.record_signal_data['ang_z']['imu'].append(data[11] * 57.3 * (-1))  # Avz
                        self.record_signal_data['acc_x']['imu'].append(data[12] * (-1))  # Ax
                        self.record_signal_data['acc_y']['imu'].append(data[13])  # Ay
                        self.record_signal_data['acc_z']['imu'].append(data[14] * (-1))  # Az
                        # self.record_signal_data['ang_acc_x']['imu'].append(data[15])  # AAx
                        # self.record_signal_data['ang_acc_y']['imu'].append(data[16])  # AAy
                        # self.record_signal_data['ang_acc_z']['imu'].append(data[17])  # AAz
                        # 其他信号数据...
                    QApplication.processEvents()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"读取文件 {file_path} 失败: {e}")

    def plot_loaded_data(self):
        # 停止实时绘图
        self.run_button.setChecked(False)
        self.plot_running = False

        # 绘制加载的数据
        for channel, curves in self.curves.items():
            for signal_type, curve in curves.items():
                if signal_type == 'input':
                    curve.setData(np.array(self.record_time_data_carsim),
                                  np.array(self.record_signal_data[channel][signal_type]))
                elif signal_type == 'moog':
                    curve.setData(np.array(self.record_time_data_moog),
                                  np.array(self.record_signal_data[channel][signal_type]))
                elif signal_type == 'imu':
                    curve.setData(np.array(self.record_time_data_imu),
                                  np.array(self.record_signal_data[channel][signal_type]))

        # 自动调整纵坐标范围
        for channel, plot in self.plots.items():
            y_min = min(
                np.min(self.record_signal_data[channel]['input']) if self.record_signal_data[channel]['input'] else 0,
                np.min(self.record_signal_data[channel]['moog']) if self.record_signal_data[channel]['moog'] else 0,
                np.min(self.record_signal_data[channel]['imu']) if self.record_signal_data[channel]['imu'] else 0)
            y_max = max(
                np.max(self.record_signal_data[channel]['input']) if self.record_signal_data[channel]['input'] else 0,
                np.max(self.record_signal_data[channel]['moog']) if self.record_signal_data[channel]['moog'] else 0,
                np.max(self.record_signal_data[channel]['imu']) if self.record_signal_data[channel]['imu'] else 0)
            plot.setYRange(y_min, y_max)

        # 自动调整横坐标范围
        if self.record_time_data_carsim:
            min_time = np.min(self.record_time_data_carsim)
            max_time = np.max(self.record_time_data_carsim)
            for plot in self.plots.values():
                plot.setXRange(min_time, max_time)


class VariableEditor(QDialog):
    def __init__(self, var_name, var_value, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"编辑变量: {var_name}")
        self.var_name = var_name
        self.var_value = var_value
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 创建多行输入框
        self.text_edit = QTextEdit()
        if isinstance(self.var_value, np.ndarray):  # 如果是 numpy 数组
            self.text_edit.setPlainText('\n'.join(map(str, self.var_value.flatten())))
        else:  # 如果是标量
            self.text_edit.setPlainText(str(self.var_value))

        layout.addWidget(self.text_edit)

        # 添加确认按钮
        confirm_button = QPushButton("确认")
        confirm_button.clicked.connect(self.confirm_edit)
        layout.addWidget(confirm_button)

        self.setLayout(layout)

    def confirm_edit(self):
        try:
            # 从输入框中获取数据
            text = self.text_edit.toPlainText().strip()

            if not text:
                QMessageBox.warning(self, "错误", "输入不能为空！")
                return

            # 解析数据
            if '\n' in text:  # 多行数据（列向量或矩阵）
                rows = text.split('\n')
                data = [row.split() for row in rows]  # 按空格或制表符分割
            else:  # 单行数据（列向量）
                data = [text.split()]

            # 将数据转换为 numpy 数组
            if len(data) == 1:  # 列向量
                self.var_value = np.array([float(x) for x in data[0]])
            else:  # 矩阵
                self.var_value = np.array([[float(x) for x in row] for row in data])

            self.accept()  # 关闭窗口
        except Exception as e:
            QMessageBox.warning(self, "错误", f"数据格式错误: {e}")


class SignalSenderThread(QThread):
    finished = pyqtSignal()

    def __init__(self, time_var, value_var, udp_socket, signal_index, gain=1.0, parent=None):
        super().__init__(parent)
        self.time_var = time_var
        self.value_var = value_var * gain
        self.signal_index = signal_index
        self.udp_socket = udp_socket
        self.parent = parent

        # 线性插值（边界外推防止异常）
        interp_func = interp1d(self.time_var, self.value_var, kind='linear', fill_value="extrapolate")
        self.new_time_var = np.arange(self.time_var.min(), self.time_var.max(), 0.001)
        self.new_value_var = interp_func(self.new_time_var)

        # 线程控制
        self._is_running = True
        self._mutex = QMutex()
        self.count = 0
        self.update_timer = None

    def run(self):
        try:
            self.update_timer = QTimer()
            self.update_timer.setTimerType(Qt.PreciseTimer)
            self.update_timer.timeout.connect(self.sendPlotData)
            self.update_timer.start(1)  # 1ms间隔（实际可能受系统限制）
            self.exec_()
        except Exception as e:
            print(f"信号发送线程异常: {e}")
            self.finished.emit()

    def sendPlotData(self):
        if not self._is_running or not hasattr(self.parent, 'sendData2Moog'):
            return

        self._mutex.lock()
        try:
            self.parent.sendData2Moog(self.signal_index, self.new_value_var[self.count])
            self.count = (self.count + 1) % len(self.new_value_var)  # 循环计数
        except Exception as e:
            print(f"发送数据时出错: {e}")
        finally:
            self._mutex.unlock()

    def stop(self):
        self._mutex.lock()
        self._is_running = False
        self._mutex.unlock()

        if self.update_timer and self.update_timer.isActive():
            self.update_timer.stop()
        self.quit()
        self.wait(500)  # 确保线程退出


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = SimulatorUI()
    window.show()
    sys.exit(app.exec_())
