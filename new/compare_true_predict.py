import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os
from matplotlib.ticker import AutoMinorLocator

# 检查是否需要非交互式模式（用于批处理）
if len(sys.argv) > 1 and sys.argv[1] == "--save":
    matplotlib.use('Agg')  # 使用非交互式后端
    SAVE_MODE = True
else:
    SAVE_MODE = False

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 16  # 设置全局字体大小

def load_comparison_data():
    """
    从 Excel 文件中加载真实数据和预测数据进行对比
    """
    # 读取 Excel 文件，第一行作为表头
    data = pd.read_excel(
        r"C:\git-program\particle_detect\manual_caculate\data\relative error.xlsx",
        sheet_name="Sheet1",
        header=0,  # 第一行作为表头
    )
    
    print("原始数据形状:", data.shape)
    print("列名:", data.columns.tolist())
    
    # 确保相关列转换为数值类型
    numeric_columns = ['height', 'diameter', 'TRUE_rotation', 'TRUE_revolution', 'predict_rotation', 'predict_revolution', 'H/D']
    for col in numeric_columns:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    
    # 如果没有H/D列，则计算
    if 'H/D' not in data.columns and 'height' in data.columns and 'diameter' in data.columns:
        data["H/D"] = data["height"] / data["diameter"] * 147
    
    # 处理 flow_velocity 列
    if 'flow_velocity' in data.columns:
        data['flow_velocity'] = data['flow_velocity'].astype(str)
    else:
        print("警告：表格中没有找到 'flow_velocity' 列")
        return pd.DataFrame()
    
    # 只过滤掉flow_velocity为空的数据
    valid_data = data[data['flow_velocity'].notna()]
    valid_data = valid_data[valid_data['flow_velocity'] != 'nan']
    valid_data = valid_data[valid_data['flow_velocity'] != 'None']
    
    print(f"有效数据行数: {len(valid_data)}")
    if len(valid_data) > 0:
        print("流速分组:", valid_data['flow_velocity'].unique())
    
    return valid_data

def standardize_flow_velocity(flow_vel):
    """
    标准化流速名称，将不同变体统一为基础名称
    """
    flow_str = str(flow_vel).replace('.0', '').split('-')[0].split('.')[0]
    return flow_str

def plot_comparison():
    """
    绘制真实数据与预测数据的对比图
    """
    # 加载数据
    data = load_comparison_data()
    
    if data.empty:
        print("没有有效数据可以绘制")
        return
    
    # 标准化流速名称
    data['flow_velocity_std'] = data['flow_velocity'].apply(standardize_flow_velocity)
    
    # 按流速分组
    flow_groups = data.groupby('flow_velocity_std')
    unique_flows = sorted(data['flow_velocity_std'].unique())
    
    print(f"发现 {len(unique_flows)} 个不同的流速条件: {unique_flows}")
    
    # 创建子图 - 每个流速一个子图
    n_flows = len(unique_flows)
    fig, axes = plt.subplots(n_flows, 1, figsize=(10, 4.5 * n_flows),
                            gridspec_kw={'hspace': 0.3})

    # 如果只有一个流速，确保axes是数组
    if n_flows == 1:
        axes = [axes]

    # 为每个流速创建合并的对比图
    for i, flow_vel in enumerate(unique_flows):
        flow_data = flow_groups.get_group(flow_vel)

        print(f"处理流速 {flow_vel}: {len(flow_data)} 个数据点")

        ax = axes[i]

        # 收集所有速度数据用于确定Y轴范围和断裂位置
        all_speeds = []
        rotation_speeds = []
        revolution_speeds = []

        # 处理旋转数据
        rotation_data = flow_data.dropna(subset=['height','TRUE_rotation', 'predict_rotation'])

        if len(rotation_data) > 0:
            # MANUAL 自转（蓝色圆圈）
            ax.scatter(
                rotation_data['height'],
                rotation_data['TRUE_rotation'],
                alpha=0.8,
                color='blue',
                marker='o',
                s=80,
                label='Rotation (MANUAL)' if i == 0 else None
            )
            # THIS STUDY 自转（红色三角）
            ax.scatter(
                rotation_data['height'],
                rotation_data['predict_rotation'],
                alpha=0.8,
                color='red',
                marker='^',
                s=80,
                label='Rotation (THIS STUDY)' if i == 0 else None
            )
            all_speeds.extend(rotation_data['TRUE_rotation'].tolist())
            all_speeds.extend(rotation_data['predict_rotation'].tolist())
            rotation_speeds.extend(rotation_data['TRUE_rotation'].tolist())
            rotation_speeds.extend(rotation_data['predict_rotation'].tolist())

            print(f"  - 旋转数据点: {len(rotation_data)} 个")
        else:
            print("  - 无旋转数据")

        # 处理公转数据
        revolution_data = flow_data.dropna(subset=['height', 'TRUE_revolution', 'predict_revolution'])

        if len(revolution_data) > 0:
            # MANUAL 公转（绿色方块）
            ax.scatter(
                revolution_data['height'],
                revolution_data['TRUE_revolution'],
                alpha=0.8,
                color='green',
                marker='s',
                s=80,
                label='Revolution (MANUAL)' if i == 0 else None
            )
            # THIS STUDY 公转（橙色菱形）
            ax.scatter(
                revolution_data['height'],
                revolution_data['predict_revolution'],
                alpha=0.8,
                color='orange',
                marker='D',
                s=80,
                label='Revolution (THIS STUDY)' if i == 0 else None
            )

            all_speeds.extend(revolution_data['TRUE_revolution'].tolist())
            all_speeds.extend(revolution_data['predict_revolution'].tolist())
            revolution_speeds.extend(revolution_data['TRUE_revolution'].tolist())
            revolution_speeds.extend(revolution_data['predict_revolution'].tolist())

            print(f"  - 公转数据点: {len(revolution_data)} 个")
        else:
            print("  - 无公转数据")

        # 设置坐标轴
        ax.set_xlabel(r"$h$ (cm)")
        ax.set_ylabel("Speed (rad/s)")

        # 固定坐标轴范围
        ax.set_xlim(0, 11)
        ax.set_ylim(0, 3000)

        # 设置纵坐标刻度
        ax.set_yticks([0, 1000, 2000, 3000])

        # 添加子图标题 (a), (b), (c), (d), (e)
        subplot_labels = ['(a)', '(b)', '(c)', '(d)', '(e)']
        if i < len(subplot_labels):
            ax.set_title(subplot_labels[i], loc='left', x=-0.1, y=0.9)

        # 添加流速标注
        flow_text = f"{flow_vel} L/h"
        ax.text(0.98, 0.98, flow_text, transform=ax.transAxes,
        verticalalignment='top', horizontalalignment='right',
        fontsize=14)

        # 只在第一个子图显示图例
        if i == 0:
            ax.legend(loc="upper left", fontsize=12, framealpha=0.9, frameon=False)

        # 设置刻度
        ax.xaxis.set_minor_locator(AutoMinorLocator(2))
        ax.yaxis.set_minor_locator(AutoMinorLocator(2))
        ax.tick_params(which='minor', direction='in')
        ax.tick_params(which='major', direction='in')

    # 根据模式决定是显示还是保存图表
    if SAVE_MODE:
        # 保存图表
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)  # 上一级目录
        output_dir = os.path.join(project_root, "plots")
        os.makedirs(output_dir, exist_ok=True)

        plt.tight_layout()
        fig.savefig(os.path.join(output_dir, "comparison_by_flow.png"), dpi=300, bbox_inches='tight')

        print(f"图表已保存到: {output_dir}")
        print("  - comparison_by_flow.png (按流速对比)")

        plt.close('all')  # 关闭所有图表释放内存
    else:
        # plt.suptitle("TRUE vs PREDICT Data Comparison by Flow Velocity", fontsize=20, y=0.98)
        plt.show()
    
    # 创建总体对比图
    # create_overall_comparison(data)

