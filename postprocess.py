# 用于对结果目录中的所有结果批量重新后处理
import os
import subprocess
import new.process_utils
import sys

scripts = [
    [sys.executable, "new/1_extract.py"],
    # [sys.executable, "new/3_images_x.py"],
    [sys.executable, "new/4_end.py"],
]


def get_subdirectories(root_directory):
    # 只获取当前目录下的子目录（不递归）
    subdirectories = [
        os.path.join(root_directory, name)
        for name in os.listdir(root_directory)
        if os.path.isdir(os.path.join(root_directory, name))
    ]
    return subdirectories


def run_scripts_in_dirs(root_directory):
    subdirectories = get_subdirectories(root_directory)
    for subdir in subdirectories:

        print(f"Processing directory: {subdir}")
        os.environ["LATEST_FOLDER"] = subdir

        # 执行脚本列表
        for script in scripts:
            try:
                # 执行脚本
                print(f"Executing script: {' '.join(script)} in {subdir}")
                result = subprocess.run(script, capture_output=True, text=True)
                # 打印脚本的输出
                print(f"Output:\n{result.stdout}")
                if result.stderr:
                    print(f"Errors:\n{result.stderr}")
                    raise RuntimeError(
                        f"Script {script} failed with error:\n{result.stderr}"
                    )
            except Exception as e:
                print(f"Error executing script {script} in {subdir}: {e}")


# 主程序入口
if __name__ == "__main__":
    root_directory = r"runs\track"  # 替换为实际的根目录路径
    run_scripts_in_dirs(root_directory)
