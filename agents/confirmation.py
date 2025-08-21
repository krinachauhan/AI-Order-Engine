class ConfirmationAgent:
    name = "confirmation"
    async def run(self, state: dict) -> dict:
        p = state["pricing"]
        lines = "\n".join([f"- {l['name']} {l['size']} × {l['qty']} = {l['total']}" for l in p["lines"]])
        msg = f"""Here’s your order summary:
{lines}
Subtotal: {p['subtotal']}, Taxes: {p['taxes']}, Delivery: {p['delivery']}
Grand Total: {p['grand_total']}
Reply CONFIRM to place the order or say what to change."""
        return {**state, "assistant_message": msg, "status": "awaiting_confirmation"}