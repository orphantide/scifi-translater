import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import traceback
import os
import json
import pandas as pd
import re
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv()

# ==========================================
# 0. 全局动态主题切换引擎 (原生 config.toml)
# ==========================================
def switch_native_theme(theme_name):
    os.makedirs(".streamlit", exist_ok=True)
    if theme_name == "明朗白昼 (Light Default)":
        config = """[theme]
base="light"
primaryColor="#007ACC"
"""
    elif theme_name == "银河深蓝 (Galaxy Blue)":
        config = """[theme]
base="dark"
backgroundColor="#0B132B"
secondaryBackgroundColor="#1C2541"
textColor="#E0F7FA"
primaryColor="#5BC0BE"
"""
    elif theme_name == "黑客帝国 (Matrix)":
        config = """[theme]
base="dark"
backgroundColor="#0E1117"
secondaryBackgroundColor="#002200"
textColor="#00FFC4"
primaryColor="#00FF00"
"""
    elif theme_name == "赛博霓虹 (Cyber Neon)":
        config = """[theme]
base="dark"
backgroundColor="#1A1A24"
secondaryBackgroundColor="#2D2D3B"
textColor="#F4D03F"
primaryColor="#FF007F"
"""
    else: # 极简护眼深灰 (Dark Care)
        config = """[theme]
base="dark"
backgroundColor="#1E1E1E"
secondaryBackgroundColor="#252526"
textColor="#D4D4D4"
primaryColor="#007ACC"
"""
    try:
        with open(".streamlit/config.toml", "r", encoding="utf-8") as f:
            current = f.read()
            if current == config:
                return False
    except FileNotFoundError:
        pass
    
    with open(".streamlit/config.toml", "w", encoding="utf-8") as f:
        f.write(config)
    return True # 返回 True 提醒需要重载

# 代理配置 (受环境变量 USE_LOCAL_PROXY 控制)
if os.getenv('USE_LOCAL_PROXY', 'false').lower() == 'true':
    proxy_port = os.getenv('PROXY_PORT', '7890')
    os.environ['http_proxy'] = f'http://127.0.0.1:{proxy_port}'
    os.environ['https_proxy'] = f'http://127.0.0.1:{proxy_port}'

st.set_page_config(page_title="星际科幻翻译高速平台", page_icon="📝", layout="wide")

# ==========================================
# 框架容器布局 (标题及右上角主题下拉)
# ==========================================
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.title("📝 科幻翻译高速平台")
with header_col2:
    theme_choice = st.selectbox(
        "光影主题切换",
        ["明朗白昼 (Light Default)", "极简护眼黑 (Dark Care)", "银河深蓝 (Galaxy Blue)", "黑客帝国 (Matrix)", "赛博霓虹 (Cyber Neon)"]
    )
    if switch_native_theme(theme_choice):
        st.rerun()

# 初始化 Session State
if 'segments' not in st.session_state:
    st.session_state.segments = []  
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0      
if 'ai_drafts' not in st.session_state:
    st.session_state.ai_drafts = {}         
if 'translations' not in st.session_state:
    st.session_state.translations = {}      

# ==========================================
# 词库本地目录与方法封装
# ==========================================
GLOS_DIR = "glossaries"
os.makedirs(GLOS_DIR, exist_ok=True)

