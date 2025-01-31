import cv2, os, shutil
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from natsort import natsorted

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
    return frame


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
    if not changes_in_range:
        print(
            f"No changes found within the range ({mid_left:.2f} to {mid_right:.2f})."
        )
    return changes_in_range


def get_box_center(x1, y1, x2, y2):
    return (x1 + x2) / 2, (y1 + y2) / 2


def detect_frame_difference(data):
    """
    检测 category_changes 中相邻类别之间的帧差距是否为 2，并标注符合条件的类别。
    """
    for key, value in data.items():
        category_changes = value.get("category_changes", [])
        start_frame_revolution = value.get("start_frame_revolution", 0)
        end_frame_revolution = value.get("end_frame_revolution", 0)
        not_use_rotation = value.get("not_use_rotation", False)
        if not not_use_rotation:
            all_frame = (
                category_changes[-1]["origin_frame"]
                - category_changes[0]["origin_frame"]
            )
            # all_frame = end_frame_revolution - start_frame_revolution
            for i in range(len(category_changes) - 1):
                current_frame = category_changes[i]["origin_frame"]
                next_frame = category_changes[i + 1]["origin_frame"]
                frame_diff = next_frame - current_frame

                # 检查帧差距是否为 2
                if frame_diff == 2:
                    print(
                        f"Detected frame difference of 2 at frame {current_frame} of id: {key}, 由于变化过快，说明无法准确检测，建议删除"
                    )
                    data[key]["not_use"] = True
                    pass
                # 排除掉保留状态过长的轨迹
                elif frame_diff >= all_frame/2:
                    print(f"have a long time not change, id: {key}, at frame {current_frame}, not use")
                    data[key]["not_use"] = True
    return data

def remove_long_time_not_change(category_changes,id):
    """
    检查相邻帧的差距是否大于 15，并根据前后部分的数量删除较少的一部分。
    """
    all_frame = category_changes[-1]["Frame"] - category_changes[0]["Frame"]
    i = 0  # 使用 while 循环以便动态修改列表
    while i < len(category_changes) - 1:
        current_frame = category_changes[i]["Frame"]
        next_frame = category_changes[i + 1]["Frame"]
        frame_diff = next_frame - current_frame

        # 检查帧差距是否大于 15
        if frame_diff >= all_frame/3:
            print(
                f"Detected frame difference greater than 15 at frame {current_frame}, 检查前后数据数量以删除较少的一部分。"
            )
            # 计算前后部分的长度
            front_part = category_changes[: i + 1]  # 前部分（包含当前帧）
            back_part = category_changes[i + 1 :]   # 后部分

            # 删除数量较少的部分
            if len(front_part) <= len(back_part):
                print(f"删除前部分，长度: {len(front_part)},id: {id}")
                category_changes = back_part  # 保留后部分
            else:
                print(f"删除后部分，长度: {len(back_part)},id: {id}")
                category_changes = front_part  # 保留前部分

            i = -1  # 重置索引以重新检查新的列表
            break  # 跳出当前循环，重新处理

        i += 1

    return category_changes

# def get_latest_folder(base_path):
#     entries = [os.path.join(base_path, entry) for entry in os.listdir(base_path)]
#     folders = [entry for entry in entries if os.path.isdir(entry)]
#     if not folders:
#         raise FileNotFoundError(f"No folders found in {base_path}")
#     latest_folder = max(folders, key=os.path.getmtime)
#     return latest_folder


def get_latest_folder(base_path):
    """
    获取 `base_path` 目录下倒数第二个最旧的文件夹。
    """
    folders = [
        os.path.join(base_path, entry)
        for entry in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, entry))
    ]

    if len(folders) < 2:
        raise ValueError(
            f"Not enough folders in {base_path} to get the second oldest one."
        )

    # 按修改时间升序排序（最旧的在前，最新的在后）
    sorted_folders = sorted(folders, key=os.path.getmtime)
    print(sorted_folders[-5])
    return sorted_folders[-5]


def get_all_folders(base_path):
    """
    返回 base_path 目录下的所有文件夹路径，按修改时间降序排列（最新的文件夹在前）。
    """
    # 获取 base_path 下所有的子目录
    entries = [os.path.join(base_path, entry) for entry in os.listdir(base_path)]
    folders = [entry for entry in entries if os.path.isdir(entry)]

    if not folders:
        raise FileNotFoundError(f"No folders found in {base_path}")

    # 按照修改时间降序排序
    sorted_folders = natsorted(folders)

    return sorted_folders


