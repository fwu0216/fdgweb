# FDG Web

一个 Flask Web 应用，提供两个功能：

1. **F18-FDG 分装计算器**
   - 输入体重（空格分隔）、剂量系数（默认 0.15）、批次人数上限
   - 支持开启/关闭第二批和第三批
   - 输出总剂量和详细剂量列表

2. **廊坊订药短信生成**
   - 三个批次可启用/关闭
   - 每批 FDG 剂量（mCi）、“刻度到”时间、“送达时间”可调整
   - 自动生成短信模板

## 本地运行

```bash
pip install -r requirements.txt
python app.py
```

访问 http://127.0.0.1:10000

## 上传到 GitHub
- 创建空仓库
- 在网页端用 “Add file → Upload files” 上传本 ZIP，GitHub 自动解压
- 可直接连接 Render 部署
