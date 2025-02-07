# 550 是H:\shnu-graduation\alldata\alldata\20180117-hfq-y\Y1-550\相机No.1_C001H001S0001 x再算一次
# 750 是 H:\shnu-graduation\alldata\alldata\20180117-hfq-y\Y1-750\No.1_C001H001S0002 后处理再算一次
# 850 是 H:\shnu-graduation\alldata\alldata\20180117-hfq-y\Y1-850\相机No.1_C001H001S0001
# 450  是 H:\shnu-graduation\alldata\alldata\20180117-hfq-y\y1-450\相机No.1_C001H001S0002
# 650 是 H:\shnu-graduation\alldata\alldata\20180117-hfq-y\Y1-650\相机No.1_C001H001S0002


import json
import matplotlib.pyplot as plt
import os
import numpy as np
from process_utils import get_all_folders


def merge_stats(folder1, folder2):
    """合并两个文件夹的 all_stats.json 数据，并对第二个文件夹的键名加上 '-2'"""
    stats1_path = os.path.join(folder1, "initial_result", "all_stats.json")
    stats2_path = os.path.join(folder2, "initial_result", "all_stats.json")

    data = {}

    # 加载第一个文件夹的 all_stats.json
    if os.path.exists(stats1_path):
        with open(stats1_path, "r") as f:
            data1 = json.load(f)
        data.update(data1)

    # 加载第二个文件夹的 all_stats.json，并调整键名
    if os.path.exists(stats2_path):
        with open(stats2_path, "r") as f:
            data2 = json.load(f)

        for key, value in data2.items():
            modified_key = f"{key}-2"  # 修改键名，在原键名后附加 '-2'
            data[modified_key] = value

    return data


# 设置基础路径
base_path = "runs/track"
folders = get_all_folders(base_path)

# 过滤出 '-2' 版本的文件夹并匹配主文件夹
folder_pairs = {}
for folder in folders:
    base_name = folder.rstrip("-2")
    if base_name in folders and folder.endswith("-2"):
        folder_pairs[base_name] = folder
    elif base_name not in folder_pairs:
        folder_pairs[base_name] = None

# 设置基础路径
base_path = "runs/track"

# 获取所有子目录
folders = get_all_folders(base_path)

# 初始化总体数据存储
exp_indices = []  # 存储实验序号
exp_avg_abs_rot = []  # 存储每次实验的平均绝对自转
exp_avg_orb_rev = []  # 存储每次实验的平均公转

# 设置画布
num_folders = len(folders) // 2
fig, axes = plt.subplots(
    num_folders + 1, 2, figsize=(12, 6 * (num_folders + 1)), constrained_layout=True
)  # 多个子图

all_heights = []
for folder in folders:
    stats_file_path = os.path.join(folder, "initial_result", "all_stats.json")
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
        all_heights.append(height)

# 获取全局的最小和最大高度
min_height = min(all_heights)
max_height = max(all_heights)
# 遍历所有子目录
print(len(folder_pairs))
for i, (folder, folder_2) in enumerate(folder_pairs.items()):

    all_stats = merge_stats(folder, folder_2) if folder_2 else merge_stats(folder, "")

    # for i, folder in enumerate(folders):
    # initial_result_directory = os.path.join(folder, "initial_result")
    # stats_file_path = os.path.join(initial_result_directory, "all_stats.json")

    # if not os.path.exists(stats_file_path):
    #     print(f"{stats_file_path} 文件不存在，跳过...")
    #     continue

    # # 读取 JSON 数据
    # with open(stats_file_path, "r") as stats_file:
    #     all_stats = json.load(stats_file)

    # 初始化当前文件夹的数据存储
    heights_abs_rot = []
    abs_rotations = []
    heights_orb_rev = []
    orbital_revs = []

    # 解析数据
    for key, value in all_stats.items():
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

            # 存储数据
            if abs_rotation > 0:
                heights_abs_rot.append(height)
                abs_rotations.append(abs_rotation)

            if orbital_rev > 0:
                heights_orb_rev.append(height)
                orbital_revs.append(orbital_rev)

        except Exception as e:
            print(f"处理 {key} 时出错: {e}")

    # 计算该实验的均值
    avg_abs_rotation = np.mean(abs_rotations) if abs_rotations else 0
    avg_orbital_rev = np.mean(orbital_revs) if orbital_revs else 0
    folder_name = os.path.basename(folder)  # 获取文件夹名称
    # 存储实验结果
    exp_indices.append(folder_name)
    exp_avg_abs_rot.append(avg_abs_rotation)
    exp_avg_orb_rev.append(avg_orbital_rev)

    # 绘制当前文件夹的图
    axes[i, 0].scatter(
        heights_abs_rot, abs_rotations, alpha=0.7, label=f"{os.path.basename(folder)}"
    )
    axes[i, 0].set_xlabel("Height (cm)")
    axes[i, 0].set_ylabel("Rotation (rad/s)")
    axes[i, 0].set_xlim(min_height, max_height)  # 设定相同的 x 轴范围
    if i == 0:
        axes[i, 0].set_title(f"Absolute Rotation vs Height")
    # axes[i, 0].grid()
    axes[i, 0].legend()
    # 计算并绘制趋势线（线性拟合）
    if len(heights_abs_rot) > 1:
        poly_coeffs = np.polyfit(heights_abs_rot, abs_rotations, 1)  # 一阶线性拟合
        trend_line = np.poly1d(poly_coeffs)
        x_trend = np.linspace(min_height, max_height, 100)
        axes[i, 0].plot(
            x_trend, trend_line(x_trend), color="blue", linestyle="--", label="Trend"
        )
    axes[i, 1].scatter(
        heights_orb_rev,
        orbital_revs,
        alpha=0.7,
        color="orange",
        label=f"{os.path.basename(folder)}",
    )
    axes[i, 1].set_xlabel("Height (cm)")
    axes[i, 1].set_ylabel("Revolution (rad/s)")
    if i == 0:
        axes[i, 1].set_title(f"Orbital Revolution vs Height")
    # axes[i, 1].grid()
    axes[i, 1].legend()
    # 计算并绘制趋势线（线性拟合）
    if len(heights_orb_rev) > 1:
        poly_coeffs = np.polyfit(heights_orb_rev, orbital_revs, 2)  # 一阶线性拟合
        trend_line = np.poly1d(poly_coeffs)
        axes[i, 1].plot(
            x_trend, trend_line(x_trend), color="red", linestyle="--", label="Trend"
        )


# 绘制实验均值趋势图（最后一行）
axes[-1, 0].plot(
    exp_indices,
    exp_avg_abs_rot,
    alpha=0.7,
    color="blue",
    label="Average Rotation",
    marker="o",
    linestyle="-",
)
axes[-1, 0].set_xlabel("Inlet Flow Rate")
axes[-1, 0].set_ylabel("Avg Rotation (rad/s)")
axes[-1, 0].set_title("Inlet Flow Rate vs Absolute Rotation")
# axes[-1, 0].grid()
axes[-1, 0].legend()

axes[-1, 1].plot(
    exp_indices,
    exp_avg_orb_rev,
    alpha=0.7,
    color="red",
    label="Average Orbital Revolution",
    marker="o",
    linestyle="-",
)
axes[-1, 1].set_xlabel("Inlet Flow Rate")
axes[-1, 1].set_ylabel("Avg Orbital Revolution (rad/s)")
axes[-1, 1].set_title("Inlet Flow Rate vs Orbital Revolution")
# axes[-1, 1].grid()
axes[-1, 1].legend()

plt.subplots_adjust(hspace=0.5, wspace=0.3)

plt.show()
