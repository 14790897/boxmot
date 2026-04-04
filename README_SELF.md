# Particle Auto Measure - BoxMOT

## 相关训练代码

gan: https://www.kaggle.com/code/liuweiqing2/sagan-particle
分类：https://www.kaggle.com/code/liuweiqing2/efficient-net-nice
识别: https://www.kaggle.com/code/liuweiq/yolov8-v9-v10/

### 启动 Web 界面

```bash
gradio app.py  # 推荐：支持热重载
# 或
python app.py
```

访问：http://127.0.0.1:7860

---

## 命令行使用示例
### 视频识别

```python
###  x图像对比 yolov8_best.pt更好, 它是通过原始y图像 混入x图像构成的(https://www.kaggle.com/code/liuweiq/yolov8/notebook?scriptVersionId=275728121)
python tracking/track.py --yolo-model yolov8_best.pt --source x_particle_video.avi --save --save-txt --save-id-crops --tracking-method bytetrack --conf 0.1 --iou 0.1 --project 'runs/track3' --name 'exp'

python tracking/track.py --yolo-model yolov8-particle-best.pt --source 650-y1-1_particle_video.mp4 --save --save-txt --save-id-crops --tracking-method bytetrack --conf 0.1 --iou 0.1 --project 'runs/track_test_y' --name 'exp'

python tracking/track.py --yolo-model yolov8-particle-best.pt --source assets\MOT17-mini\train\mot_particle\mot_particle-img1_particle_video.mp4 --save --save-txt --tracking-method bytetrack --conf 0.1 --iou 0.1
```
### 图片序列识别
```python
python tracking/track.py --yolo-model yolov8-particle-best.pt --source assets\MOT17-mini\train\mot_particle\img1 --save --save-txt --conf 0.02 --iou 0.01

python tracking/track.py --yolo-model yolov9-s-50-only-you.pt --source assets\MOT17-mini\train\modify\img1 --save --save-txt --conf 0.02 --iou 0.01

python tracking/track.py --yolo-model yolov8-particle-best.pt --source assets\MOT17-mini\train\new_modify\img1 --save --save-txt --conf 0.02 --iou 0.01
```

### 论文用的图片(识别单张图片)

python tracking/track.py --yolo-model yolov8-particle-best.pt --source example --save --save-txt --tracking-method bytetrack --conf 0.1 --iou 0.1

## 评估

<!-- ### 生成检测框和特征

python tracking/val.py generate_dets_embs --yolo-model yolov8-particle-best.pt --reid-model weights/osnet_x0_25_msmt17.pt --source ./assets/MOT17-mini/train

### 评估

python tracking/val.py --yolo-model yolov8-particle-best.pt --tracking-method bytetrack --source ./assets/MOT17-mini/train --verbose --conf 0.1 --iou 0.1
python tracking/val.py --yolo-model yolov9-200.pt --tracking-method bytetrack --source ./assets/MOT17-mini/train --verbose --conf 0.1 --iou 0.1 -->


1. 获取数据
   python tracking/track.py --yolo-model yolov8-particle-best.pt --source assets\MOT17-mini\train\mot_particle\img1 --save --save-txt --conf 0.02 --iou 0.01 --tracking-method bytetrack

   python tracking/track.py --yolo-model yolov8-particle-best.pt --source assets\MOT17-mini\train\275_particle\img1 --save --save-txt --conf 0.02 --iou 0.01 --tracking-method bytetrack

2. convert
   python .\convert_mot.py
3. 使用 easy eval

<!-- #### nano 效果不错

python tracking/val.py --yolo-model yolov8_nano.pt --tracking-method bytetrack --source ./assets/MOT17-mini/train --verbose --conf 0.1 --iou 0.1 -->

## 画出结果图

python new\plot_particle.py

## 画出相对误差图

python relative_error.py

## 批量后处理

python postprocess.py

## 真实和机器学习计算对比

python .\new\compare_true_predict.py

## 论文 todo

一个是高度要改成现在的高度 还有就是机器学习模型 还有那个摄像头的分辨率也其实应该是 1024 乘以 760
等一下我发现之前确实用的是 efficient net b1 的模型
<!-- 还有一点就是你那个 PR 曲线是画错的 但是那也不重要因为我们其实不应该去使用这个 这个没什么用 要用的话 roc 当然也可以不算了这没关系 -->
还有就是说要不要重新测一遍转速 我觉得没有必要为什么因为本来就不是很严谨嘛你顶多就看一下没有出现的那些点是不是也是正确的就行了, 为什么我说不严谨因为他这个旋转时间啊这个人为的因素很大 也就是说你既可以认为它是这个也可以认为它是那个 都有道理 还是不要拖
那个 y 相机的像素其实是 1024 乘以 768 不是 360 x 相机 640\*360

那个流程图里面最后的判断条件你要写边距啊要小于某个范围还有什么呃自转时间不能大于一半的时间 算了不写了

maskrcnn ap=0.849 recall=0.637 链接: https://www.kaggle.com/code/liuweiq/coincide-separation-detectron2-maskrcnn/notebook?scriptVersionId=280522551
y+e:precision:93.7*99.54=9326.898 recall:94.5*99.55=9407.475
Y+o:precision:0.87*99.54=86.5998  recall:0.86*99.55=85.613
还有就是论文的那个750你可以说一下因为他是数据少所以没有体现出趋势。。。

yolov8的F1 Score应该是0.937  写错了

## 数据文件夹里有一些序号不对的他是按顺序排的 就不用管

需要调研一下为什么新模型它能识别到粒子少十个 (因为他可能是不同文件夹的关系 因为我们本来也就不知道是不是有很多正确的没识别到)

## 为什么有些会表现差呢?是因为那些是模糊的但是没模糊的数据我并没有把它加入到训练集所以就会出现那些模糊的它会识别错 如果能完全排除掉模糊的话那么准确率真的会很高

然后我最近又了解到了 video transformer 或者是 lstm 根据上下文来分类当前的状态其实这个是一个很好的方向它可能会有一些提升

## 搅拌实验的涂在另一个文件夹里(黑白搅拌)

python .\sci_paper_plots.py

## 新版画图,带有 excel 数据保存功能

python .\new\plot_particle_both.py --save

## 误差

python .\new\compare_true_predict.py --save

## 我发现生成对抗网络中如果把生成的数据放到他的验证集中在训练模型会效果好一点（这个就是 gemini 一直反对的做法，不过我觉得没必要搞这么复杂，随便，当然也有可能是因为当时又加了其他的效果，反正就这还那么乱七八糟的训练出来了,等一下我刚刚对比了一下两者区别我发现可能是你的后处理程序可能是不太适合目前的模型） 因为我现在使用纯真实验证效果没有之前好


## 追踪评估方法
使用根目录下的 convert_mot.py 脚本将跟踪结果转换为 MOT 评估所需的格式，然后使用 trackeval 进行评估。