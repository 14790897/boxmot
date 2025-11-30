# Particle Auto Measure - BoxMOT

## 📚 快速开始

查看 **[USER_GUIDE.md](USER_GUIDE.md)** 获取完整的使用说明。

### 启动 Web 界面

```bash
gradio app.py  # 推荐：支持热重载
# 或
python app.py
```

访问：http://127.0.0.1:7860

---

## 命令行使用示例

```bash
python tracking/track.py --yolo-model yolov8_best.pt --source xy1-650-S14-2_particle_video.mp4 --save --save-txt --save-id-crops --tracking-method bytetrack --conf 0.1 --iou 0.1

###  x图像对比 yolov8_best.pt更好, 它是通过原始y图像 混入x图像构成的(https://www.kaggle.com/code/liuweiq/yolov8/notebook?scriptVersionId=275728121)
python tracking/track.py --yolo-model yolov8_best.pt --source x_particle_video.avi --save --save-txt --save-id-crops --tracking-method bytetrack --conf 0.1 --iou 0.1 --project 'runs/track3' --name 'exp'

python tracking/track.py --yolo-model yolov8-particle-best.pt --source x_particle_video.avi --save --save-txt --save-id-crops --tracking-method bytetrack --conf 0.1 --iou 0.1 --project 'runs/track3' --name 'exp'
python tracking/track.py --yolo-model 'yolov8-xx.pt'  --source x_particle_video.avi --save --save-txt --save-id-crops --tracking-method bytetrack --conf 0.1 --iou 0.1 --project 'runs/track3' --name 'exp'


python tracking/track.py --yolo-model yolov8-particle-best.pt --source 650-1-x1_particle_video.mp4 --save --save-txt --tracking-method bytetrack --conf 0.1 --iou 0.1
python tracking/track.py --yolo-model yolov8-particle-best.pt --source assets\MOT17-mini\train\mot_particle\mot_particle-img1_particle_video.mp4 --save --save-txt --tracking-method bytetrack --conf 0.1 --iou 0.1
python tracking/track.py --yolo-model yolov8-x.pt --source x_video.mp4 --save --save-txt --conf 0.02 --iou 0.01 --project "runs_x_me\detect"

python tracking/track.py --yolo-model yolov8-particle-best.pt --source assets\MOT17-mini\train\mot_particle\img1 --save --save-txt --conf 0.02 --iou 0.01

python tracking/track.py --yolo-model yolov9-s-50-only-you.pt --source assets\MOT17-mini\train\modify\img1 --save --save-txt --conf 0.02 --iou 0.01

python tracking/track.py --yolo-model yolov8-particle-best.pt --source assets\MOT17-mini\train\new_modify\img1 --save --save-txt --conf 0.02 --iou 0.01
```

### 论文用的图片(识别单张图片)

python tracking/track.py --yolo-model yolov8-particle-best.pt --source example --save --save-txt --tracking-method bytetrack --conf 0.1 --iou 0.1

## 评估

### 生成检测框和特征

python tracking/val.py generate_dets_embs --yolo-model yolov8-particle-best.pt --reid-model weights/osnet_x0_25_msmt17.pt --source ./assets/MOT17-mini/train

### 评估

python tracking/val.py --yolo-model yolov8-particle-best.pt --tracking-method bytetrack --source ./assets/MOT17-mini/train --verbose --conf 0.1 --iou 0.1
python tracking/val.py --yolo-model yolov9-200.pt --tracking-method bytetrack --source ./assets/MOT17-mini/train --verbose --conf 0.1 --iou 0.1

个人使用的方法

1. 获取数据
   python tracking/track.py --yolo-model yolov8-particle-best.pt --source assets\MOT17-mini\train\mot_particle\img1 --save --save-txt --conf 0.02 --iou 0.01 --tracking-method bytetrack

   python tracking/track.py --yolo-model yolov8-particle-best.pt --source assets\MOT17-mini\train\275_particle\img1 --save --save-txt --conf 0.02 --iou 0.01 --tracking-method bytetrack

2. convert
   python .\convert_mot.py
3. 使用 easy eval

#### nano 效果不错

python tracking/val.py --yolo-model yolov8_nano.pt --tracking-method bytetrack --source ./assets/MOT17-mini/train --verbose --conf 0.1 --iou 0.1

#### 有问题

python tracking/val.py trackeval1 --yolo-model yolov8-particle-best.pt --benchmark MOTCUSTOM --split test --tracking-method bytetrack --conf 0.1 --iou 0.1

## 画出结果图

python new\plot_particle.py

## 获取某个文件夹的子文件夹

## 画出相对误差图

python relative_error.py

## 批量后处理

python postprocess.py

## 真实和机器学习计算对比

python .\new\compare_true_predict.py

## 目前是在处理一次后，手动更改目录名字为特定格式后，需要再次处理（python postprocess.py），才有正确答案, 因为一开始生成目录的名字叫 exp 所以并不知道是-1 还是-2,这部分逻辑需要优化 还有就是 X 标注的框里有点小的看不清真实的样子

## mot 计算，使用 convert_mot.py，以及 exp20(这个是 mot 验证需要的)

## 论文todo

一个是高度要改成现在的高度  还有就是机器学习模型 还有那个摄像头的分辨率也其实应该是 1024 乘以 760
等一下我发现之前确实用的是efficient net b1的模型
还有一点就是你那个PR曲线是画错的  但是那也不重要因为我们其实不应该去使用这个  这个没什么用  要用的话roc 当然也可以不算了这没关系
还有就是说要不要重新测一遍转速  我觉得没有必要为什么因为本来就不是很严谨嘛你顶多就看一下没有出现的那些点是不是也是正确的就行了,  为什么我说不严谨因为他这个时间啊这个人为的因素很大 也就是说你既可以认为它是这个也可以认为它是那个 都有道理  还是不要拖
没有那个是相机的像素其实是1024乘以768  不是360  x相机640*360

那个流程图里面最后的判断条件你要写边距啊要小于某个范围还有什么呃自转时间不能大于一半的时间 算了不写了

maskrcnn   ap=0.84  recall=0.637 链接: https://www.kaggle.com/code/liuweiq/coincide-separation-detectron2-maskrcnn/edit/run/195578923

## 数据文件夹里有一些需要不对的他是按顺序排的  就不用管