

ENABLE_MOCK = False  # 开关

MOCK_TEST_PATH = r"C:\Users\93446\Desktop\test\20260205_105707"


import sys

import os


os.environ["QT_SCALE_FACTOR"] = "0"

# ==========================================

# 1. 获取当前脚本文件的绝对路径 (例如 D:\Downloads\AOS\control_carsim_qt.py)

current_file_path = os.path.abspath(__file__)


# 2. 获取它所在的文件夹 (例如 D:\Downloads\AOS)

current_dir = os.path.dirname(current_file_path)


# 3. 强行把这个文件夹加入 Python 的搜索路径

if current_dir not in sys.path:

    sys.path.insert(0, current_dir)

# ==========================================



import re

import itertools

from datetime import datetime

import time

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import (QApplication, QMainWindow,

                             QTreeWidget, QTreeWidgetItem,

                             QListWidgetItem, QMenu, QCheckBox, QTabWidget,

                             QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,

                             QListWidget, QAbstractItemView, QScrollArea, QFileDialog, QTableWidget,

                             QTableWidgetItem, QHeaderView, QProgressDialog, QMessageBox, QFrame, QSizePolicy)

from control_carsim import ControlCarsim, sanitize_filename

from offline_report_doc import CONFIGS, create_comparison_plot, IndicatorCalculator, safe_read_csv, generate_report

from utils import configure_matplotlib_style, apply_global_styles


configure_matplotlib_style()


from functools import partial

from PyQt5.QtCore import Qt, pyqtSignal


SCREEN_DPI = 150



class MainUI(QMainWindow):

    def __init__(self, carsim_controller):

        super().__init__()

        self.controller = carsim_controller

        self.setWindowTitle("CarSim 离线仿真工具")

        self.resize(1400, 900)  # 稍微加宽一点适应左右布局

        self.init_main_tabs()


    def init_main_tabs(self):

        """创建 TabWidget 并添加两个页面"""

        apply_global_styles(self)


        self.tabs = QTabWidget()

        self.setCentralWidget(self.tabs)


        self.tab_simulation = CarSimBatchUI(self.controller)

        self.tabs.addTab(self.tab_simulation, "仿真配置与执行")


        self.tab_analysis = AnalysisTab(CONFIGS, self.controller, self.tabs)

        self.tabs.addTab(self.tab_analysis, "结果分析与绘图")


        self.tab_simulation.simulation_finished.connect(self.on_simulation_done)


    # 4. 槽函数：处理页面跳转和数据加载

    def on_simulation_done(self, result_path):

        self.tab_analysis.load_result_folder(result_path)


        for i in range(self.tab_analysis.list_cars.count()):

            self.tab_analysis.list_cars.item(i).setCheckState(Qt.Checked)


        self.tabs.setCurrentIndex(1)

        self.tab_analysis.run_analysis()



