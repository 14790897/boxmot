# 先运行my_detect.py ， 求出每个id距离边距最近的那个点
# 这个测的是哪个入口流量的？
# 图片手动检测那个图片它是最开始的最后一张图片的左右两边合成在一起吗？
import shutil
import os
import json
from PIL import Image, ImageDraw, ImageFont
import cv2
from datetime import datetime
from collections import defaultdict

from process_utils import (
    calculate_distance_and_draw,
    draw_line_with_label,
    extract_frame,
    get_latest_folder,
)

base_path = "runs/track"
initial_result_directory = os.path.join(get_latest_folder(base_path), "initial_result")
if not get_latest_folder(base_path).endswith("-2"):
    # 旋流器右边的两条线
    line_dict = {"1": (269, 49, 269, 328), "2": (269, 328, 250, 638)}
else:
    # 切换位置
    line_dict = {"1": (244, 0, 213, 639), "2": (244, 0, 213, 639)}

stats_file_path = os.path.join(initial_result_directory, "all_stats.json")
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if os.path.exists(stats_file_path):
    with open(stats_file_path, "r") as stats_file:
        all_stats = json.load(stats_file)
base_path = r"runs_x_me\detect"
x_detect_result_path = os.path.join(get_latest_folder(base_path), "detections.json")
# x_detect_result_path = r"runs_x_me\detect\exp3\detections.json"  # exp2是750 exp是550

with open(x_detect_result_path, "r") as f:
    x_data = json.load(f)
offset = 496

