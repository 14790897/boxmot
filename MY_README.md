# Particle Auto Measure - BoxMOT

## 相关训练代码

生成对抗网络: https://www.kaggle.com/code/liuweiqing2/sagan-particle
分类：https://www.kaggle.com/code/liuweiqing2/efficient-net-nice
识别: https://www.kaggle.com/code/liuweiq/yolov8-v9-v10
目标分类数据集：https://www.kaggle.com/datasets/liuweiq/efficientnet-data
目标识别y相机数据集：https://www.kaggle.com/datasets/liuweiq/yolo-great-particle-data
目标识别x相机数据集: https://www.kaggle.com/datasets/liuweiq/yolo-x-camera-data

## 启动 Web 界面

```bash
gradio app.py  # 推荐：支持热重载
# 或
python app.py
```
访问：http://127.0.0.1:7860
若需修改使用的模型，可以在app.py中搜索 "yolov8" 修改文件名字
分类模型在new.convert.py的'best_model_new_eff1.pth'修改

---

## 命令行运行追踪示例(这个项目的主要功能是追踪和可视化运行整个流程。追踪评估需要有数据集的真实标注以及模型预测的结果)

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

## 误差画图

python .\new\compare_true_predict.py --save  

## 数据裁剪为分类数据集
python utils\crop_annotation_and_resize.py

## zip打包
PS C:\git-program\particle_detect\particle_auto_measure\boxmot> 7z a -tzip 代码_MY_README是文档.zip .\* "-xr!.git" "-xr!runs" "-xr!runs_x_me"  
PS C:\git-program\particle_detect\auto_generate> 7z a -tzip 数据集.zip .\* "-xr!.git"   