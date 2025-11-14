# 先运行 python .\my_detect_and_track.py --source output_video.mp4 --weights "best_c_s.pt"
# 先过滤掉只维持一帧的状态然后排除掉最后几帧,因为最后几帧它已经开始往后面旋转所以不能使用这个数据而且看不清
import copy
import json
import os
import shutil
import sys
from collections import OrderedDict, defaultdict

from process_utils import (
    calculate_distance_and_draw,
    detect_frame_difference,
    find_changes_within_range,
    get_latest_folder,
    remove_empty,
)

# 支持命令行参数或默认值
y_track_project = sys.argv[1] if len(sys.argv) > 1 else "runs/track"

base_path = os.path.normpath(y_track_project)
initial_result_directory = os.path.join(get_latest_folder(base_path), "initial_result")
video_path = "my_process_particle_video.avi"
# 如果是下半部分的话文件夹名字需要以-2结尾
# 下面是旋流器上半部分 一三代表了两边, 一二是同侧的,  437是拐点  高度是 437/147=2.97cm
if not get_latest_folder(base_path).endswith("-2"):
    line_dict = {
        "1": (175, 31, 175, 437),
        "2": (175, 437, 209, 1021),
        "3": (551, 31, 551, 437),
        "4": (551, 437, 513, 1021),
        "5": (363, 31, 363, 1021),
    }
    # 定义计算上下边界
    y_min = 20  # 最小 y 坐标（根据实际需求调整）
    y_max = 980  # 最大 y 坐标（根据实际需求调整）,注意这里对应的x图像的高度其实并没有它对应的坐标
else:
    # 一三代表了两边, 下面的二四和一三其实是一样的
    line_dict = {
        "1": (193, 0, 250, 1021),
        "2": (193, 0, 250, 1021),
        "3": (520, 0, 460, 1021),
        "4": (520, 0, 460, 1021),
        "5": (357, 0, 357, 1021),
    }
    # 定义计算上下边界
    y_min = 20  # 最小 y 坐标（根据实际需求调整）
    y_max = 758  # 最大 y 坐标（根据实际需求调整）

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