# 遍历所有ID的结果
for k, v in all_stats.items():
    try:
        id_path = os.path.join(initial_result_directory, k)
        x_images_path = os.path.join(id_path, "x_images")
        # 如果存在 x_images 文件夹，删除文件夹及其内容
        if os.path.exists(x_images_path):
            shutil.rmtree(x_images_path)
        os.makedirs(x_images_path, exist_ok=True)
        if "closest_point" in v:
            closest_point = v["closest_point"]

        id = closest_point["ID"]
        frame = closest_point["Frame"]
        half_frame = frame // 2
        max_frame = max(map(int, x_data.keys()))
        min_frame = min(map(int, x_data.keys()))
        frame_range = list(
            range(max(min_frame, half_frame - 8), min(max_frame, half_frame + 8))
        )

        aggregated_results = defaultdict(list)

        # 遍历帧范围并加载对应帧的结果
        for number in frame_range:
            # 构造文件名（帧的命名格式为：x-frame）
            frame_name = str(number)
            try:
                # 如果当前帧在检测结果中，添加到汇总结果
                if frame_name in x_data:
                    aggregated_results[frame_name].extend(
                        x_data[frame_name]["detections"]
                    )
                else:
                    # print(f"Frame {frame_name} not found in detections")
                    pass

            except KeyError:
                print(f"No detections found for frame: {frame_name}")
            except json.JSONDecodeError:
                print(f"Error decoding JSON for file: {x_detect_result_path}")
        image_y_y_coord = (closest_point["Box"][1] + closest_point["Box"][3]) / 2
        if len(aggregated_results) < 10:
            # 找到最近的帧
            available_frames = list(x_data.keys())  # 获取所有可用的帧
            available_frames = sorted(
                available_frames, key=lambda x: abs(int(x) - half_frame)
            )
            # 获取最近的十个帧（或不足十个全部）
            closest_frames = available_frames[:10]
            for closest_frame in closest_frames:
                if closest_frame in x_data:
                    aggregated_results[closest_frame].extend(
                        x_data[closest_frame]["detections"]
                    )
        min_margin = float("inf")
        min_margin_img_path = None
        for frame_name, detections in aggregated_results.items():
            frame_path = os.path.join(x_images_path, f"frame_{frame_name}.jpg")
            extract_frame(
                detections[0]["file_path"], str(int(frame_name) - 1), frame_path
            )  # 注意这里需要减一，因为opencv的frame是从0开始的，但是yolo检测结果是从1开始的
            frame_image = cv2.imread(frame_path)
            for detection in detections:
                x1, y1, x2, y2 = detection["bbox"]
                cv2.rectangle(
                    frame_image, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2
                )
            cv2.imwrite(frame_path, frame_image)
            for entry in detections:
                x1, y1, x2, y2 = entry["bbox"]
                # frame_image = cv2.imread(frame_image_path)
                x, y = (x1 + x2) / 2, (y1 + y2) / 2
                if not get_latest_folder(base_path).endswith("-2"):

                    image_x_y_coord = int(
                        (image_y_y_coord + 44) * 101 / 149 + 5
                    )  # 我觉得应该是 (y + 44 ) * 101/149 + 5  44为y图片相对于0位置缺少的距离，101/149为x/y图片的缩放比例，5为x图片相对于0的位置缺少的距离
                else:
                    # 切换位置
                    image_x_y_coord = int((image_y_y_coord) * 101 / 149)
                    # 上下去十个像素的范围
                image_x_down_threshold = image_x_y_coord - 15
                image_x_up_threshold = image_x_y_coord + 15
                if image_x_down_threshold <= y <= image_x_up_threshold:
                    dist_to_line1 = (
                        calculate_distance_and_draw((x, y), line_dict["1"])[0]
                        if y < 328
                        else None
                    )
                    dist_to_line2 = (
                        calculate_distance_and_draw((x, y), line_dict["2"])[0]
                        if y >= 328
                        else None
                    )
                    distances = [
                        d for d in [dist_to_line1, dist_to_line2] if d is not None
                    ]

                    if distances:
                        margin = min(distances)
                        if margin < min_margin:
                            min_margin = margin
                            min_margin_img_path = (
                                x_images_path + "/frame_" + frame_name + ".jpg"
                            )  # 这里其实可以使用那个ID path
                            os.makedirs(
                                os.path.dirname(min_margin_img_path), exist_ok=True
                            )  # 如果目录已存在，不会报错
                            # extract_frame(
                            #     entry["file_path"], frame_name, min_margin_img_path
                            # )
                            # min_margin_image = cv2.imread(min_margin_img_path)
                            # cv2.rectangle(
                            #     min_margin_image,
                            #     (int(x1), int(y1)),
                            #     (int(x2), int(y2)),
                            #     (255, 0, 0),
                            #     2,
                            # )
                            # cv2.imwrite(min_margin_img_path, min_margin_image)
                            # min_margin_img_path = entry["file_path"]
                            min_margin_coord = (x, y)
                # else:
                # print("中心点超出控制范围，不计算距离")
        if min_margin_img_path is not None:
            print(f"{k}最小距离为{min_margin}")
            all_stats[str(id)].update({"margin": min_margin, "timestamp": current_time})
            min_margin_image = cv2.imread(min_margin_img_path)
            color = (0, 255, 0)  # 绿色
            tl = 2  # 线条粗细

            line1 = line_dict["1"]
            line2 = line_dict["2"]

            draw_line_with_label(min_margin_image, line1[:2], line1[2:], color, tl, "1")
            draw_line_with_label(min_margin_image, line2[:2], line2[2:], color, tl, "2")
            cv2.line(
                min_margin_image,
                (0, image_x_down_threshold),
                (min_margin_image.shape[:2][1], image_x_down_threshold),
                color,
                tl,
            )
            cv2.line(
                min_margin_image,
                (0, image_x_up_threshold),
                (min_margin_image.shape[:2][1], image_x_up_threshold),
                color,
                tl,
            )

            image1 = (
                calculate_distance_and_draw(
                    min_margin_coord, line_dict["1"], min_margin_image
                )[3]
                if min_margin_coord[1] < 328
                else None
            )
            image2 = (
                calculate_distance_and_draw(
                    min_margin_coord, line_dict["2"], min_margin_image
                )[3]
                if min_margin_coord[1] >= 328
                else None
            )
            image = [d for d in [image1, image2] if d is not None]
            image_x_min_distance_path = os.path.splitext(
                os.path.basename(min_margin_img_path)
            )[0]
            # 保存结果图像到 images_x_output
            output_image_path = os.path.join(
                id_path,
                "x_images",
                f"{image_x_min_distance_path}_min_margin_result.jpg",
            )
            cv2.imwrite(output_image_path, min_margin_image)
            print(f"边距最小的结果图像已保存到 {output_image_path}")
        else:
            print(f"{k}没有找到符合条件的检测结果,设置为8")
            all_stats[str(id)].update(
                {
                    "margin": None,
                    "timestamp": current_time,
                    "not_use_revolution": False,
                }  # 不需要后面的标志
            )
            # shutil.rmtree(id_path)
    except FileNotFoundError:
        # 如果文件不存在，捕获异常并跳过
        print(f"颗粒 {k} output.json不存在，跳过处理。")

# 保存更新后的 all_stats.json
with open(stats_file_path, "w") as stats_file:
    # 在保存 all_stats.json 之前，删除没有 "margin" 字段的项
    all_stats_filtered = {k: v for k, v in all_stats.items() if "margin" in v}
    json.dump(all_stats_filtered, stats_file, indent=4)
    print(f"更新后的数据已保存到 {stats_file_path}")
