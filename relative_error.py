import pandas as pd
import matplotlib.pyplot as plt
# import math
import numpy as np

# 读取 Excel 文件
data = pd.read_excel(
    r"C:\git-program\particle_detect\manual_caculate\data\relative error.xlsx",
    sheet_name="Sheet1",
    header=None,
)

# 旋转（转置）表格，将列变为行
data = data.T

# 重新设置表头为第一行的数据
data.columns = data.iloc[0]  # 使用第一行作为表头
data = data[1:]  # 删除第一行

# 将列名转换为字符串，确保没有潜在问题
data.columns = data.columns.astype(str)

# 确保相关列转换为数值类型
data["height"] = pd.to_numeric(data["height"], errors="coerce")
data["diameter"] = pd.to_numeric(data["diameter"], errors="coerce")
data["re_revolution"] = pd.to_numeric(data["re_revolution"], errors="coerce")
data["re_rotation"] = pd.to_numeric(data["re_rotation"], errors="coerce")
data["H/D"] = data["height"] / data["diameter"] * 147
# 使用 pandas.cut 将 'height' 划分为每 3 的区间
bin_size = 1.4
# 横坐标
h_to_d_ratio = data["H/D"]
max_h_to_d_ratio = h_to_d_ratio.max()  # 获取 height 的最大值
bins = np.arange(0, max_h_to_d_ratio + bin_size, bin_size)
data["height_bin"] = pd.cut(h_to_d_ratio, bins=bins, right=False)
print(f'data["re_rotation"]: {data["re_rotation"]}')
print(data["height_bin"])

# 按分组区间计算平均值
grouped_data = data.groupby("height_bin").agg(
    re_revolution_mean=("re_revolution", "mean"),
    re_rotation_mean=("re_rotation", "mean"),
    count=("height", "size"),  # 统计每个分组的点数
)
grouped_data = grouped_data.reset_index()

# 设置区间中点为 x 轴标签
grouped_data["bin_mid"] = grouped_data["height_bin"].apply(lambda x: x.mid)

# 打印每个范围的点数
print("Number of points in each height bin:")
print(grouped_data[["height_bin", "count"]])
# 创建一个窗口，包含两张子图（左右排列）
fig, axs = plt.subplots(1, 2, figsize=(14, 6))  # 一行两列

# 绘制第一张折线图（re_revolution）
axs[0].plot(
    grouped_data["bin_mid"],
    grouped_data["re_revolution_mean"],
    marker="o",
    linestyle="-",
    color="blue",
    label="Relative Revolution Error",
)
axs[0].set_title("Relative Revolution Error", fontsize=16)
axs[0].set_xlabel("H/D", fontsize=12)
axs[0].set_ylabel("Mean Relative Revolution Error", fontsize=12)
axs[0].grid(axis="both", linestyle="--", alpha=0.7)  # 显示网格
axs[0].legend(fontsize=12)
# 在第一张图上标记 (a)
axs[0].text(
    0.5,
    -0.2,
    "(a)",
    transform=axs[0].transAxes,
    fontsize=14,
    fontweight="bold",
    va="top",
    ha="left",
)
# 绘制第二张折线图（re_rotation）
axs[1].plot(
    grouped_data["bin_mid"],
    grouped_data["re_rotation_mean"],
    marker="o",
    linestyle="-",
    color="orange",
    label="Relative Rotation Error",
)
axs[1].set_title("Relative Rotation Error", fontsize=16)
axs[1].set_xlabel("H/D", fontsize=12)
axs[1].set_ylabel("Mean Relative Rotation Error", fontsize=12)
axs[1].grid(axis="both", linestyle="--", alpha=0.7)  # 显示网格
axs[1].legend(fontsize=12)
# 在第二张图上标记 (b)
axs[1].text(
    0.5,
    -0.2,
    "(b)",
    transform=axs[1].transAxes,
    fontsize=14,
    fontweight="bold",
    va="top",
    ha="left",
)

# 自动调整子图间距
plt.tight_layout()

# 显示图形
plt.show()

# 计算总的均值
overall_revolution_mean = data["re_revolution"].mean()  # 计算 re_revolution 的全局均值
overall_rotation_mean = data["re_rotation"].mean()  # 计算 re_rotation 的全局均值

# 打印总的均值
print(
    f"Overall Mean Relative Revolution Error: {overall_revolution_mean:.2f}, accuracy: {100-overall_revolution_mean:.2f}"
)
print(
    f"Overall Mean Relative Rotation Error: {overall_rotation_mean:.2f}, accuracy: {100-overall_rotation_mean:.2f}"
)
