# 运行完成之后对于第二段需要修改目录名字为-2结尾,才能使用第二段的线的计算数据
# 启动方式:
#   1. gradio app.py  - 推荐！支持热重载，修改代码后自动重启
#   2. python app.py  - 普通模式，需要手动重启
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import gradio as gr

from new.batch import process_images_in_directory, rename_files_in_directory
from new.convert import main_convert
from new.process_utils import clear_folder, convert_to_mp4, get_latest_folder
from new.x_batch import tiff_to_jpeg
from new.y_make_images_2_video import delete_invalid_jpg_files, images_to_video

# Import delete_video_files function from 5_delete_videos.py
_delete_videos_spec = importlib.util.spec_from_file_location(
    "delete_videos_module",
    os.path.join(os.path.dirname(__file__), "new", "4_delete_videos.py")
)
if _delete_videos_spec and _delete_videos_spec.loader:
    _delete_videos_module = importlib.util.module_from_spec(_delete_videos_spec)
    _delete_videos_spec.loader.exec_module(_delete_videos_module)
    delete_video_files = _delete_videos_module.delete_video_files
else:
    raise ImportError("Failed to load 4_delete_videos.py module")

# Configuration file path
CONFIG_FILE = "config.json"

# Default configuration
DEFAULT_CONFIG = {
    "yolo_save_directories": {
        "y_track_project": "runs/track",
        "y_track_name": "exp",
        "x_detect_project": "runs_x_me/detect",
        "x_detect_name": "exp",
        "video_output": "processed_video_gradio"
    },
    "processing_options": {
        "max_files_per_folder": None  # None means process all files
    },
    "batch_directories": [
        # Example format:
        # {"y": "path/to/y/dir", "x": "path/to/x/dir"}
    ]
}

def load_config():
    """Load configuration from config.json or create default"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Ensure all required keys exist
                if "yolo_save_directories" not in config:
                    config = DEFAULT_CONFIG.copy()
                else:
                    # Fill in any missing keys with defaults
                    for key, value in DEFAULT_CONFIG["yolo_save_directories"].items():
                        if key not in config["yolo_save_directories"]:
                            config["yolo_save_directories"][key] = value
                    
                    # Ensure processing_options exist
                    if "processing_options" not in config:
                        config["processing_options"] = DEFAULT_CONFIG["processing_options"].copy()
                    else:
                        for key, value in DEFAULT_CONFIG["processing_options"].items():
                            if key not in config["processing_options"]:
                                config["processing_options"][key] = value
                    
                    # Ensure batch_directories exist
                    if "batch_directories" not in config:
                        config["batch_directories"] = DEFAULT_CONFIG["batch_directories"].copy()
                        
                return config
        except Exception as e:
            print(f"Error loading config: {e}, using default configuration")
            return DEFAULT_CONFIG
    else:
        # Create default config file
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config):
    """Save configuration to config.json"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

# Load initial configuration
config = load_config()

# 视频输出目录 - Now loaded from config
base_path = config["yolo_save_directories"]["y_track_project"]
base_x_path = config["yolo_save_directories"]["x_detect_project"]
base_video_path = config["yolo_save_directories"]["video_output"]


def update_config_values(y_track_proj, y_track_name, x_detect_proj, x_detect_name, video_out):
    """Update configuration values"""
    global config, base_path, base_x_path, base_video_path
    
    config["yolo_save_directories"]["y_track_project"] = y_track_proj
    config["yolo_save_directories"]["y_track_name"] = y_track_name
    config["yolo_save_directories"]["x_detect_project"] = x_detect_proj
    config["yolo_save_directories"]["x_detect_name"] = x_detect_name
    config["yolo_save_directories"]["video_output"] = video_out
    
    if save_config(config):
        # Update global variables
        base_path = y_track_proj
        base_x_path = x_detect_proj
        base_video_path = video_out
        return "Configuration saved successfully!"
    else:
        return "Error saving configuration!"

