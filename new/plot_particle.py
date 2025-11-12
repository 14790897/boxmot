# 550 是D:\shnu-graduation\alldata\all\20180117-hfq-y\Y1-550\相机No.1_C001H001S0001 
# 750 是 D:\shnu-graduation\alldata\all\20180117-hfq-y\Y1-750\No.1_C001H001S0002 
# 850 是 D:\shnu-graduation\alldata\all\20180117-hfq-y\Y1-850\相机No.1_C001H001S0001
# 450  是 D:\shnu-graduation\alldata\all\20180117-hfq-y\y1-450\相机No.1_C001H001S0002
# 650 是 D:\shnu-graduation\alldata\all\20180117-hfq-y\Y1-650\相机No.1_C001H001S0002


import json
import os
import sys
from collections import defaultdict

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from process_utils import get_all_folders

# 检查是否需要非交互式模式（用于批处理）
if len(sys.argv) > 1 and sys.argv[1] == "--save":
    matplotlib.use('Agg')  # 使用非交互式后端
    SAVE_MODE = True
    if len(sys.argv) > 2:
        BASE_PATH = os.path.normpath(sys.argv[2])  # 规范化路径
    else:
        BASE_PATH = "runs/track"
else:
    SAVE_MODE = False
    BASE_PATH = "runs/track"

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
    num_folders, 2, figsize=(12, 6 * num_folders), constrained_layout=True
)  # 多个子图,每个子图六英寸高

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
        label=f"Inlet Flow Rate: {os.path.basename(base_name)} L/h",
    )
    axes[i, 0].set_xlabel(r"$h/D$")
    axes[i, 0].set_ylabel("Rotation (rad/s)")
    axes[i, 0].set_xlim(min_height, max_height)  # 设定相同的 x 轴范围
    if i == 0:
        axes[i, 0].set_title("Rotation vs Height", fontsize=22)
    # axes[i, 0].grid()
    axes[i, 0].legend(loc="upper right", handlelength=0, handletextpad=0, markerscale=0)
    x_trend = np.linspace(min_height, max_height, 100)
    # 计算并绘制趋势线（线性拟合）
    if len(heights_abs_rot) > 1:
        poly_coeffs = np.polyfit(heights_abs_rot, abs_rotations, 2)  # 一阶线性拟合
        trend_line = np.poly1d(poly_coeffs)
        axes[i, 0].plot(
            x_trend, trend_line(x_trend), color="blue", linestyle="--", label="Trend"
        )
        #  sampled_data["height"],
        # sampled_data["orb_rev"],
    axes[i, 1].scatter(
        heights_orb_rev,
        orbital_revs,
        alpha=0.7,
        color="orange",
        label=f"Inlet Flow Rate: {os.path.basename(base_name)} L/h",
    )
    axes[i, 1].set_xlabel(r"$h/D$")
    axes[i, 1].set_ylabel("Revolution (rad/s)")
    if i == 0:
        axes[i, 1].set_title("Revolution vs Height", fontsize=22)
    # axes[i, 1].grid()
    axes[i, 1].legend(loc="upper right", handlelength=0, handletextpad=0, markerscale=0)
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

# 根据模式决定是显示还是保存图表
if SAVE_MODE:
    # 保存图表到项目根目录（app.py 所在目录）
    # 获取当前脚本所在目录的父目录（即项目根目录）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # 上一级目录
    output_dir = os.path.join(project_root, "plots")
    os.makedirs(output_dir, exist_ok=True)
    
    fig.savefig(os.path.join(output_dir, "particle_analysis_detailed.png"), dpi=300, bbox_inches='tight')
    fig2.savefig(os.path.join(output_dir, "particle_analysis_summary.png"), dpi=300, bbox_inches='tight')
    
    print(f"图表已保存到: {output_dir}")
    print("  - particle_analysis_detailed.png (详细分析)")
    print("  - particle_analysis_summary.png (汇总)")
    
    plt.close('all')  # 关闭所有图表释放内存
else:
    # 显示图表
    plt.show()
