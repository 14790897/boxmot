# 147，101是y,x像素对厘米的比例; 什么是相对自转速度什么是绝对自转速度？计算方式得看huanyuan的论文。 用X图片检测边距是因为它是中间的，比较准确
# 计算公转速度的时候应该使用弦长公式而不是弧长公式，其实不是，因为投影不是在弦的位置
import math
import json
import os
from process_utils import (
    get_latest_folder,
)

base_path = "runs/track"
initial_result_directory = os.path.join(get_latest_folder(base_path), "initial_result")
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
        revolution_notice = None
        not_use = value.get("not_use", False)
        not_use_rotation = value.get("not_use_rotation", False)
        not_use_revolution = value.get("not_use_revolution", False)
        must_not_use = value.get("must_not_use", False)
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
        height = value.get("height", None)
        # origin_data = value.get("origin_data", [])
        not_use_revolution_margin_large = False
        if margin is None:
            margin = 0
            not_use_revolution_margin_large = True
        if margin > 40:
            # margin = 8
            # must_not_use = True
            # 最好不进行公转速度的计算
            print(f"{key} 的 margin 大于 40, margin: {margin}")
            not_use_revolution_margin_large = True
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
            inner_diameter / 2 - margin * 147 / 101
        )  # 这里margin应该还要进行换算,缩放比例147 / 101

        # 遍历数据并进行过滤

        # 事实上可以这样子想如果说这个距离超过了使我们就可以认为他这个点可能这个时候还根本没有出现,所以就让它变成最大值
        if radius < d1_origin * 0.8:
            # radius = max(d1, d2)
            not_use_revolution = True
            if margin > 40:

                print(
                    f"{key} 的 d1_origin 大于 radius, radius: {radius}, d1_origin: {d1_origin}, margin: {margin}"
                )
                revolution_notice = (
                    f"d1_origin0.9:{d1_origin * 0.9} too large, radius: {radius}"
                )
                radius = (inner_diameter / 2) - 8 * 147 / 101
                not_use_revolution_margin_large = True
                # radius = max(
                #     d1_with_range_revolution, d2_with_range_revolution
                # )这是错误的
        if radius < d2_origin * 0.8:
            # radius = max(d1, d2)
            not_use_revolution = True
            if margin > 40:
                print(
                    f"{key} 的 d2_origin 大于 radius, radius: {radius}, d2_origin: {d2_origin}, margin: {margin}"
                )
                radius = inner_diameter / 2 - 8 * 147 / 101
                revolution_notice = (
                    f"d2_origin0.9:{d1_origin * 0.9} too large, radius: {radius}"
                )
                not_use_revolution_margin_large = True
            # radius = max(d1_with_range_revolution, d2_with_range_revolution)
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
        if not_use_revolution_margin_large:
            # margin 大于 18 的情况下不进行公转速度的计算
            orbital_rev = 0
        if not must_not_use:
            if not_use_rotation or not_use:
                # print(f"跳过编号为 {key} 的条目,因为误差较大")
                abs_rotation = 0
                rel_rotation = 0
                result = (
                    f"id: {key}, revolution: {orbital_rev:.2f} rad/s, height: {height}cm"
                    if not not_use_revolution
                    else f"id: {key}, revolution: {orbital_rev:.2f} rad/s, not_use_revolution, height: {height}cm"
                )
            else:
                abs_rotation = (
                    (changes * 3.1416 * 8000) / 2 / (total_frames_rotation - 1)
                )
                rel_rotation = orbital_rev + abs_rotation
                result = (
                    f"id: {key}, revolution: {orbital_rev:.2f}rad/s，rotation: {abs_rotation:.2f}rad/s, relative: {rel_rotation:.2f}rad/s, height: {height}cm"
                    if not not_use_revolution
                    else f"id: {key}, revolution: {orbital_rev:.2f}rad/s，rotation: {abs_rotation:.2f}rad/s, relative: {rel_rotation:.2f}rad/s, height: {height}cm, not_use_revolution"
                )
        else:
            orbital_rev = 0
            abs_rotation = 0
            rel_rotation = 0
            result = f"id: {key}, must_not_use, height: {height}cm"
        all_stats[key].update(
            {
                "orbital_rev": orbital_rev,
                "abs_rotation": abs_rotation,
                "rel_rotation": rel_rotation,
                "not_use_revolution": not_use_revolution,
                "revolution_notice": revolution_notice,
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
