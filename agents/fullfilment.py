from typing import Dict, Any


class FulfillmentAgent:
    name = "fulfillment"
    async def run(self, state: dict) -> dict:
        return {**state, "assistant_message": "✅ Order placed! You’ll get delivery updates soon.", "status": "fulfilled"}
