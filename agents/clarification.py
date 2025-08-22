from services.llm_client import GeminiClient
from models.order import Order
from services.fuzzy_service import fuzzy_match_item

class ClarificationAgent:
    name = "missing_info"

    def __init__(self):
        self.gemini = GeminiClient()

    async def run(self, state: dict) -> dict:
        # Load order from state
        order = Order(**state.get("order", {}))
        missing = []
        assistant_messages = []

        # --- Handle item name fuzzy matching ---
        corrected_items = []
        for item in order.items:
            status, best, suggestions, _ = fuzzy_match_item(item.name)

            if status == "high_confidence":
                item.name = best["ItemName"]  # silently fix

            elif status == "suggest":
                missing.append("items.name")
                assistant_messages.append(
                    f"I couldn’t find an exact match for **{item.name}**. Did you mean one of these?\n" +
                    "\n".join(f"- {s['ItemName']}" for s in suggestions)
                )

            else:
                missing.append("items.name")

            corrected_items.append(item)
        order.items = corrected_items

        # --- Check other missing fields ---
        if any(i.qty is None or i.size_or_weight is None for i in order.items):
            missing.append("items.qty/size_or_weight")
        if not order.delivery_date:
            missing.append("delivery_date")
        if not order.payment_method:
            missing.append("payment_method")
        if not order.contact.name:
            missing.append("contact.name")
        if not order.contact.phone:
            missing.append("contact.phone")
        if not order.contact.address:
            missing.append("contact.address")

        # --- Generate assistant message for missing fields ---
        if missing:
            if not assistant_messages:
                # Ask via Gemini for missing fields
                message = await self.gemini.clarify(order, missing)
            else:
                message = " ".join(assistant_messages)

            return {
                **state,
                "status": "needs_clarification",
                "missing_fields": missing,
                "assistant_message": message,
                "order": order.model_dump()
            }

        # --- All fields filled ---
        return {
            **state,
            "status": "ready_for_validation",
            "order": order.model_dump(),
            "assistant_message": "✅ All information received."
        }
    