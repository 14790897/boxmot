# 550 是H:\shnu-graduation\alldata\alldata\20180117-hfq-y\Y1-550\相机No.1_C001H001S0001 x再算一次
# 750 是 H:\shnu-graduation\alldata\alldata\20180117-hfq-y\Y1-750\No.1_C001H001S0002 后处理再算一次
# 850 是 H:\shnu-graduation\alldata\alldata\20180117-hfq-y\Y1-850\相机No.1_C001H001S0001
# 450  是 H:\shnu-graduation\alldata\alldata\20180117-hfq-y\y1-450\相机No.1_C001H001S0002
# 650 是 H:\shnu-graduation\alldata\alldata\20180117-hfq-y\Y1-650\相机No.1_C001H001S0002


import json
import os
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from process_utils import get_all_folders

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 16  # 设置全局字体大小

def load_excel_true_data():
    """
    从 Excel 文件中加载 TRUE_rotation 和 TRUE_revolution 数据，
    根据表格结构自动处理转置
    """
    # 读取 Excel 文件
    data = pd.read_excel(
        r"C:\git-program\particle_detect\manual_caculate\data\relative error.xlsx",
        sheet_name="Sheet1",
        header=None,  # 先不设置表头
    )
    
    print("原始数据形状:", data.shape)
    print("第一列前10个值:", data.iloc[:10, 0].tolist())
    
    # 检查第一列是否包含我们期望的字段名
    expected_fields = ['flow_velocity', 'TRUE_rotation', 'TRUE_revolution', 'height', 'diameter']
    first_column_values = data.iloc[:, 0].astype(str).str.lower().tolist()
    
    has_expected_fields = any(field.lower() in ' '.join(first_column_values) for field in expected_fields)
    
    if has_expected_fields:
        # 第一列包含字段名，需要转置
        print("检测到表格需要转置")
        data = data.T
        data.columns = data.iloc[0]  # 使用第一行作为列名
        data = data[1:]  # 删除第一行
    else:
        # 第一行是列名
        print("表格已经是正确格式")
        data.columns = data.iloc[0]
        data = data[1:]
    
    # 清理列名
    data.columns = data.columns.astype(str).str.strip()
    print("处理后的列名:", data.columns.tolist())
    
    # 检查并处理必要的列（支持不同的列名变体）
    column_mapping = {
        'height': ['height', 'Height', 'HEIGHT'],
        'diameter': ['diameter', 'Diameter', 'DIAMETER'],
        'TRUE_rotation': ['TRUE_rotation', 'true_rotation', 'True_rotation'],
        'TRUE_revolution': ['TRUE_revolution', 'true_revolution', 'True_revolution'],
        'flow_velocity': ['flow_velocity', 'flow_velocitiy', 'Flow_velocity']  # 注意拼写错误的兼容
    }
    
    # 找到实际的列名
    actual_columns = {}
    for standard_name, variants in column_mapping.items():
        found = False
        for variant in variants:
            if variant in data.columns:
                actual_columns[standard_name] = variant
                found = True
                break
        if not found:
            print(f"警告：未找到列 {standard_name}")
    
    if len(actual_columns) < 5:
        print(f"警告：只找到了 {len(actual_columns)} 个必需的列")
        return pd.DataFrame(columns=['H/D', 'TRUE_rotation', 'TRUE_revolution', 'flow_velocity'])
    
    # 重命名列为标准名称
    rename_dict = {v: k for k, v in actual_columns.items()}
    data = data.rename(columns=rename_dict)
    
    # 确保相关列转换为数值类型
    numeric_columns = ['height', 'diameter', 'TRUE_rotation', 'TRUE_revolution']
    for col in numeric_columns:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    
    # 计算 H/D 比值
    if 'height' in data.columns and 'diameter' in data.columns:
        data["H/D"] = data["height"] / data["diameter"] * 147
    
    # 处理 flow_velocity 列
    if 'flow_velocity' in data.columns:
        data['flow_velocity'] = data['flow_velocity'].astype(str)
    else:
        print("警告：表格中没有找到 'flow_velocity' 列")
        data['flow_velocity'] = 'unknown'
    
    # 过滤掉无效数据
    required_for_filter = [col for col in ['TRUE_rotation', 'TRUE_revolution', 'H/D'] if col in data.columns]
    if required_for_filter:
        valid_data = data.dropna(subset=required_for_filter)
        # 过滤掉 flow_velocity 为空或 'nan' 的数据
        valid_data = valid_data[valid_data['flow_velocity'].notna()]
        valid_data = valid_data[valid_data['flow_velocity'] != 'nan']
        valid_data = valid_data[valid_data['flow_velocity'] != 'None']
    else:
        valid_data = data
    
    print(f"有效数据行数: {len(valid_data)}")
    if len(valid_data) > 0 and 'flow_velocity' in valid_data.columns:
        print("流速分组:", valid_data['flow_velocity'].unique())
    
    return valid_data
