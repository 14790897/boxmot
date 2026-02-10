"""
删除 runs/track 目录下的所有视频文件
用于释放磁盘空间，视频文件处理后不再需要
"""
import os
import sys


def delete_video_files(base_path, dry_run=False):
    """
    删除指定目录下的所有 _particle_video 的 .mp4/.avi 视频文件
    
    Args:
        base_path: runs/track 的基础路径
        dry_run: 如果为 True，只显示将要删除的文件，不实际删除
    
    Returns:
        str: 删除操作的结果信息（用于 Gradio 界面显示）
    """
    base_path = os.path.normpath(base_path)
    
    if not os.path.exists(base_path):
        return f"✗ 错误：路径不存在: {base_path}"
    
    # 查找所有 _particle_video 的 mp4/avi 文件
    video_files = []
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith("_particle_video.mp4") or file.endswith("_particle_video.avi"):
                video_files.append(os.path.join(root, file))
    
    if not video_files:
        return "✓ 没有找到视频文件"
    
    result_lines = [f"找到 {len(video_files)} 个视频文件:", "=" * 60]
    
    total_size = 0
    deleted_count = 0
    failed_count = 0
    
    for video_file in video_files:
        # 获取文件大小
        try:
            file_size = os.path.getsize(video_file)
            total_size += file_size
            size_mb = file_size / (1024 * 1024)
            
            # 显示相对路径
            rel_path = os.path.relpath(video_file, base_path)
            
            if dry_run:
                result_lines.append(f"[预览] {rel_path} ({size_mb:.2f} MB)")
            else:
                try:
                    os.remove(video_file)
                    result_lines.append(f"✓ 删除成功: {rel_path} ({size_mb:.2f} MB)")
                    deleted_count += 1
                except Exception as e:
                    result_lines.append(f"✗ 删除失败: {rel_path} - {e}")
                    failed_count += 1
        except Exception as e:
            result_lines.append(f"✗ 读取文件信息失败: {video_file} - {e}")
            failed_count += 1
    
    result_lines.append("=" * 60)
    total_size_mb = total_size / (1024 * 1024)
    total_size_gb = total_size / (1024 * 1024 * 1024)
    
    if dry_run:
        result_lines.append(f"\n[预览模式] 将删除 {len(video_files)} 个视频文件")
        result_lines.append(f"总大小: {total_size_mb:.2f} MB ({total_size_gb:.2f} GB)")
        result_lines.append("\n点击 '确认删除视频文件' 按钮来实际删除")
    else:
        result_lines.append("\n删除完成!")
        result_lines.append(f"  成功: {deleted_count} 个")
        result_lines.append(f"  失败: {failed_count} 个")
        result_lines.append(f"  释放空间: {total_size_mb:.2f} MB ({total_size_gb:.2f} GB)")
    
    return "\n".join(result_lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python new/4_delete_videos.py <track_base_path> [--confirm]")
        print("示例: python new/4_delete_videos.py runs/track")
        print("      python new/4_delete_videos.py runs/track --confirm  # 确认删除")
        sys.exit(1)
    
    track_base_path = sys.argv[1]
    confirm = "--confirm" in sys.argv
    
    if confirm:
        print("⚠ 警告：即将删除所有视频文件！")
        result = delete_video_files(track_base_path, dry_run=False)
    else:
        print("预览模式（不会实际删除文件）")
        result = delete_video_files(track_base_path, dry_run=True)
    
    print(result)
