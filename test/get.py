import os

# 设置根目录
base_path = r"C:\git-program\particle_detect\manual_caculate\data\550"

# 存储所有相机2和相机1的路径
camera2_dirs = []
camera1_dirs = []

# 遍历 base_path，查找所有 "相机2" 目录
for root, dirs, files in os.walk(base_path):
    for dir_name in dirs:
        if dir_name == "相机2":
            camera2_path = os.path.join(root, dir_name)
            # **去掉路径中所有空格**
            camera2_path = camera2_path.replace(" ", "")
            camera2_dirs.append(camera2_path)

            # 生成对应的 "相机1" 目录
            camera1_path = camera2_path.replace("相机2", "相机1")
            camera1_dirs.append(camera1_path)

# 打印结果
print("相机2 目录：", ",".join(camera2_dirs))


print("\n相机1 目录：", ",".join(camera1_dirs))
