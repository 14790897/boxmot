import cv2, os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# for line_coords in line_dict.values():
#     draw.line(line_coords, fill=(255, 0, 0), width=2)


def calculate_distance_and_draw(point, line_coords, image=None):
    x, y = point
    x1, y1, x2, y2 = line_coords

    # 确保线段的y范围覆盖点的y值
    if not (min(y1, y2) <= y <= max(y1, y2)):
        print(f"点 {point} 不在直线 {line_coords} 的 y 范围内，需要关注")

    # 计算斜率和 y 值相等时的 x 值
    if x1 != x2:  # 处理非垂直线的情况
        m = (y2 - y1) / (x2 - x1)
        x0 = x1 + (y - y1) / m
    else:  # 如果是垂直线，直接取 x1
        x0 = x1

    # 计算水平距离
    distance = abs(x - x0)
    if image is not None:
        # 如果传入的 image 是图像路径，加载图像
        if isinstance(image, (str, bytes, os.PathLike)):
            image = cv2.imread(image)

        # 如果 image 是 NumPy 数组，则继续使用 OpenCV 绘制
        if isinstance(image, np.ndarray):
            offset = 10  # 上移的像素值，可以调整

            # 绘制向上偏移的线段
            cv2.line(
                image,
                (int(x), int(y - offset)),
                (int(x0), int(y - offset)),
                (0, 0, 255),
                2,
            )

            # 绘制文本（标注距离）
            cv2.putText(
                image,
                f"{distance:.2f}   y:{ int(y)}",
                (int(x + offset), int(y)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1,
                cv2.LINE_AA,
            )
        image_pillow = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        return distance, x0, y, image_pillow
    else:
        return distance, x0, y


def draw_line_with_label(
    img, start, end, color, thickness, label, line_type=cv2.LINE_AA
):
    cv2.line(img, start, end, color, thickness=thickness, lineType=line_type)
    cv2.putText(
        img,
        label,
        (start[0] + 5, start[1] - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        color,
        2,
        line_type,
    )


def extract_frame(video_path, frame_number, output_image_path):
    # 加载视频文件
    cap = cv2.VideoCapture(video_path)
    frame_number = int(frame_number)
    if not cap.isOpened():
        print(f"Error: Cannot open video file {video_path}")
        return

    # 获取总帧数
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    # print(f"Total frames in video: {total_frames}")

    # 检查帧号是否有效
    if frame_number < 0 or frame_number >= total_frames:
        print(
            f"Error: frame_number {frame_number} is out of range (0 to {total_frames - 1})"
        )
        return

    # 设置视频指针到指定帧
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

    # 读取帧
    ret, frame = cap.read()
    if not ret:
        print(f"Error: Cannot read frame {frame_number}")
        return

    # 保存帧为图片
    cv2.imwrite(output_image_path, frame)
    # print(f"Frame {frame_number} saved as {output_image_path}")

    # 释放视频对象
    cap.release()


def extract_and_stitch_columns(video_path, data):
    """
    从视频中裁剪每帧指定 X 范围的整列，并将这些列拼接成一个图像。

    参数：
        video_path (str): 输入视频的路径。
        data (list): 包含裁剪框信息的列表，每项格式为：
                     {"Frame": int, "Box": [x1, y1, x2, y2]}，只需使用 x1 和 x2。

    返回：
        stitched_image (np.ndarray): 拼接后的列图像（如果成功）。
        None: 如果未能裁剪任何列。
    """
    # 打开视频
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Unable to open video.")
        return None

    # 存储所有裁剪的列
    columns = []

    # 遍历 JSON 数据
    for entry in data:
        frame_index = entry["Frame"]
        box = entry["Box"]
        x1, x2 = box[0], box[2]  # 只使用 X 坐标范围

        # 定位到特定帧
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index - 1)
        ret, frame = cap.read()
        if not ret:
            print(f"Error: Unable to read frame {frame_index}.")
            continue

        # 裁剪整条列（全高）
        height, _, _ = frame.shape
        cropped_column = frame[0:height, x1:x2]  # Y 范围是全帧高度，X 范围是 [x1:x2]

        columns.append(cropped_column)

    # 释放视频资源
    cap.release()

    # 拼接所有列
    if columns:
        columns = columns[::-1]  # 将列顺序倒序，从右到左
        stitched_image = np.hstack(columns)  # 横向拼接
        return stitched_image
    else:
        print("No columns were extracted.")
        return None


def find_changes_within_range(
    category_changes, left_line_x, right_line_x, range_ratio=0.6
):
    """
    找出在左右两条线之间指定比例范围内的category_changes。

    :param category_changes: List of changes (each with a "Box" defining its bounding box).
    :param left_line_x: X-coordinate of the left boundary line.
    :param right_line_x: X-coordinate of the right boundary line.
    :param range_ratio: Proportion of the width to define the central range (default is 0.5 for 50%).
    :return: List of changes within the specified range.
    """
    # 计算范围的边界
    mid_left = left_line_x + (1 - range_ratio) / 2 * (right_line_x - left_line_x)
    mid_right = right_line_x - (1 - range_ratio) / 2 * (right_line_x - left_line_x)

    # 找到所有在范围内的变化
    changes_in_range = []
    for change in category_changes:
        box = change["Box"]
        center_x = (box[0] + box[2]) / 2  # 计算水平中心坐标
        if mid_left <= center_x <= mid_right:
            changes_in_range.append(change)

    return changes_in_range


def get_box_center(x1, y1, x2, y2):
    return (x1 + x2) / 2, (y1 + y2) / 2


def detect_frame_difference(data):
    """
    检测 category_changes 中相邻类别之间的帧差距是否为 2，并标注符合条件的类别。
    """
    keys_to_remove = []  # 用于存储需要删除的 keys
    for key, value in data.items():
        category_changes = value.get("category_changes", [])
        for i in range(len(category_changes) - 1):
            current_frame = category_changes[i]["Frame"]
            next_frame = category_changes[i + 1]["Frame"]
            frame_diff = next_frame - current_frame

            # 检查帧差距是否为 2
            if frame_diff == 2:
                keys_to_remove.append(key)
                print(
                    f"Detected frame difference of 2 at frame {current_frame} of id: {key}, 由于变化过快，说明无法准确检测，建议删除"
                )
                data[key]["not_use"] = True
    # 删除标记的 keys
    # for key in keys_to_remove:
    #     del data[key]
    return data


def get_latest_folder(base_path):
    entries = [os.path.join(base_path, entry) for entry in os.listdir(base_path)]
    folders = [entry for entry in entries if os.path.isdir(entry)]
    if not folders:
        raise FileNotFoundError(f"No folders found in {base_path}")
    latest_folder = max(folders, key=os.path.getmtime)
    return latest_folder
