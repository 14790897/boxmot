# 运行完成之后对于第二段需要修改目录名字为-2结尾,才能使用第二段的线的计算数据
# gradio app.py支持热重载,python app.py不支持
import gradio as gr
import subprocess
import os, json, shutil, re
import sys
import itertools

from pathlib import Path
from new.batch import process_images_in_directory, rename_files_in_directory
from new.x_batch import tiff_to_jpeg
from new.y_make_images_2_video import images_to_video, delete_invalid_jpg_files
from new.x_make_images_2_video import images_to_video as x_images_to_video
from new.process_utils import convert_to_mp4, get_latest_folder, clear_folder
from new.convert import main_convert

# 视频输出目录
base_path = r"runs/track"
base_x_path = "runs_x_me/detect"
base_video_path = "processed_video_gradio"


def remove_chinese(text):
    return re.sub(r"[^\x00-\x7F]", "", text)  # 保留 ASCII 字符


# 子命令处理函数
def process_with_subcommand(
    input_type,
    y_uploaded_video_path=None,
    x_uploaded_video_path=None,
    y_folder_path=None,
    x_folder_path=None,
    classify_checkbox=True,
):
    results = []
    y_folder_list = (
        [p.strip() for p in y_folder_path.split(",") if p.strip()]
        if y_folder_path
        else []
    )
    x_folder_list = (
        [p.strip() for p in x_folder_path.split(",") if p.strip()]
        if x_folder_path
        else []
    )
    print(f"y_folder_list: {y_folder_list}")
    for y_video, x_video in zip(y_folder_list, x_folder_list):
        y_input_video_path = None
        x_input_video_path = None
        if input_type == "upload video":
            y_input_video_path = str(Path(y_uploaded_video_path))
            x_input_video_path = str(Path(x_uploaded_video_path))

        elif input_type == "upload folder":
            y_input_directory = str(Path(y_video))
            y_output_directory = r"processed_y1_gradio"  # 自定义输出目录
            x_input_directory = str(Path(x_video))
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
            output_video = os.path.join(
                base_video_path, f"{output_name}_particle_video.mp4"
            )
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
            x_output_video = os.path.join(
                base_video_path, f"x_{output_name}_particle_video.mp4"
            )
            images_to_video(x_output_directory, x_output_video, frame_rate)
            x_input_video_path = x_output_video

        y_command = [
            sys.executable,
            "tracking/track.py",
            "--yolo-model",
            "yolov8-particle-best.pt",  # 使用的 YOLO 模型
            "--source",
            y_input_video_path,  # 输入视频路径
            "--save",  # 保存结果
            "--save-txt",  # 保存文本文件
            "--tracking-method",
            "bytetrack",  # 跟踪方法
            "--conf",
            "0.01",  # 置信度阈值
            "--iou",
            "0.01",  # IOU 阈值
            # "--name",
            # y_input_video_path,
        ]
        x_command = [
            sys.executable,
            "tracking/track.py",
            "--yolo-model",
            "yolov8_best.pt",  # 使用的 YOLO 模型
            "--source",
            x_input_video_path,  # 输入视频路径
            "--save",  # 保存结果
            "--save-txt",  # 保存文本文件
            "--conf",
            "0.01",
            "--iou",
            "0.01",  # IOU 阈值
            "--project",
            base_x_path,
        ]
        try:
            subprocess.run(y_command, check=True)
            subprocess.run(x_command, check=True)
        except subprocess.CalledProcessError as e:
            return f"Error during processing: {e}"

        output_path = os.path.join(
            get_latest_folder(base_path),
            os.path.basename(os.path.splitext(y_input_video_path)[0] + ".avi"),
        )
        output_path = convert_to_mp4(output_path)
        txt_result, log_output = post_process(classify_checkbox)
        results.append((output_path, txt_result, log_output))
    print(f"results: {results}")
    if len(results) == 1:
        return results[0][0], results[0][1], results[0][2]
    return None, results, None


