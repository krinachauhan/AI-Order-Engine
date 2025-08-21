# utils/missing.py
from typing import List
from models.order import Order

def compute_missing(order: Order) -> List[str]:
    """
    Returns a list of missing required fields in the order.
    """
    missing = []

    if not order.items or len(order.items) == 0:
        missing.append("items")
    else:
        for idx, item in enumerate(order.items):
            if not item.qty:
                missing.append(f"items[{idx}].qty")
            if not item.size_or_weight:
                missing.append(f"items[{idx}].size_or_weight")

    if not order.delivery_date:
        missing.append("delivery_date")
    if not order.payment_method:
        missing.append("payment_method")

    if not order.contact:
        missing.extend(["contact.name", "contact.phone", "contact.address"])
    else:
        if not order.contact.name:
            missing.append("contact.name")
        if not order.contact.phone:
            missing.append("contact.phone")
        if not order.contact.address:
            missing.append("contact.address")

    return missing
