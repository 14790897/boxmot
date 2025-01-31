import re

# 你的检测日志
log_data = r"""
video 1/1 (frame 1/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 112.6ms
video 1/1 (frame 2/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 7.1ms
video 1/1 (frame 3/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 8.5ms
video 1/1 (frame 4/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 9.1ms
video 1/1 (frame 5/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 10.0ms
video 1/1 (frame 6/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 14.0ms
video 1/1 (frame 7/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 11.0ms
video 1/1 (frame 8/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 8.7ms
video 1/1 (frame 9/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 5 particles, 7.0ms
video 1/1 (frame 10/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 5 particles, 10.0ms
video 1/1 (frame 11/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 5 particles, 8.5ms
video 1/1 (frame 12/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 5 particles, 9.0ms
video 1/1 (frame 13/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 5 particles, 8.1ms
video 1/1 (frame 14/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 5 particles, 8.0ms
video 1/1 (frame 15/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 5 particles, 13.0ms
video 1/1 (frame 16/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 5 particles, 7.0ms
video 1/1 (frame 17/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 5 particles, 8.0ms
video 1/1 (frame 18/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 5 particles, 11.5ms
video 1/1 (frame 19/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 5 particles, 11.0ms
video 1/1 (frame 20/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 5 particles, 7.5ms
video 1/1 (frame 21/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 8.0ms
video 1/1 (frame 22/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 11.0ms
video 1/1 (frame 23/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 7.5ms
video 1/1 (frame 24/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 9.4ms
video 1/1 (frame 25/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 3 particles, 9.0ms
video 1/1 (frame 26/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 10.8ms
video 1/1 (frame 27/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 12.6ms
video 1/1 (frame 28/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 7.0ms
video 1/1 (frame 29/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 7.5ms
video 1/1 (frame 30/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 11.0ms
video 1/1 (frame 31/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 4 particles, 7.0ms
video 1/1 (frame 32/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 5 particles, 7.5ms
video 1/1 (frame 33/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 6 particles, 8.0ms
video 1/1 (frame 34/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 6 particles, 7.0ms
video 1/1 (frame 35/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 6 particles, 9.8ms
video 1/1 (frame 36/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 6 particles, 9.0ms
video 1/1 (frame 37/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 6 particles, 8.1ms
video 1/1 (frame 38/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 6 particles, 7.0ms
video 1/1 (frame 39/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 6 particles, 7.0ms
video 1/1 (frame 40/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 6 particles, 13.4ms
video 1/1 (frame 41/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 6 particles, 9.0ms
video 1/1 (frame 42/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 6 particles, 8.7ms
video 1/1 (frame 43/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 6 particles, 12.9ms
video 1/1 (frame 44/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 6 particles, 7.0ms
video 1/1 (frame 45/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 6 particles, 7.0ms
video 1/1 (frame 46/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 7 particles, 7.5ms
video 1/1 (frame 47/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 7 particles, 8.2ms
video 1/1 (frame 48/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 7 particles, 12.0ms
video 1/1 (frame 49/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 7 particles, 8.0ms
video 1/1 (frame 50/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 7 particles, 14.0ms
video 1/1 (frame 51/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 7 particles, 15.6ms
video 1/1 (frame 52/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 8 particles, 13.0ms
video 1/1 (frame 53/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 8 particles, 11.0ms
video 1/1 (frame 54/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 8 particles, 12.0ms
video 1/1 (frame 55/55) C:\git-program\particle_detect\particle_auto_measure\boxmot\processed_video_gradio\xy1-550-S11-2_particle_video.mp4: 640x480 8 particles, 8.0ms
"""  # 这里应该放完整的日志

# 使用正则表达式提取 "X particles"
particle_counts = [
    int(match.group(1)) for match in re.finditer(r"(\d+) particles", log_data)
]
time_counts = [float(match.group(1)) for match in re.finditer(r"([\d.]+)ms", log_data)]


# 计算平均粒子数
if particle_counts:
    avg_particles = sum(particle_counts) / len(particle_counts)
    avg_time = sum(time_counts) / len(time_counts) if time_counts else 0
    print(f"📌 平均每张图片的粒子数量: {avg_particles:.2f}")
    print(f"⏳ 平均每帧检测耗时: {avg_time:.2f}ms")
else:
    print("⚠️ 未找到粒子数数据！")
