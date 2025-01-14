import json
import os
from process_utils import get_latest_folder, find_video_files, extract_frame
import cv2
from PIL import Image

from torchvision.models import efficientnet_b1, EfficientNet_B1_Weights
import torch
import torch.nn as nn
from torchvision import models
from torchvision import transforms
base_video_path = "processed_video_gradio"
image_width = 360
image_height = 640
base_path = r"runs_x_me\detect"
track_data_path = os.path.join(get_latest_folder(base_path), "labels")
track_base_path = get_latest_folder(base_path)
# result
initial_result_path = os.path.join(track_base_path)
os.makedirs(initial_result_path, exist_ok=True)
# video
video_path, video_name = find_video_files(track_base_path)
base_name, _ = os.path.splitext(video_name)
new_video_path =os.path.join(base_video_path, f"{base_name}.mp4")

def convert_results(
    detection_results,
    image_width,
    image_height,
    initial_result_path,
    frame,
    classify=True,
    model_e=None,
    device=None,
    transform=None,
):
    """
    将检测结果转换为 JSON 格式，并保存为以 id 为名字的文件夹中的 JSON 文件
    """
    detections = []
    for index, result in enumerate(detection_results):
        category = int(result[0])  # 物体类别
        x_center = float(result[1]) * image_width  # 中心点 x 坐标
        y_center = float(result[2]) * image_height  # 中心点 y 坐标
        width = float(result[3]) * image_width  # 物体的宽度
        height = float(result[4]) * image_height  # 物体的高度
        # 计算边框的左上角和右下角坐标
        x1 = round(x_center - width / 2)
        y1 = round(y_center - height / 2)
        x2 = round(x_center + width / 2)
        y2 = round(y_center + height / 2)

        detection = {
            "class": "particle",
            "confidence": 0,
            "bbox": [x1, y1, x2, y2],
            "Center": [round(x_center), round(y_center)],
            "file_path": new_video_path,
        }

        detections.append(detection)

    return {str(frame): {"detections": detections}}


def main(classify=True):
    result_dict = {}  # 存储所有帧的检测结果
    for index, filename in enumerate(
        sorted(
            os.listdir(track_data_path),
            key=lambda x: int(x.split("_")[-1].split(".")[0]),
        )
    ):
        # 由于这里的frame是按照index来的所以filename也得按照index的顺序
        detection_results = []

        file_path = os.path.join(track_data_path, filename)
        with open(file_path, "r") as f:
            detection_results = [line.strip().split() for line in f.readlines()]
        # print(f"path: {file_path}")
        print(f"正在处理第 {index + 1} 帧的检测结果")
        # print(f"数据：{detection_results}")
        frame_result = convert_results(
            detection_results,
            image_width,
            image_height,
            initial_result_path,
            index + 1,
            classify,
        )
        result_dict.update(frame_result)  # 将当前帧结果加入到result_dict

    output_dir_path = os.path.join(initial_result_path)

    output_file = os.path.join(output_dir_path, "detections.json")
    with open(output_file, "w") as f:
        json.dump(result_dict, f)


if __name__ == "__main__":
    main()
