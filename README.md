# Sci-Fi Translator (科幻翻译高速平台)

基于 Streamlit打造的高效人工干预机器翻译平台。专为科幻长篇文学设计，内置了首现术语提醒、字典自动纠偏、高亮匹配等专业机翻辅助系统。

## 功能特性
- **🌟 智能 API 双路引擎集成**：内置 Gemini (Flash/Pro) 和各大兼容 OpenAI (DeepSeek/GPT-4等) 的协议层。
- **📝 上下文及术语隔离**：通过动态词汇表提取首现提示词，严格规约模型对于专有名词的乱译、错译情况。
- **🌍 实时百科采集辅助查询**：直接接入并内嵌基于 Google Search 的实时大模型百科检索功能，并可一键提取加入持久化常驻词条库。
- **🎨 跨风格沉浸式主题**：深度定制了《黑客帝国》、《赛博霓虹》、《银河深蓝》等多套酷炫原生响应式皮肤（单色），让枯燥的翻译充满极客的浪漫感。

## 快速运行 (本地环境)

1. 克隆本项目：
   ```bash
   git clone https://github.com/YourUsername/scifi-translater.git
   cd scifi-translater
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置环境：
   将项目根目录的 `.env.example` 复制一份并重命名为 `.env`，填入你的专属环境：
   - 默认会自动填充页面左侧 Sidebar 的 API Key。
   - 如果在国内需要走本地代理，可将 `USE_LOCAL_PROXY=true`。否则保持为 `false`。

4. 启动前端平台：
   ```bash
   streamlit run app.py
   ```
   *Windows 用户也可以直接双击目录内的 `start_app.bat` 傻瓜式运行哦！*

## 🚀 部署至 Streamlit Community Cloud (免服务器，一键上线)

因为这是一个纯粹的 Streamlit 项目，非常适合使用 **Streamlit 官方云（Community Cloud）**一键免费部署给所有人访问：

1. **配置 GitHub 仓库**
   - 登录你的 GitHub，新建/推送此代码库。
   
2. **连接 Streamlit Cloud**
   - 进入 [Streamlit Cloud](https://share.streamlit.io/)，点击 `New app`。
   - 授权 GitHub，选择当前仓库 `scifi-translater`，主分支 `main`（或 `master`），启动文件填写 `app.py`。
   
3. **注入安全密钥 (Secrets)**
   - 在部署配置的 **Advanced settings** (高级设定) -> **Secrets** 一栏里，把 `.env` 里的环境变量内容粘贴进去：
     ```toml
     GEMINI_API_KEY="你的真实密钥"
     OPENAI_API_KEY="你的真实密钥"
     OPENAI_BASE_URL="对应接口地址"
     USE_LOCAL_PROXY="false"
     ```
   *(注意：绝对不要把包含真实 API Key 的 `.env` 文件直接推送到公有仓库中，我已经帮你在 `.gitignore` 中将其免疫了。)*
   
---
*Developed with AI Assist*
作者自注：目前内容仍处于demo，只作为样子试用