def reset_config():
    """Reset configuration to default values"""
    global config, base_path, base_x_path, base_video_path
    
    config = DEFAULT_CONFIG.copy()
    if save_config(config):
        base_path = config["yolo_save_directories"]["y_track_project"]
        base_x_path = config["yolo_save_directories"]["x_detect_project"]
        base_video_path = config["yolo_save_directories"]["video_output"]
        return (
            base_path,
            config["yolo_save_directories"]["y_track_name"],
            base_x_path,
            config["yolo_save_directories"]["x_detect_name"],
            base_video_path,
            "Configuration reset to default successfully!"
        )
    else:
        return (
            base_path,
            config["yolo_save_directories"]["y_track_name"],
            base_x_path,
            config["yolo_save_directories"]["x_detect_name"],
            base_video_path,
            "Error resetting configuration!"
        )

def get_batch_directories_from_config():
    """
    Get directory pairs from config.json batch_directories field.
    
    Returns:
        List of tuples: [(y_dir, x_dir), ...]
    """
    directory_pairs = []
    
    batch_dirs = config.get("batch_directories", [])
    
    for idx, entry in enumerate(batch_dirs, 1):
        if not isinstance(entry, dict):
            print(f"Warning: Entry {idx} is not a dictionary, skipping")
            continue
            
        y_dir = entry.get("y")
        x_dir = entry.get("x")
        
        if not y_dir or not x_dir:
            print(f"Warning: Entry {idx} missing 'y' or 'x' field, skipping")
            continue
        
        # Validate directories exist
        if os.path.exists(y_dir) and os.path.exists(x_dir):
            directory_pairs.append((y_dir, x_dir))
            print(f"Added directory pair: Y={y_dir}, X={x_dir}")
        else:
            if not os.path.exists(y_dir):
                print(f"Warning: Y directory does not exist: {y_dir}")
            if not os.path.exists(x_dir):
                print(f"Warning: X directory does not exist: {x_dir}")
    
    print(f"Loaded {len(directory_pairs)} directory pairs from config")
    return directory_pairs

def remove_chinese(text):
    return re.sub(r"[^\x00-\x7F]", "", text)  # 保留 ASCII 字符


def auto_name_from_path(path):
    """
    Determine track/detect name automatically from a directory or file path.
    Rules:
      - Look for one of the flow prefixes: 450, 550, 650, 750, 850 in the parent directory name.
      - If the parent directory name indicates a "second" set (contains y2, Y2, _2, -2),
        append "-2" to the base flow (e.g. "550-2").
      - Return None if no flow prefix is found.
    """
    if not path:
        return None
    try:
        # Get the parent directory name (the directory containing the actual data)
        # e.g., from "D:/path/Y1-550/相机No.1_C001H001S0001" -> "Y1-550"
        parent_dir = os.path.basename(os.path.dirname(os.path.normpath(str(path))))
    except Exception:
        return None

    # Search for flow rate in parent directory name
    m = re.search(r"(450|550|650|750|850)", parent_dir)
    if not m:
        return None
    base = m.group(1)

    # detect second dataset marker: Y2, y2, _2, -2 in parent directory name
    if re.search(r"(?:y2|Y2|_2|-2)", parent_dir):
        return f"{base}-2"
    return base


