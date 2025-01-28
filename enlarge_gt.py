import pandas as pd

# 配置文件路径
gt_file = r"assets\MOT17-mini\train\modify\gt\gt.txt"  # 真实 GT 文件路径
adjusted_gt_file = r"true_adjusted_gt.txt"  # 输出的调整后 GT 文件路径

# 调整长宽的增量
width_increment = 5  # 宽度增加值
height_increment = 5  # 高度增加值

# 读取 GT 文件
# 假设 GT 文件格式为：frame_id, object_id, top_left_x, top_left_y, w, h, confidence_score, 1, 1
columns = ["frame_id", "object_id", "top_left_x", "top_left_y", "w", "h", "confidence_score", "column_8", "column_9"]
gt_df = pd.read_csv(gt_file, header=None, names=columns)

# 调整长宽和位置
def adjust_bbox(row):
    # 原始数据
    top_left_x = row["top_left_x"] - width_increment / 2
    top_left_y = row["top_left_y"] - height_increment / 2
    width = row["w"]
    height = row["h"]

    # 增加长宽
    new_width = width + width_increment
    new_height = height + height_increment

    # 调整左上角坐标
    new_top_left_x = top_left_x - width_increment / 2
    new_top_left_y = top_left_y - height_increment / 2

    # 返回调整后的框数据
    return pd.Series([new_top_left_x, new_top_left_y, new_width, new_height])

# 应用调整到每一行
gt_df[["top_left_x", "top_left_y", "w", "h"]] = gt_df.apply(adjust_bbox, axis=1)

# 保存调整后的 GT 文件
gt_df.to_csv(adjusted_gt_file, index=False, header=False)