def load_glossary(name):
    path = os.path.join(GLOS_DIR, f"{name}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data if isinstance(data, list) else []
            except Exception:
                return []
    return []

def save_glossary(name, data_list):
    path = os.path.join(GLOS_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2)

def clean_punctuation(text):
    text = text.strip()
    replacements = {',': '，', '.': '。', '!': '！', '?': '？'}
    for en, ch in replacements.items():
        text = text.replace(en, ch)
    return text

# ==========================================
# 1. 侧边栏：API 与词库管理
# ==========================================
st.sidebar.header("⚙️ API 配置")
provider = st.sidebar.selectbox("选择 Provider", ("Gemini", "OpenAI-Compatible"))
api_key = base_url = model_name = ""

if provider == "Gemini":
    api_key = st.sidebar.text_input("API Key", type="password", value=os.getenv('GEMINI_API_KEY', ''))
    gemini_models = ["gemini-3.1-pro", "gemini-3-flash", "gemini-3.1-flash-lite", "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    model_name = st.sidebar.selectbox("Model Name", gemini_models, index=4)
elif provider == "OpenAI-Compatible":
    base_url = st.sidebar.text_input("Base URL", value=os.getenv('OPENAI_BASE_URL', "https://api.openai.com/v1"))
    api_key = st.sidebar.text_input("API Key", type="password", value=os.getenv('OPENAI_API_KEY', ''))
    model_name = st.sidebar.text_input("Model Name", value=os.getenv('OPENAI_MODEL_NAME', "gpt-3.5-turbo"))

st.sidebar.markdown("---")
with st.sidebar.expander("📖 术语词库管理", expanded=False):
    glossary_files = [f.replace(".json", "") for f in os.listdir(GLOS_DIR) if f.endswith(".json")]
    if not glossary_files:
        save_glossary("默认科幻库", [])
        glossary_files = ["默认科幻库"]

    col1, col2 = st.columns([3, 1])
    with col1: selected_glos = st.selectbox("当前词库", glossary_files + ["--新建词库--"], label_visibility="collapsed")
    with col2:
        if st.button("➕新建"): st.session_state.show_new_glos = True

    if st.session_state.get('show_new_glos', False):
        new_name = st.text_input("新词库名称 (回车保存)")
        if new_name:
            save_glossary(new_name, [])
            st.session_state.show_new_glos = False
            st.rerun()

    if selected_glos and selected_glos != "--新建词库--":
        raw_glos_data = load_glossary(selected_glos)
        df = pd.DataFrame(raw_glos_data) if raw_glos_data else pd.DataFrame(columns=["原文", "核心译文", "标签", "备注"])
        for c in ["原文", "核心译文", "标签", "备注"]:
            if c not in df.columns: df[c] = ""
        df.fillna("", inplace=True)
        search_query = st.text_input("🔍 搜索过滤词条...")
        if search_query:
            mask = (df['原文'].str.contains(search_query, case=False, na=False)) | (df['核心译文'].str.contains(search_query, case=False, na=False))
            view_df = df[mask]
        else: view_df = df
            
        st.data_editor(view_df, key="glossary_editor", num_rows="dynamic", use_container_width=True, hide_index=True,
            column_config={"标签": st.column_config.SelectboxColumn("标签", options=["常驻", "临时"], default="常驻")})
        
        changes = st.session_state.get("glossary_editor", {})
        if changes and any(changes.values()): 
            for p in changes.get("deleted_rows", []): df.drop(index=view_df.index[p], inplace=True)
            for p_idx_str, col_updates in changes.get("edited_rows", {}).items():
                real_idx = view_df.index[int(p_idx_str)]
                for col, val in col_updates.items(): df.at[real_idx, col] = val
            if changes.get("added_rows", []):
                for row in changes["added_rows"]:
                    for c in ["原文", "核心译文", "备注"]: 
                        if c not in row: row[c] = ""
                    row["标签"] = row.get("标签", "常驻")
                df = pd.concat([df, pd.DataFrame(changes["added_rows"])], ignore_index=True)
            save_glossary(selected_glos, df.to_dict('records'))
            del st.session_state["glossary_editor"]
            st.rerun()

        if st.button("🧹 清理此表临时词", type="secondary"):
            df = df[df['标签'] != '临时']
            save_glossary(selected_glos, df.to_dict('records'))
            st.rerun()

# --- 百科查阅系统与智能 JSON 分块提取 ---
st.sidebar.markdown("---")
st.sidebar.subheader("🌍 百科资料库与录入器")
enc_query = st.sidebar.text_input("查询作家、作品或名词设定：")
if st.sidebar.button("🔍 智能检索"):
    if not api_key.strip():
        st.sidebar.error("请先填好 API Key。")
    elif not enc_query.strip():
         st.sidebar.warning("请输入搜索词。")
    else:
        with st.sidebar.status("检索大模型中...") as status:
            try:
                # 附加严格的 JSON 抽取指令以便用户下方一键录入修改
                enc_prompt = f"请详细查阅响应此条目的所有百科知识（如果是作家请提供生卒年/国籍/代表作；作品或组织请提供成立时间和背景缩写等）。\n\n此外，在文字介绍完成后，请务必以代码块提取出一个标准化词条结构，仅需：原文（全名）、核心译文（常用译名）、备注（生卒年/缩写/首次出场提示）。必须输出以下格式的JSON段落：\n```json\n{{\"原文\": \"...\", \"核心译文\": \"...\", \"备注\": \"...\"}}\n```\n\n查询内容：{enc_query}"
                if provider == "Gemini":
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(model_name)
                    try:
                        response = model.generate_content(enc_prompt, tools="google_search_retrieval")
                    except Exception:
                        response = model.generate_content(enc_prompt)
                    st.session_state.enc_log = response.text
                elif provider == "OpenAI-Compatible":
                    client = OpenAI(api_key=api_key, base_url=base_url)
                    response = client.chat.completions.create(model=model_name, messages=[{"role": "user", "content": enc_prompt}], max_tokens=1000)
                    st.session_state.enc_log = response.choices[0].message.content
                status.update(label="检索完成！", state="complete")
                
                # 正则匹配捕获 JSON
                match = re.search(r'```json\s*(\{.*?\})\s*```', st.session_state.enc_log, re.DOTALL)
                if match:
                    try:
                        st.session_state.enc_parsed = json.loads(match.group(1))
                    except Exception:
                        st.session_state.enc_parsed = None
                else: 
                    st.session_state.enc_parsed = None
                    
            except Exception as e:
                status.update(label="降级失败", state="error")
                st.sidebar.error(f"异常：{e}")

if st.session_state.get("enc_log"):
    st.sidebar.info(st.session_state.enc_log)
    
    # 解析出 JSON 则展示确认缓冲垫表单
    parsed = st.session_state.get("enc_parsed")
    if parsed:
        st.sidebar.markdown("##### 📌 检测到核心实体，请确认或修改后点击入库：")
        with st.sidebar.form("enc_add_form"):
            src_val = st.text_input("原文", value=parsed.get("原文", ""))
            ans_val = st.text_input("核心译文", value=parsed.get("核心译文", ""))
            note_val = st.text_input("备注", value=parsed.get("备注", ""))
            if st.form_submit_button("📥 确认落库 (自动转为侧边栏常驻词)", type="primary"):
                if selected_glos and selected_glos != "--新建词库--":
                    raw_data = load_glossary(selected_glos)
                    raw_data.append({
                        "原文": src_val.strip(),
                        "核心译文": ans_val.strip(),
                        "标签": "常驻",
                        "备注": note_val.strip()
                    })
                    save_glossary(selected_glos, raw_data)
                    st.success("入库成功！此条目已被添加进当前编辑词库的最后一行。")

# ==========================================
# 翻译接口引擎
# ==========================================
def call_translation_api(idx, text, provider, api_key, model_name, base_url=""):
    sys_instruction = "请将以下文本流畅地翻译为简体中文，并忠实原文语境。\n"
    if selected_glos and selected_glos != "--新建词库--":
        glossary_df = pd.DataFrame(load_glossary(selected_glos))
        if not glossary_df.empty:
            matched_terms = []
            past_text = "\n".join(st.session_state.segments[:idx])
            for _, row in glossary_df.iterrows():
                src, ans, note = str(row.get('原文', '')).strip(), str(row.get('核心译文', '')).strip(), str(row.get('备注', '')).strip()
                if not src: continue
                if src.lower() in text.lower():
                    is_first_appearance = (src.lower() not in past_text.lower())
                    term_instruct = f"- `{src}` -> 必须翻译为涵盖核心译名 `{ans}` 的表述"
                    if is_first_appearance and note:
                        term_instruct += f"（附加备注要求：{note}）"
                    matched_terms.append(term_instruct)
            if matched_terms:
                sys_instruction += "\n【重要严格约束】：检测到本文包含以下专有术语，必须采纳以下译法要求：\n"
                sys_instruction += "\n".join(matched_terms) + "\n\n"
                
    prompt = sys_instruction + f"需要翻译的原文文本如下：\n{text}"
    if provider == "Gemini":
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        return model.generate_content(prompt).text
    elif provider == "OpenAI-Compatible":
        client = OpenAI(api_key=api_key, base_url=base_url)
        return client.chat.completions.create(model=model_name, messages=[{"role": "user", "content": prompt}]).choices[0].message.content

# ==========================================
# 主界面工作台
# ==========================================
if len(st.session_state.segments) == 0:
    raw_text = st.text_area("请将需要翻译的文章整体粘贴到此处：", height=250)
    if st.button("✂️ 开始分段并启动", type="primary"):
        if raw_text.strip():
            st.session_state.segments = [p.strip() for p in raw_text.split('\n') if p.strip()]
            st.session_state.current_index = 0
            st.session_state.ai_drafts = {}
            st.session_state.translations = {}
            st.rerun()
else:
    total_segments = len(st.session_state.segments)
    idx = st.session_state.current_index
    current_segment_text = st.session_state.segments[idx]
    
    st.subheader(f"📖 进度 (第 {idx + 1} 段 / 共 {total_segments} 段)")
    st.progress((idx + 1) / total_segments)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown("#### 🔹 原文段落")
        st.info(current_segment_text)

    with col2:
        st.markdown("#### 🤖 AI 初稿与词库校验")
        btn_disabled = not api_key.strip()
        if st.button("✨ 调用 AI 翻译当前段", disabled=btn_disabled, key=f"btn_trans_{idx}", type="primary", use_container_width=True):
            with st.spinner("思考翻译与应用词库规则中..."):
                try:
                    ai_result = call_translation_api(idx, current_segment_text, provider, api_key, model_name, base_url)
                    st.session_state.ai_drafts[idx] = ai_result
                    # 取消强制默认占用逻辑
                    st.rerun()
                except Exception as e:
                    st.error("调用 API 错误：")
                    st.code(traceback.format_exc(), language="python")
                    
        if idx in st.session_state.ai_drafts:
            draft_text = st.session_state.ai_drafts[idx]
            st.success(draft_text)
            
            # 校验警报逻辑
            violations = []
            if selected_glos and selected_glos != "--新建词库--":
                gdf = pd.DataFrame(load_glossary(selected_glos))
                if not gdf.empty:
                    for _, row in gdf.iterrows():
                        s, a = str(row.get('原文', '')).strip(), str(row.get('核心译文', '')).strip()
                        if s and a and s.lower() in current_segment_text.lower() and a not in draft_text:
                            violations.append(f"原文涉及到 `[ {s} ]`，但未在译文中查找到核心译文 `[ {a} ]`！")
            if violations:
                st.error("🚨 **漏译/不规范警告：**\n\n" + "\n".join(f"- {v}" for v in violations))
            
            # 手工确认采用 AI
            if st.button("📥 一键覆盖到右侧", key=f"copy_ai_draft_{idx}", use_container_width=True):
                st.session_state[f"manual_edit_{idx}"] = draft_text
                st.session_state.translations[idx] = draft_text
                st.rerun() # 立刻清爽重载避免受控组件崩溃
            
    with col3:
        st.markdown("#### ✍️ 手动修改结果")
        edit_key = f"manual_edit_{idx}"
        # 组件生命周期保护：预设 default 状态
        if edit_key not in st.session_state:
            st.session_state[edit_key] = st.session_state.translations.get(idx, "")
            
        def sync_translation_edit():
            st.session_state.translations[idx] = st.session_state[edit_key]
            
        st.text_area("精修翻译结果：", height=250, key=edit_key, on_change=sync_translation_edit, label_visibility="collapsed")
    
    st.markdown("---")
    
    # 导航区
    nav1, nav2, nav3, nav4 = st.columns(4)
    with nav1:
        if st.button("⬅️ 上一段", use_container_width=True, disabled=(idx == 0)):
            st.session_state.current_index -= 1; st.rerun()
    with nav2:
        if st.button("下一段 ➡️", use_container_width=True, disabled=(idx == total_segments - 1)):
            st.session_state.current_index += 1; st.rerun()
    with nav3:
        if st.button("🗑️ 抛弃当前项目", use_container_width=True):
            st.session_state.segments = []; st.rerun()
    with nav4:
        if st.button("📄 全景一览视图", use_container_width=True):
            st.session_state.show_export = True
            
    # 追加确认保存模块放到大块下沉位置
    st.markdown("---")
    if st.button("📌 确认采纳当前段落并清洗格式追加写入 output.md", use_container_width=True, type="primary"):
        # 完全以手工栏最新的 State 为准
        final_text = st.session_state.get(edit_key, "")
        if not final_text.strip():
            st.warning("您还未在右侧填入任何终稿文本，无法提取格式清洗执行落盘！")
        else:
            cleaned_text = clean_punctuation(final_text)
            st.session_state[edit_key] = cleaned_text       # 冲刷视图
            st.session_state.translations[idx] = cleaned_text # 更新源数据
            
            # 落盘写入
            append_str = f"> 源：\n> {current_segment_text}\n\n译：\n{cleaned_text}\n---\n\n"
            try:
                with open("output.md", "a", encoding="utf-8") as f:
                    f.write(append_str)
                st.success(f"✅ 第 {idx+1} 段安全追加落地！英文全角标点已全部清洗。")
            except Exception as e:
                st.error("写入文件失败！")

if st.session_state.get('show_export', False) and len(st.session_state.segments) > 0:
    st.markdown("---")
    st.subheader("🎉 全文译文终稿")
    completed_texts = []
    for i in range(len(st.session_state.segments)):
        part_trans = st.session_state.translations.get(i, "")
        if not part_trans: part_trans = st.session_state.ai_drafts.get(i, "[本段空缺：请手动填写或采纳 AI 译文]")
        completed_texts.append(part_trans)
        
    full_str = "\n".join(completed_texts)
    
    dl_col1, dl_col2 = st.columns([1, 4])
    with dl_col1:
        st.download_button("📥 单击此处一键下载当前整合 .txt", data=full_str, file_name="全译文精修大纲.txt", type="primary")
    with dl_col2:
        st.info("💡 阅读小贴士：您也可以用鼠标在这里全选拖拽或者直接按 `Ctrl+A` 自助复制全部。原有的不换用乱滚问题已被优化根除。")
        
    # 自适应阅读无滚动条，优雅地将换行渲染出
    st.markdown(f'<div style="background-color:rgba(128,128,128,0.08); padding:20px; border-radius:10px; line-height:1.7; font-size:16px; white-space:pre-wrap;">{full_str}</div>', unsafe_allow_html=True)
    
    if st.button("❌ 关闭概览"):
        st.session_state.show_export = False
        st.rerun()
