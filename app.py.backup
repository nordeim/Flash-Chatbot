import streamlit as st
import httpx
import json
import os
import re

# ============================================================
# 配置 - 使用 OpenRouter API
# ============================================================
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "stepfun/step-3.5-flash:free"
HF_CONFIG_URL = "https://huggingface.co/stepfun-ai/Step-3.5-Flash/raw/main/config.json"
STEPFUN_LOGO_URL = "https://huggingface.co/stepfun-ai/Step-3.5-Flash/resolve/main/stepfun.svg"
STEPFUN_LOGO_PATH = "/tmp/stepfun_logo.svg"


def download_logo():
    """下载 StepFun logo 到本地"""
    try:
        response = httpx.get(STEPFUN_LOGO_URL, timeout=10.0, follow_redirects=True)
        if response.status_code == 200:
            with open(STEPFUN_LOGO_PATH, "wb") as f:
                f.write(response.content)
            return True
    except Exception:
        pass
    return False


def get_assistant_avatar():
    """获取助手头像，优先使用下载的 logo，失败则用 emoji"""
    if os.path.exists(STEPFUN_LOGO_PATH):
        return STEPFUN_LOGO_PATH
    return "🚀"


# 启动时下载 logo
download_logo()

st.set_page_config(
    page_title="Step-3.5-Flash",
    page_icon="🚀",
    layout="centered",
)

# 简化样式 - 只定义思考区域
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

.thinking-container {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 10px;
    max-height: 150px;
    overflow-y: auto;
    font-size: 13px;
    line-height: 1.5;
    color: #64748b;
}
.thinking-container::-webkit-scrollbar {
    width: 4px;
}
.thinking-container::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 2px;
}
.thinking-label {
    font-size: 12px;
    color: #94a3b8;
    margin-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def fetch_model_config():
    try:
        response = httpx.get(HF_CONFIG_URL, timeout=10.0)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def format_messages(history, system_prompt: str, user_message: str):
    """格式化消息，保留 reasoning_details 用于多轮对话"""
    messages = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt})
    for msg in history:
        if msg["role"] == "user":
            content = msg.get("content", "")
            if content:
                messages.append({"role": "user", "content": content})
        elif msg["role"] == "assistant":
            content = msg.get("content", "")
            if content:
                assistant_msg = {"role": "assistant", "content": content}
                # 保留 reasoning_details 用于多轮对话
                if msg.get("reasoning_details"):
                    assistant_msg["reasoning_details"] = msg["reasoning_details"]
                messages.append(assistant_msg)
    messages.append({"role": "user", "content": user_message})
    return messages


def chat_stream(message: str, history: list, system_prompt: str, max_tokens: int, temperature: float, top_p: float):
    """流式聊天，返回 (reasoning, content, reasoning_details) 生成器"""
    messages = format_messages(history, system_prompt, message)

    reasoning = ""
    content = ""
    reasoning_details = None

    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "stream": True,
            "max_tokens": max_tokens,
            "temperature": temperature if temperature > 0 else 0.01,
            "top_p": top_p,
            "reasoning": {"enabled": True},  # 启用推理模式
        }

        with httpx.stream("POST", f"{OPENROUTER_BASE_URL}/chat/completions", headers=headers, json=payload, timeout=120.0) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    # 处理 reasoning (流式思考内容)
                    if delta.get("reasoning"):
                        reasoning += delta["reasoning"]
                        yield reasoning, content, reasoning_details
                    # 处理 content (流式回答内容)
                    if delta.get("content"):
                        content += delta["content"]
                        yield reasoning, content, reasoning_details
                    # 处理完整的 reasoning_details (用于多轮保留)
                    message_obj = chunk.get("choices", [{}])[0].get("message", {})
                    if message_obj.get("reasoning_details"):
                        reasoning_details = message_obj["reasoning_details"]
                except json.JSONDecodeError:
                    continue
        yield reasoning, content, reasoning_details

    except httpx.HTTPStatusError as e:
        yield reasoning, f"❌ API 错误: {e.response.status_code}", None
    except Exception as e:
        yield reasoning, f"❌ 错误: {str(e)}", None


def clean_thinking(text: str) -> str:
    """清理思考内容中的标签"""
    if not text:
        return ""
    # 移除 <think> 标签
    text = re.sub(r'</?think>', '', text)
    return text.strip()


def render_thinking_expander(thinking_text: str, is_streaming: bool = False):
    """使用 expander 渲染思考内容"""
    if thinking_text:
        cleaned = clean_thinking(thinking_text)
        with st.expander("💭 思考过程", expanded=is_streaming):
            st.text(cleaned)


def main():
    # 侧边栏设置
    with st.sidebar:
        st.header("⚙️ 设置")
        system_prompt = st.text_area("系统提示词", value="你是一个有帮助的 AI 助手。", height=80)
        max_tokens = st.slider("最大长度", 256, 131072, 4096, step=256, help="最大 128k")
        temperature = st.slider("Temperature", 0.0, 1.5, 0.7, step=0.1)
        top_p = st.slider("Top-p", 0.1, 1.0, 0.9, step=0.05)

        st.divider()
        if st.button("🗑️ 清空对话", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.divider()
        with st.expander("📋 模型配置"):
            config = fetch_model_config()
            if config:
                st.json(config)

    # 初始化 session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None

    # 标题
    st.title("🚀 Step-3.5-Flash")

    # 显示历史消息
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant", avatar=get_assistant_avatar()):
                # 思考内容用 expander
                if msg.get("thinking"):
                    render_thinking_expander(msg["thinking"], is_streaming=False)
                # 回答内容用 markdown
                st.markdown(msg.get("content", ""))

    # 示例问题（无消息时显示）
    if not st.session_state.messages:
        st.caption("💡 试试这些问题：")
        examples = [
            "请解释一下什么是机器学习？",
            "帮我写一个 Python 快速排序算法",
            "1000以内有多少个质数？",
        ]
        cols = st.columns(len(examples))
        for i, example in enumerate(examples):
            if cols[i].button(example, key=f"ex_{i}", use_container_width=True):
                st.session_state.pending_prompt = example
                st.rerun()

    # 输入框（固定在底部）
    prompt = st.chat_input("输入消息...")

    # 处理 pending_prompt（来自示例按钮）
    if st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None

    if prompt:
        # 添加并显示用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 助手回复
        with st.chat_message("assistant", avatar=get_assistant_avatar()):
            # 思考内容占位符
            thinking_placeholder = st.empty()
            # 回答内容占位符
            answer_placeholder = st.empty()

            full_response = ""
            full_thinking = ""
            full_reasoning_details = None

            for thinking, response, reasoning_details in chat_stream(
                prompt,
                st.session_state.messages[:-1],
                system_prompt,
                max_tokens,
                temperature,
                top_p,
            ):
                full_thinking = thinking
                full_response = response if response else "▌"
                if reasoning_details:
                    full_reasoning_details = reasoning_details

                # 更新思考内容
                if full_thinking:
                    with thinking_placeholder.container():
                        render_thinking_expander(full_thinking, is_streaming=True)

                # 更新回答内容
                answer_placeholder.markdown(full_response)

            # 保存消息（包含 reasoning_details 用于多轮对话）
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "thinking": full_thinking,
                "reasoning_details": full_reasoning_details,
            })
            st.rerun()


if __name__ == "__main__":
    main()
