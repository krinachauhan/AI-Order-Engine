import re
import os
import json
import google.generativeai as genai
from models.order import Order
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
MODEL = "gemini-1.5-flash"

class GeminiClient:
    def __init__(self, model=MODEL):
        self.model = genai.GenerativeModel(model)

    def clean_json(self, raw: str) -> str:
        # Remove markdown fences
        raw = re.sub(r"```json|```", "", raw).strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return "{}"
        try:
            parsed = json.loads(match.group(0))
            return json.dumps(parsed)
        except json.JSONDecodeError:
            return "{}"


    async def extract_order(self, user_message: str) -> Order:
        prompt = f"""
        Extract order details from the user message.
        Return strictly this JSON structure:
        {{
            "items": [{{"name": "...", "qty": int, "size_or_weight": "..."}}],
            "delivery_date": "...",
            "payment_method": "...",
            "contact": {{"name": "...", "phone": "...", "address": "..."}}
        }}

        User: {user_message}
        JSON only. No text explanation.
        """

        resp = await self.model.generate_content_async(prompt)
        text = resp.candidates[0].content.parts[0].text

        print("RAW Gemini output:\n", text)

        text = self.clean_json(text)
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