# 根据辅助线数据与各id颗粒的文本数据，求出迁移距离1（就是指点到中间线的距离）、迁移距离2与旋流器高度内径，写入result.txt文件，总共三项，如果两个粒子在一侧则不要
import shutil
import os
import json, sys
from PIL import Image, ImageDraw, ImageFont

from process_utils import calculate_distance_and_draw

initial_result_directory = "initial_result"
# 加载已经存在的 all_stats.json 文件，如果文件不存在则初始化一个空字典
stats_file_path = os.path.join(initial_result_directory, "all_stats.json")
if os.path.exists(stats_file_path):
    with open(stats_file_path, "r") as stats_file:
        all_stats = json.load(stats_file)
else:
    print("all_stats.json 文件不存在，退出")

# 辅助线，格式为：线段标识符: 起点(x1, y1) 和 终点(x2, y2)
line_dict = {
    "1": (175, 31, 175, 437),
    "2": (175, 437, 209, 1021),
    "3": (551, 31, 551, 437),
    "4": (551, 437, 513, 1021),
    "5": (370, 31, 370, 1021),
}


# 处理每个 id 文件夹
def process_folder(id_path):
    id_folder_name = os.path.basename(id_path)
    initial_data_json_file = os.path.join(id_path, "initial_data.json")
    first_last_output_path = os.path.join(id_path, "first_last_output")
    output_json_file = os.path.join(first_last_output_path, "output.json")

    with open(output_json_file, "r") as f:
        try:
            data = json.load(f)

            # 提取第一个出现的点和最后一个变化的点
            point1 = [
                (data[0]["Box"][0] + data[0]["Box"][2]) / 2,
                (data[0]["Box"][1] + data[0]["Box"][3]) / 2,
            ]
            point2 = [
                (data[1]["Box"][0] + data[1]["Box"][2]) / 2,
                (data[1]["Box"][1] + data[1]["Box"][3]) / 2,
            ]

        except (IndexError, KeyError) as e:
            print(f"{output_json_file} 文件格式错误，跳过处理 {id_path}: {e}")
            return

    image_files = sorted(
        f for f in os.listdir(first_last_output_path) if f.endswith(".jpg")
    )

    if len(image_files) < 2:
        print(f"{id_path} 文件夹中的图片数量小于 2，跳过")
        return

    image1_path, image2_path = (
        os.path.join(first_last_output_path, image_files[i]) for i in (0, 1)
    )

    # 使用具体的辅助线坐标在图片上绘制辅助线和距离标注
    central_line_coords = line_dict["5"]

    # 计算每个点到中间线的距离
    d1, d2 = (
        calculate_distance_and_draw(p, central_line_coords)[0] for p in (point1, point2)
    )

    # 检查点是否在同一侧，如果是则删除文件夹
    if (point1[0] - central_line_coords[0]) * (point2[0] - central_line_coords[0]) > 0:
        print(f"{id_path} 两点在同一侧不符合测量要求，删除")
        shutil.rmtree(id_path)
        return
    new_image1 = calculate_distance_and_draw(point1, central_line_coords, image1_path)[
        3
    ]
    new_image2 = calculate_distance_and_draw(point2, central_line_coords, image2_path)[
        3
    ]
    new_image1.save(os.path.join(first_last_output_path, "1_distance_result.jpg"))
    new_image2.save(os.path.join(first_last_output_path, "2_distance_result.jpg"))

    with open(initial_data_json_file, "r") as f:
        data = json.load(f)
        min_distance = float("inf")
        closest_point = None

        for item in data:
            point = [
                (item["Box"][0] + item["Box"][2]) / 2,
                (item["Box"][1] + item["Box"][3]) / 2,
            ]
            distance = calculate_distance_and_draw(point, central_line_coords)[0]
            if distance < min_distance:
                min_distance = distance
                closest_point = point
                closest_point_data = item  # 保存整个JSON对象
        # 这里最好可以保存一下这张距离最近的图片
    if closest_point:
        print(
            f"{id_folder_name} 中距离中线最近的点：{closest_point}，距离：{min_distance}"
        )

        # 从 JSON 数据中提取帧号（假设 JSON 数据中有 "Frame" 字段）
        frame_number = closest_point_data.get("Frame")
        if frame_number is not None:
            # 找到对应帧的图片文件名
            closest_image_filename = f"frame_{frame_number}.jpg"
            closest_image_path = os.path.join(id_path, "images", closest_image_filename)

            # 检查文件是否存在
            if os.path.exists(closest_image_path):
                # 保存最近的图片到指定位置
                saved_image_path = os.path.join(
                    first_last_output_path,
                    f"closest_point_{closest_image_filename}.jpg",
                )
                shutil.copy(closest_image_path, saved_image_path)
                print(f"距离最近的图片已保存到: {saved_image_path}")
            else:
                print(f"对应帧的图片文件不存在: {closest_image_path}")
        else:
            print("最近点的帧号未找到，无法保存图片")
    else:
        print(f"{id_folder_name} 中没有找到距离中线最近的点")
    # 计算中点并测量到线条的总距离
    y_mid = (point1[1] + point2[1]) / 2
    midpoint = [
        (point1[0] + point2[0]) / 2,
        (point1[1] + point2[1]) / 2,
    ]
    if y_mid > 437.0:
        # 计算中点到第2和第4条线的距离
        d_total_left = calculate_distance_and_draw(midpoint, line_dict["2"])[
            0
        ]  # 之前使用point一和point二计算机距离是错误的，要使用中点
        d_total_right = calculate_distance_and_draw(midpoint, line_dict["4"])[0]
    else:
        # 计算中点到第1和第3条线的距离
        d_total_left = calculate_distance_and_draw(midpoint, line_dict["1"])[0]
        d_total_right = calculate_distance_and_draw(midpoint, line_dict["3"])[0]

    # 计算总距离（左右相加）
    d_total = d_total_left + d_total_right

    # 更新 all_stats 字典
    all_stats[id_folder_name].update(
        {
            "d1": d1,
            "d2": d2,
            "inner_diameter": d_total,
            "closest_point": closest_point_data,
        }
    )


if __name__ == "__main__":
    # 处理所有 id 文件夹
    for id_folder in os.listdir(initial_result_directory):
        id_path = os.path.join(initial_result_directory, id_folder)
        if os.path.isdir(id_path):
            process_folder(id_path)

    with open(stats_file_path, "w") as stats_file:
        # filtered_data = {k: v for k, v in all_stats.items() if len(v) >= 5}
        filtered_data = {
            k: v
            for k, v in all_stats.items()
            if "d1" in v and "d2" in v and v["d1"] > 0 and v["d2"] > 0
        }
        json.dump(filtered_data, stats_file, indent=4)
