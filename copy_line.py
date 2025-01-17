def append_last_line(file_path, num_lines=900):
    """
    将文本文件的最后一行复制指定次数，并追加到文件末尾。
    
    Args:
        file_path (str): 文本文件路径。
        num_lines (int): 要复制的行数，默认为900。
    """
    try:
        # 打开文件读取最后一行
        with open(file_path, "r") as f:
            lines = f.readlines()
            if not lines:
                print("文件为空，无法操作。")
                return
            last_line = lines[-1].strip()  # 获取最后一行并移除换行符

        # 将最后一行复制并追加到文件
        with open(file_path, "a") as f:
            for _ in range(num_lines):
                f.write(last_line + "\n")
        
        print(f"成功将最后一行复制并追加了 {num_lines} 次。")
    
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到，请检查路径。")
    except Exception as e:
        print(f"发生错误：{e}")

# 使用示例
file_path = r"runs\dets_n_embs\yolov8-particle-best\embs\osnet_x0_25_msmt17\mot_particle-1-yolov7.txt"  # 替换为你的文本文件路径
append_last_line(file_path, num_lines=(916-643))