# 子命令处理函数
def process_with_subcommand(
    input_type,
    y_uploaded_video_path=None,
    x_uploaded_video_path=None,
    y_folder_path=None,
    x_folder_path=None,
    classify_checkbox=True,
    batch_file_path=None,
    max_files_per_folder=None,
):
    results = []
    
    # Convert max_files_per_folder: if 0 or None, set to None (process all)
    if max_files_per_folder is not None and max_files_per_folder <= 0:
        max_files_per_folder = None
    
    print(f"Max files per folder: {max_files_per_folder if max_files_per_folder else 'All files'}")
    
    # Check if we should load from config batch_directories
    if input_type == "batch file":
        directory_pairs = get_batch_directories_from_config()
        if not directory_pairs:
            return None, "No valid directory pairs found in config.json batch_directories.", None
        y_folder_list = [pair[0] for pair in directory_pairs]
        x_folder_list = [pair[1] for pair in directory_pairs]
    else:
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
    total_pairs = len(y_folder_list)
    print(f"\n{'='*60}")
    print(f"Starting batch processing: {total_pairs} directory pairs")
    print(f"{'='*60}\n")
    
    for idx, (y_video, x_video) in enumerate(zip(y_folder_list, x_folder_list), 1):
        print(f"\n{'='*60}")
        print(f"Processing pair {idx}/{total_pairs}")
        print(f"Y: {y_video}")
        print(f"X: {x_video}")
        print(f"{'='*60}\n")
        
        y_input_video_path = None
        x_input_video_path = None
        y_input_directory = None
        x_input_directory = None
        
        if input_type == "upload video":
            # guard against None to satisfy static checks
            y_input_video_path = str(Path(y_uploaded_video_path)) if y_uploaded_video_path else None
            x_input_video_path = str(Path(x_uploaded_video_path)) if x_uploaded_video_path else None

        elif input_type == "upload folder" or input_type == "batch file":
            y_input_directory = str(Path(y_video))
            y_output_directory = r"processed_y1_gradio"  # 自定义输出目录
            x_input_directory = str(Path(x_video))
            x_output_directory = r"processed_x1_gradio"  # 自定义输出目录
            rename_files_in_directory(y_input_directory)
            delete_invalid_jpg_files(y_input_directory)
            if os.path.exists(y_output_directory):
                print(f"Deleting existing output directory: {y_output_directory}")
                shutil.rmtree(y_output_directory)
            process_images_in_directory(y_input_directory, y_output_directory, max_files=max_files_per_folder)
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
            process_images_in_directory(jpeg_directory, x_output_directory, max_files=max_files_per_folder)
            x_output_video = os.path.join(
                base_video_path, f"x_{output_name}_particle_video.mp4"
            )
            images_to_video(x_output_directory, x_output_video, frame_rate)
            x_input_video_path = x_output_video

        # Try to automatically determine the --name values from the folder/file names
        # Prefer explicit processed/input directories if available, fall back to the original list entry
        y_candidate = None
        x_candidate = None
        # if upload video, prefer the uploaded path
        if input_type == "upload video":
            y_candidate = y_uploaded_video_path or y_input_video_path or y_video
            x_candidate = x_uploaded_video_path or x_input_video_path or x_video
        else:
            # for upload folder or batch file modes, use the input directory
            y_candidate = y_input_directory or y_input_video_path or y_video
            x_candidate = x_input_directory or x_input_video_path or x_video

        y_auto_name = auto_name_from_path(y_candidate)
        x_auto_name = auto_name_from_path(x_candidate)
        
        print(f"Auto-detected names: Y={y_auto_name}, X={x_auto_name} (from Y={y_candidate}, X={x_candidate})")

        y_name_for_cmd = y_auto_name if y_auto_name else config["yolo_save_directories"]["y_track_name"]
        x_name_for_cmd = x_auto_name if x_auto_name else config["yolo_save_directories"]["x_detect_name"]

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
            "--project",
            config["yolo_save_directories"]["y_track_project"],
            "--name",
            y_name_for_cmd,
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
            config["yolo_save_directories"]["x_detect_project"],
            "--name",
            x_name_for_cmd,
        ]
        try:
            # 确保在项目根目录运行，这样可以导入 boxmot 模块
            project_root = os.path.dirname(os.path.abspath(__file__))
            subprocess.run(y_command, check=True, cwd=project_root)
            subprocess.run(x_command, check=True, cwd=project_root)
        except subprocess.CalledProcessError as e:
            error_msg = f"Error during processing: {e}"
            print(error_msg)
            return None, error_msg, None

        # Safely determine a base name for the output using available candidates
        name_src = None
        if y_input_video_path:
            name_src = y_input_video_path
        elif y_input_directory:
            # If we processed a directory, use that directory name
            name_src = y_input_directory
        else:
            name_src = y_video

        if name_src:
            base_name = os.path.basename(os.path.splitext(str(name_src))[0])
        else:
            base_name = "output"

        output_path = os.path.join(get_latest_folder(base_path), base_name + ".avi")
        output_path = convert_to_mp4(output_path)
        txt_result, log_output = post_process(classify_checkbox)
        results.append((output_path, txt_result, log_output))
        
        print(f"\n{'='*60}")
        print(f"✓ Completed pair {idx}/{total_pairs}")
        print(f"{'='*60}\n")
        
    print(f"\n{'='*60}")
    print(f"Batch processing complete! Processed {total_pairs} directory pairs")
    print(f"{'='*60}\n")
    
    # 清理临时目录
    print("\n清理临时文件...")
    temp_dirs = [
        "processed_y1_gradio",
        "processed_x1_gradio", 
        "jpeg_x"
    ]
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"✓ 已删除临时目录: {temp_dir}")
            except Exception as e:
                print(f"✗ 删除临时目录失败 {temp_dir}: {e}")
    
    print(f"results: {results}")
    if len(results) == 1:
        return results[0][0], results[0][1], results[0][2]
    return None, results, None