def merge_stats(*folders):
    """
    合并每个流速的文件夹的 all_stats.json 数据，并为第二个及后续文件夹的数据键名加上 '-2', '-3', ...

    :param folders: 需要合并的文件夹路径列表
    :return: 合并后的 JSON 数据
    """
    data = {}
    len_folders = len(folders)
    for index, folder in enumerate(folders):
        stats_path = os.path.join(folder, "initial_result", "all_stats.json")
        if index == 1:
            print("folder", folder, "number", len_folders)
        if os.path.exists(stats_path):
            with open(stats_path, "r") as f:
                stats_data = json.load(f)

            # 第一个文件夹不修改键名，后续的加上 "-2", "-3"...
            if index == 0:
                data.update(stats_data)
            else:
                for key, value in stats_data.items():
                    modified_key = f"{key}-{index+1}"  # 例如 key-2, key-3...
                    data[modified_key] = value
                    # 这边改了也没什么效果，还是顺其自然
                    # if folder == r"runs/track\750" or folder == r"runs/track\750-2":
                    #     # print("清空")
                    #     data[modified_key]["orbital_rev"] = 0
                    # if index == 1 and len_folders > 2:
                    #     data[modified_key]["orbital_rev"] = 0

    return data


# 设置基础路径
base_path = "runs/track"
folders = get_all_folders(base_path)

# 加载 Excel 中的真实数据
true_data = load_excel_true_data()

# 过滤出 '-2' 版本的文件夹并匹配主文件夹
# 初始化字典，按 "头部名称" 归类
folder_groups = defaultdict(list)

# 遍历所有文件夹，将具有相同前缀的分组
for folder__ in folders:
    base_name = folder__.split("-")[0]  # 获取 `-` 之前的前缀
    folder_groups[base_name].append(folder__)


# 初始化总体数据存储
exp_indices = []  # 存储实验序号
exp_avg_abs_rot = []  # 存储每次实验的平均绝对自转
exp_avg_orb_rev = []  # 存储每次实验的平均公转

# 设置画布
num_folders = len(folder_groups)
fig, axes = plt.subplots(
    num_folders + 1, 2, figsize=(12, 6 * (num_folders + 1)), constrained_layout=True
)  # 多个子图

all_heights = []
for folder_ in folders:
    stats_file_path = os.path.join(folder_, "initial_result", "all_stats.json")
    if not os.path.exists(stats_file_path):
        continue

    with open(stats_file_path, "r") as stats_file:
        all_stats = json.load(stats_file)

    for key, value in all_stats.items():
        closest_point = value.get("closest_point", {})
        box = closest_point.get("Box", [0, 0, 0, 0])
        height = None
        if value.get("height") is None:
            height = (box[1] + box[3]) / 2 / 147 + 42 / 147  # 高度计算公式
        else:
            height = value.get("height")
        inner_diameter = value.get("inner_diameter", 0)
        all_heights.append(height / inner_diameter * 147)

# 获取全局的最小和最大高度
min_height = min(all_heights)
max_height = max(all_heights)
# 遍历所有子目录
print(len(folder_groups), folder_groups)

