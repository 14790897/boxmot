import cv2
import os,shutil
from .batch import process_images_in_directory, rename_files_in_directory
import numpy as np

def delete_invalid_jpg_files(folder_path):
    """
    删除文件夹中所有无法打开的 JPG 文件。
    :param folder_path: 图片文件夹路径
    """
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".jpg"):
            file_path = os.path.join(folder_path, filename)
            try:
                # 尝试读取图片
                img = cv2.imdecode(
                    np.fromfile(file=file_path, dtype=np.uint8), cv2.IMREAD_COLOR
                )
                # img = cv2.imread(file_path)
                if img is None:
                    # 如果无法读取，删除文件
                    print(f"Deleting invalid JPG file: {file_path}")
                    os.remove(file_path)
            except Exception as e:
                # 如果读取过程中发生异常，删除文件
                print(f"Error reading file {file_path}. Deleting it. Error: {e}")
                os.remove(file_path)


def images_to_video(image_folder, output_video, frame_rate=25):
    # 这里是全英文路径所以不需要再处理
    # 获取目录下的所有图片文件并排序
    images = [
        img
        for img in os.listdir(image_folder)
        if img.endswith((".png", ".jpg", ".jpeg"))
    ]
    images.sort()  # 确保按文件名排序
    # images = images[1000:1500]  # 从第1000张开始取500张图片

    # 如果目录下没有足够的图片，报错退出
    # if len(images) < 500:
    #     print(
    #         f"Error: Found only {len(images)} images in the range, need at least 500 images."
    #     )
    #     return

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
        # print(f"Writing image {image_path} to video")
        img = cv2.imread(image_path)
        video.write(img)

    # 释放视频文件
    video.release()
    print(f"Video saved as {output_video}")

if __name__ == "__main__":
    input_directory = r"mot_particle\img1"  # 替换为实际的图像目录路径  "550-y\Y2-550\相机No.1_C001H001S0001" "550-y\Y1-550\C001H001S0001"
    output_directory = r"processed_y1_750"  # 自定义输出目录
    rename_files_in_directory(input_directory)
    delete_invalid_jpg_files(input_directory)
    # 如果目标目录存在，删除它
    if os.path.exists(output_directory):
        print(f"Deleting existing output directory: {output_directory}")
        shutil.rmtree(output_directory)
    process_images_in_directory(input_directory, output_directory)
    frame_rate = 1  # 每秒帧数
    path_parts = os.path.normpath(input_directory).split(os.sep)
    last_two_parts = path_parts[-2:]
    output_name = "-".join(last_two_parts)

    # 设置图片目录和输出视频路径
    output_video = os.path.join(input_directory, f"{output_name}_particle_video.mp4")

    images_to_video(output_directory, output_video, frame_rate)
