from typing import Any, Dict, List, Optional
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