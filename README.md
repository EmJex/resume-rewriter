# 📝 智能简历改写助手

根据目标岗位描述（JD），AI 自动改写简历，突出相关经验和技能。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置 API Key（也可以在页面左侧输入）
export ANTHROPIC_API_KEY="sk-ant-xxx"

# 3. 启动
streamlit run app.py
```

浏览器自动打开 http://localhost:8501

## 功能

- 📄 支持上传 PDF / Word / TXT 简历，或直接粘贴文本
- 🎯 粘贴目标岗位 JD，AI 自动分析匹配度
- ✍️ 智能改写：匹配关键词、突出相关经验、量化成果
- 📥 一键下载改写后的 Word 文档
- 🔍 原始 vs 改写 对比查看

## 改写原则

- 从 JD 提取核心技能关键词，自然融入简历
- 用 STAR 法则重写工作经验
- 量化成果（提升XX%、节省XX万）
- **不捏造经历**，只调整表达和侧重点
- 教育背景、个人信息等事实不变
