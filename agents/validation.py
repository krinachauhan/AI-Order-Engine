from typing import Dict, Any
from models.order import Order

class ValidationAgent:
    name = "validation"
    async def run(self, state: dict) -> dict:
        # very basic rules
        return {**state, "status": "validated"}
