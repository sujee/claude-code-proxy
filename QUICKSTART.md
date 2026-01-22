# Quick Start Guide - Nebius Edition

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies
```bash
# Using UV (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### Step 2: Configure for Nebius

This proxy is optimized specifically for Nebius token factory:

#### Nebius Token Factory (Recommended)
```bash
cp .env.example .env
# Edit .env with your Nebius configuration:
# OPENAI_API_KEY="your-nebius-api-key"
# OPENAI_BASE_URL="https://api.tokenfactory.nebius.com/v1"
# BIG_MODEL="zai-org/GLM-4.5"
# MIDDLE_MODEL="zai-org/GLM-4.5"
# SMALL_MODEL="zai-org/GLM-4.5"
# VISION_MODEL="Qwen/Qwen2.5-VL-72B-Instruct"
# STRIP_IMAGE_CONTEXT=true
```


### Step 3: Start and Use

```bash
# Start the proxy server
python start_proxy.py

# In another terminal, use with Claude Code
ANTHROPIC_BASE_URL=http://localhost:8083 claude
```

## 🎯 How It Works

| Your Input                                     | Proxy Action                  | Result                                       |
| ---------------------------------------------- | ----------------------------- | -------------------------------------------- |
| Claude Code sends `claude-3-5-sonnet-20241022` | Maps to your `MIDDLE_MODEL`   | Uses `zai-org/GLM-4.5` (or your config)      |
| Claude Code sends `claude-3-5-haiku-20241022`  | Maps to your `SMALL_MODEL`    | Uses `zai-org/GLM-4.5` (or your config)      |
| Claude Code sends `claude-3-opus-20240229`     | Maps to your `BIG_MODEL`      | Uses `zai-org/GLM-4.5` (or your config)      |
| Claude Code sends request with **images**      | Maps to your `VISION_MODEL`   | Uses `Qwen/Qwen2.5-VL-72B-Instruct`          |

## 📋 What You Need

- Python 3.9+
- Nebius API key from token factory
- Claude Code CLI installed
- 2 minutes to configure

## 🔧 Default Settings
- Server runs on `http://localhost:8083`
- Nebius endpoint: `https://api.tokenfactory.nebius.com/v1`
- Maps: haiku → SMALL_MODEL, sonnet → MIDDLE_MODEL, opus → BIG_MODEL, images → VISION_MODEL
- Supports streaming, function calling, and **image processing**
- Image context stripping enabled for non-vision models

## 🧪 Test Your Setup
```bash
# Comprehensive test including image support
python src/test_claude_to_openai.py
```

That's it! Now Claude Code works seamlessly with Nebius token factory! 🎉

> **Pro Tip**: The proxy automatically detects images in your requests and routes them to the vision model while maintaining conversation context.