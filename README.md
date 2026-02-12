---
title: Step-3.5-Flash Chatbot
emoji: "🚀"
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 8501
pinned: false
license: apache-2.0
---

# Step-3.5-Flash Chatbot

基于 [stepfun-ai/Step-3.5-Flash](https://huggingface.co/stepfun-ai/Step-3.5-Flash) 模型的智能对话助手，使用官方 API。

## 特性

- 左右分栏布局：左侧展示思考过程，右侧展示对话
- 多轮对话支持
- 流式输出
- 可调节参数（temperature, top_p, max_tokens）

## 环境变量

在 HuggingFace Space 的 Settings > Repository secrets 中设置：

- [`STEPFUN_API_KEY`](https://platform.stepfun.com/interface-key): StepFun 官方 API Key [https://platform.stepfun.com/interface-key](https://platform.stepfun.com/interface-key)

## 本地运行

```bash
export STEPFUN_API_KEY="your-api-key"
pip install streamlit httpx
streamlit run app.py
```
