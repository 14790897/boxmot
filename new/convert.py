import json, os
from .process_utils import get_latest_folder

image_width = 768
image_height = 1024
base_path = "runs/track"
track_data_path = os.path.join(get_latest_folder(base_path), "labels")
track_base_path = get_latest_folder(base_path)

for i in os.listdir(track_data_path):
    detection_results= []
    with open(os.path.join(track_data_path, i), "r") as f:
        detection_results = 

    convert_results(detection_results)


def convert_results(detection_results, image_width, image_height):
    for index, result in enumerate(detection_results):
        category = result[0]
        x_center = result[1] * image_width
        y_center = result[2] * image_height
        width = result[3] * image_width
        height = result[4] * image_height
        id = result[5]

        # 计算边框的左上角和右下角坐标
        x1 = round(x_center - width / 2)
        y1 = round(y_center - height / 2)
        x2 = round(x_center + width / 2)
        y2 = round(y_center + height / 2)

        # 将结果保存到列表中，包含中心点和宽高信息
        object_data = {
            "Frame": index + 1,  # 帧号从1开始
            "ID": id,
            "Category": category,
            "Box": [x1, y1, x2, y2],
            "Center": [round(x_center), round(y_center)],
            "WidthHeight": [round(width), round(height)],
        }

        output_dir_path = os.path.join(track_base_path, id)
        if not os.path.exists(output_dir_path):
            os.makedirs(output_dir_path)
        output_file = os.path.join(output_dir_path, "initial_data.json")
        with open(output_file, "w") as f:
            json.dump(object_data, f, indent=2)

        print(f"物体 {id} 的数据已保存到 {output_file}")
