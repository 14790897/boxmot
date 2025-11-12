import os
import shutil

import cv2
import numpy as np

from .batch import process_images_in_directory, rename_files_in_directory


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
    """
    使用 FFmpeg 将图片序列转换为视频。
    优先使用 FFmpeg，如果失败则回退到 OpenCV。
    
    :param image_folder: 图片文件夹路径
    :param output_video: 输出视频路径
    :param frame_rate: 帧率（默认 25）
    """
    # 获取目录下的所有图片文件并排序
    images = [
        img
        for img in os.listdir(image_folder)
        if img.endswith((".png", ".jpg", ".jpeg"))
    ]
    images.sort()  # 确保按文件名排序
    
    if not images:
        print(f"Error: No images found in {image_folder}")
        return
    
    print(f"Found {len(images)} images to convert to video")
    
    # 尝试使用 FFmpeg
    try:
        import subprocess

        # 创建临时文件列表
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            list_file = f.name
            for img in images:
                # FFmpeg concat 格式需要每行写入 "file 'path'"
                img_path = os.path.join(image_folder, img)
                # 使用绝对路径并转换为正斜杠
                abs_path = os.path.abspath(img_path).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")
                # 每张图片显示的时长 = 1/帧率
                f.write(f"duration {1.0/frame_rate}\n")
            # 最后一张图片需要再写一次（FFmpeg concat 要求）
            if images:
                last_img_path = os.path.abspath(os.path.join(image_folder, images[-1])).replace('\\', '/')
                f.write(f"file '{last_img_path}'\n")
        
        # 使用 FFmpeg concat demuxer
        ffmpeg_command = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-y",
            output_video
        ]
        
        result = subprocess.run(
            ffmpeg_command,
            capture_output=True,
            text=True,
            check=True
        )
        
        # 删除临时文件
        os.remove(list_file)
        
        print(f"Video saved as {output_video} (using FFmpeg)")
        return
        
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg conversion failed: {e}")
        print(f"FFmpeg stderr: {e.stderr}")
        print("\nFalling back to OpenCV method...")
        if 'list_file' in locals() and os.path.exists(list_file):
            os.remove(list_file)
        
    except FileNotFoundError:
        print("FFmpeg not found in system PATH.")
        print("Falling back to OpenCV method...")
    
    except Exception as e:
        print(f"Unexpected error with FFmpeg: {e}")
        print("Falling back to OpenCV method...")
        if 'list_file' in locals() and os.path.exists(list_file):
            os.remove(list_file)
    
    # 回退到 OpenCV 方法
    _images_to_video_opencv(image_folder, images, output_video, frame_rate)


def _images_to_video_opencv(image_folder, images, output_video, frame_rate):
    """
    使用 OpenCV 将图片序列转换为视频的备用方法。
    
    :param image_folder: 图片文件夹路径
    :param images: 已排序的图片文件名列表
    :param output_video: 输出视频路径
    :param frame_rate: 帧率
    """
    # 读取第一张图片来获取视频的宽度和高度
    first_image_path = os.path.join(image_folder, images[0])
    first_image = cv2.imread(first_image_path)
    
    if first_image is None:
        print(f"Error: Cannot read first image {first_image_path}")
        return
    
    height, width, layers = first_image.shape

    # 尝试使用不同的编码器
    codecs = [("avc1", "H.264"), ("mp4v", "MPEG-4"), ("h264", "H.264")]
    video = None
    
    for codec, codec_name in codecs:
        try:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            video = cv2.VideoWriter(output_video, fourcc, frame_rate, (width, height))
            if video.isOpened():
                print(f"Successfully initialized VideoWriter with codec: {codec} ({codec_name})")
                break
            else:
                video.release()
                video = None
        except Exception as e:
            print(f"Failed to use codec {codec}: {e}")
            continue
    
    if video is None or not video.isOpened():
        print("Error: Failed to initialize VideoWriter with any codec.")
        return

    # 将每一张图片写入视频
    frame_count = 0
    for image in images:
        image_path = os.path.join(image_folder, image)
        img = cv2.imread(image_path)
        if img is not None:
            video.write(img)
            frame_count += 1
        else:
            print(f"Warning: Could not read image {image_path}")

    # 释放视频文件
    video.release()
    print(f"OpenCV conversion complete. Processed {frame_count}/{len(images)} frames.")
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
