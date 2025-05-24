# 只能使用这个来获得GT文件
# 只保留指定范围内gt的检测结果
import os
import pandas as pd
from natsort import natsorted  # 需要安装 natsort 库：pip install natsort

# 配置路径
input_folder = r"runs\track\exp20\labels"  # 预测框文件夹路径
output_file = r"gt_predfict.txt"  # 过滤后的预测框输出路径
gt_file = r"assets\MOT17-mini\train\275_particle\gt\gt.txt"  # 真实 GT 文件路径 assets\MOT17-mini\train\mot_particle\gt\gt.txt
# gt_file = r"yolov7_result\gt.txt"  # 预测框文件夹路径
filtered_gt_file = r"gt_true.txt"  # 过滤后的真实 GT 文件输出路径

# 图像尺寸
image_width = 768
image_height = 1024

# 设置坐标区间（归一化范围）
x_range = (0.25, 0.75)  # 中心点横坐标在 [0.3, 0.7]
y_range = (0.2, 0.9)  # 中心点纵坐标在 [0.4, 0.8]
center_y_threshold = 0.35  # 中心点纵坐标阈值
local_x_range_preset = (0.35, 0.6)  # 锥段部分的 x 范围 ，为什么取这段？是因为这段标注的比较准确，如果是旁边的话会有漏标的情况
# 初始化结果列表
all_pred_data = []  # 存储过滤后的预测数据
filtered_gt_data = []  # 存储过滤后的真实 GT 数据

# 处理预测框文件夹中的文件
file_list = natsorted([f for f in os.listdir(input_folder) if f.endswith(".txt")])
new_frame_id = 1  # 从1开始分配新的帧号

for file_name in file_list:
    file_path = os.path.join(input_folder, file_name)

    # 读取文件内容
    with open(file_path, "r") as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) < 6:
                print("No object_id found, skipping...", parts)
                continue
            class_id, center_x, center_y, width, height, object_id = map(
                float, parts[:6]
            )
            object_id = int(object_id)  # 仅对 object_id 转换为整数
            # print(center_x, center_y, width, height, object_id)
            local_x_range = x_range  # 默认使用全局 x_range
            if center_y > center_y_threshold:  # 锥段部分需要继续缩小
                local_x_range = local_x_range_preset

            # 判断是否在坐标区间内
            if not (
                local_x_range[0] <= center_x <= local_x_range[1]
                and y_range[0] <= center_y <= y_range[1]
            ):
                continue  # 跳过不符合条件的框

            # 计算 GT 格式参数
            top_left_x = (center_x - width / 2) * image_width
            top_left_y = (center_y - height / 2) * image_height
            w = width * image_width
            h = height * image_height
            confidence_score = 1  # 默认置信度

            # 添加到结果列表
            all_pred_data.append(
                [
                    new_frame_id,
                    object_id,
                    top_left_x,
                    top_left_y,
                    w,
                    h,
                    confidence_score,
                    1,
                    1,
                ]
            )

    # 增加新的帧号
    new_frame_id += 1

# 处理真实 GT 文件
gt_columns = [
    "frame_id",
    "object_id",
    "top_left_x",
    "top_left_y",
    "w",
    "h",
    "confidence_score",
    "1",
    "2",
]
gt_df = pd.read_csv(gt_file, header=None, names=gt_columns)
adjust_range = 3
for _, row in gt_df.iterrows():
    # 转换真实 GT 的中心点坐标
    center_x = (row["top_left_x"] + row["w"] / 2) / image_width
    center_y = (row["top_left_y"] + row["h"] / 2) / image_height
    local_x_range = x_range  # 默认使用全局 x_range
    if center_y > center_y_threshold:  # 锥段部分需要继续缩小
        local_x_range = local_x_range_preset

    # 判断是否在坐标区间内
    if not (
        local_x_range[0] <= center_x <= local_x_range[1]
        and y_range[0] <= center_y <= y_range[1]
    ):
        # print(f"GT {row['object_id']} 不在坐标区间内，已被过滤。 center_x: {center_x}, center_y: {center_y}")
        continue  # 跳过不符合条件的框

    # 重新计算左上角坐标和宽高
    adjusted_top_left_x = row["top_left_x"] - adjust_range * 1.5 // 2 + 1
    adjusted_top_left_y = row["top_left_y"] - adjust_range * 1.5 // 2 - 2
    adjusted_w = row["w"] + adjust_range * 1.5
    adjusted_h = row["h"] + adjust_range * 1.5 + 2
    confidence_score = row["confidence_score"]

    # 添加到过滤后的 GT 列表
    filtered_gt_data.append(
        [
            int(row["frame_id"]),
            int(row["object_id"]),
            adjusted_top_left_x,
            adjusted_top_left_y,
            adjusted_w,
            adjusted_h,
            confidence_score,
            1,
            1,
        ]
    )

# **保存结果**
# 保存过滤后的预测框
pred_columns = [
    "frame_id",
    "object_id",
    "top_left_x",
    "top_left_y",
    "w",
    "h",
    "confidence_score",
    "1",
    "2",
]
pred_df = pd.DataFrame(all_pred_data, columns=pred_columns)
pred_df.to_csv(output_file, index=False, header=False, sep=",")

# 保存过滤后的真实 GT
filtered_gt_df = pd.DataFrame(filtered_gt_data, columns=gt_columns)
filtered_gt_df.to_csv(filtered_gt_file, index=False, header=False, sep=",")
