---
title: Flash Chatbot
emoji: "🚀"
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 8501
pinned: false
license: apache-2.0
---

# Flash Chatbot

An intelligent conversational assistant built upon the 'stepfun-ai/Step-3.5-Flash' model, utilising its official API.

## Features

- Split-pane layout: The left pane displays the thought process, whilst the right pane shows the conversation.
- Supports multi-turn conversations.
- Streaming output.
- Adjustable parameters (temperature, top_p, max_tokens).

## Environment Variables

These should be configured within HuggingFace Space's Settings > Repository secrets:

- `STEPFUN_API_KEY`: Your official StepFun API Key

## Running Locally

```bash
export STEPFUN_API_KEY="your-api-key"
pip install streamlit httpx
streamlit run app.py
```
