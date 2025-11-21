# 550 是D:\shnu-graduation\alldata\all\20180117-hfq-y\Y1-550\相机No.1_C001H001S0001 
# 750 是 D:\shnu-graduation\alldata\all\20180117-hfq-y\Y1-750\No.1_C001H001S0002 
# 850 是 D:\shnu-graduation\alldata\all\20180117-hfq-y\Y1-850\相机No.1_C001H001S0001
# 450  是 D:\shnu-graduation\alldata\all\20180117-hfq-y\y1-450\相机No.1_C001H001S0002
# 650 是 D:\shnu-graduation\alldata\all\20180117-hfq-y\Y1-650\相机No.1_C001H001S0002

# h/d = 1.22的地方是拐角  那么 h = 1.22 * d 
import json
import os
import sys
from collections import defaultdict

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import AutoMinorLocator
from process_utils import get_all_folders

# 检查是否需要非交互式模式（用于批处理）
BASE_PATH_INITIAL = "runs/eff1_new"
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # 上一级目录
plot_output_dir = os.path.join(project_root, "plots-eff1-new")
if len(sys.argv) > 1 and sys.argv[1] == "--save":
    matplotlib.use('Agg')  # 使用非交互式后端
    SAVE_MODE = True
    if len(sys.argv) > 2:
        BASE_PATH = os.path.normpath(sys.argv[2])  # 规范化路径
    else:
        BASE_PATH = BASE_PATH_INITIAL
else:
    SAVE_MODE = False
    BASE_PATH = BASE_PATH_INITIAL

print(f"路径:{BASE_PATH}")
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 16  # 设置全局字体大小
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
base_path = BASE_PATH
folders = get_all_folders(base_path)

# 过滤：只保留以流量开头的文件夹（450, 550, 650, 750, 850）
valid_flow_rates = ['450', '550', '650', '750', '850']
folders = [
    f for f in folders 
    if any(os.path.basename(f).startswith(flow) for flow in valid_flow_rates)
]
print(f"过滤后的文件夹数量: {len(folders)}")
print(f"文件夹列表: {[os.path.basename(f) for f in folders]}")

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
    num_folders, 1, figsize=(8, 3.3 * num_folders),
    gridspec_kw={'hspace': 0.25}
)  # 多个子图,减小子图间距


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
        # 1
        # all_heights.append(height / inner_diameter * 147)
        all_heights.append(height)

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
                # 2
                # heights_abs_rot.append(height / inner_diameter * 147)  # h/D
                heights_abs_rot.append(height)
                abs_rotations.append(abs_rotation)

            if orbital_rev > 0:
                # 3
                # heights_orb_rev.append(height / inner_diameter * 147)
                heights_orb_rev.append(height)
                orbital_revs.append(orbital_rev)

        except Exception as e:
            print(f"处理 {key} 时出错: {e}")
    data = pd.DataFrame(
        {
            "height": heights_orb_rev,
            "orb_rev": orbital_revs,
        }
    )
    # print("sampled_data:", sampled_data)
    avg_abs_rotation = np.mean(abs_rotations) if abs_rotations else 0
    avg_orbital_rev = np.mean(orbital_revs) if orbital_revs else 0
    # avg_orbital_rev = np.mean(sampled_data["orb_rev"]) if not sampled_data.empty else 0
    folder_name = os.path.basename(base_name)  # 获取文件夹名称
    # 存储实验结果
    exp_indices.append(folder_name)
    exp_avg_abs_rot.append(avg_abs_rotation)
    exp_avg_orb_rev.append(avg_orbital_rev)

    # 绘制当前文件夹的图 - 使用单一Y轴
    ax = axes[i]

    # 获取数据的极值
    y1_min, y1_max = min(abs_rotations), max(abs_rotations)
    y2_min, y2_max = min(orbital_revs), max(orbital_revs)

    # 合并所有数据以确定整体范围
    all_speeds = abs_rotations + orbital_revs
    y_min, y_max = min(all_speeds), max(all_speeds)

    # 绘制 Rotation 数据（蓝色）
    scatter1 = ax.scatter(
        heights_abs_rot,
        abs_rotations,
        alpha=0.7,
        color="blue",
    )

    # 绘制 Revolution 数据（橙色）
    scatter2 = ax.scatter(
        heights_orb_rev,
        orbital_revs,
        alpha=0.7,
        color="orange",
    )

    ax.set_xlabel(r"$h$ (cm)")
    ax.set_ylabel("Speed (rad/s)")
    ax.set_xlim(min_height, max_height)

    # 计算断裂位置：在公转最大值和自转最小值之间
    revolution_max = max(orbital_revs)
    rotation_min = min(abs_rotations)

    # 设置Y轴范围为0到3000
    ax.set_ylim(0, 3000)

    # 在公转最大值和自转最小值之间添加断裂标记
    if rotation_min > revolution_max:  # 确保有间隙
        # 计算断裂标记的中间位置
        break_center = (revolution_max + rotation_min) / 2

        # 计算断裂位置在Y轴上的相对位置（0-1之间）
        y_range = 3000
        break_pos = break_center / y_range

        # 添加断裂标记（斜线）
        d = 0.015  # 断裂标记的大小
        kwargs = dict(transform=ax.transAxes, color='k', clip_on=False, linewidth=1.5)

        # 在Y轴左侧绘制断裂标记（两条平行斜线）
        ax.plot((-d, +d), (break_pos - d, break_pos + d), **kwargs)
        ax.plot((-d, +d), (break_pos + 0.015 - d, break_pos + 0.015 + d), **kwargs)

    # 计算趋势线的x值
    x_trend = np.linspace(min_height, max_height, 100)

    # 计算并绘制 Rotation 趋势线（蓝色虚线）
    if len(heights_abs_rot) > 1:
        poly_coeffs = np.polyfit(heights_abs_rot, abs_rotations, 2)
        trend_line = np.poly1d(poly_coeffs)
        line1 = ax.plot(
            x_trend, trend_line(x_trend), color="blue", linestyle="--", alpha=0.5
        )

    # 计算并绘制 Revolution 趋势线（橙色虚线）
    if len(heights_orb_rev) > 1:
        poly_coeffs = np.polyfit(heights_orb_rev, orbital_revs, 2)
        trend_line = np.poly1d(poly_coeffs)
        line2 = ax.plot(
            x_trend, trend_line(x_trend), color="orange", linestyle="--", alpha=0.5
        )

    # 添加流量标注
    flow_text = f"{os.path.basename(base_name)} L/h"
    ax.text(0.98, 0.98, flow_text, transform=ax.transAxes,
             verticalalignment='top', horizontalalignment='right',
             fontsize=14)

    # 添加子图标题 (a), (b), (c), (d), (e)
    subplot_labels = ['(a)', '(b)', '(c)', '(d)', '(e)']
    if i < len(subplot_labels):
        ax.set_title(subplot_labels[i], loc='left', x=-0.13,y=0.87)

    # 设置刻度
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.tick_params(which='minor', direction='in')
    ax.tick_params(which='major', direction='in')
    
    # 确保Y轴刻度显示到3000
    ax.set_yticks([0, 1000, 2000, 3000])