for i, (base_name, folder_list) in enumerate(folder_groups.items()):
    merged_stats = merge_stats(*folder_list)  # 传入所有相关文件夹进行合并

    # 初始化当前文件夹的数据存储
    heights_abs_rot = []
    abs_rotations = []
    heights_orb_rev = []
    orbital_revs = []

    # 解析数据
    for key, value in merged_stats.items():
        try:
            abs_rotation = value.get("abs_rotation", 0)
            orbital_rev = value.get("orbital_rev", 0)
            closest_point = value.get("closest_point", {})

            # 计算高度
            box = closest_point.get("Box", [0, 0, 0, 0])
            height = None
            if value.get("height") is None:
                height = (box[1] + box[3]) / 2 / 147 + 42 / 147  # 高度计算公式
            else:
                height = value.get("height")
            inner_diameter = value.get("inner_diameter", 0)
            # 存储数据
            if abs_rotation > 0:
                heights_abs_rot.append(height / inner_diameter * 147)  # h/D
                abs_rotations.append(abs_rotation)

            if orbital_rev > 0:
                heights_orb_rev.append(height / inner_diameter * 147)
                orbital_revs.append(orbital_rev)

        except Exception as e:
            print(f"处理 {key} 时出错: {e}")
    data = pd.DataFrame(
        {
            "height": heights_orb_rev,
            "orb_rev": orbital_revs,
        }
    )

    # 使用核密度估计（KDE）来计算密度
    # kde = KernelDensity(kernel="gaussian", bandwidth=7).fit(
    #     np.array(data["height"]).reshape(-1, 1)
    # )
    # log_density = kde.score_samples(np.array(data["height"]).reshape(-1, 1))
    # density = np.exp(log_density)  # 转换为线性密度

    # # 计算采样权重：密度的倒数
    # weights = 1 / density
    # normalized_weights = weights / weights.sum()  # 标准化为概率分布

    # # 根据权重随机采样
    # num_samples = 150  # 采样的点数
    # sampled_indices = np.random.choice(
    #     data.index, size=num_samples, replace=False, p=normalized_weights
    # )
    # sampled_data = data.loc[sampled_indices]
    # num_bins = 50  # 设定高度的分箱数
    # data["bin"] = pd.qcut(data["height"], num_bins, duplicates="drop")  # 按分位数分箱
    # sampled_data = (
    #     data.groupby("bin")
    #     .apply(lambda x: x.sample(n=1, replace=True))
    #     .reset_index(drop=True)
    # )
    # print("sampled_data:", sampled_data)
    avg_abs_rotation = np.mean(abs_rotations) if abs_rotations else 0
    avg_orbital_rev = np.mean(orbital_revs) if orbital_revs else 0
    # avg_orbital_rev = np.mean(sampled_data["orb_rev"]) if not sampled_data.empty else 0
    folder_name = os.path.basename(base_name)  # 获取文件夹名称
    # 存储实验结果
    exp_indices.append(folder_name)
    exp_avg_abs_rot.append(avg_abs_rotation)
    exp_avg_orb_rev.append(avg_orbital_rev)

    # 绘制当前文件夹的图
    axes[i, 0].scatter(
        heights_abs_rot,
        abs_rotations,
        alpha=0.7,
        label=f"{os.path.basename(base_name)}",
    )
    
    # 添加对应流速的TRUE_rotation数据叠加
    folder_name = os.path.basename(base_name)  # 获取文件夹名称，如 '550', '750' 等
    
    # 过滤出匹配当前文件夹流速的TRUE数据
    matching_true_data = true_data[true_data['flow_velocity'].str.contains(folder_name, na=False)]
    
    if not matching_true_data.empty:
        # 合并所有匹配的流速数据，统一显示为一个标签
        all_h_d = []
        all_true_rotation = []
        
        for flow_vel, flow_data in matching_true_data.groupby('flow_velocity'):
            all_h_d.extend(flow_data['H/D'].tolist())
            all_true_rotation.extend(flow_data['TRUE_rotation'].tolist())
        
        # 统一显示为一个标签
        axes[i, 0].scatter(
            all_h_d,
            all_true_rotation,
            alpha=0.8,
            marker='x',
            s=50,
            label=f"TRUE {folder_name}",
        )
    
    axes[i, 0].set_xlabel(r"$h/D$")
    axes[i, 0].set_ylabel("Rotation (rad/s)")
    axes[i, 0].set_xlim(min_height, max_height)  # 设定相同的 x 轴范围
    if i == 0:
        axes[i, 0].set_title("Rotation vs Height", fontsize=22)
    # axes[i, 0].grid()
    axes[i, 0].legend(loc="upper right")
    x_trend = np.linspace(min_height, max_height, 100)
    # 计算并绘制趋势线（线性拟合）
    if len(heights_abs_rot) > 1:
        poly_coeffs = np.polyfit(heights_abs_rot, abs_rotations, 2)  # 一阶线性拟合
        trend_line = np.poly1d(poly_coeffs)
        axes[i, 0].plot(
            x_trend, trend_line(x_trend), color="blue", linestyle="--", label="Trend"
        )

    axes[i, 1].scatter(
        heights_orb_rev,
        orbital_revs,
        alpha=0.7,
        color="orange",
        label=f"{os.path.basename(base_name)}",
    )
    
    # 添加对应流速的TRUE_revolution数据叠加
    if not matching_true_data.empty:
        # 合并所有匹配的流速数据，统一显示为一个标签
        all_h_d_rev = []
        all_true_revolution = []
        
        for flow_vel, flow_data in matching_true_data.groupby('flow_velocity'):
            all_h_d_rev.extend(flow_data['H/D'].tolist())
            all_true_revolution.extend(flow_data['TRUE_revolution'].tolist())
        
        # 统一显示为一个标签
        axes[i, 1].scatter(
            all_h_d_rev,
            all_true_revolution,
            alpha=0.8,
            marker='x',
            s=50,
            color='red',
            label=f"TRUE {folder_name}",
        )
    
    axes[i, 1].set_xlabel(r"$h/D$")
    axes[i, 1].set_ylabel("Revolution (rad/s)")
    if i == 0:
        axes[i, 1].set_title("Revolution vs Height", fontsize=22)
    # axes[i, 1].grid()
    axes[i, 1].legend(loc="upper right")
    # 计算并绘制趋势线（线性拟合）
    if len(heights_orb_rev) > 1:
        poly_coeffs = np.polyfit(heights_orb_rev, orbital_revs, 2)  # 一阶线性拟合
        trend_line = np.poly1d(poly_coeffs)
        axes[i, 1].plot(
            x_trend, trend_line(x_trend), color="red", linestyle="--", label="Trend"
        )


