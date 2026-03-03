---
name: skillboss-ai-gateway
description: Access 100+ AI services through a unified OpenAI-compatible API. Use when the user needs to call multiple AI models or services (LLMs, image generation, video, audio, embeddings) through a single interface.
---

# SkillBoss AI Gateway

SkillBoss provides unified access to 100+ AI services through a single API key and OpenAI-compatible interface.

## When to Use

- User needs to call multiple AI models (Claude, GPT, Gemini, DeepSeek, Llama, Mistral)
- User needs image generation (DALL-E, Midjourney, Flux, Stable Diffusion)
- User needs video generation (Runway, Kling, Luma, Pika)
- User needs audio/speech (ElevenLabs, OpenAI TTS/STT)
- User wants a single API key for all AI services
- User needs OpenAI-compatible API for any model

## Setup

### MCP Server (Recommended)
```json
{
  "mcpServers": {
    "skillboss": {
      "command": "npx",
      "args": ["skillboss-mcp-server"],
      "env": {
        "SKILLBOSS_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Direct API Usage
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.heybossai.com/v1",
    api_key="your-skillboss-api-key"
)

# Use any model
response = client.chat.completions.create(
    model="anthropic/claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Supported Services

### LLMs
- Claude (Sonnet 4, Opus 4, Haiku)
- GPT (GPT-4.1, GPT-4.5, GPT-5, o3, o4-mini)
- Gemini (2.5 Pro, 2.5 Flash)
- DeepSeek (R1, V3)
- Llama, Mistral, Qwen, and more

### Image Generation
- DALL-E 3/4
- Midjourney
- Flux (Pro, Dev, Schnell)
- Stable Diffusion 3.5

### Video Generation
- Runway Gen-3/4
- Kling 2.0
- Luma Dream Machine
- Pika 2.2

### Audio
- ElevenLabs TTS
- OpenAI TTS/STT
- Whisper

### Other Services
- Embeddings (text-embedding-3-large)
- Web Search
- Payments (Stripe integration)
- Hosting (deploy documents as websites)

## Links

- Documentation: https://skillboss.co/docs
- Skills Repo: https://github.com/heeyo-life/skillboss-skills
- MCP Server: https://github.com/heeyo-life/skillboss-mcp

Origin: https://github.com/heeyo-life/skillboss-skills
