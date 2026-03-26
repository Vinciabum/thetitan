"""
main.py - Main execution script for AI News Agent
"""

import asyncio
import json
import os
from pathlib import Path

from core.agent import AINewsAgent, AgentConfig
from core.agent import BrandTheme


def load_agent_config(config_path: str = "agent_config.json") -> AgentConfig:
    """Load agent configuration from JSON file"""
    default_config = {
        "name": "Monologue",
        "personality": "professional",
        "news_sources": ["gnews"],
        "post_frequency": 3,
        "max_news_age": 24,
        "engagement_threshold": 0.5,
        "memory_path": "agent_memory.json",
        "output_dir": "./output",
        "credentials": {
            k: v for k, v in {
                "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
                "REPLICATE_API_TOKEN": os.getenv("REPLICATE_API_TOKEN"),
                "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
                "IG_USERNAME": os.getenv("IG_USERNAME"),
                "IG_PASSWORD": os.getenv("IG_PASSWORD"),
                "THREADS_ACCESS_TOKEN": os.getenv("THREADS_ACCESS_TOKEN"),
                "THREADS_USER_ID": os.getenv("THREADS_USER_ID"),
            }.items() if v is not None
        }
    }

    try:
        if Path(config_path).exists():
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                default_config.update(config_data)
    except Exception as e:
        print(f"Error loading config file: {e}")
        print("Using default configuration...")

    default_config["memory_path"] = Path(default_config["memory_path"])
    default_config["output_dir"] = Path(default_config["output_dir"])

    return AgentConfig(**default_config)


async def main():
    config = load_agent_config()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    theme = BrandTheme(
        primary_color="#1A1A1A",
        secondary_color="#F5F0E8",
        accent_color="#8B7355",
        background_color="#FAFAF8",
        text_color="#2C2C2C",
        font_style="Noto Sans KR",
        visual_style="minimalist",
        content_tone="warm and philosophical"
    )

    agent = AINewsAgent(config, theme)
    try:
        await agent.run()
    except KeyboardInterrupt:
        print("\nShutting down agent gracefully...")
        agent.memory.save(config.memory_path)
        print("Agent state saved. Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())
