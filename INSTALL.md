# 环境安装指南

## 1. 安装 Python

从官网下载 Python 3.12：https://www.python.org/ftp/python/pymanager/python-manager-25.2.msix

安装时勾选 **"Add Python to PATH"**。

## 2. 安装项目依赖

```bash
pip install poetry
poetry install --with yolo  # installed boxmot + yolo dependencies
poetry shell 
```

## 3. 运行

```bash
python app.py
```

启动后在浏览器中打开终端显示的 URL（默认 http://127.0.0.1:7860 ）。