def find_video_files(directory):
    # 视频文件的扩展名
    video_extensions = (".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv")

    # 获取文件夹中的所有文件
    video_files = []
    video_name = None
    for filename in os.listdir(directory):
        # 检查文件是否为视频文件
        if filename.endswith(video_extensions):
            video_files.append(os.path.join(directory, filename))
            video_name = filename

    return video_files, video_name


def convert_to_mp4(input_video: str) -> None:
    """
    将输入的视频文件直接转换为 .mp4 格式，并替换原文件。如果输入文件已为 .mp4 格式，则不进行转换。

    :param input_video: 输入视频文件路径（包括文件名和扩展名）
    :return: 转换后的 .mp4 文件路径
    """
    input_video = os.path.normpath(input_video)
    output_video = os.path.splitext(input_video)[0] + ".mp4"
    # 检查输入视频文件是否为 MP4 格式
    if not input_video.lower().endswith(".mp4"):
        print(f"The input video '{input_video}' is not in MP4 format.")
        print("Proceeding to convert the video to MP4 format.")

        # 构造转换后的 .mp4 文件路径，使用原始文件路径，但修改扩展名为 .mp4

        # 如果目标文件已经存在，先删除它（直接替换）
        if os.path.exists(output_video):
            print(f"The file '{output_video}' already exists. It will be replaced.")
            os.remove(output_video)

        # 打开输入视频文件
        cap = cv2.VideoCapture(input_video)

        # 检查视频是否成功打开
        if not cap.isOpened():
            print("Error: Couldn't open the video file.")
            error_code = cap.get(cv2.CAP_PROP_FOURCC)
            print(f"Error Code: {error_code}")
            return

        # 获取视频的宽度、高度和帧率
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_rate = cap.get(cv2.CAP_PROP_FPS)

        # 创建 VideoWriter 对象，指定输出文件，编码器，帧率和帧大小
        fourcc = cv2.VideoWriter_fourcc(*"h264")  # 'h264' 编码器，适用于 .mp4 文件
        out = cv2.VideoWriter(
            output_video, fourcc, frame_rate, (frame_width, frame_height)
        )

        # 循环读取每一帧并写入输出视频
        while cap.isOpened():
            ret, frame = cap.read()

            if not ret:
                break  # 如果视频读完，退出循环

            # 将每一帧写入输出视频文件
            out.write(frame)

        # 释放资源
        cap.release()
        out.release()

        print(f"Video conversion complete. Saved as '{output_video}'.")

        os.remove(input_video)
        print("The input video has been replaced with the converted MP4 file.")

    else:
        print(
            f"The input video '{input_video}' is already in MP4 format. No conversion needed."
        )
    return output_video


def shorten_video_opencv(
    input_video: str, start_time: float, end_time: float, output_video: str
):
    """
    使用 OpenCV 截取视频的指定时间段。

    :param input_video: 输入视频路径
    :param start_time: 截取开始的时间（单位：秒）
    :param end_time: 截取结束的时间（单位：秒）
    :param output_video: 输出视频路径
    """
    # 打开视频文件
    cap = cv2.VideoCapture(input_video)

    # 获取视频的帧率
    fps = cap.get(cv2.CAP_PROP_FPS)

    # 计算起始帧和结束帧
    start_frame = int(start_time * fps)
    end_frame = int(end_time * fps)

    # 获取视频的宽度和高度
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 创建一个 VideoWriter 对象，输出视频
    fourcc = cv2.VideoWriter_fourcc(*"h264")  # 使用 'mp4v' 编码器
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    # 跳到起始帧
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    current_frame = start_frame

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break  # 如果没有更多帧，退出循环

        if current_frame >= end_frame:
            break  # 如果到达结束帧，停止读取视频

        out.write(frame)  # 写入输出视频文件
        current_frame += 1

    # 释放资源
    cap.release()
    out.release()
    print(f"视频截取完成，保存为 {output_video}")

def clear_folder(folder_path):
    if not os.path.exists(folder_path):
        print(f"文件夹 {folder_path} 不存在。")
        return

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path) 
        except Exception as e:
            print(f"无法删除 {item_path}。错误: {e}")
    print(f"已清理文件夹: {folder_path}")


if __name__ == "__main__":
    # 使用示例
    # shorten_video_opencv(
    #     "650-1-x1_particle_video.mp4", 0, 5, "x_video.mp4"
    # )
    convert_to_mp4(r"xy1-650-S14-2_particle_video.avi")