exclude_last_frames = 8
exclude_first_frames = 0  # 这里使用去除第一次变化来取代这个

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
            # shutil.rmtree(id_path)
            # 这里会导致这个键只有它被定义其他的数据是空的,最后后处理的时候会访问不到其他数据,报错,使用remove_empty解决
            results[i]["not_use"] = True
            results[i]["reason"] = "Out of Y coordinate range"
            continue

        # else:
        #     print(f"拼接图片已存在，跳过: {stitched_image_path}")
        for count in range(
            0, len(initial_id_data)
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
            elif count < len(initial_id_data) - 1:  # 处理中间帧
                if (
                    initial_id_data[count - 1]["Category"]
                    == initial_id_data[count + 1]["Category"]  # 前后帧的 Category 相同
                    and initial_id_data[count]["Category"]
                    != initial_id_data[count - 1]["Category"]  # 当前帧的 Category 不同
                ):
                    initial_id_data[count]["Category"] = initial_id_data[count - 1][
                        "Category"
                    ]  # 修正为前一帧的值
            else:
                if count == len(initial_id_data) - 1:
                    if (
                        len(initial_id_data) > 2
                        and initial_id_data[count - 1]["Category"]
                        == initial_id_data[count - 2]["Category"]
                    ):
                        initial_id_data[count]["Category"] = initial_id_data[count - 1][
                            "Category"
                        ]  # 修正为前两帧的值
        previous_category = None
        category_start_frame = None
        category_changes = []
        # for count, entry in enumerate(initial_id_data):
        #     current_category = entry["Category"]
        #     id_ = entry["ID"]  # 这个应该是固定的
        #     # 忽略第一次比较（previous_category 为 None 的情况）
        #     if previous_category is None:
        #         previous_category = current_category
        #         continue

        #     if current_category != previous_category:
        #         category_changes.append(
        #             entry
        #         )  # 这里相对于忽略了初始的状态，因为不知道持续多久
        #         # results[id_]["changes"] += 1

        #     previous_category = current_category
        for count, entry in enumerate(initial_id_data):
            current_category = entry["Category"]
            current_frame = entry["Frame"]
            id_ = entry["ID"]

            # 初始化第一个类别
            if previous_category is None:
                previous_category = current_category
                category_start_frame = current_frame
                continue

            # 如果类别发生变化
            if current_category != previous_category:
                # 计算类别持续时间
                duration = current_frame - category_start_frame

                # 计算中间帧
                mid_frame = category_start_frame + duration // 2

                # 找到最接近的帧
                closest_entry = min(
                    initial_id_data,
                    key=lambda x: abs(x["Frame"] - mid_frame),  # 按帧差值排序
                )
                closest_entry["origin_frame"] = category_start_frame  # 保存原始帧数
                category_changes.append(closest_entry)

                # 更新变量
                previous_category = current_category
                category_start_frame = current_frame

        # 最后一段的处理
        if category_start_frame is not None and previous_category is not None:
            duration = current_frame - category_start_frame
            mid_frame = category_start_frame + duration // 2

            # 找到最接近的帧
            closest_entry = min(
                initial_id_data, key=lambda x: abs(x["Frame"] - mid_frame)
            )
            closest_entry["origin_frame"] = category_start_frame  # 保存原始帧数
            # print(f"最后一段的处理: {closest_entry},mid_frame: {mid_frame},duration: {duration}")
            category_changes.append(closest_entry)
        # if len(category_changes) == 0:
        #     不会触发这个条件，因为至少有一个状态
        #     print(f"ID {i} 没有变化，删除")
        #     break
        category_changes_with_all = copy.deepcopy(category_changes)
        true_last_appear_data = initial_id_data[-1]
        true_last_appear_data["origin_frame"] = initial_id_data[-1]["Frame"]
        # 如果最后一帧差距太大也要加上去（因为前面最后加的是中间的一帧，所以如果中间差距过大的话他会不能识别出）
        if (
            true_last_appear_data["origin_frame"]
            - category_changes_with_all[-1]["origin_frame"]
            > 6
        ):
            category_changes_with_all.append(true_last_appear_data)
        origin_all_frame = (
            category_changes_with_all[-1]["origin_frame"]
            - category_changes_with_all[0]["origin_frame"]
        )
        all_frame = (
            category_changes_with_all[-1]["Frame"]
            - category_changes_with_all[0]["Frame"]
        )
        for id_category in range(len(category_changes_with_all) - 1):
            current_frame = category_changes_with_all[id_category]["origin_frame"]
            next_frame = category_changes_with_all[id_category + 1]["origin_frame"]
            origin_frame_diff = next_frame - current_frame
            frame_diff = (
                category_changes_with_all[id_category + 1]["Frame"]
                - category_changes_with_all[id_category]["Frame"]
            )
            print(f"{id_}Frame difference: {frame_diff}")
            # 检查帧差距是否为 2
            # if frame_diff == 2:
            #     print(
            #         f"Main Detected frame difference of 2 at frame {current_frame} of id: {i}, 由于变化过快，说明无法准确检测，建议删除"
            #     )
            #     results[i]["not_use"] = True
            #     results[i]["reason"] = f"Main change too fast at frame {current_frame}"
            # # 排除掉保留状态过长的轨迹
            # el
            if origin_frame_diff >= origin_all_frame / 2 or frame_diff >= all_frame / 2:
                print(
                    f"Main have a long time not change, id: {i}, at frame {current_frame}, not use"
                )
                results[id_]["not_use"] = True
                results[id_][
                    "reason"
                ] = f"Main have a long time not change，at frame {current_frame}"
        # 忽略最后一次变化(由于改成距离检测，这里不删除最后一次变化)
        # if category_changes:
        #     category_changes = category_changes[:-1]
        # 减一是因为从第一次变化开始那一次是不能加一的所以这里要减一
        # results[id_]["total_frames"] = (
        #     data[-exclude_last_frames - 1]["Frame"] - data[0]["Frame"] + 1
        # )  # 由于中间可能会出现断的情况，就是没有追踪到，这种情况的话这种就必须使用初始的和最后的帧数相差的来作为总帧数
        # results[id_]["filter_data"] = initial_id_data[0:-exclude_last_frames]
        # 复制第一次和最后一次变化对应的图片
        first_appear = initial_id_data[0]
        last_appear = initial_id_data[-1]
        first_appear_x_coord = (first_appear["Box"][0] + first_appear["Box"][2]) / 2
        first_appear_y_coord = (first_appear["Box"][1] + first_appear["Box"][3]) / 2
        last_appear_x_coord = (last_appear["Box"][0] + last_appear["Box"][2]) / 2
        last_appear_y_coord = (last_appear["Box"][1] + last_appear["Box"][3]) / 2
        # 添加新的过滤条件：如果最后帧的Y坐标高于第一帧(顶部是0)，跳过
        # if last_appear_y_coord < first_appear_y_coord:
        #     print(f"ID {i}: Last frame is higher than the first frame, skipping.")
        #     shutil.rmtree(id_path)  # 删除文件夹
        #     continue
        first_appear_coordinates = (first_appear_x_coord, first_appear_y_coord)
        last_appear_coordinates = (last_appear_x_coord, last_appear_y_coord)
        # 检查点是否在同一侧，如果是则删除文件夹
        if (first_appear_coordinates[0] - central_line_coords[0]) * (
            last_appear_coordinates[0] - central_line_coords[0]
        ) > 0:
            print(f"{id_} 两点在同一侧不符合测量要求，删除")
            shutil.rmtree(id_path)
            # del results[id_]
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
            # 只找出在这个范围内的变化
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
        # category_changes = remove_long_time_not_change(category_changes,id_)
        # 更新范围后的第一次和最后一次变化
        first_appear = initial_id_data_with_range[
            0
        ]  # 这里使用第一和最后出现的数据计算公转速度
        last_appear = initial_id_data_with_range[-1]
        if not category_changes:  # 如果没有变化就跳过
            first_change = initial_id_data[0]
            first_change["origin_frame"] = initial_id_data[0]["Frame"]
            last_change = initial_id_data[-1]
            last_change["origin_frame"] = initial_id_data[-1]["Frame"]
        else:
            first_change = category_changes[0]
            last_change = category_changes[-1]
        first_appear_x_coord = (first_appear["Box"][0] + first_appear["Box"][2]) / 2
        first_appear_y_coord = (first_appear["Box"][1] + first_appear["Box"][3]) / 2
        last_appear_x_coord = (last_appear["Box"][0] + last_appear["Box"][2]) / 2
        last_appear_y_coord = (last_appear["Box"][1] + last_appear["Box"][3]) / 2
        first_appear_coordinates = (
            first_appear_x_coord,
            first_appear_y_coord,
        )
        last_appear_coordinates = (last_appear_x_coord, last_appear_y_coord)
        # 检查点是否在同一侧，如果是则删除文件夹
        if (first_appear_coordinates[0] - central_line_coords[0]) * (
            last_appear_coordinates[0] - central_line_coords[0]
        ) > 0:
            print(f"{id_} 在过滤范围内两点在同一侧不符合测量要求，删除")
            shutil.rmtree(id_path)
            # del results[id_]
            continue
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
        new_image1.save(os.path.join(first_last_output_path, "1_distance_result.jpg"))
        new_image2.save(os.path.join(first_last_output_path, "2_distance_result.jpg"))
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
            distance = calculate_distance_and_draw(point, central_line_coords)[0]
            if distance < min_distance:
                min_distance = distance
                closest_point = point
                closest_point_data = item  # 保存整个JSON对象
            # 这里最好可以保存一下这张距离最近的图片
        if closest_point:
            # print(
            #     f"{id_} 中距离中线最近的点：{closest_point}，距离：{min_distance}"
            # )
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
                    # print(f"距离最近的图片已保存到: {saved_image_path}")
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
        with open(os.path.join(first_last_output_path, "output.json"), "w") as file:
            json.dump([first_appear, last_appear], file, indent=4)

        print(f"id {i} Category 发生了 {len(category_changes) - 1} 次变化")
        total_frames_revolution = last_appear["Frame"] - first_appear["Frame"] + 1
        total_frames_rotation = last_change["Frame"] - first_change["Frame"] + 1
        total_frames_rotation_origin = (
            last_change["origin_frame"] - first_change["origin_frame"] + 1
        )
        box = closest_point_data.get("Box", [0, 0, 0, 0])
        if not get_latest_folder(base_path).endswith("-2"):
            height = (
                (box[1] + box[3]) / 2 / 147
            )  # + 42 / 147（0-1缺失的部分）不要了，因为高度从旋流器顶端算
        else:
            # 如果是下侧的话需要加上之前的高度, 减去重叠的部分
            height = (box[1] + box[3]) / 2 / 147 + 1024 / 147 - (40 + 147 + 17) / 147
            # 举例 ,6对应的位置是y=838,height=838/147,y2=17,height=837/147
        results[id_]["changes"] = (
            len(category_changes)
            - 1  # 如果是-2就是减去最后的那次变化的次数，同时保留倒数第二个状态的时间
        )
        results[id_]["category_changes"] = category_changes
        results[id_]["total_frames_revolution"] = total_frames_revolution
        results[id_]["start_frame_revolution"] = first_appear["Frame"]
        results[id_]["end_frame_revolution"] = last_appear["Frame"]
        results[id_]["total_frames_rotation"] = total_frames_rotation
        results[id_]["start_frame_rotation"] = first_change["Frame"]
        results[id_]["end_frame_rotation"] = last_change["Frame"]
        results[id_]["d1_with_range_revolution"] = d1_with_range_revolution
        results[id_]["d2_with_range_revolution"] = d2_with_range_revolution
        results[id_]["d1_origin"] = d1_origin
        results[id_]["d2_origin"] = d2_origin
        results[id_]["inner_diameter"] = d_total
        results[id_]["closest_point"] = closest_point_data
        results[id_]["height"] = height
        if len(category_changes_with_all) < 2:
            print(f"Not enough frames to process for id: {i}")
            results[id_]["not_use_rotation"] = True
            results[id_]["reason"] = "Not enough frames to process"
            continue
        # d1_with_range_revolution和d2_with_range_revolution比例要相近
        if (
            min(d1_with_range_revolution, d2_with_range_revolution)
            / max(d1_with_range_revolution, d2_with_range_revolution)
            < 0.6
        ):
            results[id_]["must_not_use"] = True
            # results[id_]["not_use"] = True
            results[id_]["reason"] = "the difference between d1 and d2 is too large"
            print(f"id {i} Category 两点距离比例差距过大，不计算")
        if (
            height > 10.5
        ):  # 10.68相对于刻度尺的11cm,（1024+751）/147 - (40+147+17)/147=10.68   H/D
            results[id_]["not_use_rotation"] = True
            print(f"id {i} Category 高度大于10.68，只计算公转速")
        if len(category_changes) < 3:
            results[id_]["not_use_rotation"] = True
            print(f"id {i} Category 在指定范围内次数变化小于3，只计算公转速")
        else:
            print(f"id {i} Category 在指定范围内发生了大于2次变化")
        if total_frames_rotation_origin / total_frames_revolution < 0.4:
            results[id_]["not_use_rotation"] = True
            print(f"id {i} Category 旋转时间占比小于0.4，只计算公转速度")

    # 在整个循环结束后，将所有统计信息保存到一个文件中
    stats_filepath = os.path.join(initial_result_directory, "all_stats.json")

    # 如果文件存在，则读取现有数据，否则初始化为空字典
    if os.path.exists(stats_filepath):
        with open(stats_filepath, "r") as stats_file:
            try:
                all_stats = json.load(stats_file)  # 读取现有统计信息
            except json.JSONDecodeError:
                # 如果文件内容为空或非JSON格式，初始化为空字典
                all_stats = {}
    else:
        all_stats = {}

    # 更新现有统计数据或添加新的统计数据
    for id_, result in results.items():
        # 初始化ID对应的字典
        if f"{id_}" not in all_stats:
            all_stats[f"{id_}"] = {}
        # 统计信息按照ID更新或新增
        all_stats[f"{id_}"].update(
            OrderedDict(
                [
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
                    ("height", result.get("height")),
                    ("not_use", result.get("not_use")),
                    ("not_use_rotation", result.get("not_use_rotation")),
                    ("must_not_use", result.get("must_not_use")),
                    ("reason", result.get("reason")),
                ]
            )
        )
        # print("id", id_)
        # print(
        #     f"ID: {id_}, 变化次数: {result['changes']}, 总公转帧数: {result['total_frames_revolution']}, "
        #     f"Category Changes: {result['changes']}, height："
        #     f"{height}cm"
        # )
    all_stats = remove_empty(all_stats)
    all_stats = detect_frame_difference(all_stats)
    # 将更新后的统计数据写回文件
    with open(stats_filepath, "w") as stats_file:
        json.dump(all_stats, stats_file, indent=4)


if __name__ == "__main__":
    process_data()
