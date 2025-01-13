python tracking/track.py --yolo-model yolov8_best.pt --source xy1-650-S14-2_particle_video.mp4 --save --save-txt --save-id-crops --tracking-method bytetrack
--conf 0.1 --iou 0.1
python tracking/track.py --yolo-model yolov8-particle-best.pt --source 650-1-x1_particle_video.mp4 --save --save-txt --tracking-method bytetrack --conf 0.1 --iou 0.1

python tracking/track.py --yolo-model yolov8-x.pt --source 650-1-x1_particle_video.mp4 --save --save-txt --conf 0.02 --iou 0.01 --project "runs_x_me\detect"
