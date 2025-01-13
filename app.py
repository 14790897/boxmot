import gradio as gr
import subprocess
import os, json, shutil, re
from pathlib import Path
from new.batch import process_images_in_directory, rename_files_in_directory
from new.x_batch import tiff_to_jpeg
from new.y_make_images_2_video import images_to_video, delete_invalid_jpg_files
from new.x_make_images_2_video import images_to_video as x_images_to_video

# 视频输出目录
base_path = r"runs\detect"
initial_result_directory = "initial_result"


# 获取最新文件夹的函数
def get_latest_folder(base_path):
    entries = [os.path.join(base_path, entry) for entry in os.listdir(base_path)]
    folders = [entry for entry in entries if os.path.isdir(entry)]
    if not folders:
        raise FileNotFoundError(f"No folders found in {base_path}")
    latest_folder = max(folders, key=os.path.getmtime)
    return latest_folder


def remove_chinese(text):
    return re.sub(r"[^\x00-\x7F]", "", text)  # 保留 ASCII 字符


# 子命令处理函数
def process_with_subcommand(
    input_type,
    y_uploaded_video_path=None,
    x_uploaded_video_path=None,
    y_folder_path=None,
    x_folder_path=None,
):
    y_input_video_path = None
    if input_type == "upload video":
        y_input_video_path = str(Path(y_uploaded_video_path))
        x_input_video_path = str(Path(x_uploaded_video_path))

    elif input_type == "upload folder":
        y_input_directory = str(Path(y_folder_path))
        y_output_directory = r"processed_y1_gradio"  # 自定义输出目录
        x_input_directory = str(Path(x_folder_path))
        x_output_directory = r"processed_x1_gradio"  # 自定义输出目录
        rename_files_in_directory(y_input_directory)
        delete_invalid_jpg_files(y_input_directory)
        if os.path.exists(y_output_directory):
            print(f"Deleting existing output directory: {y_output_directory}")
            shutil.rmtree(y_output_directory)
        process_images_in_directory(y_input_directory, y_output_directory)
        frame_rate = 1  # 每秒帧数
        path_parts = os.path.normpath(y_input_directory).split(os.sep)
        # 去除中文字符

        # 处理每个路径部分
        processed_parts = [remove_chinese(part) for part in path_parts]

        last_two_parts = processed_parts[-2:]
        output_name = "-".join(last_two_parts)
        # 设置图片目录和输出视频路径
        output_video = f"{output_name}_particle_video.mp4"
        images_to_video(y_output_directory, output_video, frame_rate)
        y_input_video_path = output_video

        jpeg_directory = "jpeg_x"
        # 如果目标目录存在，删除它
        if os.path.exists(x_output_directory):
            print(f"Deleting existing output directory: {x_output_directory}")
            shutil.rmtree(x_output_directory)
        if os.path.exists(jpeg_directory):
            print(f"Deleting existing output directory: {jpeg_directory}")
            shutil.rmtree(jpeg_directory)
        rename_files_in_directory(x_input_directory)
        tiff_to_jpeg(x_input_directory, jpeg_directory)
        process_images_in_directory(jpeg_directory, x_output_directory)
        x_output_video = f"{output_name}_x_particle_video.mp4"
        images_to_video(x_output_directory, x_output_video, frame_rate)
        x_input_video_path = x_output_video

    y_command = [
        "python",
        "tracking/track.py",
        "--yolo-model",
        "yolov8-particle-best.pt",  # 使用的 YOLO 模型
        "--source",
        y_input_video_path,  # 输入视频路径
        "--save",  # 保存结果
        "--save-txt",  # 保存文本文件
        "--save-id-crops",  # 保存裁剪后的图像
        "--tracking-method",
        "bytetrack",  # 跟踪方法
        "--conf",
        "0.1",  # 置信度阈值
        "--iou",
        "0.1",  # IOU 阈值
    ]
    x_command = [
        "python",
        "tracking/track.py",
        "--yolo-model",
        "yolov8_best.pt",  # 使用的 YOLO 模型
        "--source",
        x_input_video_path,  # 输入视频路径
        "--save",  # 保存结果
        "--save-txt",  # 保存文本文件
        "--save-id-crops",  # 保存裁剪后的图像
        "--conf",
        "0.1",  # 置信度阈值
        "--iou",
        "0.1",  # IOU 阈值
    ]
    try:
        subprocess.run(y_command, check=True)
        subprocess.run(x_command, check=True)
    except subprocess.CalledProcessError as e:
        return f"Error during processing: {e}"

    output_path = os.path.join(
        get_latest_folder(base_path),
        os.path.basename(y_input_video_path),
    )
    return output_path


