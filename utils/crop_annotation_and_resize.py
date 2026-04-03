import os
import cv2
import numpy as np


def crop_yolo_annotations(image_path, txt_path, output_dir, target_size=160):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Image not found: {image_path}")
        return
    height, width = img.shape[:2]

    if not os.path.exists(txt_path):
        print(f"Annotation file not found: {txt_path}")
        return

    with open(txt_path, "r") as file:
        count = 0  # 用于命名裁剪出的目标文件
        for line in file:
            parts = line.strip().split()
            if parts:
                class_id = int(parts[0])  # YOLO class ID
                x_center = float(parts[1]) * width
                y_center = float(parts[2]) * height
                box_width = float(parts[3]) * width
                box_height = float(parts[4]) * height

                x_min = int(x_center - box_width / 2)
                y_min = int(y_center - box_height / 2)
                x_max = int(x_center + box_width / 2)
                y_max = int(y_center + box_height / 2)

                # 确保坐标在图像范围内
                x_min = max(0, x_min)
                y_min = max(0, y_min)
                x_max = min(width, x_max)
                y_max = min(height, y_max)

                # 裁剪目标区域
                cropped_img = img[y_min:y_max, x_min:x_max]
                # 调整裁剪后的图像大小
                image = cv2.resize(
                    cropped_img,
                    (target_size, target_size),
                    interpolation=cv2.INTER_LANCZOS4,
                )
                # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                # # 去噪
                # blurred = cv2.GaussianBlur(gray, (5, 5), 0)

                # # 计算图像的灰度直方图
                # min_val = np.min(gray)
                # max_val = np.max(gray)
                # print(f"Gray Min: {min_val}, Gray Max: {max_val}")

                # # 自动设定低阈值和高阈值
                # low_threshold = max(30, min_val + 30)  # 低阈值设为最黑处加上一个偏移量
                # high_threshold = low_threshold * 2  # 高阈值设为低阈值的2倍
                # _, image = cv2.threshold(
                #     blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                # )
                if len(image.shape) == 2:
                    cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
                class_dir = os.path.join(output_dir, f"{class_id}")
                if not os.path.exists(class_dir):
                    os.makedirs(class_dir)

                # 保存裁剪后的目标
                crop_filename = (
                    f"{os.path.splitext(os.path.basename(image_path))[0]}_{count}.png"
                )
                crop_output_path = os.path.join(class_dir, crop_filename)
                cv2.imwrite(crop_output_path, image)
                print(f"Saved cropped object: {crop_output_path}")

                count += 1


def process_images(image_dir, label_dir, output_dir):
    # Create the output directory if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Iterate over all files in the image directory
    for filename in os.listdir(image_dir):
        if filename.endswith(".jpg") or filename.endswith(
            ".png"
        ):  # Check for image files
            image_path = os.path.join(image_dir, filename)
            txt_path = os.path.join(
                label_dir, filename.rsplit(".", 1)[0] + ".txt"
            )  # Assuming txt files have the same base name as images

            crop_yolo_annotations(image_path, txt_path, output_dir)


base_dir = r"yolo_great_particle_data"  # coincide & separation_new   yolo_me efficient_net_data_me   efficient2 yolo_particle_data
image_dir = os.path.join(base_dir, "images")
label_dir = os.path.join(base_dir, "labels")
output_dir = os.path.join(base_dir, "cropped_objects")

# print current path
print(os.getcwd())
process_images(image_dir, label_dir, output_dir)
