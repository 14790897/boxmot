# 147，101是y,x像素对厘米的比例; 什么是相对自转速度什么是绝对自转速度？计算方式得看huanyuan的论文。 用X图片检测边距是因为它是中间的，比较准确
# 计算公转速度的时候应该使用弦长公式而不是弧长公式，其实不是，因为投影不是在弦的位置
import math
import json
import os

initial_result_directory = "initial_result"
stats_file_path = os.path.join(initial_result_directory, "all_stats.json")
calculation_results_path = os.path.join(
    initial_result_directory, "calculation_results.json"
)

if os.path.exists(stats_file_path):
    with open(stats_file_path, "r") as stats_file:
        all_stats = json.load(stats_file)
else:
    print("all_stats.json 文件不存在，退出")
    exit()
calculation_results = []

# 遍历字典并将数据赋值给变量
for key, value in all_stats.items():
    try:
        not_use = value.get("not_use", False)
        # if not_use:
        #     # print(f"跳过编号为 {key} 的条目,因为误差较大")
        #     continue
        changes = value.get("changes")
        closest_point = value.get("closest_point")
        total_frames_revolution = value.get("total_frames_revolution")
        total_frames_rotation = value.get("total_frames_rotation")
        d1_with_range_revolution = value.get(
            "d1_with_range_revolution", None
        )  # 使用 .get() 方法获取键值，如果不存在则默认为 None
        d2_with_range_revolution = value.get("d2_with_range_revolution", None)
        d1_origin = value.get("d1_origin", None)
        d2_origin = value.get("d2_origin", None)
        inner_diameter = value.get("inner_diameter", None)
        margin = value.get("margin", None) 
        # origin_data = value.get("origin_data", [])

        if None in [
            d1_with_range_revolution,
            d2_with_range_revolution,
            d1_origin,
            d2_origin,
            inner_diameter,
            margin,
        ]:
            raise ValueError(f"缺少必要的参数在编号为 {key} 的条目中，跳过计算。")
        radius = (
            inner_diameter / 2 - margin * 640 / 360
        )  # 这里margin应该还要进行换算,缩放比例640/360

        # 遍历数据并进行过滤

        # 事实上可以这样子想如果说这个距离超过了使我们就可以认为他这个点可能这个时候还根本没有出现,所以就让它变成最大值
        if radius < d1_origin:
            # radius = max(d1, d2)
            radius = (
                inner_diameter / 2
            )  # 我觉得这里直接设置为半径是更好因为他那边可能真的是他暂时没有出现这个粒子
            print(
                f"{key} 的 d1 大于 radius, d1: {d1_with_range_revolution}, radius: {radius}, d1_origin: {d1_origin}, margin: {margin}"
            )
        if radius < d2_origin:
            # radius = max(d1, d2)
            radius = inner_diameter / 2
            print(
                f"{key} 的 d2 大于 radius, d2: {d2_with_range_revolution}, radius: {radius}, d2_origin: {d2_origin}, margin: {margin}"
            )
        # 防止 math domain error 的错误处理
        value1 = d1_with_range_revolution / radius
        value2 = d2_with_range_revolution / radius

        # if not (-1 <= value1 <= 1) or not (-1 <= value2 <= 1):
        #     raise ValueError(
        #         f"错误：{key} 的 d1 或 d2 大于radius, d1: {d1}, d2: {d2}, radius: {radius}"
        #     )

        alpha1 = math.asin(value1)
        alpha2 = math.asin(value2)
        # 8000是相机的帧数
        orbital_rev = (8000 * (alpha1 + alpha2)) / (
            total_frames_revolution - 1
        )  # 减一是因为这个才是真正时间
        abs_rotation = (changes * 3.1416 * 8000) / 2 / (total_frames_rotation - 1)
        rel_rotation = orbital_rev + abs_rotation
        if not_use:
            # print(f"跳过编号为 {key} 的条目,因为误差较大")
            result = f"id: {key}, revloution: {orbital_rev:.2f}rad/s"
        else:
            result = f"id: {key}, revloution: {orbital_rev:.2f}rad/s，rotation: {abs_rotation:.2f}rad/s, relative: {rel_rotation:.2f}rad/s, height: {(closest_point.get("Box")[1]+closest_point.get("Box")[3])/2}"
        all_stats[key].update(
            {
                "orbital_rev": orbital_rev,
                "abs_rotation": abs_rotation,
                "rel_rotation": rel_rotation,
            }
        )
        print(result)
        calculation_results.append(result)

    except ValueError as e:
        print(f"Error processing entry with key {key}: {e}")
    except Exception as e:
        print(f"Unexpected error processing entry with key {key}: {e}")

# 可以选择将更新后的 all_stats 写回文件
with open(stats_file_path, "w") as stats_file:
    json.dump(all_stats, stats_file, indent=4)
with open(calculation_results_path, "w") as calc_file:
    json.dump(calculation_results, calc_file, indent=4)