def post_process():
    scripts = [
        [
            "python",
            "new/convert.py",
        ],
        [
            "python",
            "new/1_extract.py",
        ],
        [
            "python",
            "new/3_images_x.py",
        ],
        [
            "python",
            "new/4_end.py",
        ],
        ["python", "new/4_end.py"],
    ]
    for script in scripts:
        try:
            print(f"正在执行脚本: {script[1]}...")
            result = subprocess.run(script, check=True, capture_output=False, text=True)
            print(f"脚本 {script[1]} 执行完成，输出:\n{result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"脚本 {script[1]} 执行失败，错误:\n{e.stderr}")
            break
    calculation_results_path = os.path.join(
        initial_result_directory, "calculation_results.json"
    )
    # stats_file_path = os.path.join(initial_result_directory, "all_stats.json")
    if os.path.exists(calculation_results_path):
        try:
            with open(calculation_results_path, "r") as stats_file:
                content = json.load(stats_file)  # 解析 JSON 数据
                return json.dumps(content, ensure_ascii=False, indent=4)
        except json.JSONDecodeError:
            return "JSON decoding error. The file content might be invalid."
    else:
        return f"File {calculation_results_path} does not exist."


# 创建 Gradio 界面
with gr.Blocks() as demo:
    gr.Markdown("# 视频处理界面")

    # 动态显示输入组件
    def toggle_inputs(input_type):
        if input_type == "upload video":
            return (
                gr.update(visible=True),
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
            )
        elif input_type == "upload folder":
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(visible=True),
            )

    with gr.Row():
        with gr.Column(scale=1):  # 左侧视频框
            # video_input = gr.Video(label="原始视频", interactive=True)
            # 用户选择输入类型
            input_type = gr.Radio(
                ["upload video", "upload folder"], label="select input type"
            )

            # 上传视频组件
            y_uploaded_video = gr.Video(label="y upload video", visible=False)
            x_uploaded_video = gr.Video(label="x upload video", visible=False)
            # 输入文件夹路径组件
            y_folder_input = gr.Textbox(label="y_folder_input", visible=False)
            x_folder_input = gr.Textbox(label="x_folder_input", visible=False)
            input_type.change(
                fn=toggle_inputs,
                inputs=[input_type],
                outputs=[
                    y_uploaded_video,
                    x_uploaded_video,
                    y_folder_input,
                    x_folder_input,
                ],
            )
        with gr.Column(scale=1):  # 右侧视频框
            video_output = gr.Video(label="处理后的视频")

    process_button = gr.Button("开始处理")
    post_process_button = gr.Button("后处理")
    text_output = gr.Textbox(label="输出结果")
    post_process_button.click(fn=post_process, inputs=None, outputs=text_output)
    process_button.click(
        fn=process_with_subcommand,
        inputs=[
            input_type,
            y_uploaded_video,
            x_uploaded_video,
            y_folder_input,
            x_folder_input,
        ],
        outputs=video_output,
    )
    # 上传处理后的视频的按钮
    y_uploaded_video = gr.File(
        label="上传处理后的视频", file_types=[".mp4", ".avi", ".mov"]
    )
    y_uploaded_video.change(
        fn=lambda x: x, inputs=y_uploaded_video, outputs=video_output
    )
demo.launch(debug=True)
