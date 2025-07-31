import asyncio
import uuid


from src.utils import logger
from src.agents.registry import BaseAgent
from src.agents.react.configuration import ReActConfiguration

class ReActAgent(BaseAgent):
    name = "ReAct"
    description = "A react agent that can answer questions and help with tasks."
    api_type = "react"
    config_schema = ReActConfiguration

    async def get_graph(self, **kwargs):
        from .workflows import graph
        return graph





if __name__ == "__main__":
    pass
