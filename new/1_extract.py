# 先运行 python .\my_detect_and_track.py --source output_video.mp4 --weights "best_c_s.pt"
# 先过滤掉只维持一帧的状态然后排除掉最后几帧,因为最后几帧它已经开始往后面旋转所以不能使用这个数据而且看不清
import json
import os
import shutil
from collections import defaultdict, OrderedDict
from process_utils import (
    extract_and_stitch_columns,
    find_changes_within_range,
    calculate_distance_and_draw,
    detect_frame_difference,
)
import cv2

line_dict = {
    "1": (175, 31, 175, 437),
    "2": (175, 437, 209, 1021),
    "3": (551, 31, 551, 437),
    "4": (551, 437, 513, 1021),
    "5": (370, 31, 370, 1021),
}
central_line_coords = line_dict["5"]
results = {}
results = defaultdict(
    lambda: {
        "changes": 0,
        "total_frames": 0,
        "category_changes": [],
        # "filter_data": [],
    }
)
# 定义计算上下边界
y_min = 150  # 最小 y 坐标（根据实际需求调整）
y_max = 1000  # 最大 y 坐标（根据实际需求调整）


exclude_last_frames = 8
exclude_first_frames = 0  # 这里使用去除第一次变化来取代这个
initial_result_directory = "initial_result"
video_path = "my_process_particle_video.avi"
# 用于保存所有ID的统计信息
all_stats = {}


