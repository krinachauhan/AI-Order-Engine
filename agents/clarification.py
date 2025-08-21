from services.llm_client import GeminiClient
from models.order import Order

class ClarificationAgent:
    name = "missing_info"
    def __init__(self): self.gemini = GeminiClient()

    async def run(self, state: dict) -> dict:
        order = Order(**state["order"])
        missing = []
        if not order.items: missing.append("items")
        if any(i.qty is None or i.size_or_weight is None for i in order.items):
            missing.append("items.qty/size_or_weight")
        if not order.delivery_date: missing.append("delivery_date")
        if not order.payment_method: missing.append("payment_method")
        if not order.contact.name: missing.append("contact.name")
        if not order.contact.phone: missing.append("contact.phone")
        if not order.contact.address: missing.append("contact.address")

        if missing:
            ask = await self.gemini.clarify(order, missing)
            return {**state, "status": "needs_clarification", "missing_fields": missing, "assistant_message": ask}
        return {**state, "status": "ready_for_validation"}