def post_process(classify):
    log_output = ""
    scripts = [
        [
            sys.executable,
            "new/detect_convert.py",
        ],
        [
            sys.executable,
            "new/1_extract.py",
        ],
        [
            sys.executable,
            "new/3_images_x.py",
        ],
        [
            sys.executable,
            "new/4_end.py",
        ],
    ]
    print("正在执行脚本: main_convert")
    main_convert(classify)
    for script in scripts:
        try:
            print(f"正在执行脚本: {script[1]}...")
            if script[1] == "new/1_extract.py":
                result = subprocess.run(
                    script, check=True, capture_output=True, text=True
                )
                log_output = f"{result.stdout}"
            else:
                result = subprocess.run(
                    script, check=True, capture_output=False, text=True
                )
            print(f"脚本 {script[1]} 执行完成，输出:\n{result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"脚本 {script[1]} 执行失败，错误:\n{e.stderr}")
            break
    latest_folder_path = get_latest_folder(base_path)
    initial_result_directory = os.path.join(latest_folder_path, "initial_result")
    calculation_results_path = os.path.join(
        initial_result_directory, "calculation_results.json"
    )
    # stats_file_path = os.path.join(initial_result_directory, "all_stats.json")
    if os.path.exists(calculation_results_path):
        try:
            with open(calculation_results_path, "r") as stats_file:
                content = json.load(stats_file)  # 解析 JSON 数据
                return json.dumps(content, ensure_ascii=False, indent=4), log_output
        except json.JSONDecodeError:
            return "JSON decoding error. The file content might be invalid."
    else:
        return (
            f"File {calculation_results_path} does not exist.",
            f"File {calculation_results_path} does not exist.",
        )


# 创建 Gradio 界面
with gr.Blocks() as demo:
    gr.Markdown("# particle process interface")
    os.makedirs(base_video_path, exist_ok=True)

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
            y_folder_input.change(
                fn=lambda y: y,  # lambda 直接返回输入值
                inputs=y_folder_input,  # 输入 y_folder_input 的值
                outputs=x_folder_input,  # 输出到 x_folder_input
            )
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
            video_output = gr.Video(label="processed video")

    classify_checkbox = gr.Checkbox(label="classify", value=True)
    process_button = gr.Button("start process")
    # post_process_button = gr.Button("post process")
    text_output = gr.Textbox(label="result", type="text", lines=10)
    log_output = gr.Textbox(label="log", type="text", lines=10)
    # clear folder
    clear_button = gr.Button("clear folder")
    clear_button.click(
        fn=lambda: (
            clear_folder(base_path),
            clear_folder(base_x_path),
            clear_folder(base_video_path),
        ),
        inputs=[],
        outputs=[],
    )
    process_button.click(
        fn=process_with_subcommand,
        inputs=[
            input_type,
            y_uploaded_video,
            x_uploaded_video,
            y_folder_input,
            x_folder_input,
            classify_checkbox,
        ],
        outputs=[video_output, text_output, log_output],
    )
    # post_process_button.click(
    #     fn=post_process, inputs=classify_checkbox, outputs=text_output
    # )
    # 上传处理后的视频的按钮
    # y_uploaded_video = gr.File(
    #     label="上传处理后的视频", file_types=[".mp4", ".avi", ".mov"]
    # )
    # y_uploaded_video.change(
    #     fn=lambda x: x, inputs=y_uploaded_video, outputs=video_output
    # )
demo.launch(debug=True)
# H:\shnu-graduation\alldata\all\20180117-hfq-y\y1-450\相机No.1_C001H001S0001,H:\shnu-graduation\alldata\all\20180117-hfq-y\y1-550\相机No.1_C001H001S0001,H:\shnu-graduation\alldata\all\20180117-hfq-y\y1-650\相机No.1_C001H001S0001,H:\shnu-graduation\alldata\all\20180117-hfq-y\y1-750\相机No.1_C001H001S0001,H:\shnu-graduation\alldata\all\20180117-hfq-y\y1-850\相机No.1_C001H001S0001,H:\shnu-graduation\alldata\all\20180117-hfq-y\Y2-450\相机No.1_C001H001S0001,H:\shnu-graduation\alldata\all\20180117-hfq-y\Y2-550\相机No.1_C001H001S0001,H:\shnu-graduation\alldata\all\20180117-hfq-y\Y2-650\相机No.1_C001H001S0001,H:\shnu-graduation\alldata\all\20180117-hfq-y\Y2-750\相机No.1_C001H001S0001,H:\shnu-graduation\alldata\all\20180117-hfq-y\Y2-850\相机No.1_C001H001S0001,H:\shnu-graduation\alldata\all\20180117-hfq-y\Y1-750\相机No.1_C001H001S0002

# H:\shnu-graduation\alldata\all\20180117hefengqin-x\x1-450\Acq_A_001,H:\shnu-graduation\alldata\all\20180117hefengqin-x\x1-550\Acq_A_001,H:\shnu-graduation\alldata\all\20180117hefengqin-x\x1-650\Acq_A_002,H:\shnu-graduation\alldata\all\20180117hefengqin-x\x1-750\Acq_A_001,H:\shnu-graduation\alldata\all\20180117hefengqin-x\x1-850\Acq_A_001,H:\shnu-graduation\alldata\all\20180117hefengqin-x\x2-450\Acq_A_001,H:\shnu-graduation\alldata\all\20180117hefengqin-x\x2-550\Acq_A_001,H:\shnu-graduation\alldata\all\20180117hefengqin-x\x2-650\Acq_A_001,H:\shnu-graduation\alldata\all\20180117hefengqin-x\x2-750\Acq_A_001,H:\shnu-graduation\alldata\all\20180117hefengqin-x\x2-850\Acq_A_001,H:\shnu-graduation\alldata\all\20180117hefengqin-x\x1-750\Acq_A_002


# H:\shnu-graduation\alldata\all\20180117-hfq-y\Y1-550\相机No.1_C001H001S0002,H:\shnu-graduation\alldata\all\20180117-hfq-y\Y1-850\相机No.1_C001H001S0002
# H:\shnu-graduation\alldata\all\20180117hefengqin-x\x1-550\Acq_A_002,H:\shnu-graduation\alldata\all\20180117hefengqin-x\x1-850\Acq_A_002
# H:\shnu-graduation\alldata\all\20180117-hfq-y\Y2-850\相机No.1_C001H001S0002
# H:\shnu-graduation\alldata\all\20180117hefengqin-x\x2-850\Acq_A_002
# H:\shnu-graduation\alldata\all\20180117-hfq-y\Y2-750\相机No.1_C001H001S0002
# H:\shnu-graduation\alldata\all\20180117hefengqin-x\x2-750\Acq_A_002

# H:\shnu-graduation\alldata\all\20180117-hfq-y\Y1-450\相机No.1_C001H001S0002
# H:\shnu-graduation\alldata\all\20180117hefengqin-x\x1-450\Acq_A_002
