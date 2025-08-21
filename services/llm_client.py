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
        """Extract first valid JSON object from Gemini output."""
        # Find first '{' and last '}' and slice the string
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            json_str = raw[start:end+1]
            try:
                # Validate JSON
                parsed = json.loads(json_str)
                return json.dumps(parsed)  # valid JSON string
            except json.JSONDecodeError as e:
                print("JSON parse error:", e)
                return "{}"
        else:
            return "{}"

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