def process_data():
    for i in os.listdir(initial_result_directory):
        if not os.path.isdir(os.path.join(initial_result_directory, i)):
            continue
        category_changes = []

        # 记录 Category 变化
        previous_category = None
        data_path = os.path.join(initial_result_directory, i, "initial_data.json")
        with open(data_path, "r") as file:
            initial_id_data = json.load(file)  # JSON列表是有序的
        id_path = os.path.join(initial_result_directory, str(i))
        if not all(
            y_min <= (entry["Box"][1] + entry["Box"][3]) / 2 <= y_max
            for entry in initial_id_data
        ):
            print(f"轨迹 {i} 超出 Y 坐标范围，跳过")
            shutil.rmtree(id_path)
            continue

        # else:
        #     print(f"拼接图片已存在，跳过: {stitched_image_path}")
        for count in range(
            0, len(initial_id_data) - 1
        ):  # 从第一帧到倒数第'二'帧遍历,因为最后一帧的话会是none所以不能处理
            if count == 0:  # 处理第一帧
                if (
                    len(initial_id_data) > 2
                    and initial_id_data[count + 1]["Category"]
                    == initial_id_data[count + 2]["Category"]
                ):
                    initial_id_data[count]["Category"] = initial_id_data[count + 1][
                        "Category"
                    ]  # 修正为后两帧的值
            else:
                if (
                    initial_id_data[count - 1]["Category"]
                    == initial_id_data[count + 1]["Category"]  # 前后帧的 Category 相同
                    and initial_id_data[count]["Category"]
                    != initial_id_data[count - 1]["Category"]  # 当前帧的 Category 不同
                ):
                    initial_id_data[count]["Category"] = initial_id_data[count - 1][
                        "Category"
                    ]  # 修正为前一帧的值
        for count, entry in enumerate(initial_id_data):
            current_category = entry["Category"]
            id_ = entry["ID"]  # 这个应该是固定的
            # 忽略第一次比较（previous_category 为 None 的情况）
            if previous_category is None:
                previous_category = current_category
                continue

            if current_category != previous_category:
                category_changes.append(
                    entry
                )  # 这里相对于忽略了初始的状态，因为不知道持续多久
                # results[id_]["changes"] += 1

            previous_category = current_category
        # 忽略最后一次变化(由于改成距离检测，这里不删除最后一次变化)
        # if category_changes:
        #     category_changes = category_changes[:-1]
        # 减一是因为从第一次变化开始那一次是不能加一的所以这里要减一
        # results[id_]["total_frames"] = (
        #     data[-exclude_last_frames - 1]["Frame"] - data[0]["Frame"] + 1
        # )  # 由于中间可能会出现断的情况，就是没有追踪到，这种情况的话这种就必须使用初始的和最后的帧数相差的来作为总帧数
        # results[id_]["filter_data"] = initial_id_data[0:-exclude_last_frames]
        # 复制第一次和最后一次变化对应的图片
        if len(category_changes) >= 3:
            first_appear = initial_id_data[0]
            last_appear = initial_id_data[-1]
            first_appear_x_coord = (first_appear["Box"][0] + first_appear["Box"][2]) / 2
            first_appear_y_coord = (first_appear["Box"][1] + first_appear["Box"][3]) / 2
            last_appear_x_coord = (last_appear["Box"][0] + last_appear["Box"][2]) / 2
            last_appear_y_coord = (last_appear["Box"][1] + last_appear["Box"][3]) / 2
            # 添加新的过滤条件：如果最后帧的Y坐标高于第一帧(顶部是0)，跳过
            if last_appear_y_coord < first_appear_y_coord:
                print(f"ID {i}: Last frame is higher than the first frame, skipping.")
                shutil.rmtree(id_path)  # 删除文件夹
                continue
            first_appear_coordinates = (first_appear_x_coord, first_appear_y_coord)
            last_appear_coordinates = (last_appear_x_coord, last_appear_y_coord)
            # 检查点是否在同一侧，如果是则删除文件夹
            if (first_appear_coordinates[0] - central_line_coords[0]) * (
                last_appear_coordinates[0] - central_line_coords[0]
            ) > 0:
                print(f"{id_} 两点在同一侧不符合测量要求，删除")
                shutil.rmtree(id_path)
                continue
            d1_origin, d2_origin = (
                calculate_distance_and_draw(p, central_line_coords)[0]
                for p in (first_appear_coordinates, last_appear_coordinates)
            )
            midpoint = [
                (first_appear_x_coord + last_appear_x_coord) / 2,
                (first_appear_y_coord + last_appear_y_coord) / 2,
            ]
            if midpoint[1] > 437.0:
                # 计算中点到第2和第4条线的距离(下面的两条边距)
                result_left = calculate_distance_and_draw(midpoint, line_dict["2"])
                result_right = calculate_distance_and_draw(midpoint, line_dict["4"])

                # 分别提取结果
                d_total_left = result_left[0]
                x_left = result_left[1]

                d_total_right = result_right[0]
                x_right = result_right[1]
                category_changes = find_changes_within_range(
                    category_changes,
                    x_left,
                    x_right,
                    range_ratio=0.6,
                )
                initial_id_data_with_range = find_changes_within_range(
                    initial_id_data,
                    x_left,
                    x_right,
                    range_ratio=0.6,
                )
            else:
                # 计算中点到第1和第3条线的距离
                result_left = calculate_distance_and_draw(midpoint, line_dict["1"])
                result_right = calculate_distance_and_draw(midpoint, line_dict["3"])
                d_total_left = result_left[0]
                x_left = result_left[1]

                d_total_right = result_right[0]
                x_right = result_right[1]
                category_changes = find_changes_within_range(
                    category_changes,
                    x_left,
                    x_right,
                    range_ratio=0.6,
                )
                initial_id_data_with_range = find_changes_within_range(
                    initial_id_data,
                    x_left,
                    x_right,
                    range_ratio=0.6,
                )
            # 更新范围后的第一次和最后一次变化
            if len(category_changes) >= 1:
                first_appear = initial_id_data_with_range[
                    0
                ]  # 这里使用第一和最后出现的数据计算公转速度
                last_appear = initial_id_data_with_range[-1]
                first_change = category_changes[0]
                last_change = category_changes[-1]
                first_appear_x_coord = (
                    first_appear["Box"][0] + first_appear["Box"][2]
                ) / 2
                first_appear_y_coord = (
                    first_appear["Box"][1] + first_appear["Box"][3]
                ) / 2
                last_appear_x_coord = (
                    last_appear["Box"][0] + last_appear["Box"][2]
                ) / 2
                last_appear_y_coord = (
                    last_appear["Box"][1] + last_appear["Box"][3]
                ) / 2
                first_appear_coordinates = (
                    first_appear_x_coord,
                    first_appear_y_coord,
                )
                last_appear_coordinates = (last_appear_x_coord, last_appear_y_coord)
                # 检查点是否在同一侧，如果是则删除文件夹
                # if (first_appear_coordinates[0] - central_line_coords[0]) * (
                #     last_appear_coordinates[0] - central_line_coords[0]
                # ) > 0:
                #     print(f"{id_} 在过滤范围内两点在同一侧不符合测量要求，删除")
                #     shutil.rmtree(id_path)
                #     continue
                d_total = d_total_left + d_total_right

                first_image = os.path.join(
                    initial_result_directory,
                    i,
                    "images",
                    f"frame_{first_appear['Frame']}.jpg",
                )
                last_image = os.path.join(
                    initial_result_directory,
                    i,
                    "images",
                    f"frame_{last_appear['Frame']}.jpg",
                )
                first_last_output_path = os.path.join(
                    initial_result_directory, i, "first_last_output"
                )
                os.makedirs(first_last_output_path, exist_ok=True)

                shutil.copy(first_image, first_last_output_path)
                shutil.copy(last_image, first_last_output_path)

                new_image1 = calculate_distance_and_draw(
                    first_appear_coordinates,
                    central_line_coords,
                    first_image,
                )[3]
                new_image2 = calculate_distance_and_draw(
                    last_appear_coordinates, central_line_coords, last_image
                )[3]
                new_image1.save(
                    os.path.join(first_last_output_path, "1_distance_result.jpg")
                )
                new_image2.save(
                    os.path.join(first_last_output_path, "2_distance_result.jpg")
                )
                # stitched_image_path = os.path.join(
                #     initial_result_directory, i, "images", "stitched_image.jpg"
                # )
                # if not os.path.exists(stitched_image_path):
                #     stitched_image = extract_and_stitch_columns(
                #         video_path, category_changes
                #     )
                #     cv2.imwrite(
                #         stitched_image_path,
                #         stitched_image,
                #     )
                min_distance = float("inf")
                closest_point = None

                for item in initial_id_data:
                    point = [
                        (item["Box"][0] + item["Box"][2]) / 2,
                        (item["Box"][1] + item["Box"][3]) / 2,
                    ]
                    distance = calculate_distance_and_draw(point, central_line_coords)[
                        0
                    ]
                    if distance < min_distance:
                        min_distance = distance
                        closest_point = point
                        closest_point_data = item  # 保存整个JSON对象
                    # 这里最好可以保存一下这张距离最近的图片
                if closest_point:
                    print(
                        f"{id_} 中距离中线最近的点：{closest_point}，距离：{min_distance}"
                    )
                    frame_number = closest_point_data.get("Frame")
                    if frame_number is not None:
                        # 找到对应帧的图片文件名
                        closest_image_filename = f"frame_{frame_number}.jpg"
                        closest_image_path = os.path.join(
                            id_path, "images", closest_image_filename
                        )
                        if os.path.exists(closest_image_path):
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
                    print(f"{id_} 中没有找到距离中线最近的点")
                d1_with_range_revolution, d2_with_range_revolution = (
                    calculate_distance_and_draw(p, central_line_coords)[0]
                    for p in (first_appear_coordinates, last_appear_coordinates)
                )
                # 将对应的json数据也复制进去
                with open(
                    os.path.join(first_last_output_path, "output.json"), "w"
                ) as file:
                    json.dump([first_appear, last_appear], file, indent=4)

                print(f"id {i} Category 发生了 {len(category_changes) - 1} 次变化")
                results[id_]["changes"] = (
                    len(category_changes)
                    - 1  # 如果是-2就是减去最后的那次变化的次数，同时保留倒数第二个状态的时间
                )
                results[id_]["category_changes"] = category_changes
                results[id_]["total_frames_revolution"] = (
                    last_appear["Frame"] - first_appear["Frame"] + 1
                )  # 这里要使用第一次变化到最后一次变化的时间
                results[id_]["start_frame_revolution"] = first_appear["Frame"]
                results[id_]["end_frame_revolution"] = last_appear["Frame"]
                results[id_]["total_frames_rotation"] = (
                    last_change["Frame"] - first_change["Frame"] + 1
                )
                results[id_]["start_frame_rotation"] = first_change["Frame"]
                results[id_]["end_frame_rotation"] = last_change["Frame"]
                results[id_]["d1_with_range_revolution"] = d1_with_range_revolution
                results[id_]["d2_with_range_revolution"] = d2_with_range_revolution
                results[id_]["d1_origin"] = d1_origin
                results[id_]["d2_origin"] = d2_origin
                results[id_]["inner_diameter"] = d_total
                results[id_]["closest_point"] = closest_point_data
                results[id_]["not_use"] = False
                if len(category_changes) < 3:
                    results[id_]["not_use"] = True
                    print(f"id {i} Category 在指定范围内次数变化小于3，删除文件夹")
                else:
                    print(f"id {i} Category 在指定范围内发生了大于2次变化")
            else:
                print(f"id {i} Category 在指定范围内没有发生变化，删除文件夹")
                shutil.rmtree(id_path)
        else:
            shutil.rmtree(id_path)
            print(f"id {i} Category 没有发生变化，删除文件夹")

    # 在整个循环结束后，将所有统计信息保存到一个文件中
    with open(
        os.path.join(initial_result_directory, "all_stats.json"), "w"
    ) as stats_file:
        # 将每个ID的变化次数和总帧数保存到 all_stats 中

        for id_, result in results.items():
            all_stats[f"{id_}"] = OrderedDict(
                [
                    ("not_use", result.get("not_use")),
                    ("start_frame_revolution", result.get("start_frame_revolution")),
                    ("end_frame_revolution", result.get("end_frame_revolution")),
                    ("total_frames_revolution", result.get("total_frames_revolution")),
                    ("start_frame_rotation", result.get("start_frame_rotation")),
                    ("end_frame_rotation", result.get("end_frame_rotation")),
                    ("total_frames_rotation", result.get("total_frames_rotation")),
                    ("changes", result.get("changes")),
                    ("category_changes", result.get("category_changes")),
                    (
                        "d1_with_range_revolution",
                        result.get("d1_with_range_revolution"),
                    ),
                    (
                        "d2_with_range_revolution",
                        result.get("d2_with_range_revolution"),
                    ),
                    ("d1_origin", result.get("d1_origin")),
                    ("d2_origin", result.get("d2_origin")),
                    ("inner_diameter", result.get("inner_diameter")),
                    ("closest_point", result.get("closest_point")),
                ]
            )
            print(
                f"ID: {id_}, 变化次数: {result['changes']}, 总公转帧数: {result['total_frames_revolution']}, Category Changes: {result['changes']},{(closest_point_data.get("Box")[1]+closest_point_data.get("Box")[3])/2}"
            )
        detect_frame_difference(all_stats)
        json.dump(all_stats, stats_file, indent=4)


if __name__ == "__main__":
    process_data()
