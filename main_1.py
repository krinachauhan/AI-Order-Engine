import os
import asyncio
import google.generativeai as genai
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
import uvicorn
import re
from typing import Any, Dict, List, Optional

# ==============================
# CONFIG
# ==============================
genai.configure(api_key="AIzaSyB-j0TKOC8ORqxuy1pPIITVCZZ6IUgzqVs")
MODEL = "gemini-2.5-flash"   # or "gemini-1.5-pro"

# ==============================
# SCHEMAS
# ==============================
from typing import List, Optional
from pydantic import BaseModel as PBase

class Contact(PBase):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class OrderItem(PBase):
    name: str
    qty: Optional[int] = None
    size_or_weight: Optional[str] = None

class Order(PBase):
    items: List[OrderItem] = []
    delivery_date: Optional[str] = None
    payment_method: Optional[str] = None
    contact: Contact = Contact()

STATE: Dict[str, Any] = {
    "status": "new",
    "order": {
        "items": [],
        "delivery_date": None,
        "payment_method": None,
        "contact": {
            "name": None,
            "phone": None,
            "address": None
        }
    },
    "transcript": []
}

class ChatRequest(PBase):
    user_message: str

class ChatResponse(PBase):
    assistant_message: str
    state: Dict[str, Any]
# ==============================
# GEMINI CLIENT
# ==============================
class GeminiClient:
    def __init__(self, model=MODEL):
        self.model = genai.GenerativeModel(model)

    def clean_json(self, raw: str) -> str:   # 👈 must have self
        """Extract the first valid JSON object from Gemini output."""
        match = re.search(r"\{[\s\S]*\}", raw)
        return match.group(0) if match else raw

    async def extract_order(self, user_message: str) -> Order:
        prompt = f"""
        Extract order details as JSON with fields:
        - items: list of {{name, qty, size_or_weight}}
        - delivery_date
        - payment_method
        - contact: {{name, phone, address}}

        User: {user_message}
        Output JSON only.
        """

        resp = await self.model.generate_content_async(prompt)
        text = resp.candidates[0].content.parts[0].text

        print("RAW Gemini output:\n", text)

        text = self.clean_json(text)   # ✅ will now work
        return Order.model_validate_json(text)

    async def clarify(self, order: Order, missing: list[str]) -> str:
        """
        Ask the user for missing order details in a natural way.
        """
        missing_fields = ", ".join(missing)
        prompt = f"""
        The current extracted order is:
        {order.model_dump_json(indent=2)}

        The following fields are missing or incomplete: {missing_fields}.

        Write a polite, short question to the user asking for this info.
        Example: "Could you please tell me your delivery date?"
        """
        resp = await self.model.generate_content_async(prompt)
        return resp.candidates[0].content.parts[0].text.strip()

# ==============================
# AGENTS
# ==============================
class ExtractionAgent:
    name = "extraction"
    def __init__(self): self.gemini = GeminiClient()
    async def run(self, state: dict) -> dict:
        order = await self.gemini.extract_order(state["user_message"])
        return {**state, "order": order.model_dump()}

class MissingInfoAgent:
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

class ValidationAgent:
    name = "validation"
    async def run(self, state: dict) -> dict:
        # very basic rules
        return {**state, "status": "validated"}

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

class FulfillmentAgent:
    name = "fulfillment"
    async def run(self, state: dict) -> dict:
        return {**state, "assistant_message": "✅ Order placed! You’ll get delivery updates soon.", "status": "fulfilled"}

# ==============================
# GRAPH
# ==============================
extract = ExtractionAgent()
missing = MissingInfoAgent()
validate = ValidationAgent()
price = PricingAgent()
confirm = ConfirmationAgent()
fulfill = FulfillmentAgent()

def _after_missing(state): return "validation" if state["status"]=="ready_for_validation" else END
def _after_validation(state): return "pricing" if state["status"]=="validated" else END
def _after_pricing(state): return "confirmation"

def build_graph():
    g = StateGraph(dict)
    g.add_node("extraction", extract.run)
    g.add_node("missing_info", missing.run)
    g.add_node("validation", validate.run)
    g.add_node("pricing", price.run)
    g.add_node("confirmation", confirm.run)
    g.add_node("fulfillment", fulfill.run)

    g.set_entry_point("extraction")
    g.add_edge("extraction", "missing_info")
    g.add_conditional_edges("missing_info", _after_missing, {"validation": "validation", END: END})
    g.add_conditional_edges("validation", _after_validation, {"pricing": "pricing", END: END})
    g.add_edge("pricing", "confirmation")
    g.add_edge("fulfillment", END)
    return g.compile()

GRAPH = build_graph()

# ==============================
# API
# ==============================
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
app = FastAPI()
SESSIONS = {}

class Input(BaseModel):
    session_id: str
    user_message: str

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    global STATE
    
    # Add new user message to transcript
    STATE["user_message"] = req.user_message
    STATE["transcript"].append(req.user_message)

    # Run graph/agent step
    new_state = await GRAPH.ainvoke(STATE)

    # If all fields are filled → mark order as completed
    if new_state["status"] == "needs_clarification" and not new_state["missing_fields"]:
        new_state["status"] = "completed"
        new_state["assistant_message"] = (
            f"✅ Your order has been placed!\n\n"
            f"📦 Item(s): {new_state['order']['items']}\n"
            f"📅 Delivery: {new_state['order']['delivery_date']}\n"
            f"💳 Payment: {new_state['order']['payment_method']}\n"
            f"📞 Contact: {new_state['order']['contact']}\n\n"
            "Thank you for ordering! 🎉"
        )

    # Update global STATE
    STATE.update(new_state)

    return ChatResponse(
        assistant_message=new_state.get("assistant_message", ""),
        state=new_state
    )
# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    uvicorn.run(app)