def create_overall_comparison(data):
    """
    创建总体的真实值vs预测值散点图 - 使用单一纵坐标
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    # 收集所有速度数据
    all_speeds = []

    # 按流速着色
    unique_flows = sorted(data['flow_velocity_std'].unique())
    colors_rotation = ['blue', 'cyan', 'navy', 'steelblue', 'dodgerblue']
    colors_revolution = ['orange', 'coral', 'darkorange', 'orangered', 'tomato']

    # 旋转数据对比
    if 'TRUE_rotation' in data.columns and 'predict_rotation' in data.columns:
        valid_rotation = data.dropna(subset=['TRUE_rotation', 'predict_rotation'])

        for i, flow_vel in enumerate(unique_flows):
            flow_data = valid_rotation[valid_rotation['flow_velocity_std'] == flow_vel]
            if len(flow_data) > 0:
                # 蓝色系表示旋转
                ax.scatter(
                    flow_data['TRUE_rotation'],
                    flow_data['predict_rotation'],
                    alpha=0.7,
                    color=colors_rotation[i % len(colors_rotation)],
                    s=80,
                    marker='o'
                )
                all_speeds.extend(flow_data['TRUE_rotation'].tolist())
                all_speeds.extend(flow_data['predict_rotation'].tolist())

    # 公转数据对比
    if 'TRUE_revolution' in data.columns and 'predict_revolution' in data.columns:
        valid_revolution = data.dropna(subset=['TRUE_revolution', 'predict_revolution'])

        for i, flow_vel in enumerate(unique_flows):
            flow_data = valid_revolution[valid_revolution['flow_velocity_std'] == flow_vel]
            if len(flow_data) > 0:
                # 橙色系表示公转
                ax.scatter(
                    flow_data['TRUE_revolution'],
                    flow_data['predict_revolution'],
                    alpha=0.7,
                    color=colors_revolution[i % len(colors_revolution)],
                    s=80,
                    marker='^'
                )
                all_speeds.extend(flow_data['TRUE_revolution'].tolist())
                all_speeds.extend(flow_data['predict_revolution'].tolist())

    # 添加y=x参考线
    if len(all_speeds) > 0:
        min_val = min(all_speeds)
        max_val = max(all_speeds)
        ax.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.8, linewidth=2)
        ax.set_xlim(min_val * 0.95, max_val * 1.05)
        ax.set_ylim(min_val * 0.95, max_val * 1.05)

    ax.set_xlabel("MANUAL Speed (rad/s)")
    ax.set_ylabel("THIS STUDY Speed (rad/s)")

    # 设置刻度
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.tick_params(which='minor', direction='in')
    ax.tick_params(which='major', direction='in')
    ax.grid(True, alpha=0.3)

    # 根据模式决定是显示还是保存图表
    if SAVE_MODE:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        output_dir = os.path.join(project_root, "plots")
        os.makedirs(output_dir, exist_ok=True)

        plt.tight_layout()
        fig.savefig(os.path.join(output_dir, "comparison_overall.png"), dpi=300, bbox_inches='tight')
        print("  - comparison_overall.png (总体对比)")
        plt.close('all')
    else:
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    plot_comparison()