# 绘制实验均值趋势图（最后一行）
# axes[-1, 0].plot(
#     exp_indices,
#     exp_avg_abs_rot,
#     alpha=0.7,
#     color="blue",
#     label="Average Rotation",
#     marker="o",
#     linestyle="-",
# )
# axes[-1, 0].set_xlabel("Inlet Flow Rate (L/h)")
# axes[-1, 0].set_ylabel("Avg Rotation (rad/s)")
# axes[-1, 0].set_title("Inlet Flow Rate vs Absolute Rotation")
# # axes[-1, 0].grid()
# axes[-1, 0].legend()

# axes[-1, 1].plot(
#     exp_indices,
#     exp_avg_orb_rev,
#     alpha=0.7,
#     color="red",
#     label="Average Orbital Revolution",
#     marker="o",
#     linestyle="-",
# )
# axes[-1, 1].set_xlabel("Inlet Flow Rate (L/h)")
# axes[-1, 1].set_ylabel("Avg Orbital Revolution (rad/s)")
# axes[-1, 1].set_title("Inlet Flow Rate vs Orbital Revolution")
# # axes[-1, 1].grid()
# axes[-1, 1].legend()


# ==== 单独绘制平均趋势图 ====
fig2, axes2 = plt.subplots(1, 2, figsize=(12, 6), constrained_layout=True)

# 左图：Absolute Rotation vs Inlet Flow Rate（原右图）
axes2[0].plot(
    exp_indices,
    exp_avg_abs_rot,
    alpha=0.7,
    color="blue",
    label="Average Rotation",
    marker="o",
    linestyle="-",
)
axes2[0].set_xlabel("Inlet Flow Rate (L/h)")
axes2[0].set_ylabel("Avg Rotation (rad/s)")
axes2[0].set_title("Inlet Flow Rate vs Absolute Rotation", fontsize=18)
axes2[0].legend(loc="upper left")

# 右图：Orbital Revolution vs Inlet Flow Rate（原左图）
axes2[1].plot(
    exp_indices,
    exp_avg_orb_rev,
    alpha=0.7,
    color="red",
    label="Average Orbital Revolution",
    marker="o",
    linestyle="-",
)
axes2[1].set_xlabel("Inlet Flow Rate (L/h)")
axes2[1].set_ylabel("Avg Orbital Revolution (rad/s)")
axes2[1].set_title("Inlet Flow Rate vs Orbital Revolution", fontsize=18)
axes2[1].legend(loc="upper left")

plt.show()
