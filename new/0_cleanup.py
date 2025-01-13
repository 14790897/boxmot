# cleanup.py
# 没什么用

import os
import shutil
import json


def cleanup_if_few_detections(save_dir, threshold=3):
    """
    检查 JSON 文件的条目数量，如果少于 threshold 条，则删除整个文件夹。

    :param save_dir: 文件夹路径
    :param threshold: 删除文件夹的阈值，默认为 3
    """
    json_file_path = os.path.join(save_dir, "initial_data.json")

    if os.path.exists(json_file_path):
        delete = False
        with open(json_file_path, "r") as file:
            try:
                data = json.load(file)
                if len(data) < threshold:
                    delete = True
            except json.JSONDecodeError:
                # 处理 JSON 解码错误的情况
                print(f"无法解析 JSON 文件: {json_file_path}")
                shutil.rmtree(save_dir)
                print(f"由于无法解析，删除文件夹: {save_dir}")
        if delete:
            shutil.rmtree(save_dir)  # 如果条目少于阈值，删除整个文件夹
            print(f"删除文件夹: {save_dir}")


def cleanup_all_dirs(root_dir, threshold=3):
    """
    遍历 root_dir 下的所有子目录，并对每个子目录调用 cleanup_if_few_detections 进行清理。

    :param root_dir: 根目录路径
    :param threshold: 删除文件夹的阈值，默认为 3
    """
    for subdir in os.listdir(root_dir):
        full_path = os.path.join(root_dir, subdir)
        if os.path.isdir(full_path):
            cleanup_if_few_detections(full_path, threshold)


if __name__ == "__main__":
    cleanup_all_dirs("initial_result", threshold=3)
