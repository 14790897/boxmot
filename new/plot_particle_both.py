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
plot_output_dir = os.path.join(project_root, "plots-eff1-new-both")
if len(sys.argv) > 1 and sys.argv[1] == "--save":
    matplotlib.use("Agg")  # 使用非交互式后端
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

    return data


# 设置基础路径
base_path = BASE_PATH
folders = get_all_folders(base_path)

# 过滤：只保留以流量开头的文件夹（450, 550, 650, 750, 850）
valid_flow_rates = ["450", "550", "650", "750", "850"]
folders = [
    f
    for f in folders
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
exp_sem_abs_rot = []  # 存储每次实验的自转标准误差
exp_sem_orb_rev = []  # 存储每次实验的公转标准误差

# 用于存储所有详细数据以导出Excel
all_excel_data = []

# 设置画布 - 修改为一行两张图的布局
num_folders = len(folder_groups)
num_rows = (num_folders + 1) // 2  # 计算需要的行数
fig, axes = plt.subplots(
    num_rows, 2, figsize=(12, 3.5 * num_rows), gridspec_kw={"hspace": 0.2, "wspace": 0.2}
)  # 一行两张图

# 如果只有一行，确保axes是二维数组
if num_rows == 1:
    axes = axes.reshape(1, -1)


all_heights = []
for folder_ in folders:
    stats_file_path = os.path.join(folder_, "initial_result", "all_stats.json")
    if not os.path.exists(stats_file_path):
        continue

    with open(stats_file_path, "r") as stats_file:
        all_stats = json.load(stats_file)

    for key, value in all_stats.items():
        # 只统计同时有自转和公转的粒子
        abs_rotation = value.get("abs_rotation", 0)
        orbital_rev = value.get("orbital_rev", 0)

        if abs_rotation > 0 and orbital_rev > 0:
            closest_point = value.get("closest_point", {})
            box = closest_point.get("Box", [0, 0, 0, 0])
            height = None
            if value.get("height") is None:
                height = (box[1] + box[3]) / 2 / 147 + 42 / 147  # 高度计算公式
            else:
                height = value.get("height")
            all_heights.append(height)

# 获取全局的最小和最大高度
min_height = min(all_heights) if all_heights else 0
max_height = max(all_heights) if all_heights else 1

# 遍历所有子目录
print(len(folder_groups), folder_groups)

for i, (base_name, folder_list) in enumerate(folder_groups.items()):
    # 计算子图位置
    row = i // 2
    col = i % 2
    
    merged_stats = merge_stats(*folder_list)  # 传入所有相关文件夹进行合并

    # 初始化当前文件夹的数据存储
    heights_both = []  # 同时有自转和公转的粒子的高度
    abs_rotations_both = []  # 对应的自转速度
    orbital_revs_both = []  # 对应的公转速度
    is_high_speed = []  # 标记是否为高速颗粒

    # 解析数据 - 只保留同时有自转和公转的粒子
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

            # 只存储同时有自转和公转的粒子数据
            if abs_rotation > 0 and orbital_rev > 0:
                # 计算旋转半径比值来判断是否为高速颗粒
                inner_diameter = value.get("inner_diameter", 0)
                margin = value.get("margin", 0)
                
                # radius = (inner_diameter / 2 - margin * 147 / 101)
                # dz/2 = inner_diameter / 2
                # ratio = radius / (dz/2) = (inner_diameter / 2 - margin * 147 / 101) / (inner_diameter / 2)
                if inner_diameter > 0:
                    radius = inner_diameter / 2 - margin * 147 / 101
                    dz_half = inner_diameter / 2
                    ratio = radius / dz_half
                    high_speed = ratio > 0.9
                else:
                    high_speed = False
                
                heights_both.append(height)
                abs_rotations_both.append(abs_rotation)
                orbital_revs_both.append(orbital_rev)
                is_high_speed.append(high_speed)

                # 添加到Excel数据列表，包含所有相关数据
                all_excel_data.append({
                    'Flow_Rate_L_h': os.path.basename(base_name),
                    'Particle_ID': key,
                    'Height_cm': height,
                    'Inner_Diameter_cm': value.get("inner_diameter", 0)/147,
                    'Rotation_rad_s': abs_rotation,
                    'Revolution_rad_s': orbital_rev,
                    'Relative_Rotation_rad_s': value.get("rel_rotation", 0),
                    # 'Start_Frame_Revolution': value.get("start_frame_revolution", 0),
                    # 'End_Frame_Revolution': value.get("end_frame_revolution", 0),
                    'Total_Frames_Revolution': value.get("total_frames_revolution", 0),
                    # 'Start_Frame_Rotation': value.get("start_frame_rotation", 0),
                    # 'End_Frame_Rotation': value.get("end_frame_rotation", 0),
                    'Total_Frames_Rotation': value.get("total_frames_rotation", 0),
                    'Category_Changes': value.get("changes", 0),
                    'D1': value.get("d1_with_range_revolution", 0),
                    'D2': value.get("d2_with_range_revolution", 0),
                    'Margin': value.get("margin", 0),
                    "Inner_Radius_cm": value.get("inner_diameter", 0)/147/2,
                    "Revolution_Radius_cm": radius/147,
                    "radius / dz_half": ratio,
                    "High_Speed": high_speed,
                    
                    
                    # 'Closest_Point_Center_X': closest_point.get("Center", [0, 0])[0] if closest_point else 0,
                    # 'Closest_Point_Center_Y': closest_point.get("Center", [0, 0])[1] if closest_point else 0,
                    # 'Closest_Point_Box': str(closest_point.get("Box", [])) if closest_point else "",
                    # 'Not_Use': value.get("not_use", False),
                    # 'Must_Not_Use': value.get("must_not_use", False),
                    # 'Reason': value.get("reason", ""),
                    # 'Timestamp': value.get("timestamp", "")
                })

        except Exception as e:
            print(f"处理 {key} 时出错: {e}")

    avg_abs_rotation = np.mean(abs_rotations_both) if abs_rotations_both else 0
    avg_orbital_rev = np.mean(orbital_revs_both) if orbital_revs_both else 0
    
    # 计算标准误差 (SEM = std / sqrt(n))
    sem_abs_rotation = np.std(abs_rotations_both, ddof=1) / np.sqrt(len(abs_rotations_both)) if len(abs_rotations_both) > 1 else 0
    sem_orbital_rev = np.std(orbital_revs_both, ddof=1) / np.sqrt(len(orbital_revs_both)) if len(orbital_revs_both) > 1 else 0
    
    folder_name = os.path.basename(base_name)  # 获取文件夹名称

    # 存储实验结果
    exp_indices.append(folder_name)
    exp_avg_abs_rot.append(avg_abs_rotation)
    exp_avg_orb_rev.append(avg_orbital_rev)
    exp_sem_abs_rot.append(sem_abs_rotation)
    exp_sem_orb_rev.append(sem_orbital_rev)

    # 绘制当前文件夹的图 - 使用单一Y轴
    ax = axes[row, col]

    if abs_rotations_both and orbital_revs_both:
        # 合并所有数据以确定整体范围
        all_speeds = abs_rotations_both + orbital_revs_both
        y_min, y_max = min(all_speeds), max(all_speeds)

        # 分离高速和低速颗粒数据
        heights_rot_high = [h for h, hs in zip(heights_both, is_high_speed) if hs]
        abs_rot_high = [r for r, hs in zip(abs_rotations_both, is_high_speed) if hs]
        heights_rot_low = [h for h, hs in zip(heights_both, is_high_speed) if not hs]
        abs_rot_low = [r for r, hs in zip(abs_rotations_both, is_high_speed) if not hs]
        
        heights_rev_high = [h for h, hs in zip(heights_both, is_high_speed) if hs]
        orb_rev_high = [r for r, hs in zip(orbital_revs_both, is_high_speed) if hs]
        heights_rev_low = [h for h, hs in zip(heights_both, is_high_speed) if not hs]
        orb_rev_low = [r for r, hs in zip(orbital_revs_both, is_high_speed) if not hs]

        # 绘制 Rotation 数据 - 高速颗粒（深蓝色圆形）
        if heights_rot_high:
            scatter1_high = ax.scatter(
                heights_rot_high,
                abs_rot_high,
                alpha=0.7,
                color="darkblue",
                marker="o",
                s=30,
                label="Rotation (High)" if i == 0 else None,
            )
        
        # 绘制 Rotation 数据 - 低速颗粒（浅蓝色圆形）
        if heights_rot_low:
            scatter1_low = ax.scatter(
                heights_rot_low,
                abs_rot_low,
                alpha=0.7,
                color="lightblue",
                marker="o",
                s=30,
                label="Rotation (Low)" if i == 0 else None,
            )

        # 绘制 Revolution 数据 - 高速颗粒（深橙色方形）
        if heights_rev_high:
            scatter2_high = ax.scatter(
                heights_rev_high,
                orb_rev_high,
                alpha=0.7,
                color="red",
                marker="s",
                s=30,
                label="Revolution (High)" if i == 0 else None,
            )
        
        # 绘制 Revolution 数据 - 低速颗粒（浅橙色方形）
        if heights_rev_low:
            scatter2_low = ax.scatter(
                heights_rev_low,
                orb_rev_low,
                alpha=0.7,
                color="gold",
                marker="s",
                s=30,
                label="Revolution (Low)" if i == 0 else None,
            )

        ax.set_xlabel(r"h (cm)", labelpad=-5)
        ax.set_ylabel("Speed (rad/s)")
        ax.set_xlim(min_height, max_height)

        # 计算断裂位置：在公转最大值和自转最小值之间
        revolution_max = max(orbital_revs_both)
        rotation_min = min(abs_rotations_both)

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
            kwargs = dict(transform=ax.transAxes, color="k", clip_on=False, linewidth=1.5)

            # 在Y轴左侧绘制断裂标记（两条平行斜线）
            ax.plot((-d, +d), (break_pos - d, break_pos + d), **kwargs)
            ax.plot((-d, +d), (break_pos + 0.015 - d, break_pos + 0.015 + d), **kwargs)

        # 计算趋势线的x值
        x_trend = np.linspace(min_height, max_height, 100)

        # 计算并绘制 Rotation 趋势线（深蓝色虚线）- 使用所有rotation数据
        if len(heights_both) > 1:
            poly_coeffs = np.polyfit(heights_both, abs_rotations_both, 2)
            trend_line = np.poly1d(poly_coeffs)
            line1 = ax.plot(
                x_trend, trend_line(x_trend), color="darkblue", linestyle="--", alpha=0.5
            )

        # 计算并绘制 Revolution 趋势线（红色虚线）- 使用所有revolution数据
        if len(heights_both) > 1:
            poly_coeffs = np.polyfit(heights_both, orbital_revs_both, 2)
            trend_line = np.poly1d(poly_coeffs)
            line2 = ax.plot(
                x_trend, trend_line(x_trend), color="red", linestyle="--", alpha=0.5
            )

        # 添加流量标注
        flow_text = f"Qi={os.path.basename(base_name)} L/h"
        ax.text(
            0.98,
            0.98,
            flow_text,
            transform=ax.transAxes,
            verticalalignment="top",
            horizontalalignment="right",
            fontsize=14,
        )

        # 添加子图标题 (a), (b), (c), (d), (e)
        subplot_labels = ["(a)", "(b)", "(c)", "(d)", "(e)"]
        if i < len(subplot_labels):
            ax.set_title(subplot_labels[i], loc="left", x=-0.19, y=0.9)

        # 只在第一个子图显示图例
        if i == 0:
            ax.legend(loc="upper left", fontsize=12, framealpha=0.9, frameon=False)

        # 设置刻度
        ax.xaxis.set_minor_locator(AutoMinorLocator(5))
        ax.yaxis.set_minor_locator(AutoMinorLocator(2))
        ax.tick_params(which="minor", direction="in")
        ax.tick_params(which="major", direction="in")

        # 确保Y轴刻度显示到3000，间隔500
        ax.set_yticks([0, 500, 1000, 1500, 2000, 2500, 3000])

# 如果有空余的子图位置，隐藏它们
for j in range(num_folders, num_rows * 2):
    row = j // 2
    col = j % 2
    axes[row, col].set_visible(False)

# 在最后一个位置绘制平均值图（如果有空余位置）
if num_folders < num_rows * 2:
    # 使用最后一个位置绘制平均值图
    last_row = (num_rows * 2 - 1) // 2
    last_col = (num_rows * 2 - 1) % 2
    ax_summary = axes[last_row, last_col]
    ax_summary.set_visible(True)
else:
    # 如果没有空余位置，创建新图
    fig2, ax_summary = plt.subplots(1, 1, figsize=(3.5, 2.5))
    create_separate_summary = True

# 如果在原图中绘制平均值
if num_folders < num_rows * 2:

    # Average Rotation（蓝色圆形）with error bars
    ax_summary.errorbar(
        exp_indices,
        exp_avg_abs_rot,
        yerr=exp_sem_abs_rot,
        color="blue",
        marker="o",
        linestyle="-",
        linewidth=2,
        markersize=1,
        capsize=3,
        capthick=3,
        elinewidth=1,
        alpha=0.7,
        label="Rotation"
    )

    # Average Revolution（橙色方形）with error bars
    ax_summary.errorbar(
        exp_indices,
        exp_avg_orb_rev,
        yerr=exp_sem_orb_rev,
        color="orange",
        marker="s",
        linestyle="-",
        linewidth=2,
        markersize=1,
        capsize=3,
        capthick=3,
        elinewidth=1,
        alpha=0.7,
        label="Revolution"
    )

    ax_summary.set_xlabel("Inlet Flow Rate (L/h)")
    ax_summary.set_ylabel("Speed (rad/s)")

    # 固定坐标轴范围，与第一张图保持一致
    ax_summary.set_ylim(0, 3000)
    ax_summary.set_yticks([0, 500, 1000, 1500, 2000, 2500, 3000])

    # 添加子图标题
    ax_summary.set_title("(f)", loc="left", x=-0.19, y=0.9)

    # 设置刻度
    ax_summary.xaxis.set_minor_locator(AutoMinorLocator(5))
    ax_summary.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax_summary.tick_params(which="minor", direction="in")
    ax_summary.tick_params(which="major", direction="in")
else:
    # 单独创建平均值图的情况
    # Average Rotation（蓝色圆形）with error bars
    ax_summary.errorbar(
        exp_indices,
        exp_avg_abs_rot,
        yerr=exp_sem_abs_rot,
        color="blue",
        marker="o",
        linestyle="-",
        linewidth=2,
        markersize=5,
        capsize=3,
        capthick=3,
        elinewidth=1,
        alpha=0.7,
        label="Rotation"
    )

    # Average Revolution（橙色方形）with error bars
    ax_summary.errorbar(
        exp_indices,
        exp_avg_orb_rev,
        yerr=exp_sem_orb_rev,
        color="orange",
        marker="s",
        linestyle="-",
        linewidth=2,
        markersize=5,
        capsize=3,
        capthick=3,
        elinewidth=1,
        alpha=0.7,
        label="Revolution"
    )

    ax_summary.set_xlabel("Inlet Flow Rate (L/h)")
    ax_summary.set_ylabel("Speed (rad/s)")

    # 固定坐标轴范围，与第一张图保持一致
    ax_summary.set_ylim(0, 3000)
    ax_summary.set_yticks([0, 500, 1000, 1500, 2000, 2500, 3000])

    # 设置刻度
    ax_summary.xaxis.set_minor_locator(AutoMinorLocator(5))
    ax_summary.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax_summary.tick_params(which="minor", direction="in")
    ax_summary.tick_params(which="major", direction="in")

# ==== 导出数据到Excel ====
# 创建DataFrame
df_detailed = pd.DataFrame(all_excel_data)

# 创建汇总数据的DataFrame
df_summary = pd.DataFrame({
    'Flow_Rate_L_h': exp_indices,
    'Avg_Rotation_rad_s': exp_avg_abs_rot,
    'Avg_Revolution_rad_s': exp_avg_orb_rev
})

# 导出到Excel
os.makedirs(plot_output_dir, exist_ok=True)
excel_path = os.path.join(plot_output_dir, "particle_both_motion_data.xlsx")

with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    # 详细数据sheet
    df_detailed.to_excel(writer, sheet_name='Detailed_Data', index=False)
    # 汇总数据sheet
    df_summary.to_excel(writer, sheet_name='Summary_Data', index=False)

print(f"数据已导出到Excel: {excel_path}")
print(f"  - 总共 {len(df_detailed)} 个同时具有自转和公转的粒子")
print("  - Detailed_Data sheet: 每个粒子的详细数据")
print("  - Summary_Data sheet: 每个流速的平均值汇总")

# 根据模式决定是显示还是保存图表
if SAVE_MODE:
    # 保存图表到项目根目录（app.py 所在目录）
    # 获取当前脚本所在目录的父目录（即项目根目录）
    os.makedirs(plot_output_dir, exist_ok=True)

    fig.savefig(
        os.path.join(plot_output_dir, "particle_analysis_combined.png"),
        dpi=300,
        bbox_inches="tight",
    )
    
    # 如果有单独的汇总图，也保存它
    if 'fig2' in locals():
        fig2.savefig(
            os.path.join(plot_output_dir, "particle_analysis_summary.png"),
            dpi=300,
            bbox_inches="tight",
        )

    print(f"图表已保存到: {plot_output_dir}")
    if num_folders < num_rows * 2:
        print("  - particle_analysis_combined.png (包含平均值的组合图)")
    else:
        print("  - particle_analysis_combined.png (详细分析)")
        print("  - particle_analysis_summary.png (汇总)")

    plt.close("all")  # 关闭所有图表释放内存
else:
    # 显示图表
    plt.show()
