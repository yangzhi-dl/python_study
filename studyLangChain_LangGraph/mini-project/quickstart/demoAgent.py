#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : demoAgent.py
@Author  : yz.yangzhi
@Date    : 2026/10/21 21:47
@Desc    : 
"""
from quickstart import config
from langchain.agents import create_agent

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_agent(
    model=config.MODEL,
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

result = agent.invoke(
    {"messages": [
        {
            "role": "user",
            "content": "What's the weather in San Francisco?"
        }]
    }
)
print(result["messages"][-1].content_blocks)