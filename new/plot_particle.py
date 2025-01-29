# exp是H:\shnu-graduation\alldata\alldata\20180117-hfq-y\Y1-550\相机No.1_C001H001S0001
# exp2是 H:\shnu-graduation\alldata\alldata\20180117-hfq-y\Y1-750\No.1_C001H001S0002

import json
import matplotlib.pyplot as plt
import os
from process_utils import (
    get_latest_folder,
)

base_path = "runs/track"
initial_result_directory = os.path.join(get_latest_folder(base_path), "initial_result")
stats_file_path = os.path.join(initial_result_directory, "all_stats.json")
# stats_file_path = r"runs/track\exp2\initial_result\all_stats.json"
# Check if the file exists
if not os.path.exists(stats_file_path):
    raise FileNotFoundError(f"{stats_file_path} does not exist.")

# Read the data
with open(stats_file_path, "r") as stats_file:
    all_stats = json.load(stats_file)
# 加载 JSON 数据
if not os.path.exists(stats_file_path):
    print(f"{stats_file_path} 文件不存在。")
    exit()

with open(stats_file_path, "r") as stats_file:
    all_stats = json.load(stats_file)

# 初始化数据存储
heights = []
abs_rotations = []
orbital_revs = []

# 遍历数据并提取非零的 abs_rotation 和 orbital_rev
for key, value in all_stats.items():
    try:
        abs_rotation = value.get("abs_rotation", 0)
        orbital_rev = value.get("orbital_rev", 0)
        closest_point = value.get("closest_point", {})

        # 计算高度
        box = closest_point.get("Box", [0, 0, 0, 0])
        height = (box[1] + box[3]) / 2 / 147 + 42 / 147  # 高度计算公式

        if abs_rotation > 0:
            heights.append(height)
            abs_rotations.append(abs_rotation)

        if orbital_rev > 0:
            heights.append(height)
            orbital_revs.append(orbital_rev)

    except Exception as e:
        print(f"Error processing key {key}: {e}")

# 绘图
plt.figure(figsize=(12, 6))

# 绘制 abs_rotation 的分布
plt.subplot(1, 2, 1)
plt.scatter(heights[: len(abs_rotations)], abs_rotations, alpha=0.7)
plt.xlabel("Height (cm)")
plt.ylabel("Absolute Rotation (rad/s)")
plt.title("Absolute Rotation vs Height")
plt.grid()

# 绘制 orbital_rev 的分布
plt.subplot(1, 2, 2)
plt.scatter(heights[len(abs_rotations) :], orbital_revs, alpha=0.7, color="orange")
plt.xlabel("Height (cm)")
plt.ylabel("Orbital Revolution (rad/s)")
plt.title("Orbital Revolution vs Height")
plt.grid()

# 显示图像
plt.tight_layout()
plt.show()
