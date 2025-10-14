import matplotlib.pyplot as plt
import pandas as pd

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
    
    # 创建子图
    n_flows = len(unique_flows)
    fig, axes = plt.subplots(n_flows, 2, figsize=(15, 6 * n_flows), constrained_layout=True)
    
    # 如果只有一个流速，确保axes是二维数组
    if n_flows == 1:
        axes = axes.reshape(1, -1)
    
    # 为每个流速创建对比图
    for i, flow_vel in enumerate(unique_flows):
        flow_data = flow_groups.get_group(flow_vel)
        
        print(f"处理流速 {flow_vel}: {len(flow_data)} 个数据点")
        
        # 左图：旋转对比
        # 分别处理有旋转数据的点
        rotation_data = flow_data.dropna(subset=['H/D','TRUE_rotation', 'predict_rotation'])
        
        if len(rotation_data) > 0:
            # 散点图
            axes[i, 0].scatter(
                rotation_data['H/D'], 
                rotation_data['TRUE_rotation'], 
                alpha=0.8, 
                color='blue', 
                label=f'MANUAL {flow_vel}',
                marker='o'
            )
            axes[i, 0].scatter(
                rotation_data['H/D'], 
                rotation_data['predict_rotation'], 
                alpha=0.8, 
                color='red', 
                label=f'THIS STUDY {flow_vel}',
                marker='^'
            )
            
            # 连线显示对应关系
            for idx, row in rotation_data.iterrows():
                axes[i, 0].plot(
                    [row['H/D'], row['H/D']], 
                    [row['TRUE_rotation'], row['predict_rotation']], 
                    'k--', alpha=0.3, linewidth=0.5
                )
            
            print(f"  - 旋转数据点: {len(rotation_data)} 个")
        else:
            print("  - 无旋转数据")
            axes[i, 0].text(0.5, 0.5, 'No Rotation Data', 
                          transform=axes[i, 0].transAxes, 
                          ha='center', va='center', fontsize=14)
        
        axes[i, 0].set_xlabel(r"$h/D$")
        axes[i, 0].set_ylabel("Rotation (rad/s)")
        axes[i, 0].set_title(f"Rotation Comparison - Flow {flow_vel}", fontsize=18)
        axes[i, 0].legend(loc="upper right")
        axes[i, 0].grid(True, alpha=0.3)
        
        # 右图：公转对比
        # 分别处理有公转数据的点
        revolution_data = flow_data.dropna(subset=['H/D', 'TRUE_revolution', 'predict_revolution'])
        
        if len(revolution_data) > 0:
            # 散点图
            axes[i, 1].scatter(
                revolution_data['H/D'], 
                revolution_data['TRUE_revolution'], 
                alpha=0.8, 
                color='green', 
                label=f'MANUAL {flow_vel}',
                marker='o'
            )
            axes[i, 1].scatter(
                revolution_data['H/D'], 
                revolution_data['predict_revolution'], 
                alpha=0.8, 
                color='orange', 
                label=f'THIS STUDY {flow_vel}',
                marker='^'
            )
            
            # 连线显示对应关系
            for idx, row in revolution_data.iterrows():
                axes[i, 1].plot(
                    [row['H/D'], row['H/D']], 
                    [row['TRUE_revolution'], row['predict_revolution']], 
                    'k--', alpha=0.3, linewidth=0.5
                )
            
            print(f"  - 公转数据点: {len(revolution_data)} 个")
        else:
            print("  - 无公转数据")
            axes[i, 1].text(0.5, 0.5, 'No Revolution Data', 
                          transform=axes[i, 1].transAxes, 
                          ha='center', va='center', fontsize=14)
        
        axes[i, 1].set_xlabel(r"$h/D$")
        axes[i, 1].set_ylabel("Revolution (rad/s)")
        axes[i, 1].set_title(f"Revolution Comparison - Flow {flow_vel}", fontsize=18)
        axes[i, 1].legend(loc="upper right")
        axes[i, 1].grid(True, alpha=0.3)
    
    # plt.suptitle("TRUE vs PREDICT Data Comparison by Flow Velocity", fontsize=20, y=0.98)
    plt.show()
    
    # 创建总体对比图
    create_overall_comparison(data)

def create_overall_comparison(data):
    """
    创建总体的真实值vs预测值散点图
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), constrained_layout=True)
    
    # 左图：旋转数据对比
    if 'TRUE_rotation' in data.columns and 'predict_rotation' in data.columns:
        valid_rotation = data.dropna(subset=['H/D','TRUE_rotation', 'predict_rotation'])
        
        # 按流速着色
        unique_flows = sorted(data['flow_velocity_std'].unique())
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
        
        for i, flow_vel in enumerate(unique_flows):
            flow_data = valid_rotation[valid_rotation['flow_velocity_std'] == flow_vel]
            axes[0].scatter(
                flow_data['TRUE_rotation'], 
                flow_data['predict_rotation'],
                alpha=0.7,
                color=colors[i % len(colors)],
                label=f'Flow {flow_vel}',
                s=60
            )
        
        # 添加y=x参考线
        min_val = min(valid_rotation['TRUE_rotation'].min(), valid_rotation['predict_rotation'].min())
        max_val = max(valid_rotation['TRUE_rotation'].max(), valid_rotation['predict_rotation'].max())
        axes[0].plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.8, label='Perfect Prediction')
        
        axes[0].set_xlabel("MANUAL Rotation (rad/s)")
        axes[0].set_ylabel("THIS STUDY Rotation (rad/s)")
        axes[0].set_title("MANUAL vs THIS STUDY - Rotation", fontsize=18)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
    
    # 右图：公转数据对比
    if 'TRUE_revolution' in data.columns and 'predict_revolution' in data.columns:
        valid_revolution = data.dropna(subset=['H/D','TRUE_revolution', 'predict_revolution'])
        
        for i, flow_vel in enumerate(unique_flows):
            flow_data = valid_revolution[valid_revolution['flow_velocity_std'] == flow_vel]
            axes[1].scatter(
                flow_data['TRUE_revolution'], 
                flow_data['predict_revolution'],
                alpha=0.7,
                color=colors[i % len(colors)],
                label=f'Flow {flow_vel}',
                s=60
            )
        
        # 添加y=x参考线
        min_val = min(valid_revolution['TRUE_revolution'].min(), valid_revolution['predict_revolution'].min())
        max_val = max(valid_revolution['TRUE_revolution'].max(), valid_revolution['predict_revolution'].max())
        axes[1].plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.8, label='Perfect Prediction')
        
        axes[1].set_xlabel("MANUAL Revolution (rad/s)")
        axes[1].set_ylabel("THIS STUDY Revolution (rad/s)")
        axes[1].set_title("MANUAL vs THIS STUDY - Revolution", fontsize=18)
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
    
    # plt.suptitle("Overall MANUAL vs THIS STUDY Comparison", fontsize=20)
    plt.show()

if __name__ == "__main__":
    plot_comparison()