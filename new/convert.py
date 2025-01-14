import json
import os
from .process_utils import get_latest_folder, find_video_files, extract_frame
import cv2
from PIL import Image

from torchvision.models import efficientnet_b1, EfficientNet_B1_Weights
import torch
import torch.nn as nn
from torchvision import models
from torchvision import transforms


def convert_results(
    detection_results,
    image_width,
    image_height,
    initial_result_path,
    frame,
    new_video_path,
    classify=True,
    model_e=None,
    device=None,
    transform=None,
):
    """
    将检测结果转换为 JSON 格式，并保存为以 id 为名字的文件夹中的 JSON 文件
    """
    for index, result in enumerate(detection_results):
        category = int(result[0])  # 物体类别
        x_center = float(result[1]) * image_width  # 中心点 x 坐标
        y_center = float(result[2]) * image_height  # 中心点 y 坐标
        width = float(result[3]) * image_width  # 物体的宽度
        height = float(result[4]) * image_height  # 物体的高度
        id = int(result[5])  # 物体 ID
        # 计算边框的左上角和右下角坐标
        x1 = round(x_center - width / 2)
        y1 = round(y_center - height / 2)
        x2 = round(x_center + width / 2)
        y2 = round(y_center + height / 2)

        object_data = {
            "Frame": frame,
            "ID": id,
            "Category": category,
            "Box": [x1, y1, x2, y2],
            "Center": [round(x_center), round(y_center)],
            "WidthHeight": [round(width), round(height)],
        }

        output_dir_path = os.path.join(initial_result_path, str(id))
        if not os.path.exists(output_dir_path):
            os.makedirs(output_dir_path)

        output_image_file_path = os.path.join(
            output_dir_path, "images", f"frame_{frame}.jpg"
        )
        # print(f"正在保存物体 {id} 的图像到 {output_image_file_path}")
        os.makedirs(os.path.join(output_dir_path, "images"), exist_ok=True)
        output_image = extract_frame(
            new_video_path,
            str(int(frame) - 1),
            output_image_file_path,
        )
        classify_cat = None
        if classify:
            # 转换 NumPy 数组为 PIL 图像
            output_image_pil = Image.fromarray(
                cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB)
            )

            # 然后进行转换
            cropped_image = output_image_pil.crop((x1, y1, x2, y2))
            transformed_image = transform(cropped_image).unsqueeze(0).to(device)
            outputs = model_e(transformed_image)
            confidences = torch.softmax(outputs, dim=1)  # 计算每个类别的置信度
            _, classify_cat = confidences.max(1)  # 获取每个图像的最高置信度
            classify_cat = classify_cat.item()  # 将 Tensor 转换为 Python 标量
            object_data["Category"] = classify_cat
            print("classify_cat:", classify_cat)
        cv2.rectangle(output_image, (x1, y1), (x2, y2), (0, 0, 255), 1)

        text = f"id:{id} cat:{classify_cat}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(
            output_image,
            text,
            (x1, y1 - 10),  # 文本位置，稍微在框的上方
            font,
            0.5,  # 字体大小
            (0, 0, 255),  # 红色文本
            1,  # 字体粗细
            cv2.LINE_AA,  # 抗锯齿
        )

        cv2.imwrite(output_image_file_path, output_image)
        output_file = os.path.join(output_dir_path, "initial_data.json")
        # 打开文件并追加数据
        try:
            # 如果文件已经存在，则打开并追加数据，否则创建新文件
            if os.path.exists(output_file):
                with open(output_file, "r") as f:
                    existing_data = json.load(f)
                existing_data.append(object_data)  # 添加新的数据到现有数据列表
            else:
                existing_data = [object_data]

            # 写入或追加数据
            with open(output_file, "w") as f:
                json.dump(existing_data, f, indent=2)

            # print(f"物体 {id} 的数据已保存到 {output_file}")

        except json.JSONDecodeError:
            with open(output_file, "w") as f:
                json.dump([object_data], f, indent=2)
            print(f"物体 {id} 的数据已保存到 {output_file} (空文件初始化)")


def main_convert(classify=True):
    # 因为这里是直接调用函数的所以它这个上面的如果写死全局变量的话它是不会更新的所以只能放在函数里
    base_video_path = "processed_video_gradio"
    image_width = 768
    image_height = 1024
    base_path = "runs/track"
    track_data_path = os.path.join(get_latest_folder(base_path), "labels")
    track_base_path = get_latest_folder(base_path)
    # result
    initial_result_directory = "initial_result"
    initial_result_path = os.path.join(track_base_path, initial_result_directory)
    os.makedirs(initial_result_path, exist_ok=True)
    # video
    video_path, video_name = find_video_files(track_base_path)
    base_name, _ = os.path.splitext(video_name)
    new_video_path =os.path.join(base_video_path, f"{base_name}.mp4")
    if classify:
        model_e = efficientnet_b1(weights=EfficientNet_B1_Weights.DEFAULT)
        model_e.classifier[1] = nn.Linear(model_e.classifier[1].in_features, 2)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        model_e = model_e.to(device)
        model_e.load_state_dict(
            torch.load("best_model (10).pth", map_location=device)
        )  # without_generate.pth  best_model (10).pth
        transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),  # 调整图像大小
                transforms.ToTensor(),  # 转换为Tensor
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),  # 归一化
            ]
        )
        model_e.eval()  # 设置模型为推理模式
    else:
        model_e = None
        device = None
        transform = None
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
        print(f"path: {file_path}")
        print(f"正在处理第 {index + 1} 帧的检测结果")
        # print(f"数据：{detection_results}")
        convert_results(
            detection_results,
            image_width,
            image_height,
            initial_result_path,
            index + 1,
            new_video_path,
            classify,
            model_e,
            device,
            transform,
        )


if __name__ == "__main__":
    main_convert()
