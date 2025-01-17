# 这里用于读取所有检测最终的结果然后变成GT的格式
import os
import pandas as pd
from natsort import natsorted  # 需要安装 natsort 库：pip install natsort

# 配置路径
input_folder = r"runs\track\exp11\labels"  # 替换为实际文件夹路径
output_file = r"gt_format.txt"  # 输出文件路径

image_width = 768
image_height = 1024

# 初始化结果列表
all_gt_data = []

# 获取文件列表并排序（按帧号从小到大）
file_list = natsorted(
    [f for f in os.listdir(input_folder) if f.endswith(".txt")]
)


# 遍历排序后的文件列表
new_frame_id = 1  # 从1开始分配新的帧号
for file_name in file_list:
    file_path = os.path.join(input_folder, file_name)

    # 读取文件内容
    with open(file_path, "r") as file:
        for line in file:
            parts = line.strip().split()
            print(parts)
            class_id, center_x, center_y, width, height, object_id = map(float, parts[:6])
            center_x, center_y, width, height, object_id = float(center_x), float(center_y), float(width), float(height), int(object_id)

            # 计算 GT 格式参数
            top_left_x = (center_x - width / 2) * image_width
            top_left_y = (center_y - height / 2) * image_height
            w = width * image_width
            h = height * image_height
            confidence_score = 1  # 默认置信度

            # 添加到结果列表
            all_gt_data.append([new_frame_id, object_id, top_left_x, top_left_y, w, h, confidence_score, 1, 1])

    # 增加新的帧号
    new_frame_id += 1

# 转换为 DataFrame
columns = ["frame_id", "object_id", "top_left_x", "top_left_y", "w", "h", "confidence_score", "1","1"]
gt_df = pd.DataFrame(all_gt_data, columns=columns)

# 保存为 .txt 文件（无表头，空格分隔）
gt_df.to_csv(output_file, index=False, header=False, sep=",")


