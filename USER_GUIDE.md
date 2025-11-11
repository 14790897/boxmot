# Particle Processing 用户指南

## 快速开始

### 启动应用
```bash
gradio app.py  # 支持热重载，开发推荐
# 或
python app.py  # 普通模式
```

浏览器访问：http://127.0.0.1:7860

---

## 功能说明

### 1. 配置保存目录

在界面顶部展开 **"YOLO Save Directory Configuration"**，可以配置：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| Y-axis Tracking Project | Y轴跟踪结果保存目录 | `runs/track` |
| Y-axis Tracking Name | Y轴跟踪实验名称 | `exp` |
| X-axis Detection Project | X轴检测结果保存目录 | `runs_x_me/detect` |
| X-axis Detection Name | X轴检测实验名称 | `exp` |
| Video Output Directory | 视频输出目录 | `processed_video_gradio` |

修改后点击 **"Save Configuration"** 保存，或点击 **"Reset to Default"** 恢复默认。

配置保存在 `config.json` 文件中，重启后仍然有效。

---

### 2. 处理数据

#### 方式1：上传视频（适合单次测试）

1. 选择 **"upload video"**
2. 分别上传 Y 和 X 视频文件
3. 勾选是否需要 "classify"
4. 设置 "Max Files Per Folder"（可选，留空表示全部处理）
5. 点击 **"start process"**

#### 方式2：输入文件夹路径（适合少量批处理）

1. 选择 **"upload folder"**
2. 在输入框中输入目录路径，多个目录用逗号分隔：
   ```
   Y目录1, Y目录2, Y目录3
   ```
3. X目录会自动复制Y目录的输入（可手动修改）
4. 设置其他选项并点击 **"start process"**

#### 方式3：批量文件配置（适合大量批处理）⭐推荐

1. 创建配置文件 `batch_directories.txt`：
   ```text
   # 这是注释
   Y目录1, X目录1
   Y目录2, X目录2
   Y目录3, X目录3
   ```

2. 在界面选择 **"batch file"**
3. 输入配置文件路径（如 `batch_directories.txt`）
4. 设置其他选项并点击 **"start process"**

**批量文件格式说明：**
- 每行一对目录，用逗号或Tab分隔
- `#` 开头的行是注释
- 空行会被忽略
- 路径可以包含中文

**示例：**
```text
# 实验批次1 - Y1系列
H:\data\y1-450\cam1, H:\data\x1-450\acq1
H:\data\y1-550\cam1, H:\data\x1-550\acq1
H:\data\y1-650\cam1, H:\data\x1-650\acq1

# 实验批次2 - Y2系列  
H:\data\y2-450\cam1, H:\data\x2-450\acq1
H:\data\y2-550\cam1, H:\data\x2-550\acq1
```

---

### 3. 限制处理文件数量（新功能）

在 **"Max Files Per Folder"** 输入框中设置每个文件夹最多处理多少个文件：

| 设置 | 效果 | 适用场景 |
|------|------|----------|
| 留空或0 | 处理所有文件 | 生产环境、完整处理 |
| 5 | 只处理前5个 | 快速测试流程 |
| 10-20 | 处理前10-20个 | 功能调试验证 |
| 50-100 | 处理前50-100个 | 部分数据分析 |

**优点：**
- ⚡ 快速测试不需要等待处理所有文件
- 💾 节省磁盘空间和内存
- 🐛 调试时更高效

**示例：**
```
目录有500个文件，设置Max=10
→ 只处理前10个文件，耗时约为原来的2%
```

---

## 处理选项

### Classify（分类）
- 勾选：对结果进行分类处理
- 不勾选：不分类

### Max Files Per Folder（文件数量限制）
- 留空：处理所有文件
- 输入数字：只处理前N个文件

---

## 其他功能

### Clear Folder（清理文件夹）
点击 **"clear folder"** 按钮可以清空以下目录：
- Y轴跟踪结果目录
- X轴检测结果目录  
- 视频输出目录

---

## 常见问题

### Q1: 配置文件在哪里？
**A:** `config.json` 在项目根目录，可以直接编辑。

### Q2: 批量文件目录不存在怎么办？
**A:** 会显示警告并跳过该目录，其他目录正常处理。

### Q3: 如何查看处理进度？
**A:** 查看控制台输出，会显示当前处理状态和文件数量。

### Q4: 处理失败怎么办？
**A:** 查看控制台错误信息，检查：
- 目录路径是否正确
- 目录是否包含有效的图片文件
- 磁盘空间是否充足

### Q5: 如何重复处理相同配置？
**A:** 使用批量文件方式，保存配置文件后可以随时重复使用。

---

## 配置文件示例

### config.json
```json
{
  "yolo_save_directories": {
    "y_track_project": "runs/track",
    "y_track_name": "exp",
    "x_detect_project": "runs_x_me/detect",
    "x_detect_name": "exp",
    "video_output": "processed_video_gradio"
  },
  "processing_options": {
    "max_files_per_folder": null
  }
}
```

### batch_directories.txt
```text
# Y目录, X目录（逗号分隔）
H:\data\y1-450\cam1, H:\data\x1-450\acq1
H:\data\y1-550\cam1, H:\data\x1-550\acq1
```

---

## 最佳实践

### 开发测试阶段
1. 使用 `gradio app.py` 启动（支持热重载）
2. 设置 Max Files = 5-10
3. 选择单个目录快速测试

### 批量处理阶段  
1. 创建批量配置文件
2. 添加详细注释说明实验信息
3. 留空 Max Files（处理所有）
4. 使用版本控制保存配置文件

### 生产环境
1. 使用 `python app.py` 启动
2. 确保配置文件正确
3. 处理前检查磁盘空间
4. 保存处理日志

---

## 技巧提示

1. **批量文件命名**：使用有意义的名称，如 `batch_20251106_experiment1.txt`

2. **目录组织**：建议按日期或实验批次组织目录结构

3. **配置备份**：定期备份 `config.json` 和批量配置文件

4. **测试先行**：处理大量数据前，先用少量文件测试

5. **日志查看**：处理过程中注意查看控制台输出，及时发现问题

---

## 控制台输出示例

```bash
# 启动应用
Watching: 'C:\...\boxmot'
Running on local URL: http://127.0.0.1:7860

# 处理信息
Max files per folder: 10
Processing 10 files (limited to 10) from H:\data\y1-450\cam1
Processing 10 files (limited to 10) from H:\data\x1-450\acq1

# 批量文件加载
Added directory pair: Y=H:\data\y1-450\cam1, X=H:\data\x1-450\acq1
Added directory pair: Y=H:\data\y1-550\cam1, X=H:\data\x1-550\acq1
Loaded 2 directory pairs from batch_directories.txt
```

---

## 帮助与支持

- 配置问题：检查 `config.json` 文件
- 批量处理：参考 `batch_directories.txt` 模板
- 更多信息：查看项目 README.md

---

**版本信息**
- 支持热重载
- 支持批量目录处理
- 支持文件数量限制
- 支持配置持久化
