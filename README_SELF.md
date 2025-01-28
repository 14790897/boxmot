python tracking/track.py --yolo-model yolov8_best.pt --source xy1-650-S14-2_particle_video.mp4 --save --save-txt --save-id-crops --tracking-method bytetrack
--conf 0.1 --iou 0.1
python tracking/track.py --yolo-model yolov8-particle-best.pt --source 650-1-x1_particle_video.mp4 --save --save-txt --tracking-method bytetrack --conf 0.1 --iou 0.1
python tracking/track.py --yolo-model yolov8-particle-best.pt --source assets\MOT17-mini\train\mot_particle\mot_particle-img1_particle_video.mp4 --save --save-txt --tracking-method bytetrack --conf 0.1 --iou 0.1
python tracking/track.py --yolo-model yolov8-x.pt --source x_video.mp4 --save --save-txt --conf 0.02 --iou 0.01 --project "runs_x_me\detect"

python tracking/track.py --yolo-model yolov8-particle-best.pt --source assets\MOT17-mini\train\mot_particle\img1 --save --save-txt --conf 0.02 --iou 0.01

python tracking/track.py --yolo-model yolov9-s-50-only-you.pt --source assets\MOT17-mini\train\modify\img1 --save --save-txt --conf 0.02 --iou 0.01

python tracking/track.py --yolo-model yolov8-particle-best.pt --source assets\MOT17-mini\train\new_modify\img1 --save --save-txt --conf 0.02 --iou 0.01

## 评估

### 生成检测框和特征

python tracking/val.py generate_dets_embs --yolo-model yolov8-particle-best.pt --reid-model weights/osnet_x0_25_msmt17.pt --source ./assets/MOT17-mini/train

### 评估

python tracking/val.py --yolo-model yolov8-particle-best.pt --tracking-method bytetrack --source ./assets/MOT17-mini/train --verbose --conf 0.1 --iou 0.1
python tracking/val.py --yolo-model yolov9-200.pt --tracking-method bytetrack --source ./assets/MOT17-mini/train --verbose --conf 0.1 --iou 0.1

#### nano 效果不错

python tracking/val.py --yolo-model yolov8_nano.pt --tracking-method bytetrack --source ./assets/MOT17-mini/train --verbose --conf 0.1 --iou 0.1

#### 有问题

python tracking/val.py trackeval1 --yolo-model yolov8-particle-best.pt --benchmark MOTCUSTOM --split test --tracking-method bytetrack --conf 0.1 --iou 0.1