class CarSimBatchUI(QWidget):

    # 即结果路径

    simulation_finished = pyqtSignal(str)


    def __init__(self, carsim_controller):

        super().__init__()

        try:

            self.controller = carsim_controller

            self.com_connected = True

        except Exception as e:

            QMessageBox.critical(self, "错误", f"无法连接 CarSim，请确认软件已打开。\n错误信息: {e}")

            self.com_connected = False


        self.init_simulation_ui()


        if self.com_connected:

            self.load_vehicles()


    def init_simulation_ui(self):

        main_layout = QHBoxLayout()

        self.setLayout(main_layout)


        # ==========================================

        # 左侧区域: 车型选择

        # ==========================================

        left_widget = QWidget()

        left_layout = QVBoxLayout()

        left_widget.setLayout(left_layout)


        gb_veh = QGroupBox("1. 选择基准车型 (点击加载)")

        v_layout = QVBoxLayout()

        self.lbl_veh_status = QLabel("就绪")

        self.lbl_veh_status.setStyleSheet("color: #138496")


        self.tree_veh = QTreeWidget()

        self.tree_veh.setHeaderLabel("车型库 (Category / Dataset)")

        self.tree_veh.itemClicked.connect(self.on_vehicle_clicked)


        v_layout.addWidget(self.tree_veh)

        v_layout.addWidget(self.lbl_veh_status)

        gb_veh.setLayout(v_layout)


        left_layout.addWidget(gb_veh)

        main_layout.addWidget(left_widget, 1)


        # ==========================================

        # 右侧区域: 参数配置 + 结果列表

        # ==========================================

        right_widget = QWidget()

        right_layout = QVBoxLayout()

        right_widget.setLayout(right_layout)


        # --- 2. 悬架部件多选 ---

        gb_comp = QGroupBox("2. 悬架配置 (Ctrl/Shift 多选)")

        c_layout = QVBoxLayout()


        row_f = QHBoxLayout()

        self.list_f_spr = self.create_list_widget("前弹簧 [F.Spring]")

        self.list_f_dmp = self.create_list_widget("前阻尼 [F.Damper]")

        self.list_f_bar = self.create_list_widget("前稳定杆 [F.Bar]")

        row_f.addWidget(self.list_f_spr['container'])

        row_f.addWidget(self.list_f_dmp['container'])

        row_f.addWidget(self.list_f_bar['container'])

        c_layout.addLayout(row_f)


        row_r = QHBoxLayout()

        self.list_r_spr = self.create_list_widget("后弹簧 [R.Spring]")

        self.list_r_dmp = self.create_list_widget("后阻尼 [R.Damper]")

        self.list_r_bar = self.create_list_widget("后稳定杆 [R.Bar]")

        row_r.addWidget(self.list_r_spr['container'])

        row_r.addWidget(self.list_r_dmp['container'])

        row_r.addWidget(self.list_r_bar['container'])

        c_layout.addLayout(row_r)


        gb_comp.setLayout(c_layout)

        gb_comp.setFixedHeight(300)  # [修改] 减小高度，给下方腾出空间

        right_layout.addWidget(gb_comp)


        # ---3. 轮胎与 Simulink 配置 ---

        gb_extra = QGroupBox("3. 联合仿真配置")

        e_layout = QHBoxLayout()


        # 创建三个列表

        # self.list_f_tire = self.create_list_widget("前轮胎 [F.Tire]")

        # self.list_r_tire = self.create_list_widget("后轮胎 [R.Tire]")

        self.list_simulink = self.create_list_widget("Simulink模型 [Simulink]")


        # e_layout.addWidget(self.list_f_tire['container'])

        # e_layout.addWidget(self.list_r_tire['container'])

        e_layout.addWidget(self.list_simulink['container'])


        gb_extra.setLayout(e_layout)

        gb_extra.setFixedHeight(200)  # 设置适当的高度

        right_layout.addWidget(gb_extra)


        # ============================================================

        # 4. 工况选择 (原 3 改为 4)

        # ============================================================

        gb_proc = QGroupBox("4. 工况选择 (勾选要执行的任务)")

        gb_proc.setFixedHeight(80)

        p_layout = QHBoxLayout()

        p_layout.setContentsMargins(10, 5, 10, 5)

        self.proc_checkboxes = []


        self.cb_select_all = QCheckBox("[全选] ")

        self.cb_select_all.setStyleSheet("font-weight: bold; color: #17a2b8;")

        self.cb_select_all.stateChanged.connect(self.on_select_all_changed)

        p_layout.addWidget(self.cb_select_all)


        line = QFrame()

        line.setFrameShape(QFrame.VLine)

        line.setFrameShadow(QFrame.Sunken)

        p_layout.addWidget(line)


        proc_keys = [k for k in self.controller.configs.keys() if k != 'common_config']

        for key in proc_keys:

            cb = QCheckBox(key)

            cb.setChecked(False)

            cb.stateChanged.connect(self.update_select_all_state)

            p_layout.addWidget(cb)

            self.proc_checkboxes.append(cb)


        p_layout.addStretch()

        gb_proc.setLayout(p_layout)

        right_layout.addWidget(gb_proc)


        # --- 生成按钮 ---

        self.btn_gen = QPushButton("↓↓ 添加组合方案到列表 ↓↓")

        self.btn_gen.setFixedHeight(45)

        self.btn_gen.clicked.connect(self.generate_combinations)

        right_layout.addWidget(self.btn_gen)


        # --- 结果列表添加新列 ---

        # cols = ["配置名称", "基准车型", "F.Spr", "R.Spr", "F.Dmp", "R.Dmp", "F.Bar", "R.Bar", "F.Tire", "R.Tire",

        #         "Simulink"]

        cols = ["配置名称", "基准车型", "F.Spr", "R.Spr", "F.Dmp", "R.Dmp", "F.Bar", "R.Bar", "Simulink"]

        self.table = QTableWidget()

        self.table.setColumnCount(len(cols))

        self.table.setHorizontalHeaderLabels(cols)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.table.horizontalHeader().setSectionsMovable(True)

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)

        self.table.customContextMenuRequested.connect(self.show_table_context_menu)

        right_layout.addWidget(self.table)


        # --- 底部执行按钮 ---

        h_exec = QHBoxLayout()

        self.btn_clear = QPushButton("清空所有方案")

        self.btn_clear.clicked.connect(lambda: self.table.setRowCount(0))

        self.btn_del = QPushButton("删除选中行")

        self.btn_del.clicked.connect(self.delete_selected_rows)

        self.btn_run = QPushButton("执行仿真")

        self.btn_run.clicked.connect(self.execute_batch)


        h_exec.addWidget(self.btn_clear)

        h_exec.addWidget(self.btn_del)

        h_exec.addStretch()

        h_exec.addWidget(self.btn_run)

        right_layout.addLayout(h_exec)


        main_layout.addWidget(right_widget, 3)


    def create_list_widget(self, title):

        w = QWidget()

        l = QVBoxLayout()

        l.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel(title)

        lst = QListWidget()

        lst.setSelectionMode(QAbstractItemView.ExtendedSelection)

        l.addWidget(lbl)

        l.addWidget(lst)

        w.setLayout(l)

        return {'container': w, 'widget': lst}


    def load_vehicles(self):

        raw_list = self.controller.get_veh_list()


        categories = {}

        for raw in raw_list:

            match = re.search(r'<([^>]+)>(.*)', raw)

            if match:

                cat = match.group(1).strip()

                name = match.group(2).strip()

            else:

                cat = "Uncategorized"

                name = raw.strip()


            if cat not in categories: categories[cat] = []

            categories[cat].append((name, raw))


        self.tree_veh.clear()

        for cat in sorted(categories.keys()):

            parent = QTreeWidgetItem(self.tree_veh)

            parent.setText(0, cat)

            parent.setFlags(parent.flags() & ~Qt.ItemIsSelectable)

            # parent.setBackground(0, Qt.lightGray)

            parent.setFont(0, self.font())


            for name, raw_val in categories[cat]:

                child = QTreeWidgetItem(parent)

                child.setText(0, name)

                child.setToolTip(0, name)

                child.setData(0, Qt.UserRole, raw_val)

                child.setData(0, Qt.UserRole + 1, cat)

            # self.tree_veh.expandItem(parent)


        self.tree_veh.collapseAll()


    def on_select_all_changed(self, state):

        """当点击‘全选’按钮时触发，批量设置所有工况复选框"""

        for cb in self.proc_checkboxes:

            cb.blockSignals(True)

            cb.setChecked(state == Qt.Checked)

            cb.blockSignals(False)


    def update_select_all_state(self):

        """当任意单个工况复选框状态改变时触发，动态更新‘全选’按钮的状态"""

        all_checked = all(cb.isChecked() for cb in self.proc_checkboxes)

        self.cb_select_all.blockSignals(True)

        self.cb_select_all.setChecked(all_checked)

        self.cb_select_all.blockSignals(False)


    def on_vehicle_clicked(self, item, col):

        if item.childCount() > 0 or item.parent() is None: return


        veh_raw = item.data(0, Qt.UserRole)

        match = re.search(r'<([^>]+)>(.*)', veh_raw)

        if match:

            veh_cate = match.group(1).strip()

            veh_ds = match.group(2).strip()

        else:

            return


        progress = QProgressDialog(f"正在分析弹性件: {veh_ds}", None, 0, 0, self)

        progress.setWindowTitle("请稍候")

        progress.setWindowModality(Qt.WindowModal)  # 模态窗口，通过它阻挡用户操作主界面

        progress.setMinimumDuration(0)  # 立即显示，不等待

        progress.show()


        self.lbl_veh_status.setText(f"正在分析: {veh_ds} ...")

        simulink_model, crnt_s_model = self.controller.get_crnt_simulink()

        print(f"正在分析: {veh_ds} ...")


        QApplication.processEvents()

        success = self.controller.change_vehicle(veh_ds, veh_cate)


        if not success:

            self.lbl_veh_status.setText(f"切换车型失败: {veh_ds}")

            return


        f_spr, crnt_f_spr = self.controller.get_crnt_spring('F')

        # f_dmp, crnt_f_damp = self.get_supplementary_component('F', "#BlueLink1")

        f_dmp, crnt_f_damp = self.controller.get_crnt_dmp('F')

        f_arb, crnt_f_arb = self.controller.get_crnt_arb('F')


        # f_tire, crnt_f_tire = self.controller.get_crnt_tire('F')


        r_spr, crnt_r_spr = self.controller.get_crnt_spring('R')

        # r_dmp, crnt_r_damp = self.get_supplementary_component('R', "#BlueLink1")

        r_dmp, crnt_r_damp = self.controller.get_crnt_dmp('R')

        r_arb, crnt_r_arb = self.controller.get_crnt_arb('R')

        # r_tire, crnt_r_tire = self.controller.get_crnt_tire('R')


        self.update_list(self.list_f_spr['widget'], f_spr, crnt_f_spr)

        self.update_list(self.list_f_dmp['widget'], f_dmp, crnt_f_damp)

        self.update_list(self.list_f_bar['widget'], f_arb, crnt_f_arb)

        # self.update_list(self.list_f_tire['widget'], f_tire, crnt_f_tire)


        self.update_list(self.list_r_spr['widget'], r_spr, crnt_r_spr)

        self.update_list(self.list_r_dmp['widget'], r_dmp, crnt_r_damp)

        self.update_list(self.list_r_bar['widget'], r_arb, crnt_r_arb)

        # self.update_list(self.list_r_tire['widget'], r_tire, crnt_r_tire)

        self.update_list(self.list_simulink['widget'], simulink_model, crnt_s_model)


        self.lbl_veh_status.setText(f"车型 {veh_ds} 部件加载完毕")

        progress.close()


    def get_supplementary_component(self, f_or_r, link_id):

        h = self.controller.h

        h.GoHome()

        veh_lib, veh_ds, veh_cat, _ = h.GetBlueLink("#BlueLink2")

        if not veh_lib: return []

        h.GoToLibrary(veh_lib, veh_ds, veh_cat)


        target_sus_link = "#BlueLink16" if f_or_r == 'F' else "#BlueLink17"

        sus_lib, sus_ds, sus_cat, _ = h.GetBlueLink(target_sus_link)

        if not sus_lib: return []

        h.GoToLibrary(sus_lib, sus_ds, sus_cat)


        comp_lib, comp_ds, comp_cat, _ = h.GetBlueLink(link_id)

        if not comp_lib: return []


        raw_list = h.GetDatasetList(comp_lib)

        if not raw_list: return []


        clean_names = self.controller.clean_list_name(raw_list)

        filter_names = self.controller.filter_list(comp_cat, clean_names)


        return filter_names


    def update_list(self, list_widget, items, target_val=None):

        list_widget.clear()

        if not items:

            it = QListWidgetItem("<无可用/不适用>")

            it.setFlags(Qt.NoItemFlags)

            it.setToolTip("该车型此位置无可用部件")

            list_widget.addItem(it)

        else:

            select_row = 0  # 默认选中第0行

            for i, txt in enumerate(items):

                item = QListWidgetItem(txt)

                item.setToolTip(txt)

                list_widget.addItem(item)


                if target_val and txt == target_val:

                    select_row = i


            # 选中找到的行（如果没有找到匹配的，则选中第0行）

            if list_widget.count() > 0:

                list_widget.item(select_row).setSelected(True)

                list_widget.scrollToItem(list_widget.item(select_row))  # 确保滚动到可见区域


    def generate_combinations(self):

        # 1. 获取当前选中的基准车型

        curr = self.tree_veh.currentItem()

        if not curr or curr.parent() is None:

            QMessageBox.warning(self, "提示", "请先选择车型")

            return


        current_car_name = curr.text(0)

        current_car_cat = curr.data(0, Qt.UserRole + 1)  # 获取类别用于后续存储


        # 2. 获取用户选择的部件列表

        def get_sel(lw):

            sel = [i.text() for i in lw.selectedItems() if i.flags() & Qt.ItemIsSelectable]

            return sel if sel else ["ori"]  # 如果未选，默认为保留原车配置


        lists = [

            get_sel(self.list_f_spr['widget']), get_sel(self.list_r_spr['widget']),

            get_sel(self.list_f_dmp['widget']), get_sel(self.list_r_dmp['widget']),

            get_sel(self.list_f_bar['widget']), get_sel(self.list_r_bar['widget']),

            # get_sel(self.list_f_tire['widget']), get_sel(self.list_r_tire['widget']),

            get_sel(self.list_simulink['widget'])

        ]

        # 生成所有可能的组合 (笛卡尔积)

        combos = list(itertools.product(*lists))


        # =========================================================

        # 去重

        # =========================================================


        # A. 获取当前表格中已有的所有方案签名

        # 签名格式: (基准车型, F.Spr, R.Spr, F.Dmp, R.Dmp, F.Bar, R.Bar)

        existing_signatures = set()

        rows = self.table.rowCount()

        for r in range(rows):

            sig = tuple(self.table.item(r, c).text() for c in range(1, 9))

            existing_signatures.add(sig)


        new_combos_to_add = []

        duplicate_count = 0


        for combo in combos:

            current_sig = (current_car_name,) + combo


            if current_sig in existing_signatures:

                duplicate_count += 1

            else:

                new_combos_to_add.append(combo)


        # C. 如果没有新数据，提示用户

        if not new_combos_to_add:

            if duplicate_count > 0:

                QMessageBox.information(self, "提示", f"未添加新方案。\n检测到 {duplicate_count} 个重复配置已自动忽略。")

            else:

                QMessageBox.information(self, "提示", "未生成任何方案，请检查部件选择。")

            return


        # =========================================================

        # 添加到表格

        # =========================================================


        # 辅助函数：创建带悬停提示的单元格

        def create_item(text):

            item = QTableWidgetItem(str(text))

            item.setToolTip(str(text))  # 鼠标悬停显示全名

            return item


        start_row = self.table.rowCount()

        self.table.setRowCount(start_row + len(new_combos_to_add))


        # 智能获取当前表格中最大的后缀数字，防止删除行后再添加导致编号重复

        max_idx = 0

        for r in range(start_row):

            existing_name = self.table.item(r, 0).text()

            # 尝试提取名字末尾的 "_数字"

            match = re.search(r'_(\d+)$', existing_name)

            if match:

                max_idx = max(max_idx, int(match.group(1)))


        # for i, (fs, rs, fd, rd, fb, rb, ft, rt, sim) in enumerate(new_combos_to_add):

        for i, (fs, rs, fd, rd, fb, rb, sim) in enumerate(new_combos_to_add):

            row_idx = start_row + i


            # 生成配置名

            def get_part_suffix(prefix, front_val, rear_val):

                f_code = front_val.split('_')[-1]

                r_code = rear_val.split('_')[-1]


                if f_code.lower() == 'ori' and r_code.lower() == 'ori':

                    return ""


                return f"_{prefix}{f_code}{r_code}"


            short_car_name = current_car_name.split(' ')[0].split('_')[0][:7]

            spr_name = get_part_suffix('S', fs, rs)

            dmp_name = get_part_suffix('D', fd, rd)

            arb_name = get_part_suffix('B', fb, rb)

            # tire_name = get_part_suffix('T', ft, rt)

            sim_name = "" if sim == "ori" else "_Sim"


            max_idx += 1

            name = f"{short_car_name}_{max_idx}"


            # name = f"{short_car_name}{spr_name}{dmp_name}{arb_name}{tire_name}{sim_name}"


            # 填充列

            self.table.setItem(row_idx, 0, create_item(name))


            # 基准车型列 (需存入 Category 数据以便执行时切换)

            item_car = create_item(current_car_name)

            item_car.setData(Qt.UserRole, current_car_cat)

            self.table.setItem(row_idx, 1, item_car)

            self.table.setItem(row_idx, 2, create_item(fs))

            self.table.setItem(row_idx, 3, create_item(rs))

            self.table.setItem(row_idx, 4, create_item(fd))

            self.table.setItem(row_idx, 5, create_item(rd))

            self.table.setItem(row_idx, 6, create_item(fb))

            self.table.setItem(row_idx, 7, create_item(rb))

            # self.table.setItem(row_idx, 8, create_item(ft))

            # self.table.setItem(row_idx, 9, create_item(rt))

            self.table.setItem(row_idx, 8, create_item(sim))

        # 滚动到底部并提示

        self.table.scrollToItem(self.table.item(self.table.rowCount() - 1, 0))


        msg = f"成功添加 {len(new_combos_to_add)} 个新方案。"

        if duplicate_count > 0:

            msg += f"\n({duplicate_count} 个重复方案已被忽略)"


    # ==========================================================================

    # 删除与右键菜单逻辑

    # ==========================================================================

    def show_table_context_menu(self, pos):

        """右键菜单"""

        menu = QMenu()

        del_action = menu.addAction("删除选中行")

        action = menu.exec_(self.table.mapToGlobal(pos))


        if action == del_action:

            self.delete_selected_rows()


    def delete_selected_rows(self):

        """删除选中的行"""

        selected_rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)

        if not selected_rows:

            return


        confirm = QMessageBox.question(self, "确认删除", f"确定要删除选中的 {len(selected_rows)} 行方案吗？",

                                       QMessageBox.Yes | QMessageBox.No)

        if confirm == QMessageBox.Yes:

            for row in selected_rows:

                self.table.removeRow(row)


    def keyPressEvent(self, event):

        """监听按键事件，处理 Delete 键"""

        if event.key() == Qt.Key_Delete:

            # 检查焦点是否在表格上

            if self.table.hasFocus():

                self.delete_selected_rows()

        super().keyPressEvent(event)


    def execute_batch(self):

        self.controller.create_test_dataset()

        self.controller.clear_restore_stack()


        rows = self.table.rowCount()

        if rows == 0:

            QMessageBox.warning(self, "提示", "列表中没有任务")

            return


        selected_procs = []

        for cb in self.proc_checkboxes:

            if cb.isChecked():

                selected_procs.append(cb.text())


        if not selected_procs:

            QMessageBox.warning(self, "提示", "请至少勾选一个工况！")

            return


        export_root_path = current_dir

        start_time = datetime.now()

        time_stamp = start_time.strftime('%Y%m%d_%H%M%S')

        time_path = os.path.join(export_root_path, "Results", time_stamp)

        if not os.path.exists(time_path):

            os.makedirs(time_path)


            # ================== 保存方案配置说明 ==================

            mapping_text = "【各方案配置说明】\n"

            for r in range(rows):

                cfg_name = self.table.item(r, 0).text()

                base_car = self.table.item(r, 1).text()

                fs = self.table.item(r, 2).text()

                rs = self.table.item(r, 3).text()

                fd = self.table.item(r, 4).text()

                rd = self.table.item(r, 5).text()

                fb = self.table.item(r, 6).text()

                rb = self.table.item(r, 7).text()

                sim = self.table.item(r, 8).text()


                mapping_text += f"{cfg_name}: 基准[{base_car}] | 弹簧[{fs}/{rs}] | 阻尼[{fd}/{rd}] | 稳定杆[{fb}/{rb}] | 联合仿真模型[{sim}] \n"


            mapping_file = os.path.join(time_path, "model_info.txt")

            try:

                with open(mapping_file, 'w', encoding='utf-8') as f:

                    f.write(mapping_text)

            except Exception as e:

                print(f"写入配置说明失败: {e}")

            # ====================================


        # 3. 计算总进度 (行数 * 工况数)

        proc_count = len(selected_procs)

        total_steps = rows * proc_count


        prog = QProgressDialog("正在执行批处理...", "取消", 0, total_steps, self)

        prog.setWindowModality(Qt.WindowModal)

        prog.setMinimumDuration(0)


        prog.setValue(0)

        prog.show()

        QApplication.processEvents()


        current_step = 0

        cancel_flag = False


        # =========================================================

        # 外层循环：遍历表格中的每一行配置 (物理参数)

        # =========================================================


        def check_cancel():

            QApplication.processEvents()

            if prog.wasCanceled():

                return True

            return False


        for i in range(rows):

            if check_cancel():

                cancel_flag = True

                break


            # --- A. 获取表格数据 ---

            config_name = self.table.item(i, 0).text()  # 配置名称

            base_car_name = self.table.item(i, 1).text()

            veh_cat_data = self.table.item(i, 1).data(Qt.UserRole)


            prog.setLabelText(f"正在配置第 {i + 1}/{rows} 组方案...\n基准车型: {base_car_name}")

            QApplication.processEvents()


            # --- B. 准备该配置的导出文件夹 ---

            # 文件夹名: 配置名_车型名

            folder_name = sanitize_filename(f"{config_name}")

            curr_export_path = os.path.join(time_path, folder_name)

            if not os.path.exists(curr_export_path):

                os.makedirs(curr_export_path)

            print(f"\n🚗 [配置 {i + 1}/{rows}] 正在设置车辆: {base_car_name}")


            # --- C. 切换车辆 ---

            if veh_cat_data:

                res = self.controller.change_vehicle(base_car_name, veh_cat_data)


                if not res:

                    print(f"  ❌ 切换车辆失败，跳过此行")

                    current_step += proc_count

                    prog.setValue(current_step)

                    continue

                self.controller.get_crnt_veh_param(base_car_name, veh_cat_data, save_path=curr_export_path)


            QApplication.processEvents()


            # --- D. 替换悬架部件 (修改物理参数) ---

            # 列索引: 0:Name, 1:Car, 2:FSpr, 3:RSpr, 4:FDmp, 5:RDmp, 6:FBar, 7:RBar

            try:

                self.controller.change_crnt_spring('F', self.table.item(i, 2).text())

                self.controller.change_crnt_spring('R', self.table.item(i, 3).text())

                self.controller.change_crnt_dmp('F', self.table.item(i, 4).text())

                self.controller.change_crnt_dmp('R', self.table.item(i, 5).text())

                self.controller.change_crnt_arb('F', self.table.item(i, 6).text())

                self.controller.change_crnt_arb('R', self.table.item(i, 7).text())

                # self.controller.change_crnt_tire('F', self.table.item(i, 8).text())

                # self.controller.change_crnt_tire('R', self.table.item(i, 9).text())

                self.controller.change_simulink(self.table.item(i, 8).text())


            except Exception as e:

                print(f"  ⚠️ 部件替换出错: {e}")


            # =========================================================

            # 内层循环：遍历 Config JSON 中的所有工况 (运行仿真)

            # =========================================================

            for keyword in selected_procs:

                if check_cancel():

                    cancel_flag = True

                    break


                if keyword == 'common_config': continue


                info = self.controller.configs.get(keyword)

                proc_ds = info.get('Dataset')

                prog.setWindowTitle("执行中...")

                prog.setLabelText(f"配置: {config_name}\n正在执行工况: {keyword}")

                QApplication.processEvents()


                # --- E. 切换工况 (Procedure) ---

                common = self.controller.configs.get('common_config', {})

                self.controller.proc_cate = common.get('Procedure_Category', "")


                res = self.controller.change_procedure(proc_ds)

                if res:

                    # --- F. 执行仿真 ---

                    success = self.controller.execute_simulation()

                    if check_cancel():

                        cancel_flag = True

                        break


                    # --- G. 特殊检查 ---

                    if "Step" in proc_ds:

                        self.controller.step_cond_check()


                    if success:

                        time.sleep(0.5)

                        self.controller.rename_carsim_output_csv(curr_export_path, keyword)

                    else:

                        print(f"  ⚠️ 仿真失败: {keyword}")

                else:

                    print(f"  ❌ 切换工况失败: {proc_ds}")


                current_step += 1

                prog.setValue(current_step)

            if cancel_flag:

                break


        # 4. 恢复环境

        self.controller.recover_dataset()

        if not cancel_flag:

            prog.setValue(total_steps)

            prog.setLabelText(f"仿真结束，结果已保存至:{time_path}\n...")

            prog.setWindowTitle("请稍候")

            prog.setWindowModality(Qt.WindowModal)  # 模态窗口，通过它阻挡用户操作主界面

            prog.setMinimumDuration(0)  # 立即显示，不等待

            prog.show()

            QApplication.processEvents()

            self.simulation_finished.emit(time_path)

            # try:

            #     output_file_name = generate_report(time_path, CONFIGS)

            # finally:

            #     os.startfile(output_file_name)

        prog.close()