def generate_plots():
    """Generate and return plot images"""
    y_track_proj = config["yolo_save_directories"]["y_track_project"]
    
    try:
        print("正在生成粒子运动分析图表...")
        plot_script = [sys.executable, "new/plot_particle.py", "--save", y_track_proj]
        result = subprocess.run(
            plot_script, check=True, capture_output=True, text=True
        )
        print(f"图表生成完成:\n{result.stdout}")
        
        # 返回生成的图表路径
        output_dir = os.path.join(y_track_proj, "plots")
        detailed_plot = os.path.join(output_dir, "particle_analysis_detailed.png")
        summary_plot = os.path.join(output_dir, "particle_analysis_summary.png")
        
        if os.path.exists(detailed_plot) and os.path.exists(summary_plot):
            return detailed_plot, summary_plot, "图表生成成功！"
        else:
            return None, None, "图表文件未找到，请确保有处理数据。"
            
    except subprocess.CalledProcessError as e:
        error_msg = f"图表生成失败，错误:\n{e.stderr}"
        print(error_msg)
        return None, None, error_msg
    except Exception as e:
        error_msg = f"图表生成时发生错误: {e}"
        print(error_msg)
        return None, None, error_msg


def post_process(classify):
    log_output = ""
    # 准备配置路径参数
    y_track_proj = config["yolo_save_directories"]["y_track_project"]
    x_detect_proj = config["yolo_save_directories"]["x_detect_project"]
    video_out = config["yolo_save_directories"]["video_output"]
    
    scripts = [
        [
            sys.executable,
            "new/detect_convert.py",
            x_detect_proj,
            video_out,
        ],
        [
            sys.executable,
            "new/1_extract.py",
            y_track_proj,
        ],
        [
            sys.executable,
            "new/2_images_x.py",
            y_track_proj,
            x_detect_proj,
        ],
        [
            sys.executable,
            "new/3_end.py",
            y_track_proj,
        ],
    ]
    print("正在执行脚本: main_convert")
    main_convert(
        classify,
        y_track_project=y_track_proj,
        video_output=video_out
    )
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
    
    # 生成绘图
    try:
        print("正在生成粒子运动分析图表...")
        plot_script = [sys.executable, "new/plot_particle.py", "--save", y_track_proj]
        result = subprocess.run(
            plot_script, check=True, capture_output=True, text=True
        )
        print(f"图表生成完成:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"图表生成失败，错误:\n{e.stderr}")
    except Exception as e:
        print(f"图表生成时发生错误: {e}")
    
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
    gr.Markdown("# Particle Process Interface")
    os.makedirs(base_video_path, exist_ok=True)

    # Configuration section
    with gr.Accordion("YOLO Save Directory Configuration", open=False):
        gr.Markdown("""
        Configure the save directories for YOLO tracking and detection results.
        All paths are relative to the project root directory.
        """)
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Y-axis Tracking Configuration")
                y_track_project_input = gr.Textbox(
                    label="Y-axis Tracking Project Directory",
                    value=config["yolo_save_directories"]["y_track_project"],
                    placeholder="e.g., runs/track"
                )
                y_track_name_input = gr.Textbox(
                    label="Y-axis Tracking Name",
                    value=config["yolo_save_directories"]["y_track_name"],
                    placeholder="e.g., exp"
                )
            
            with gr.Column():
                gr.Markdown("### X-axis Detection Configuration")
                x_detect_project_input = gr.Textbox(
                    label="X-axis Detection Project Directory",
                    value=config["yolo_save_directories"]["x_detect_project"],
                    placeholder="e.g., runs_x_me/detect"
                )
                x_detect_name_input = gr.Textbox(
                    label="X-axis Detection Name",
                    value=config["yolo_save_directories"]["x_detect_name"],
                    placeholder="e.g., exp"
                )
        
        video_output_input = gr.Textbox(
            label="Video Output Directory",
            value=config["yolo_save_directories"]["video_output"],
            placeholder="e.g., processed_video_gradio"
        )
        
        with gr.Row():
            save_config_button = gr.Button("Save Configuration", variant="primary")
            reset_config_button = gr.Button("Reset to Default")
        
        config_status = gr.Textbox(label="Configuration Status", interactive=False)
        
        # Configuration button actions
        save_config_button.click(
            fn=update_config_values,
            inputs=[
                y_track_project_input,
                y_track_name_input,
                x_detect_project_input,
                x_detect_name_input,
                video_output_input
            ],
            outputs=config_status
        )
        
        reset_config_button.click(
            fn=reset_config,
            inputs=[],
            outputs=[
                y_track_project_input,
                y_track_name_input,
                x_detect_project_input,
                x_detect_name_input,
                video_output_input,
                config_status
            ]
        )

    gr.Markdown("---")  # Separator
    gr.Markdown("## Processing Interface")

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
        elif input_type == "batch file":
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
            )

    with gr.Row():
        with gr.Column(scale=1):  # 左侧视频框
            # video_input = gr.Video(label="原始视频", interactive=True)
            # 用户选择输入类型
            input_type = gr.Radio(
                ["upload video", "upload folder", "batch file"], 
                label="select input type",
                value="batch file"
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

    # 处理选项
    with gr.Row():
        with gr.Column():
            classify_checkbox = gr.Checkbox(label="classify", value=True)
        with gr.Column():
            max_files_input = gr.Number(
                label="Max Files Per Folder",
                value=config["processing_options"]["max_files_per_folder"],
                precision=0,
                minimum=1,
                info="Maximum number of files to process per folder (leave empty or 0 for all files)"
            )
    
    process_button = gr.Button("start process")
    # post_process_button = gr.Button("post process")
    text_output = gr.Textbox(label="result", type="text", lines=10)
    log_output = gr.Textbox(label="log", type="text", lines=10)
    
    # 添加图表生成和显示部分
    gr.Markdown("---")  # Separator
    gr.Markdown("## Particle Analysis Plots")
    
    with gr.Row():
        generate_plot_button = gr.Button("Generate and Display Plots", variant="secondary")
    
    plot_status = gr.Textbox(label="Plot Status", interactive=False)
    
    detailed_plot_output = gr.Image(label="Detailed Analysis (Rotation & Revolution vs Height)", type="filepath")
    summary_plot_output = gr.Image(label="Summary (Flow Rate vs Avg Rotation & Revolution)", type="filepath")
    
    # clear folder
    gr.Markdown("---")  # Separator
    gr.Markdown("## Cleanup Operations")
    
    with gr.Row():
        clear_button = gr.Button("Clear Working Folders", variant="secondary")
        preview_delete_videos_button = gr.Button("Preview Video Files", variant="secondary")
        delete_videos_button = gr.Button("Confirm Delete Videos", variant="stop")
    
    delete_videos_output = gr.Textbox(label="Video Deletion Status", lines=15, interactive=False)
    
    # 绑定按钮事件
    clear_button.click(
        fn=lambda: (
            clear_folder(base_path),
            clear_folder(base_x_path),
            clear_folder(base_video_path),
        ),
        inputs=[],
        outputs=[],
    )
    
    preview_delete_videos_button.click(
        fn=lambda: delete_video_files(config["yolo_save_directories"]["y_track_project"], dry_run=True),
        inputs=[],
        outputs=delete_videos_output,
    )
    
    delete_videos_button.click(
        fn=lambda: delete_video_files(config["yolo_save_directories"]["y_track_project"], dry_run=False),
        inputs=[],
        outputs=delete_videos_output,
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
            gr.Textbox(visible=False),  # batch_file_path not used anymore
            max_files_input,
        ],
        outputs=[video_output, text_output, log_output],
    )
    
    generate_plot_button.click(
        fn=generate_plots,
        inputs=[],
        outputs=[detailed_plot_output, summary_plot_output, plot_status],
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

if __name__ == "__main__":
    # 使用 debug=True 启用调试模式
    # 使用 gradio app.py 命令可以获得热重载功能
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
