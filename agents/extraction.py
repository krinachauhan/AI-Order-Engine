import copy
from typing import Dict, Any, Optional, List
from models.order import Order, OrderItem
from services.llm_client import GeminiClient


class ExtractionAgent:
    name = "extraction"
    def __init__(self): self.gemini = GeminiClient()
    async def run(self, state: dict) -> dict:
        order = await self.gemini.extract_order(state["user_message"])
        return {**state, "order": order.model_dump()}
