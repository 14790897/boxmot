import cv2
import os, shutil
from .x_batch import (
    process_images_in_directory,
    rename_files_in_directory,
    tiff_to_jpeg,
)


def images_to_video(image_folder, output_video, frame_rate=30):
    # 获取目录下的所有图片文件并排序
    images = [
        img
        for img in os.listdir(image_folder)
        if img.endswith((".png", ".jpg", ".jpeg"))
    ]
    images.sort()  # 确保按文件名排序
    # images = images[497:1000]  # 从第1000张开始取500张图片

    # 如果目录下没有足够的图片，报错退出
    if len(images) < 250:
        print(
            f"Error: Found only {len(images)} images in the range, need at least 500 images."
        )
        return

    # 读取第一张图片来获取视频的宽度和高度
    first_image_path = os.path.join(image_folder, images[0])
    first_image = cv2.imread(first_image_path)
    height, width, layers = first_image.shape

    # 初始化视频编码器（这里使用 MJPEG 编码，保存为 .avi 格式）
    fourcc = cv2.VideoWriter_fourcc(*"h264")
    video = cv2.VideoWriter(output_video, fourcc, frame_rate, (width, height))

    # 将每一张图片写入视频
    for image in images:
        image_path = os.path.join(image_folder, image)
        img = cv2.imread(image_path)
        video.write(img)

    # 释放视频文件
    video.release()
    print(f"Video saved as {output_video}")


if __name__ == "__main__":
    input_directory = r"650-1\x1"  # 替换为实际的图像目录路径  "550-y\Y2-550\相机No.1_C001H001S0001" "550-y\Y1-550\C001H001S0001"
    output_directory = r"processed_x1_750"  # 自定义输出目录
    jpeg_directory = "jpeg_x"
    # 如果目标目录存在，删除它
    if os.path.exists(output_directory):
        print(f"Deleting existing output directory: {output_directory}")
        shutil.rmtree(output_directory)
    if os.path.exists(jpeg_directory):
        print(f"Deleting existing output directory: {jpeg_directory}")
        shutil.rmtree(jpeg_directory)
    rename_files_in_directory(input_directory)
    tiff_to_jpeg(input_directory, jpeg_directory)
    process_images_in_directory(jpeg_directory, output_directory)
    # 设置图片目录和输出视频路径
    frame_rate = 20  # 每秒帧数
    output_name = input_directory.replace("\\", "-").replace("/", "-")

    # 设置图片目录和输出视频路径
    output_video = f"{input_directory}/{output_name}_particle_video.mp4"

    images_to_video(output_directory, output_video, frame_rate)
