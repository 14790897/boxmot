import json
import os
import time

import cv2
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

from .process_utils import extract_frame, find_video_files, get_latest_folder

times = []  # 存储所有运行时间
missing_id_count = 0  # 统计缺少 ID 的检测结果数量


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
    global missing_id_count  # 声明使用全局变量
    
    for index, result in enumerate(detection_results):
        category = int(result[0])  # 物体类别
        x_center = float(result[1]) * image_width  # 中心点 x 坐标
        y_center = float(result[2]) * image_height  # 中心点 y 坐标
        width = float(result[3]) * image_width  # 物体的宽度
        height = float(result[4]) * image_height  # 物体的高度
        try:
            id = int(result[5])  # 物体 ID
        except IndexError:
            id = 99999
            missing_id_count += 1  # 统计缺少 ID 的数量
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
        )  # cv的frame是从0开始的，但是yolo检测结果是从1开始的
        classify_cat = None
        if classify:
            # 转换 NumPy 数组为 PIL 图像
            output_image_pil = Image.fromarray(
                cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB)
            )

            # 然后进行转换
            cropped_image = output_image_pil.crop((x1, y1, x2, y2))
            transformed_image = transform(cropped_image).unsqueeze(0).to(device)
            start_time = time.time()
            outputs = model_e(transformed_image)
            end_time = time.time()
            elapsed_time = end_time - start_time
            times.append(elapsed_time)  # 记录时间
            # print(f"目标检测耗时: {elapsed_time:.4f} 秒")
            confidences = torch.softmax(outputs, dim=1)  # 计算每个类别的置信度
            _, classify_cat = confidences.max(1)  # 获取每个图像的最高置信度
            classify_cat = classify_cat.item()  # 将 Tensor 转换为 Python 标量
            object_data["Category"] = classify_cat
            # print("classify_cat:", classify_cat)
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


def main_convert(classify=True, y_track_project=None, video_output=None):
    # 因为这里是直接调用函数的所以它这个上面的如果写死全局变量的话它是不会更新的所以只能放在函数里
    # 使用传入的参数或默认值
    global missing_id_count  # 声明使用全局变量
    missing_id_count = 0  # 重置计数器
    
    base_video_path = video_output if video_output else "processed_video_gradio"
    image_width = 768
    image_height = 1024
    base_path = y_track_project if y_track_project else "runs/track"
    track_data_path = os.path.join(get_latest_folder(base_path), "labels")
    track_base_path = get_latest_folder(base_path) # 获取最新的track文件夹
    # result
    initial_result_directory = "initial_result"
    initial_result_path = os.path.join(track_base_path, initial_result_directory)
    os.makedirs(initial_result_path, exist_ok=True)
    # video
    video_path, video_name = find_video_files(track_base_path)
    base_name, _ = os.path.splitext(video_name)
    new_video_path = os.path.join(base_video_path, f"{base_name}.mp4")
    if classify:
        # ========================================
        # 模型初始化：EfficientNet-V2-S
        # ========================================
        # EfficientNet-V2 是 EfficientNet 的改进版本，主要优化：
        # 1. 训练速度更快（比 EfficientNet-B1 快 5-11 倍）
        # 2. 参数效率更高（更少的参数达到更好的精度）
        # 3. 使用 Fused-MBConv 模块替代部分 MBConv，减少内存访问
        # 4. 渐进式学习策略，动态调整图像大小和正则化
        
        # 加载预训练模型（在 ImageNet-1K 数据集上训练的权重）
        # ImageNet1K_V1 是在 ImageNet-1K (1000类) 数据集上训练的权重
        model_e = models.efficientnet_v2_s(
            weights=models.EfficientNet_V2_S_Weights.IMAGENET1K_V1
        )
        
        # ========================================
        # 修改分类器层（迁移学习）
        # ========================================
        # EfficientNet-V2 的结构：
        # - features: 特征提取层（卷积层）
        # - avgpool: 全局平均池化层
        # - classifier: 分类器（Sequential 包含 Dropout 和 Linear）
        #   - classifier[0]: Dropout(p=0.2) - 防止过拟合
        #   - classifier[1]: Linear(in_features=1280, out_features=1000) - 全连接层
        
        # 获取原始全连接层的输入特征数（1280）
        in_features = model_e.classifier[1].in_features
        
        # 替换最后的全连接层为 2 分类（NUM_CLASSES=2）
        # 保留预训练的特征提取能力，只重新训练分类器
        NUM_CLASSES = 2  # 二分类任务（例如：柱段/球段）
        model_e.classifier[1] = nn.Linear(in_features, NUM_CLASSES)
        
        # ========================================
        # 设备配置（GPU/CPU）
        # ========================================
        # 检测是否有可用的 CUDA GPU
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 将模型转移到指定设备（GPU 加速推理）
        model_e = model_e.to(device)
        
        # ========================================
        # 加载训练好的权重
        # ========================================
        # 加载微调后的模型权重（在你的数据集上训练的）
        model_e.load_state_dict(
            torch.load("new_best_model.pth", map_location=device)
        )  # map_location 确保权重加载到正确的设备
        
        # ========================================
        # 图像预处理转换
        # ========================================
        # 定义图像预处理管道，与训练时保持一致
        transform = transforms.Compose(
            [
                # 1. 调整图像大小为 224x224（EfficientNet-V2-S 的输入尺寸）
                transforms.Resize((224, 224)),
                
                # 2. 转换为 PyTorch Tensor（[0, 255] -> [0.0, 1.0]）
                transforms.ToTensor(),
                
                # 3. 标准化（使用 ImageNet 的均值和标准差）
                #    mean=[0.485, 0.456, 0.406] - RGB 三通道的均值
                #    std=[0.229, 0.224, 0.225]  - RGB 三通道的标准差
                #    这与预训练模型的输入要求一致
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], 
                    std=[0.229, 0.224, 0.225]
                ),
            ]
        )
        
        # ========================================
        # 设置为评估模式
        # ========================================
        # eval() 模式会：
        # - 禁用 Dropout（p=0.2 的丢弃层不再随机丢弃）
        # - 冻结 Batch Normalization（使用训练时的统计量）
        # - 确保推理时的确定性和一致性
        model_e.eval()
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
        # print(f"path: {file_path}")
        # print(f"正在处理第 {last_number} 帧的检测结果")
        # print(f"数据：{detection_results}")
        last_number = int(filename.split("_")[-1].split(".")[0])
        convert_results(
            detection_results,
            image_width,
            image_height,
            initial_result_path,
            last_number,
            new_video_path,
            classify,
            model_e,
            device,
            transform,
        )
        average_time = sum(times) / len(times)
        if index % 100 == 0:
            print(f"平均目标分类时间: {average_time:.6f} 秒")
    
    # 处理完成后显示统计信息
    total_frames = index + 1
    print("\n✓ 检测结果转换完成")
    print(f"  - 总帧数: {total_frames}")
    if missing_id_count > 0:
        print(f"  - ⚠️  缺少 ID 的检测结果: {missing_id_count} 个（已分配 ID=99999）")
    else:
        print("  - ✓ 所有检测结果都有 ID")


if __name__ == "__main__":
    main_convert()
