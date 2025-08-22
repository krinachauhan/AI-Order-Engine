import copy
from typing import Dict, Any, Optional, List
from models.order import Order, OrderItem
from services.llm_client import GeminiClient


class ExtractionAgent:
    name = "extraction"

    def __init__(self):
        self.gemini = GeminiClient()

    async def run(self, state: dict) -> dict:
        # Combine all previous messages into one text
        all_text = " ".join(state.get("transcript", []))

        # Extract order from the full transcript
        order = await self.gemini.extract_order(all_text)
        extracted = order.model_dump()

        # Merge extracted fields into existing state
        current_order = state.get("order", {})
        for k, v in extracted.items():
            # Only update if value exists
            if v:
                if isinstance(v, dict) and k in current_order:
                    current_order[k].update(v)
                else:
                    current_order[k] = v

        # Detect missing fields
        missing_fields = []
        for field in ["items", "delivery_date", "payment_method", "contact"]:
            if not current_order.get(field):
                missing_fields.append(field)

        # Update state
        state["order"] = current_order
        state["missing_fields"] = missing_fields
        state["status"] = "needs_clarification" if missing_fields else "ready_for_validation"

        return state
