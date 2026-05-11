"""
智能简历改写助手 - 根据岗位描述定制简历
"""

import streamlit as st
from openai import OpenAI
import io
import os
import re
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

st.set_page_config(page_title="智能简历改写助手", page_icon="📝", layout="wide")

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o"

SYSTEM_PROMPT = """你是一位资深HR顾问和简历优化专家。你的任务是根据目标岗位描述（JD），改写用户的简历，使其更匹配目标岗位。

改写原则：
1. **关键词匹配**：从JD中提取核心技能、资质要求和关键词，自然地融入简历中
2. **经验重塑**：重写工作经验的描述，突出与目标岗位相关的成就和技能，使用STAR法则
3. **量化成果**：尽可能用数据量化工作成果（如提升XX%、节省XX万等）
4. **保持真实**：不捏造经历，只调整表达方式和侧重点。教育背景、个人信息、时间线等事实性内容保持不变
5. **语言一致**：输出语言与原始简历一致（中文简历输出中文，英文简历输出英文）
6. **专业措辞**：使用该行业的专业术语，提升简历的专业感

输出格式：
- 直接输出改写后的完整简历内容
- 使用清晰的段落和层级结构
- 不要输出额外的解释或说明"""

ANALYSIS_PROMPT = """请分析这份简历与目标岗位的匹配情况，给出简短的改写说明：

1. **JD核心要求**（列出3-5个关键要求）
2. **简历匹配点**（已有的相关经验）
3. **需要强化的点**（哪些方面需要重点改写）
4. **改写策略**（简要说明改写方向）

请用中文回答，简明扼要。"""


def extract_text_from_pdf(file) -> str:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        st.error(f"PDF解析失败: {e}")
        return ""


def extract_text_from_docx(file) -> str:
    try:
        doc = Document(file)
        text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        return text.strip()
    except Exception as e:
        st.error(f"Word文档解析失败: {e}")
        return ""


def create_docx(text: str) -> bytes:
    doc = Document()
    style = doc.styles['Normal']
    font = style.font
    font.name = '微软雅黑'
    font.size = Pt(11)
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('# '):
            doc.add_heading(line[2:], level=1)
        elif line.startswith('## '):
            doc.add_heading(line[3:], level=2)
        elif line.startswith('### '):
            doc.add_heading(line[4:], level=3)
        elif line.startswith('- ') or line.startswith('• '):
            doc.add_paragraph(line[2:], style='List Bullet')
        elif re.match(r'^\d+\.\s', line):
            content = re.sub(r'^\d+\.\s', '', line)
            doc.add_paragraph(content, style='List Number')
        else:
            p = doc.add_paragraph()
            parts = re.split(r'(\*\*.*?\*\*)', line)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    run = p.add_run(part[2:-2])
                    run.bold = True
                else:
                    p.add_run(part)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def call_llm(api_key: str, base_url: str, model: str, system: str, user_message: str, max_tokens: int = 4096) -> str:
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message.content


st.title("📝 智能简历改写助手")
st.caption("上传简历 + 粘贴岗位描述 → AI 帮你量身定制简历")

with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("API Key", type="password", value=os.environ.get("OPENAI_API_KEY", ""), help="OpenAI 或兼容平台的 API Key")
    base_url = st.text_input("API Base URL", value=os.environ.get("OPENAI_BASE_URL", DEFAULT_BASE_URL), help="默认 OpenAI 官方地址，代理平台请填对应地址")
    model = st.text_input("模型名称", value=os.environ.get("MODEL_NAME", DEFAULT_MODEL), help="如 gpt-4o, gpt-4o-mini, gpt-3.5-turbo 等")
    st.divider()
    st.markdown("**使用说明：**\n1. 输入 API Key 和配置\n2. 上传简历或粘贴文本\n3. 粘贴目标岗位描述\n4. 点击「开始改写」\n5. 下载改写后的简历")

col1, col2 = st.columns(2)
with col1:
    st.subheader("📄 原始简历")
    upload_method = st.radio("输入方式", ["上传文件", "粘贴文本"], horizontal=True, label_visibility="collapsed")
    resume_text = ""
    if upload_method == "上传文件":
        uploaded_file = st.file_uploader("上传简历", type=["pdf", "docx", "doc", "txt"], help="支持 PDF、Word、TXT 格式")
        if uploaded_file:
            if uploaded_file.name.endswith('.pdf'):
                resume_text = extract_text_from_pdf(uploaded_file)
            elif uploaded_file.name.endswith(('.docx', '.doc')):
                resume_text = extract_text_from_docx(uploaded_file)
            elif uploaded_file.name.endswith('.txt'):
                resume_text = uploaded_file.read().decode('utf-8')
            if resume_text:
                st.text_area("简历内容预览", resume_text, height=400, disabled=True)
    else:
        resume_text = st.text_area("粘贴简历内容", height=400, placeholder="在此粘贴你的简历全文...")

with col2:
    st.subheader("🎯 目标岗位描述")
    jd_text = st.text_area("粘贴JD", height=400, placeholder="在此粘贴目标岗位的招聘描述...", label_visibility="collapsed")

st.divider()
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
with col_btn2:
    rewrite_btn = st.button("🚀 开始改写", type="primary", use_container_width=True, disabled=not (resume_text and jd_text and api_key))

if not api_key:
    st.info("👈 请先在左侧输入 API Key")
elif not resume_text:
    st.info("📄 请上传或粘贴简历")
elif not jd_text:
    st.info("🎯 请粘贴目标岗位描述")

if rewrite_btn and resume_text and jd_text and api_key:
    with st.status("🔍 分析岗位匹配度...", expanded=True) as status:
        try:
            analysis_input = f"## 原始简历\n{resume_text}\n\n## 目标岗位描述\n{jd_text}"
            analysis = call_llm(api_key, base_url, model, ANALYSIS_PROMPT, analysis_input, max_tokens=1024)
            st.markdown(analysis)
            status.update(label="✅ 分析完成", state="complete")
        except Exception as e:
            st.error(f"分析失败: {e}")
            st.stop()
    with st.status("✍️ 正在改写简历...", expanded=False) as status:
        try:
            rewrite_input = f"## 原始简历\n{resume_text}\n\n## 目标岗位描述\n{jd_text}\n\n请根据目标岗位描述改写这份简历。"
            rewritten = call_llm(api_key, base_url, model, SYSTEM_PROMPT, rewrite_input)
            status.update(label="✅ 改写完成", state="complete")
        except Exception as e:
            st.error(f"改写失败: {e}")
            st.stop()
    st.divider()
    st.subheader("✨ 改写结果")
    result_col1, result_col2 = st.columns(2)
    with result_col1:
        st.markdown("**📄 原始简历**")
        st.text_area("原始", resume_text, height=500, disabled=True, label_visibility="collapsed")
    with result_col2:
        st.markdown("**✨ 改写后简历**")
        st.text_area("改写后", rewritten, height=500, disabled=True, label_visibility="collapsed")
    st.divider()
    dl_col1, dl_col2, dl_col3 = st.columns([1, 1, 1])
    with dl_col1:
        docx_bytes = create_docx(rewritten)
        st.download_button(label="📥 下载 Word 文档", data=docx_bytes, file_name="改写简历.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    with dl_col2:
        st.download_button(label="📥 下载纯文本", data=rewritten.encode('utf-8'), file_name="改写简历.txt", mime="text/plain", use_container_width=True)
