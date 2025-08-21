from models.order import Order

class PricingAgent:
    name = "pricing"
    async def run(self, state: dict) -> dict:
        order = Order(**state["order"])
        subtotal = 0
        lines = []
        for it in order.items:
            unit = 100 if it.size_or_weight and "250" in (it.size_or_weight or "").upper() else 400
            qty = it.qty or 0
            line_total = unit * qty
            subtotal += line_total
            lines.append({"name": it.name, "size": it.size_or_weight, "qty": qty, "unit": unit, "total": line_total})
        taxes = round(subtotal * 0.05)
        delivery = 40 if subtotal < 1000 else 0
        grand = subtotal + taxes + delivery
        return {**state, "pricing": {"lines": lines, "subtotal": subtotal, "taxes": taxes, "delivery": delivery, "grand_total": grand}, "status": "priced"}