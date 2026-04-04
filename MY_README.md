# Particle Auto Measure - BoxMOT

## 相关训练代码

gan: https://www.kaggle.com/code/liuweiqing2/sagan-particle
分类：https://www.kaggle.com/code/liuweiqing2/efficient-net-nice
识别: https://www.kaggle.com/code/liuweiq/yolov8-v9-v10/

## 启动 Web 界面

```bash
gradio app.py  # 推荐：支持热重载
# 或
python app.py
```

访问：http://127.0.0.1:7860

---

## 命令行运行追踪示例

### 视频追踪

```python
###  x图像对比 yolov8_best.pt更好, 它是通过原始y图像 混入x图像构成的(https://www.kaggle.com/code/liuweiq/yolov8/notebook?scriptVersionId=275728121)
python tracking/track.py --yolo-model yolov8_best.pt --source x_particle_video.avi --save --save-txt --save-id-crops --tracking-method bytetrack --conf 0.1 --iou 0.1 --project 'runs/track3' --name 'exp'

python tracking/track.py --yolo-model yolov8-particle-best.pt --source 650-y1-1_particle_video.mp4 --save --save-txt --save-id-crops --tracking-method bytetrack --conf 0.1 --iou 0.1 --project 'runs/track_test_y' --name 'exp'

python tracking/track.py --yolo-model yolov8-particle-best.pt --source assets\MOT17-mini\train\mot_particle\mot_particle-img1_particle_video.mp4 --save --save-txt --tracking-method bytetrack --conf 0.1 --iou 0.1
```

### 图片序列追踪

```python
python tracking/track.py --yolo-model yolov8-particle-best.pt --source assets\MOT17-mini\train\mot_particle\img1 --save --save-txt --conf 0.02 --iou 0.01

python tracking/track.py --yolo-model yolov9-s-50-only-you.pt --source assets\MOT17-mini\train\modify\img1 --save --save-txt --conf 0.02 --iou 0.01

python tracking/track.py --yolo-model yolov8-particle-best.pt --source assets\MOT17-mini\train\new_modify\img1 --save --save-txt --conf 0.02 --iou 0.01
```

### 论文用的图片(识别单张图片)

python tracking/track.py --yolo-model yolov8-particle-best.pt --source example --save --save-txt --tracking-method bytetrack --conf 0.1 --iou 0.1

## 追踪评估

1. 获取预测数据
   python tracking/track.py --yolo-model yolov8-particle-best.pt --source assets\MOT17-mini\train\275_particle\img1 --save --save-txt --conf 0.02 --iou 0.01 --tracking-method bytetrack

2. convert
   python .\convert_mot.py
3. 使用 easy eval（视频：https://www.bilibili.com/video/BV1d8XQBMErv/）

## 搅拌实验的涂在另一个文件夹里(黑白搅拌)

python .\sci_paper_plots.py

## 新版画图,带有 excel 数据保存功能

python .\new\plot_particle_both.py --save

## 误差

python .\new\compare_true_predict.py --save
