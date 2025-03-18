import cv2
import os
import pandas as pd
import natsort  # 导入自然排序库

# 标注数据的文本文件路径
annotation_file = r"C:\git-program\particle_detect\particle_auto_measure\boxmot\assets\MOT17-mini\train\275_particle\gt\gt.txt"  # 替换为你的标注文件路径

image_folder = r"C:\git-program\particle_detect\particle_auto_measure\boxmot\assets\MOT17-mini\train\275_particle\img1"  # 替换为你的输入视频路径
output_folder = r"C:\git-program\particle_detect\particle_auto_measure\boxmot\assets\MOT17-mini\train\275_particle\output_frames"  # 替换为保存输出帧的文件夹路径

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 从文本文件读取数据
df = pd.read_csv(
    annotation_file,
    header=None,
    names=[
        "frame_id",
        "object_id",
        "x",
        "y",
        "width",
        "height",
        "confidence",
        "class_id",
        "visible",
    ],
)

# 获取所有图片文件名，并按自然顺序排序
image_files = natsort.natsorted(os.listdir(image_folder))  # 使用自然排序

frame_id = 1

# 遍历图片目录中的每一帧
for image_file in image_files:
    # 构造图片路径
    image_path = os.path.join(image_folder, image_file)

    # 读取当前帧图片
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Error: Unable to read image {image_path}")
        continue

    # 获取当前帧的标注数据
    frame_data = df[df["frame_id"] == frame_id]

    # 绘制标注框
    for _, row in frame_data.iterrows():
        x, y, w, h = int(row["x"]), int(row["y"]), int(row["width"]), int(row["height"])
        object_id = row["object_id"]

        # 绘制矩形框
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # 标注对象 ID
        cv2.putText(
            frame,
            f"ID: {object_id}",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
        )

    # 保存当前帧
    output_path = os.path.join(output_folder, f"123frame_{frame_id:04d}.png")
    cv2.imwrite(output_path, frame)

    print(f"Processed frame {frame_id}")
    frame_id += 1

print("All frames processed and saved.")

print(f"Output folder: {output_folder}")