class AnalysisTab(QWidget):

    def __init__(self, configs, carsim_controler, tab_controller=None, ):

        super().__init__()

        self.configs = configs

        self.calc = IndicatorCalculator(carsim_controler)

        self.current_result_path = ""

        self.tab_controller = tab_controller


        # 数据缓存

        self.analysis_results = {}

        # 控件缓存

        self.plot_rows = {}


        self.init_ui()


        if ENABLE_MOCK:

            from PyQt5.QtCore import QTimer

            QTimer.singleShot(500, self.run_mock_test)


    def init_ui(self):

        # 主布局：白色背景

        main_layout = QVBoxLayout()

        main_layout.setSpacing(10)

        self.setLayout(main_layout)


        # ============================================================

        # 区域 1: 顶部控制面板 (垂直布局：上层选数据，下层放按钮)

        # ============================================================

        top_panel = QGroupBox("加载数据与操作")

        # [调整高度] 因为分了两层，高度需要增加 (原160 -> 280左右)

        top_panel.setFixedHeight(280)


        # --- 顶层主布局 (垂直 QVBox) ---

        top_main_layout = QVBoxLayout()

        top_main_layout.setContentsMargins(15, 20, 15, 15)

        top_main_layout.setSpacing(15)


        # ---------------------------------------------------------

        # A. 上半部分：路径选择 + 方案列表 (水平 QHBox)

        # ---------------------------------------------------------

        upper_data_layout = QHBoxLayout()

        upper_data_layout.setSpacing(20)


        # --- 左侧：路径加载模块 ---

        left_widget = QWidget()

        left_layout = QVBoxLayout(left_widget)

        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.setSpacing(5)


        lbl_load_info = QLabel("数据源路径:")

        lbl_load_info.setStyleSheet("color: #333;")


        btn_load = QPushButton(" 📂 加载结果文件夹")

        btn_load.setFixedHeight(35)

        btn_load.clicked.connect(self.load_result_folder)


        self.lbl_path = QLabel("未选择路径")

        self.lbl_path.setStyleSheet("color: #888; border: 1px dashed #ccc; padding: 5px; border-radius: 4px;")

        self.lbl_path.setWordWrap(True)

        self.lbl_path.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # 给路径显示一个固定高度，防止路径太长撑乱布局，或者太短导致空白

        self.lbl_path.setMinimumHeight(60)


        left_layout.addWidget(lbl_load_info)

        left_layout.addWidget(btn_load)

        left_layout.addWidget(self.lbl_path)

        left_layout.addStretch()  # 底部顶起


        # --- 右侧：对比方案列表模块 ---

        right_widget = QWidget()

        right_layout = QVBoxLayout(right_widget)

        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.setSpacing(5)


        lbl_sel = QLabel("选择对比方案:")

        self.list_cars = QListWidget()

        self.list_cars.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # 稍微美化一下列表

        self.list_cars.setStyleSheet("border: 1px solid #ccc; border-radius: 4px;")


        right_layout.addWidget(lbl_sel)

        right_layout.addWidget(self.list_cars)


        # 将左右加入上层布局 (比例 1:2，给列表更多空间)

        upper_data_layout.addWidget(left_widget, 0)

        upper_data_layout.addWidget(right_widget, 1)


        # ---------------------------------------------------------

        # B. 下半部分：操作按钮 (水平 QHBox)

        # ---------------------------------------------------------

        lower_btn_layout = QHBoxLayout()

        lower_btn_layout.setSpacing(50)  # 按钮之间的间距

        lower_btn_layout.setContentsMargins(20, 0, 20, 0)  # 左右缩进


        self.btn_analyze = QPushButton("▶ 开始计算")

        self.btn_analyze.setFixedHeight(40)

        self.btn_analyze.clicked.connect(self.run_analysis)


        self.btn_report = QPushButton("📄 生成报告")

        self.btn_report.setFixedHeight(40)

        self.btn_report.clicked.connect(self.on_click_generate_report)


        self.btn_open_folder = QPushButton("📂 打开目录")

        self.btn_open_folder.setFixedHeight(40)

        self.btn_open_folder.clicked.connect(self.open_report_folder)


        lower_btn_layout.addWidget(self.btn_analyze, 1)

        lower_btn_layout.addWidget(self.btn_report, 1)

        lower_btn_layout.addWidget(self.btn_open_folder, 1)


        # ---------------------------------------------------------

        # C. 组合到主 Panel

        # ---------------------------------------------------------

        top_main_layout.addLayout(upper_data_layout)


        line = QFrame()

        line.setFrameShape(QFrame.HLine)

        line.setFrameShadow(QFrame.Sunken)

        line.setStyleSheet("color: #ddd;")

        top_main_layout.addWidget(line)


        top_main_layout.addLayout(lower_btn_layout)


        top_panel.setLayout(top_main_layout)

        main_layout.addWidget(top_panel)


        # ============================================================

        # 区域 2: 结果展示控制 (保持不变)

        # ============================================================

        self.btn_group_box = QGroupBox("工况指标展示")

        self.btn_group_box.setFixedHeight(80)


        self.btn_scroll = QScrollArea()

        self.btn_scroll.setWidgetResizable(True)

        self.btn_scroll.setFrameShape(QFrame.NoFrame)

        self.btn_scroll.setStyleSheet("background-color: transparent;")


        self.btn_container = QWidget()

        self.btn_container.setStyleSheet("background-color: transparent;")

        self.btn_layout = QHBoxLayout()

        self.btn_layout.setContentsMargins(0, 5, 0, 5)

        self.btn_container.setLayout(self.btn_layout)

        self.btn_scroll.setWidget(self.btn_container)


        btn_main_layout = QVBoxLayout()

        btn_main_layout.setContentsMargins(10, 15, 10, 5)

        btn_main_layout.addWidget(self.btn_scroll)

        self.btn_group_box.setLayout(btn_main_layout)


        main_layout.addWidget(self.btn_group_box)


        # ============================================================

        # 区域 3: 详细分析区 (保持不变)

        # ============================================================

        self.plot_scroll = QScrollArea()

        self.plot_scroll.setWidgetResizable(True)

        self.plot_scroll.setFrameShape(QFrame.NoFrame)

        self.plot_scroll.setStyleSheet("background-color: white;")


        self.plot_content = QWidget()

        self.plot_content.setStyleSheet("background-color: white;")


        self.plot_layout = QVBoxLayout()

        self.plot_layout.setSpacing(20)

        self.plot_layout.addStretch()


        self.plot_content.setLayout(self.plot_layout)

        self.plot_scroll.setWidget(self.plot_content)


        main_layout.addWidget(self.plot_scroll)


    def run_mock_test(self):

        """[新增] 自动化测试流程"""

        print(f"--- 正在运行 Mock 测试: {MOCK_TEST_PATH} ---")


        # 1. 检查路径

        if not os.path.exists(MOCK_TEST_PATH):

            print(f"Error: Mock path not found: {MOCK_TEST_PATH}")

            return


        self.tab_controller.setCurrentIndex(1)


        # 2. 加载文件夹 (复用 load_result_folder 逻辑)

        self.load_result_folder(MOCK_TEST_PATH)


        # 3. 全选列表中的车辆

        if self.list_cars.count() > 0:

            for i in range(self.list_cars.count()):

                self.list_cars.item(i).setCheckState(Qt.Checked)


            # 4. 触发计算

            print("Auto clicking 'Run Analysis'...")

            self.run_analysis()

        else:

            print("Warning: No cars found in mock path.")


    def load_result_folder(self, path=None):

        if not path:

            default_open_path = os.path.join(current_dir, "Results")

            if not os.path.exists(default_open_path):

                default_open_path = current_dir

            path = QFileDialog.getExistingDirectory(self, "选择仿真结果根目录", default_open_path)


        if path:

            self.current_result_path = path

            self.lbl_path.setText(os.path.basename(path))

            self.list_cars.clear()

            if os.path.exists(path):

                dirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

                dirs.sort()

                for d in dirs:

                    item = QListWidgetItem(d)

                    item.setCheckState(Qt.Checked)

                    self.list_cars.addItem(item)


    def on_click_generate_report(self):

        """生成报告按钮的回调"""

        if not self.current_result_path or not os.path.exists(self.current_result_path):

            QMessageBox.warning(self, "提示", "请先加载有效的结果文件夹")

            return


        progress = None

        try:

            progress = QProgressDialog("正在整合数据并生成 Word 报告...\n这可能需要一些时间，请耐心等待。", None, 0, 0,

                                       self)

            progress.setWindowTitle("处理中")

            progress.setWindowModality(Qt.WindowModal)

            progress.setMinimumDuration(0)  # 立即显示


            # 2. 显示并强制刷新

            progress.show()

            QApplication.processEvents()


            # 3. 执行耗时任务

            output_file = generate_report(

                self.current_result_path,

                self.configs,

                self.calc.carsim_controller,  # 传入控制器实例

                self.analysis_results  # 传入界面上已经算好的数据(pre_calc_data)

            )


            # 任务完成，关闭进度条

            # 任务完成，关闭进度条

            progress.close()


            if output_file:

                # 1. 不询问，直接尝试打开文件

                try:

                    os.startfile(output_file)

                except Exception as e:

                    QMessageBox.warning(self, "提示", f"尝试自动打开文件失败: {e}")


                # 2. 创建自定义的成功弹窗

                msg_box = QMessageBox(self)

                msg_box.setIcon(QMessageBox.Information)

                msg_box.setWindowTitle("成功")

                msg_box.setText(f"报告生成完毕,\n\n文件路径: {output_file}\n\n(此弹窗将在 5 秒后自动关闭)")


                # 3. 引入 QTimer，设定 5000 毫秒后自动调用 accept() 关闭弹窗

                from PyQt5.QtCore import QTimer

                QTimer.singleShot(5000, msg_box.accept)


                # 显示弹窗并阻塞等待（5秒后被定时器解除阻塞）

                msg_box.exec_()


        except Exception as e:

            # 4. 异常处理：先关进度条，再弹窗

            if progress:

                progress.close()

            QMessageBox.critical(self, "错误", f"报告生成失败: {e}")


    def run_analysis(self):

        # 1. 获取选中车辆

        selected_cars = []

        for i in range(self.list_cars.count()):

            item = self.list_cars.item(i)

            if item.checkState() == Qt.Checked:

                selected_cars.append(item.text())


        if not selected_cars:

            QMessageBox.warning(self, "提示", "请至少勾选一个方案")

            return


        cond_keys = [k for k in self.configs.keys() if k != 'common_config']

        total_tasks = len(cond_keys) * len(selected_cars)


        progress = QProgressDialog("正在分析数据...", "取消", 0, total_tasks, self)

        progress.setWindowModality(Qt.WindowModal)

        progress.setMinimumDuration(0)

        progress.setAutoClose(False)  # 到达100%时不要自动关闭

        progress.setAutoReset(False)  # 不要自动重置

        progress.show()


        self.analysis_results.clear()

        self.calc._results_cache.clear()

        self.calc.veh_info_map.clear()


        self.clear_plot_area()

        self.clear_button_area()


        current_step = 0


        for cond_key in cond_keys:

            self.analysis_results[cond_key] = {}

            for car_folder in selected_cars:

                if progress.wasCanceled(): break


                progress.setLabelText(f"正在分析工况: {cond_key}\n当前方案: {car_folder}")

                QApplication.processEvents()


                folder_full_path = os.path.join(self.current_result_path, car_folder)

                csv_path = self.find_file_in_folder(folder_full_path, cond_key)

                df = safe_read_csv(csv_path) if csv_path else None


                res = self.calc.get_condition_results(car_folder, cond_key, df, self.configs, folder_full_path)

                self.analysis_results[cond_key][car_folder] = res

                current_step += 1

                progress.setValue(current_step)


        progress.setLabelText("分析完成，正在生成图表界面...")

        QApplication.processEvents()


        self.generate_indicator_buttons(cond_keys, selected_cars)

        progress.close()


    def generate_indicator_buttons(self, cond_keys, selected_cars):

        if self.btn_container.layout():

            QWidget().setLayout(self.btn_container.layout())

            self.btn_layout = QHBoxLayout()  # 按钮横向排布

            self.btn_layout.setContentsMargins(0, 0, 0, 0)

            self.btn_container.setLayout(self.btn_layout)


        has_buttons = False


        for cond_key in cond_keys:

            cars_results = self.analysis_results.get(cond_key, {})

            valid_results = [r for r in cars_results.values() if r.get('data') is not None and not r.get('data').empty]

            if not valid_results: continue


            cond_cfg = self.configs.get(cond_key, {})

            indicators = cond_cfg.get('indicators', [])


            # 创建一个容器放该工况下的所有指标

            cond_group = QWidget()

            cond_layout = QHBoxLayout(cond_group)

            cond_layout.setContentsMargins(0, 0, 10, 0)


            # 工况标签

            lbl = QLabel(f"{cond_key}:")

            lbl.setStyleSheet("font-weight: bold; color: #333;")

            cond_layout.addWidget(lbl)


            for ind in indicators:

                ind_label = ind['label']

                has_data = False

                for res in valid_results:

                    # 检查是否有图

                    if res.get('figs', {}).get(ind_label):

                        has_data = True

                        break


                    metric_val = res.get('metrics', {}).get(ind_label)

                    if metric_val is not None and metric_val != "-":

                        has_data = True

                        break


                    x = ind.get('x', {}).get('name')

                    y = ind.get('y1', {}).get('name')

                    if x and y and x in res['data'].columns:

                        has_data = True

                        break


                if has_data:

                    btn = QPushButton(ind_label)

                    btn.setCheckable(True)

                    btn.setCursor(Qt.PointingHandCursor)

                    btn.setStyleSheet("""

                                            QPushButton { 

                                                background-color: #f0f0f0; 

                                                border: 1px solid #ccc; 

                                                border-radius: 4px; 

                                                padding: 5px 10px;

                                            }

                                            QPushButton:checked { 

                                                background-color: #17a2b8; 

                                                color: white; 

                                                border: 1px solid #138496; 

                                                font-weight: bold;

                                            }

                                            QPushButton:hover { 

                                                border-color: #17a2b8; 

                                            }

                                        """)


                    btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

                    font_metrics = btn.fontMetrics()

                    text_width = font_metrics.width(ind_label)

                    btn.setMinimumWidth(text_width + 80)


                    btn.clicked.connect(partial(self.toggle_indicator_row, cond_key, ind_label, selected_cars))

                    cond_layout.addWidget(btn)


                    # 默认选中

                    btn.setChecked(True)

                    self.toggle_indicator_row(cond_key, ind_label, selected_cars, True)

                    has_buttons = True


            self.btn_layout.addWidget(cond_group)


        self.btn_layout.addStretch()


        if not has_buttons:

            self.btn_layout.addWidget(QLabel("没有找到有效的数据或指标"))


    def toggle_indicator_row(self, cond_key, ind_label, selected_cars, checked):

        unique_key = f"{cond_key}|{ind_label}"

        if checked:

            if unique_key in self.plot_rows:

                self.plot_rows[unique_key].show()

            else:

                self.create_indicator_row(cond_key, ind_label, unique_key, selected_cars)

        else:

            if unique_key in self.plot_rows:

                self.plot_rows[unique_key].hide()


    def create_indicator_row(self, cond_key, ind_label, unique_key, selected_cars):


        row_container = QFrame()

        row_container.setFrameShape(QFrame.NoFrame)

        row_container.setStyleSheet("background-color:transparent;")


        main_v_layout = QVBoxLayout(row_container)

        main_v_layout.setContentsMargins(10, 10, 10, 10)

        main_v_layout.setSpacing(5)


        # 标题栏

        title_lbl = QLabel(f"📊 {cond_key} - {ind_label}")

        title_lbl.setStyleSheet("font-weight: bold; color: #333; border: none; font-size: 14px;")  # 稍微加大字体

        main_v_layout.addWidget(title_lbl)


        cars_data_map = self.analysis_results.get(cond_key, {})

        cond_cfg = self.configs.get(cond_key, {})

        target_ind = next((i for i in cond_cfg.get('indicators', []) if i['label'] == ind_label), None)


        if not target_ind: return


        # ========================================================

        # [上方] 嵌入式数据表

        # ========================================================

        table_headers = ["计算方法"] + selected_cars

        table = QTableWidget()

        table.setColumnCount(len(table_headers))

        table.setHorizontalHeaderLabels(table_headers)

        table.setFrameShape(QFrame.NoFrame)

        table.setShowGrid(True)

        table.setStyleSheet("""

            QTableWidget { border: 2px solid #DCDFE6; gridline-color: #E4E7ED; }

            QHeaderView::section { padding: 4px; border: none; border-bottom: 2px solid #DCDFE6; color: #606266; }

            QTableWidget::item { border-bottom: 1px solid #EBEEF5; color: #606266; }

        """)


        raw_method = target_ind.get('method', '-')

        method_list = [str(m) for m in raw_method] if isinstance(raw_method, list) else [str(raw_method)]

        method_cell_text = "\n".join(method_list)

        table.setRowCount(1)

        item_method = QTableWidgetItem(method_cell_text)

        item_method.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        item_method.setToolTip(method_cell_text)

        table.setItem(0, 0, item_method)


        for col_idx, car in enumerate(selected_cars):

            res = cars_data_map.get(car, {})

            val_data = res.get('metrics', {}).get(ind_label, "-")

            val_list = [str(v) for v in val_data] if isinstance(val_data, list) else [str(val_data)]

            max_lines = max(len(method_list), len(val_list))

            final_val_lines = [val_list[i] if i < len(val_list) else "" for i in range(max_lines)]

            item_val = QTableWidgetItem("\n".join(final_val_lines))

            item_val.setTextAlignment(Qt.AlignCenter)

            table.setItem(0, col_idx + 1, item_val)


        # 表格高度自适应

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        table.resizeRowsToContents()

        total_h = table.horizontalHeader().height() + table.rowHeight(0) + 15

        table_height = min(total_h, 160)

        table.setFixedHeight(table_height)

        main_v_layout.addWidget(table)


        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll.setFrameShape(QFrame.NoFrame)

        scroll.setStyleSheet("background-color: transparent;")


        charts_content = QWidget()

        charts_layout = QHBoxLayout(charts_content)

        charts_layout.setAlignment(Qt.AlignLeft)

        charts_layout.setContentsMargins(0, 5, 0, 5)

        charts_layout.setSpacing(15)

        scroll.setWidget(charts_content)

        main_v_layout.addWidget(scroll)


        current_dpi = self.logicalDpiX()

        scale_factor = 1.0


        fig_comp = create_comparison_plot(target_ind, cars_data_map, selected_cars)

        has_any_plot = False

        max_img_height_px = 0


        def add_canvas_to_layout(fig, parent_layout, is_comp=False):

            nonlocal max_img_height_px

            fig.patch.set_facecolor('none')

            fig.set_dpi(current_dpi)

            frame = QFrame()

            if is_comp:

                frame.setStyleSheet(

                    "QFrame { background-color: white; border: 1px solid #E4E7ED; border-radius: 6px; }")

            else:

                frame.setStyleSheet(

                    "QFrame { background-color: #e3f2fd; border: 1px solid #bbdefb; border-radius: 6px; }")


            vbox = QVBoxLayout(frame)

            vbox.setContentsMargins(5, 5, 5, 5)


            canvas = FigureCanvas(fig)

            canvas.setStyleSheet("background-color: transparent; border: none;")


            w_in, h_in = fig.get_size_inches()


            target_w = int(w_in * current_dpi * scale_factor)

            target_h = int(h_in * current_dpi * scale_factor)

            canvas.setFixedSize(target_w, target_h)


            if target_h > max_img_height_px:

                max_img_height_px = target_h


            # 5. Toolbar

            toolbar = NavigationToolbar(canvas, frame)

            if not is_comp:

                toolbar.coordinates = False

                toolbar.setFixedHeight(20)

            toolbar.setStyleSheet("background-color: #F0F0F0; border: none;")


            vbox.addWidget(toolbar)

            vbox.addWidget(canvas)

            parent_layout.addWidget(frame)


        if fig_comp:

            has_any_plot = True

            add_canvas_to_layout(fig_comp, charts_layout, is_comp=True)


        for car_name in selected_cars:

            res = cars_data_map.get(car_name, {})

            figs_data = res.get('figs', {}).get(ind_label)

            if not figs_data: continue


            fig_list = figs_data if isinstance(figs_data, list) else [figs_data]

            for fig in fig_list:

                if not fig: continue

                has_any_plot = True

                add_canvas_to_layout(fig, charts_layout, is_comp=False)


        # ========================================================

        # 容器高度计算

        # ========================================================

        if not has_any_plot:

            scroll.setVisible(False)

            row_container.setFixedHeight(table_height + 60)

        else:

            scroll.setVisible(True)

            # 增加一些余量给 Toolbar 和边距

            scroll_height = max_img_height_px + 80

            scroll.setMinimumHeight(scroll_height)

            row_container.setMinimumHeight(table_height + scroll_height + 50)


        count = self.plot_layout.count()

        self.plot_layout.insertWidget(count - 1, row_container)

        self.plot_rows[unique_key] = row_container


    def find_file_in_folder(self, folder, keyword):

        if not os.path.exists(folder): return None

        files = [f for f in os.listdir(folder) if keyword in f and f.lower().endswith('.csv')]

        return os.path.join(folder, files[0]) if files else None


    def open_report_folder(self):

        """打开报告所在的文件夹"""

        target_path = current_dir  # 默认根目录


        if self.current_result_path and os.path.exists(self.current_result_path):

            target_path = self.current_result_path


        try:

            os.startfile(target_path)

        except Exception as e:

            QMessageBox.warning(self, "错误", f"无法打开文件夹:\n{e}")


    def clear_plot_area(self):

        self.plot_rows.clear()

        while self.plot_layout.count() > 1:

            item = self.plot_layout.takeAt(0)

            if item.widget():

                item.widget().deleteLater()


    def clear_button_area(self):

        if self.btn_layout:

            while self.btn_layout.count():

                item = self.btn_layout.takeAt(0)

                if item.widget():

                    item.widget().deleteLater()



if __name__ == "__main__":

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):

        QApplication.setHighDpiScaleFactorRoundingPolicy(

            Qt.HighDpiScaleFactorRoundingPolicy.Floor)


    app = QApplication(sys.argv)


    carsim_controler = ControlCarsim()

    win = MainUI(carsim_controler)

    win.show()

    sys.exit(app.exec_())