# ==== 单独绘制平均趋势图 - 使用单一Y轴 ====
fig2, ax_summary = plt.subplots(1, 1, figsize=(7, 4.5))

# Average Rotation（蓝色）
line1 = ax_summary.plot(
    exp_indices,
    exp_avg_abs_rot,
    alpha=0.7,
    color="blue",
    marker="o",
    linestyle="-",
    linewidth=2,
)

# Average Revolution（橙色）
line2 = ax_summary.plot(
    exp_indices,
    exp_avg_orb_rev,
    alpha=0.7,
    color="orange",
    marker="s",
    linestyle="-",
    linewidth=2,
)

ax_summary.set_xlabel("Inlet Flow Rate (L/h)")
ax_summary.set_ylabel("Speed (rad/s)")

# 固定坐标轴范围，与第一张图保持一致
ax_summary.set_ylim(0, 3000)
ax_summary.set_yticks([0, 1000, 2000, 3000])

# 设置刻度
ax_summary.xaxis.set_minor_locator(AutoMinorLocator(2))
ax_summary.yaxis.set_minor_locator(AutoMinorLocator(2))
ax_summary.tick_params(which='minor', direction='in')
ax_summary.tick_params(which='major', direction='in')

# 根据模式决定是显示还是保存图表
if SAVE_MODE:
    # 保存图表到项目根目录（app.py 所在目录）
    # 获取当前脚本所在目录的父目录（即项目根目录）
    os.makedirs(plot_output_dir, exist_ok=True)

    fig.savefig(os.path.join(plot_output_dir, "particle_analysis_detailed.png"), dpi=300, bbox_inches='tight')
    fig2.savefig(os.path.join(plot_output_dir, "particle_analysis_summary.png"), dpi=300, bbox_inches='tight')

    print(f"图表已保存到: {plot_output_dir}")
    print("  - particle_analysis_detailed.png (详细分析)")
    print("  - particle_analysis_summary.png (汇总)")
    
    plt.close('all')  # 关闭所有图表释放内存
else:
    # 显示图表
    plt.show()
