

from datetime import datetime

import time


import numpy as np

import pandas as pd

import win32com.client

import os

import re

import shutil
from pathlib import Path


from utils import load_configs


CONFIG_PATH = str(Path(__file__).resolve().with_name('offline_report_config.json'))

CONFIGS = load_configs(CONFIG_PATH)



def sanitize_filename(name):

    """

    清洗字符串，使其符合 Windows 文件名规范

    """

    if not name:

        return "Unknown_Category"

    # 定义 Windows 非法字符正则 [cite: 35]

    illegal_chars = r'[\\/:\*\?"<>|]'

    # 替换非法字符为下划线

    clean_name = re.sub(illegal_chars, "_", str(name))

    # 去除首尾空格并限制长度（防止路径过长）

    return clean_name.strip()[:50]



class ControlCarsim():

    def __init__(self):

        self.proc_cate = None

        self.h = win32com.client.Dispatch("CarSim.Application")

        self.h.GoHome()

        self.prog_folder = self.h.GetProgFolder()

        version_info = {}

        version_path = self.prog_folder + 'version.txt'

        if os.path.exists(version_path):

            with open(version_path, 'r', encoding='utf-8') as f:

                for line in f:

                    line = line.strip()

                    if not line or line.startswith('['):

                        continue


                    if '=' in line:

                        key, value = line.split('=', 1)

                        version_info[key.strip()] = value.strip()


            # 提取结果

            product = version_info.get('Product')

            self.version = int(float(version_info.get('Version')))

            print(f"当前Carsim版本：{self.version}")

            print(f"对2020/2024版本适配，其他版本可能存在bluelink/keyword等错误")

            #    return

            build = version_info.get('Build')


        self.initial_lib, self.initial_ds, self.initial_cat = self.h.GetCurrentLibInfo()


        self.configs = CONFIGS

        self.veh_list = None

        self.restore_stack = []

        self.veh_param_list = []


    def clean_list_name(self, raw_list):

        # 去掉id

        names = []

        for raw_string in raw_list:

            # 直接判断有没有冒号

            if ':' in raw_string:

                # split(':', 1) 代表最多只切一刀，分成两份

                # 取 [1] 也就是第一个冒号后面的“所有”内容

                name = raw_string.split(':', 1)[1].strip()

            else:

                name = raw_string.strip()

            names.append(name)

        return names


    def filter_list(self, target_cat, raw_list):

        filtered_names = []

        # 匹配 <...> 里面的内容

        for item in raw_list:

            match = re.search(r'<([^>]+)>', item)


            if match:

                item_category = match.group(1).strip()

                if item_category == target_cat:

                    # 提取 > 后面的纯名称

                    clean_name = item.split('>')[-1].strip()

                    filtered_names.append(clean_name)

            else:

                clean_name = item.split('>')[-1].strip() if '>' in item else item

                filtered_names.append(clean_name)


        return filtered_names


    def get_veh_list(self):

        raw_list = self.h.GetDatasetList("Vehicle: Assembly")


        if not raw_list:

            return []

        vehicle_names = self.clean_list_name(raw_list)

        # <Articulated Bus>Artic Bus Lead, damping, no pwrtrn

        return vehicle_names


    def get_crnt_spring(self, f_or_r):

        """

        钻取获取当前车辆->当前悬架->适配的弹簧列表

        """

        self.h.GoHome()

        veh_lib, veh_ds, veh_cat, _ = self.h.GetBlueLink("#BlueLink2")

        if not veh_lib: return [], []


        self.h.GoToLibrary(veh_lib, veh_ds, veh_cat)


        target_sus_link = "#BlueLink16" if f_or_r == 'F' else "#BlueLink17"

        sus_lib, sus_ds, sus_cat, _ = self.h.GetBlueLink(target_sus_link)

        if not sus_lib: return [], []


        self.h.GoToLibrary(sus_lib, sus_ds, sus_cat)

        spring_lib, spring_ds, spring_cat, _ = self.h.GetBlueLink("#BlueLink0")


        if not spring_lib:

            print("当前悬架未配置弹簧链接")

            if self.h.GetRing('*OPT_SPR') == '0' and self.h.GetRing('#RingCtrl1') == '1':

                print("数字类型弹簧未写读取逻辑")


            return [], []


        raw_list = self.h.GetDatasetList(spring_lib)


        if not raw_list: return [], []


        clean_names = self.clean_list_name(raw_list)

        filter_names = self.filter_list(spring_cat, clean_names)


        return filter_names, spring_ds


    def get_crnt_arb(self, f_or_r):

        """

        钻取获取当前车辆->当前悬架->适配的弹簧列表

        """

        self.h.GoHome()

        veh_lib, veh_ds, veh_cat, _ = self.h.GetBlueLink("#BlueLink2")

        if not veh_lib: return [], []


        self.h.GoToLibrary(veh_lib, veh_ds, veh_cat)


        target_sus_link = "#BlueLink16" if f_or_r == 'F' else "#BlueLink17"

        sus_lib, sus_ds, sus_cat, _ = self.h.GetBlueLink(target_sus_link)

        if not sus_lib: return [], []


        self.h.GoToLibrary(sus_lib, sus_ds, sus_cat)

        arb_lib, arb_ds, arb_cat, _ = self.h.GetBlueLink("#BlueLink2")


        if not arb_lib:

            print("当前悬架未配置稳定杆链接")

            return [], []


        raw_list = self.h.GetDatasetList(arb_lib)


        if not raw_list: return [], []


        clean_names = self.clean_list_name(raw_list)

        filter_names = self.filter_list(arb_cat, clean_names)


        return filter_names, arb_ds


    def get_crnt_dmp(self, f_or_r):

        """

        钻取获取当前车辆->当前悬架->适配的弹阻尼列表

        """

        self.h.GoHome()

        veh_lib, veh_ds, veh_cat, _ = self.h.GetBlueLink("#BlueLink2")

        if not veh_lib: return [], []


        self.h.GoToLibrary(veh_lib, veh_ds, veh_cat)


        target_sus_link = "#BlueLink16" if f_or_r == 'F' else "#BlueLink17"

        sus_lib, sus_ds, sus_cat, _ = self.h.GetBlueLink(target_sus_link)

        if not sus_lib: return [], []


        self.h.GoToLibrary(sus_lib, sus_ds, sus_cat)

        dmp_lib, dmp_ds, dmp_cat, _ = self.h.GetBlueLink("#BlueLink1")


        if not dmp_lib:

            print("当前悬架未配置阻尼链接")

            return [], []


        raw_list = self.h.GetDatasetList(dmp_lib)


        if not raw_list: return [], []


        clean_names = self.clean_list_name(raw_list)

        filter_names = self.filter_list(dmp_cat, clean_names)


        return filter_names, dmp_ds




    def get_crnt_simulink(self):

        """

        simulink

        """

        self.h.GoHome()

        simu_lib, simu_ds, simu_cat, _ = self.h.GetBlueLink("#BlueLink12")

        print(simu_lib)

        print(simu_ds)

        print(simu_cat)

        #Models: Simulink

        raw_list = self.h.GetDatasetList(simu_lib)


        clean_names = self.clean_list_name(raw_list)

        filter_names = self.filter_list(simu_cat, clean_names)


        if not simu_lib: return [], []


        return filter_names, simu_ds


    # def get_crnt_tire(self, f_or_r):

    #     return None,None


    def create_test_dataset(self):

        # 目标数据集信息

        target_lib = "CarSim Run Control"

        target_ds = "OfflineSimulation"

        target_cat = "*AutoOfflineSimulation"

        common_cfg = CONFIGS.get('common_config', {})

        write_list = common_cfg.get('write_list', [])


        exists = self.h.DataSetExists(target_lib, target_ds, target_cat)

        if exists:

            self.h.Gotolibrary(target_lib, target_ds, target_cat)

        else:

            self.h.CreateNew()

            self.h.DatasetCategory(target_ds, target_cat)

            self.h.Gotolibrary(target_lib, target_ds, target_cat)


        # 设置勾选框 (Checkboxes: 1 为勾选, 0 为不勾选)

        self.h.Checkbox("#CheckBox2", "0")

        self.h.Checkbox("#CheckBox3", "0")

        self.h.Checkbox("#CheckBox6", "1")

        self.h.Checkbox("#CheckBox8", "1")


        # --- Write Channels ---

        self.h.Ring("#RingCtrl7", "4")

        self.h.Checkbox("#CheckBox9", "1")

        # 设置下拉列表/环形控件 (Ring controls)

        # self.h.Ring("#RingCtrl7", "4")

        # self.h.Checkbox("#CheckBox9", "0")#考虑simulink write all 会报错

        #

        # write_ds_name = "AOS Write"

        # write_cate_name = "*AutoOfflineSimulation"

        #

        # exists = self.h.DataSetExists("I/O Channels: Write", write_ds_name, write_cate_name)

        # if exists:

        #     self.h.Gotolibrary("I/O Channels: Write", write_ds_name, write_cate_name)

        # else:

        #     self.h.Gotolibrary("I/O Channels: Write", "", "")

        #     self.h.CreateNew()

        #     self.h.DatasetCategory(write_ds_name, write_cate_name)

        #

        # self.h.Ring("#RingCtrl1", "1")

        # self.h.Ring("#RingCtrl3", "1")

        # self.h.Ring("#RingCtrl4", "0")

        # self.h.Ring("#RingCtrl2", "1")

        # self.h.BlueLink("#BlueLink0", target_lib, target_ds, target_cat)

        #

        # content = "\n".join(write_list)#看了下20和24是AVy这种格式

        # self.h.MiscYellow("#MiscYellow0", content)

        # self.h.GoHome()

        # self.h.BlueLink("#BlueLink13", "I/O Channels: Write", write_ds_name, write_cate_name)


        # --- 基础设置 ---

        self.h.Yellow("*TSTEP", "0.001")

        self.h.Yellow("*TSTEP_OUT", "0.01")


        # --- 链接置空 ---

        self.h.BlueLink("#BlueLink9", "", "", "")

        self.h.BlueLink("#BlueLink10", "", "", "")

        self.h.BlueLink("#BlueLink11", "", "", "")

        #simulink保留

        # self.h.BlueLink("#BlueLink12", "", "", "")


    def recover_dataset(self):

        """

        [恢复] 倒序还原所有修改

        """

        if not self.restore_stack:

            print("  没有需要恢复的修改。")

            return


        print(f"\n正在还原 {len(self.restore_stack)} 处修改...")


        while self.restore_stack:

            item = self.restore_stack.pop()


            ctx_lib, ctx_ds, ctx_cat = item['context']

            link_id = item['link_id']

            old_lib, old_ds, old_cat = item['old_val']


            try:

                self.h.GoToLibrary(ctx_lib, ctx_ds, ctx_cat)


                if old_lib:

                    self.h.BlueLink(link_id, old_lib, old_ds, old_cat)

                else:

                    self.h.BlueLink(link_id, "", "", "")  # 原来是空的就清空


            except Exception as e:

                print(f"  ❌ 还原失败: {ctx_ds} 的 {link_id}. 错误: {e}")


        # 最后回到初始界面

        self.h.Gotolibrary(self.initial_lib, self.initial_ds, self.initial_cat)

        print("✅ 所有数据集已恢复至原厂状态。")


    def dynamic_change_ws(self, fw, rw, fs, rs):

        """修改 CarSim 内部库参数并运行"""

        res_mass = self.h.GetBlueLink('#BlueLink16')

        res_susp_f = self.h.GetBlueLink('#BlueLink16')

        res_susp_r = self.h.GetBlueLink('#BlueLink17')


        # 修改簧下质量

        self.h.Gotolibrary(res_mass[0], res_mass[1], res_mass[2])

        self.h.Unlock()

        self.h.Yellow('*W_RF', str(fw))

        self.h.Yellow('*W_RR', str(rw))

        self.h.Yellow('*W_LF', str(fw))

        self.h.Yellow('*W_LR', str(rw))


        # 修改前悬架刚度

        self.h.Gotolibrary(res_susp_f[0], res_susp_f[1], res_susp_f[2])

        self.h.Unlock()

        self.h.Yellow('*KSPRING_L', str(fs))


        # 修改后悬架刚度

        self.h.Gotolibrary(res_susp_r[0], res_susp_r[1], res_susp_r[2])

        self.h.Unlock()

        self.h.Yellow('*KSPRING_L', str(rs))


        self.h.GoHome()


    def get_safe_float(self,keyword):

        """安全读取，失败或为空时返回 None"""

        val = self.h.GetYellow(keyword)

        try:

            return float(val) if val and str(val).strip() else None

        except ValueError:

            return None


    def safe_change_bluelink(self, bluelink_id, target_ds, target_cat=None):

        """

        安全修改 BlueLink

        :param target_cat: (可选) 如果跨类别切换，必须传入目标 Category

        """

        ctx_lib, ctx_ds, ctx_cat = self.h.GetCurrentLibInfo()
        curr_lib, _, curr_cat, _ = self.h.GetBlueLink(bluelink_id)

        if curr_lib:

            self._save_restore_point(bluelink_id)


            # 智能判断：如果传了新的 cat 就用新的，否则沿用旧的

            cat_to_use = target_cat if target_cat is not None else curr_cat


            self.h.BlueLink(bluelink_id, curr_lib, target_ds, cat_to_use)


            current_lib, current_dataset, current_cat, _ = self.h.GetBlueLink(bluelink_id)

            if current_dataset != target_ds or current_cat != cat_to_use:

                print(
                    f"    ❌ 链接设置不匹配：位置 {ctx_lib}/{ctx_ds}/{ctx_cat}，"
                    f"链接 {bluelink_id}，期望 {curr_lib}/{target_ds}/{cat_to_use}，"
                    f"实际为 {current_lib}/{current_dataset}/{current_cat}"
                )

                return False

            return True

        print(
            f"    ❌ 链接不可用：位置 {ctx_lib}/{ctx_ds}/{ctx_cat}，"
            f"链接 {bluelink_id} 无法读取当前 Library"
        )

        return False


    def get_crnt_veh_param(self, veh_ds=None, veh_cat=None, save_path=None):

        """

        提取当前车辆参数，并可选地保存到指定路径下的 config.txt

        :param veh_ds: 车辆Dataset名

        :param veh_cat: 车辆Category名

        :param save_path: (新增) 保存 config.txt 的文件夹路径

        """

        if (veh_ds or veh_cat) is None:

            self.h.GoHome()

            # 1. 获取车辆基本信息 (用于后续去重判断)

            veh_lib, veh_ds, veh_cat, _ = self.h.GetBlueLink("#BlueLink2")

            if not veh_lib:

                return None


        # 初始化一个临时字典存储本次提取的值

        params = {

            "name": veh_ds,

            "category": veh_cat,

            "wheel_base": 1.0,

            "f_wheel_base": 1.0,

            "r_wheel_base": 1.0,

            "f_weight": 1.0,

            "r_weight": 1.0,

            "f_track_width": 1.0,

            "r_track_width": 1.0,

            "steer_ratio": 1.0

        }


        # 2. 处理车身/轴距数据 (保持原有逻辑不变)

        self.h.GoToLibrary("Vehicle: Assembly", veh_ds, veh_cat)

        self.h.Checkbox("#CheckBox2", "1")#制动俯仰工况需要


        body_lib, body_ds, body_cat, _ = self.h.GetBlueLink('#BlueLink0')

        steer_lib, steer_ds, steer_cat, _ = self.h.GetBlueLink('#BlueLink7')


        self.h.GoToLibrary(body_lib, body_ds, body_cat)


        # 确定轴距关键字

        raw_wb = self.get_safe_float('L_WHEELBASE')


        # 如果 L_WHEELBASE 没读到内容（为空或 None），则尝试读 LX_AXLE

        if raw_wb is None:

            raw_wb = self.get_safe_float('LX_AXLE')


        if raw_wb is not None:

            params["wheel_base"] = raw_wb / 1000.0  # mm 转 m

        else:

            print("⚠️ 轴距参数(L_WHEELBASE/LX_AXLE)解析失败，已沿用默认值 1.0m。")


        if 'Sprung Mass (from Whole Vehicle)' in body_lib:

            # 轴荷计算

            w_lf = self.get_safe_float('*W_LF')

            w_rf = self.get_safe_float('*W_RF')

            w_lr = self.get_safe_float('*W_LR')

            w_rr = self.get_safe_float('*W_RR')


            f_track = self.get_safe_float('*L_TRACK(1)')

            if f_track is not None:

                params["f_track_width"] = f_track


            r_track = self.get_safe_float('*L_TRACK(2)')

            if r_track is not None:

                params["r_track_width"] = r_track


            if all(v is not None for v in [w_lf, w_rf, w_lr, w_rr]):

                params["f_weight"] = w_lf + w_rf

                params["r_weight"] = w_lr + w_rr

                # 质心位置计算

                total_weight = params["f_weight"] + params["r_weight"]

                if total_weight > 0:

                    params["f_wheel_base"] = params["wheel_base"] * params["r_weight"] / total_weight

                    params["r_wheel_base"] = params["wheel_base"] - params["f_wheel_base"]

            else:

                print(f"⚠️ {veh_ds} 载荷数据缺失或解析异常，已沿用默认值 1.0")


        else:

            print(f"⚠️ {veh_ds}无载荷信息节点，已沿用默认值 1.0")


        #传动比

        self.h.GoToLibrary(steer_lib, steer_ds, steer_cat)

        cfactor_val = self.get_safe_float('*CF_F')

        cfactor_unit = self.h.GetRing('*RingCtrl8') #24版有两个单位可以选择

        if cfactor_unit is not None:

            unit_str = str(cfactor_unit).strip()

            if unit_str == '1':

                # 如果是 '1' (mm/deg)，转换为 mm/rev

                cfactor_val *= 360.0

                print(f"⚠️ {veh_ds} 读取到Cfactor单位mm/deg，已转换为 mm/rev")


        if cfactor_val is None:

            print(f"⚠️ {veh_ds} 无Cfactor，已沿用默认值 1.0")


        params["cfactor"] = cfactor_val


        steer_kine_lib, steer_kine_ds, steer_kine_cat, _ = self.h.GetBlueLink('#BlueLink10')

        self.h.GoToLibrary(steer_kine_lib, steer_kine_ds, steer_kine_cat)


        kine_table = self.h.GetTable("#DiagramOne0")

        if kine_table and len(kine_table[0]) > 1:

            data_array = np.array(kine_table)

            x = data_array[:, 0]

            y = data_array[:, 1]

            slopes = np.gradient(y, x)


            zero_idx = np.argmin(np.abs(x))

            center_slope = slopes[zero_idx]


            if center_slope != 0 and cfactor_val != 0:

                params["steer_ratio"] = 1.0 / ((params["cfactor"] / 360) * center_slope)


        # params["steer_ratio"] = 1.0


        # 4. 更新内部列表 (保持原有逻辑不变)

        if not hasattr(self, 'veh_param_list'):

            self.veh_param_list = []


        is_exist = any(item['name'] == veh_ds for item in self.veh_param_list)

        if not is_exist:

            self.veh_param_list.append(params)

        else:

            print(f"{veh_ds} 已经成功提取过物理参数的车辆信息（换件不影响），跳过添加。")


        if save_path:

            try:

                if not os.path.exists(save_path):

                    os.makedirs(save_path)


                txt_file = os.path.join(save_path, 'config.txt')

                with open(txt_file, 'w', encoding='utf-8') as f:

                    f.write("=== Vehicle Parameters Configuration ===\n")

                    f.write(f"Dataset: {params['name']}\n")

                    f.write(f"Category:     {params['category']}\n")

                    f.write("----------------------------------------\n")

                    f.write(f"Wheel Base (m):      {params['wheel_base']:.4f}\n")

                    f.write(f"Front Wheel Base (m):{params['f_wheel_base']:.4f}\n")

                    f.write(f"Rear Wheel Base (m): {params['r_wheel_base']:.4f}\n")

                    f.write(f"Front Track Width (m): {params['f_track_width']:.2f}\n")

                    f.write(f"Rear Track Width (m): {params['r_track_width']:.2f}\n")

                    f.write(f"Front Weight (kg):   {params['f_weight']:.2f}\n")

                    f.write(f"Rear Weight (kg):    {params['r_weight']:.2f}\n")

                    f.write(f"CFactor(mm/rev):     {params['cfactor']:.2f}\n")

                    f.write(f"Steer Ratio:         {params['steer_ratio']:.2f}\n")

                    f.write("========================================\n")

                print(f"    📄 参数已保存至: {txt_file}")

                print(f"    📄 计算传动比: {params['steer_ratio']:.2f}")

            except Exception as e:

                print(f"    ❌ 保存config.txt失败: {e}")


        self.h.GoHome()


        return params


    def change_procedure(self, proc_ds):

        if proc_ds == 'Multi-Condition':

            print(f"    多工况")

            return True

        return self.safe_change_bluelink('#BlueLink28', proc_ds, target_cat=self.proc_cate)


    def change_vehicle(self, veh_ds, veh_cate):

        self.h.GoHome()

        return self.safe_change_bluelink('#BlueLink2', veh_ds, target_cat=veh_cate)


    def change_crnt_spring(self, axle, sus_ds):

        if sus_ds == "ori" or sus_ds == "<无可用/不适用>": return

        self.h.GoHome()

        v_lib, v_ds, v_cat, _ = self.h.GetBlueLink("#BlueLink2")

        self.h.GoToLibrary(v_lib, v_ds, v_cat)

        sl = "#BlueLink16" if axle == 'F' else "#BlueLink17"

        s_lib, s_ds, s_cat, _ = self.h.GetBlueLink(sl)

        self.h.GoToLibrary(s_lib, s_ds, s_cat)


        return self.safe_change_bluelink("#BlueLink0", sus_ds)


    def change_crnt_arb(self, axle, arb_ds):

        if arb_ds == "ori" or arb_ds == "<无可用/不适用>": return

        self.h.GoHome()

        v_lib, v_ds, v_cat, _ = self.h.GetBlueLink("#BlueLink2")

        self.h.GoToLibrary(v_lib, v_ds, v_cat)

        sl = "#BlueLink16" if axle == 'F' else "#BlueLink17"

        s_lib, s_ds, s_cat, _ = self.h.GetBlueLink(sl)

        self.h.GoToLibrary(s_lib, s_ds, s_cat)


        return self.safe_change_bluelink("#BlueLink2", arb_ds)


    def change_crnt_dmp(self, axle, dmp_ds):

        if dmp_ds == "ori" or dmp_ds == "<无可用/不适用>": return

        self.h.GoHome()

        v_lib, v_ds, v_cat, _ = self.h.GetBlueLink("#BlueLink2")

        self.h.GoToLibrary(v_lib, v_ds, v_cat)

        sl = "#BlueLink16" if axle == 'F' else "#BlueLink17"

        s_lib, s_ds, s_cat, _ = self.h.GetBlueLink(sl)

        self.h.GoToLibrary(s_lib, s_ds, s_cat)


        return self.safe_change_bluelink("#BlueLink1", dmp_ds)


    def change_simulink(self, sim_ds):

        """

        切换或关闭 Simulink 联合仿真模型

        :param sim_ds: Simulink Dataset 的名字，或特定关断口令(如 "None", "ori", "无")

        """

        self.h.GoHome()


        SIM_LINK_ID = "#BlueLink12"

        SIM_LIB = "Models: Simulink"


        curr_lib, curr_ds, curr_cat, _ = self.h.GetBlueLink(SIM_LINK_ID)

        self._save_restore_point(SIM_LINK_ID)


        # ================= 核心修复区 =================

        # 1. 如果用户在界面取消了模型，强制清空底层的 Simulink 链接

        if sim_ds in ["", "ori", "<无可用/不适用>", "无", "None"]:

            if str(curr_lib).strip() != "":

                self.h.BlueLink(SIM_LINK_ID, "", "", "")


                # 校验是否清空成功

                test_lib, _, _, _ = self.h.GetBlueLink(SIM_LINK_ID)

                if str(test_lib).strip() == "" or test_lib is not None:

                    print("    ❌ 无法清除 Simulink 链接，退回离线模式失败")

                    return False

                print("    ▶ 界面已取消选择模型，强制清空 Simulink 链接转为离线模式")

            return True


        # 2. 如果用户选择了某个具体的 Simulink 模型，则挂载新模型

        self.h.BlueLink(SIM_LINK_ID, SIM_LIB, sim_ds, curr_cat)


        # 3. 校验是否修改成功

        _, new_ds, _, _ = self.h.GetBlueLink(SIM_LINK_ID)

        if str(new_ds).strip() != str(sim_ds).strip():

            print(f"    ❌ Simulink 模型设置失败：期望 [{sim_ds}]，实际为 [{new_ds}]")

            print("       (请检查该名称是否存在于 Models: Simulink 库中)")

            return False


        # print(f"    ✅ Simulink 模型成功切换至: {sim_ds}")

        return True


    def find_alias_col_name(self, col_name, columns):

        """

        查找别名列

        :param col_name:

        :param columns:

        :return:

        """

        if col_name in columns:

            return col_name


        common_cfg = CONFIGS.get('common_config', {})

        alias_map = common_cfg.get('col_alias', {})

        config_aliases = alias_map.get(col_name, [])

        search_candidates = []

        seen = set()

        for alias in config_aliases:

            if alias not in seen:

                search_candidates.append(alias)

                seen.add(alias)


        find_col = next((col for col in search_candidates if col in columns), None)


        return find_col


    def step_cond_check(self):

        """

        闭环控制：调整方向盘转角，直到 11s-15s 的平均侧向加速度(Ay)在 0.3g~0.39g 之间

        """

        target_ay = 0.3  # 目标中心值

        tolerance = 0.005


        lower_bound = target_ay - tolerance  # 0.295

        upper_bound = target_ay + tolerance * 5 # 0.325


        max_iter = 8  # 最大迭代次数，防止死循环


        current_angle = 30.0


        step_steer_ds = "Step"


        print(f"\n[Step Check] 开始迭代寻找 0.3g Ay (目标范围: {lower_bound}~{upper_bound}g)")


        for i in range(max_iter):

            print(f"  > 迭代 [{i + 1}/{max_iter}] 当前尝试转角: {current_angle:.2f} deg")


            self.change_steer_table(current_angle, step_steer_ds,1)


            success = self.execute_simulation()

            if not success:

                print("  ❌ 仿真运行失败，停止迭代")

                break


            csv_path = self.get_latest_csv_path()  # 获取最新生成的 CSV

            if not csv_path:

                print("  ❌ 未找到结果文件")

                break


            df = pd.read_csv(csv_path, header=0)

            df.columns = [c.strip() for c in df.columns]


            ay_col = self.find_alias_col_name('Ay', df.columns)

            time_col = self.find_alias_col_name('TimeStep', df.columns)


            if (ay_col is None) or (time_col is None):

                print(f"  ⚠️ CSV中未找到 TimeStep 或 Ay 相关列")

                return None


            # 稳态均值 (11s - 15s)

            start_time = 11.0

            end_time = 15.0


            # 筛选时间段

            steady_data = df[(df[time_col] >= start_time) & (df[time_col] <= end_time)]


            if steady_data.empty:

                print("  ⚠️ 仿真时间不足，无法获取稳态数据")

                mean_ay = 0.0

            else:

                mean_ay = abs(steady_data[ay_col].mean())


            print(f"    --> 仿真结果: Mean Ay = {mean_ay:.4f} g")


            # 5. 判断条件

            if (mean_ay >= lower_bound) and (mean_ay <= upper_bound):

                print(f"  ✅ 满足条件！最终转角: {current_angle:.2f} deg")

                return current_angle  # 返回最终角度，结束函数


            if mean_ay < 0.001:

                mean_ay = 0.001  # 防止除以0


            # 计算修正系数

            ratio = target_ay / mean_ay


            new_angle = round(current_angle * ratio, 4)


            if (new_angle >= 50) & (new_angle <= 10):

                new_angle = 30


            current_angle = new_angle


        print("  ⚠️ 达到最大迭代次数，未完全收敛。")

        return current_angle


    def pulse_cond_check(self):

        """

        角脉冲 Ay max 4m/s2

        """

        target_ay = 0.401  # 目标中心值g

        tolerance = 0.005


        lower_bound = target_ay - tolerance

        upper_bound = target_ay + tolerance * 5


        max_iter = 8  # 最大迭代次数，防止死循环


        current_angle = 35


        pulse_steer_ds = "Pulse Steer"


        print(f"\n[Pulse Steer Check] 开始迭代寻找 0.401g Ay (目标范围: {lower_bound}~{upper_bound}g)")


        for i in range(max_iter):

            print(f"  > 迭代 [{i + 1}/{max_iter}] 当前尝试转角: {current_angle:.2f} deg")


            self.change_steer_table(current_angle, pulse_steer_ds, 2)


            success = self.execute_simulation()

            if not success:

                print("  ❌ 仿真运行失败，停止迭代")

                break


            csv_path = self.get_latest_csv_path()  # 获取最新生成的 CSV

            if not csv_path:

                print("  ❌ 未找到结果文件")

                break


            df = pd.read_csv(csv_path, header=0)

            df.columns = [c.strip() for c in df.columns]


            ay_col = self.find_alias_col_name('Ay', df.columns)

            time_col = self.find_alias_col_name('TimeStep', df.columns)


            if (ay_col is None) or (time_col is None):

                print(f"  ⚠️ CSV中未找到 TimeStep 或 Ay 相关列")

                return None


            max_ay = df['Ay'].max()


            print(f"    --> 仿真结果: Max Ay = {max_ay:.4f} g")


            # 5. 判断条件

            if (max_ay >= lower_bound) and (max_ay <= upper_bound):

                print(f"  ✅ 满足条件！最终转角: {current_angle:.2f} deg")

                return current_angle  # 返回最终角度，结束函数


            if max_ay < 0.001:

                max_ay = 0.001  # 防止除以0


            # 计算修正系数

            ratio = target_ay / max_ay


            new_angle = round(current_angle * ratio, 4)


            if (new_angle >= 50) & (new_angle <= 10):

                new_angle = 30


            current_angle = new_angle


        print("  ⚠️ 达到最大迭代次数，未完全收敛。")

        return current_angle


    def moose_cond_check(self, step=5.0):

        """

        麋鹿工况 (基于直接修改桩桶坐标)

        :param step: 每次递增的车速 (km/h)

        """

        max_iter = 10  # 最大迭代次数，防止死循环

        highest_pass_speed = 0.0


        # 假设从之前的流程中获取了车宽，这里默认 1.8m (你可以根据提取的参数动态传入)

        car_width = 1.8


        print(f"\n[Moose Check] 开始迭代寻找最高不离地且不触桩车速")


        # ==========================================

        # 内部函数：设置桩桶边界

        # ==========================================

        def set_moose_boundary(width):

            """

            根据车宽计算 ISO 3888-2 边界，并写入 Repeated Object 的坐标表

            每隔约 3m 放置一个桩桶，单侧 15 个，共 30 个坐标点

            """

            self.h.GoHome()

            self.h.Gotolibrary("Road: Animator Repeated Object", "Moose Cones", "Stardard_0122")


            # 计算各区间半宽

            w1_half = (1.1 * width + 0.25) / 2

            w3_half = (width + 1.0) / 2

            w5_half = max(1.3 * width + 0.25, 3.0) / 2


            # 各区间的 X 坐标序列 (每隔 3 米)

            x_sec1 = [0.0, 3.0, 6.0, 9.0, 12.0]

            x_sec3 = [25.5, 28.5, 31.5, 34.5, 36.5]

            x_sec5 = [49.0, 52.0, 55.0, 58.0, 61.0]


            left_cones = []

            right_cones = []


            # 区间 1 坐标填充

            for x in x_sec1:

                left_cones.append([x, w1_half])

                right_cones.append([x, -w1_half])


            # 区间 3 坐标填充 (中心偏置 1.0m)

            for x in x_sec3:

                left_cones.append([x, 1.0 + w3_half])

                right_cones.append([x, 1.0 - w3_half])


            # 区间 5 坐标填充

            for x in x_sec5:

                left_cones.append([x, w5_half])

                right_cones.append([x, -w5_half])


            # 写入坐标表格

            self.h.SetTable("#DiagramOne0", left_cones)

            try:

                self.h.SetTable("#DiagramOne1", right_cones)

            except Exception as e:

                print(f"  ⚠️ 警告：无法写入右侧桩桶表(#DiagramOne1)。错误: {e}")


            print(f"  --> 当前车宽 {width}m，已更新 3D 桩桶边界坐标 (左右各15个)")


        # 1. 运行设置桩桶函数

        set_moose_boundary(car_width)


        # 2. 获取初始车速

        self.h.GoHome()

        self.h.Gotolibrary("Procedures", "Moose", self.proc_cate)

        try:

            current_speed = float(self.h.GetYellow("*SPEED"))

        except (ValueError, TypeError):

            print("  ⚠️ 无法读取初始车速，默认设置为 60 km/h")

            current_speed = 60.0


        # ==========================================

        # 开始迭代寻优

        # ==========================================

        for i in range(max_iter):

            print(f"\n  > 迭代 [{i + 1}/{max_iter}] 当前尝试车速: {current_speed:.2f} km/h")


            # 写入新车速

            self.h.Gotolibrary("Procedures", "Moose", self.proc_cate)

            self.h.Yellow("*SPEED", str(current_speed))


            # 执行仿真

            success = self.execute_simulation()

            if not success:

                print("  ❌ 仿真运行失败，停止迭代")

                break


            # 获取 CSV 数据

            csv_path = self.get_latest_csv_path()

            if not csv_path:

                print("  ❌ 未找到结果文件")

                break


            df = pd.read_csv(csv_path, header=0)

            df.columns = [c.strip() for c in df.columns]


            # ==========================================

            # 判定函数 1：不触碰桩桶判定

            # ==========================================

            def check_no_cone_hit(dataframe):

                """基于车辆质心坐标(Xo, Yo)与赛道边界比对，判断是否越界"""

                x_col = self.find_alias_col_name('Xo', dataframe.columns)

                y_col = self.find_alias_col_name('Yo', dataframe.columns)


                if not x_col or not y_col:

                    print("  ⚠️ CSV中缺失 Xo 或 Yo 坐标，无法判定触桩！")

                    return False


                # 动态宽度阈值

                w1_half = (1.1 * car_width + 0.25) / 2

                w3_half = (car_width + 1.0) / 2

                w5_half = max(1.3 * car_width + 0.25, 3.0) / 2


                x_vals = dataframe[x_col].values

                y_vals = dataframe[y_col].values


                for x, y in zip(x_vals, y_vals):

                    if 0 <= x <= 12.0:

                        if abs(y) > w1_half: return False

                    elif 25.5 <= x <= 36.5:

                        if y > (1.0 + w3_half) or y < (1.0 - w3_half): return False

                    elif 49.0 <= x <= 61.0:

                        if abs(y) > w5_half: return False

                return True  # 全程未越界


            # ==========================================

            # 判定函数 2：不离地判定

            # ==========================================

            def check_no_wheel_lift(dataframe):

                """监控四个车轮的垂向力(Fz)，低于阈值判定为离地"""

                fz_cols = ['Fz_L1', 'Fz_R1', 'Fz_L2', 'Fz_R2']

                available_cols = [col for col in fz_cols if self.find_alias_col_name(col, dataframe.columns)]


                if not available_cols:

                    print("  ⚠️ CSV中缺失轮胎垂向力(Fz)，跳过离地判定")

                    return True


                threshold = 10.0  # 过滤计算底噪

                for col in available_cols:

                    act_col = self.find_alias_col_name(col, dataframe.columns)

                    min_fz = dataframe[act_col].min()

                    if min_fz < threshold:

                        print(f"    --> 🚗 车轮离地: {act_col} = {min_fz:.2f} N")

                        return False

                return True


            # 综合判定

            is_safe_cone = check_no_cone_hit(df)

            is_safe_lift = check_no_wheel_lift(df)


            # 额外校验：是否失控翻车 (未完成整个工况)

            station_col = self.find_alias_col_name('Station', df.columns)

            max_station = df[station_col].max() if station_col else 61.0


            if max_station < 50.0:

                print(f"    --> 💥 失败：车辆严重失控未跑完全程 ({max_station:.1f} m)")

                break

            if not is_safe_cone:

                print(f"    --> 💥 失败：触碰桩桶 (越界)！")

                break

            if not is_safe_lift:

                print(f"    --> 💥 失败：发生车轮离地！")

                break


            print(f"    --> ✅ 成功：车速 {current_speed} km/h 完美通过！")

            highest_pass_speed = current_speed

            current_speed += step


        # ==========================================

        # 结果输出

        # ==========================================

        if highest_pass_speed > 0:

            print(f"\n🏆 麋鹿测试最高通过车速: {highest_pass_speed} km/h")

        else:

            print(f"\n😭 危险！起步车速即失败。")


        return highest_pass_speed



    def change_steer_table(self, target_angle, steer_ds, cond_switch):

        """

        修改方向盘转角 Table 为阶跃输入

        Args:

            target_angle (float): 阶跃后的目标转角 (deg)

            steer_ds (str): 转向数据集名称 (Dataset Name)

        """

        self.h.Gotolibrary("Control: Steering (Open Loop)", steer_ds, self.proc_cate)


        self.h.Ring("#RingCtrl0", "LINEAR")

        self.h.Radio("#RadioCtrl0", "0")  # customsetting


        if cond_switch == 1:

            table_data = [

                [0.0, 0.0],

                [10.0, 0.0],

                [10.1, float(target_angle)],

                [15.0, float(target_angle)]

            ]

        else:

            table_data = [

                [0, 0],

                [10, 0],

                [10.2, float(target_angle)],

                [10.4, 0],

                [20, 0]

            ]

        self.h.SetTable("#DiagramOne0", table_data)


    def set_vehicle_list(self, veh_list):

        self.veh_list = veh_list


    def run_carsim_batch(self, export_root_path):

        """

        循环执行仿真任务

        """

        self.create_test_dataset()

        self.clear_restore_stack()


        common = self.configs.get('common_config', {})

        self.proc_cate = common.get('Procedure_Category', "")

        start_time = datetime.now()

        time_stamp = start_time.strftime('%Y%m%d_%H%M%S')

        time_path = os.path.join(export_root_path, time_stamp)


        # 不同车

        for (veh_ds, veh_cate) in self.veh_list:

            self.h.GoHome()


            res = self.change_vehicle(veh_ds, veh_cate)


            if not res:

                continue


            veh_folder_name = sanitize_filename(veh_ds)

            curr_car_export_path = os.path.join(time_path, veh_folder_name)


            if not os.path.exists(curr_car_export_path):

                os.makedirs(curr_car_export_path)


            print(f"\n🚗 当前车型: {veh_ds} | 导出路径: {curr_car_export_path}")


            # 不同工况

            for i, (keyword, info) in enumerate(self.configs.items()):

                if keyword == 'common_config':

                    continue


                proc_ds = info.get('Dataset')

                print(f"\n  >>> 任务进度 [{i}/{len(self.configs) - 1}]: {keyword}")


                res = self.change_procedure(proc_ds)

                if not res:

                    continue


                success = self.execute_simulation()


                if "Step" in proc_ds:

                    self.step_cond_check()

                elif "Pulse"in proc_ds:

                    self.pulse_cond_check()


                if success:

                    time.sleep(1.0)

                    self.rename_carsim_output_csv(curr_car_export_path, keyword)

                else:

                    print(f"  ⚠️ 跳过工况 {keyword} 的后续文件处理")


        print("\n[FINISH] 所有批处理任务已完成。")

        return time_path


    def execute_simulation(self):

        """执行仿真并确保完成后再移动文件"""

        self.h.GoHome()

        lib, ds, _, _ = self.h.GetBlueLink("#BlueLink12")

        is_offline = (lib is None or ds is None)


        if is_offline:

            # ==========================================

            # 模式 A：使用 CarSim 内置求解器 (纯物理)

            # ==========================================

            threw_error = self.h.Run_CheckError('', '')


            if threw_error:

                code, msg = self.h.GetError()

                print(f"    ❌ 仿真运行失败! 错误码: {code}, 信息: {msg}")

                return False

            return True


        else:

            # ==========================================

            # 模式 B：联合 Simulink 运行

            # ==========================================

            print(f"    ▶ 准备联合 Simulink 运行 (模型: {ds})...")


            try:

                self.h.RunButtonClick(1)

            except Exception as e:

                print(f"    ❌ Simulink 运行异常: {e}")

                return False

            return True


    def get_latest_csv_path(self):

        """

        从 CarSim 结果目录找到最新的 CSV

        """

        curr_pars = self.h.GetCurrentDataSetID()

        results_list = self.h.QueryRunForResults(curr_pars)

        # print(f"{results_list}")


        curr_output_file = None


        if results_list:

            curr_output_files = [f for f in results_list if f.lower().endswith('.csv')]

            curr_output_files.sort(key=os.path.getmtime, reverse=True)

            curr_output_file = curr_output_files[0]


        return curr_output_file


    def clear_restore_stack(self):

        """

        任务开始前强制清空栈，防止残留上一轮的记录

        """

        self.restore_stack = []


    def _save_restore_point(self, link_id):

        """

        在修改链接前，保存当前状态。

        关键逻辑：如果同一个位置之前保存过，则不覆盖！确保栈底永远是“原厂值”。

        """

        cur_lib, cur_ds, cur_cat = self.h.GetCurrentLibInfo()


        # 是否已存在该位置的备份

        for item in self.restore_stack:

            if (item['context'] == (cur_lib, cur_ds, cur_cat) and

                    item['link_id'] == link_id):

                # print(f"  [保护] {cur_ds} 的 {link_id} 已有原厂备份，跳过本次覆盖。")

                return


        old_lib, old_ds, old_cat, _ = self.h.GetBlueLink(link_id)


        self.restore_stack.append({

            'context': (cur_lib, cur_ds, cur_cat),

            'link_id': link_id,

            'old_val': (old_lib, old_ds, old_cat)

        })


    def rename_carsim_output_csv(self, final_export_dir, new_base_name):

        """

        从 CarSim 结果目录找到最新的 CSV，重命名并移动到目标位置

        """

        curr_output_file = self.get_latest_csv_path()


        # 3. 准备目标路径

        if not os.path.exists(final_export_dir):

            os.makedirs(final_export_dir)


        target_path = os.path.join(final_export_dir, f"{new_base_name}.csv")


        if os.path.exists(target_path):

            os.remove(target_path)


        shutil.move(curr_output_file, target_path)
