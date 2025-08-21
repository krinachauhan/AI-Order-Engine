# from typing import Dict, Any
# from langgraph.graph import StateGraph, END
# from models.order import Order
# from agents.extraction import ExtractionAgent
# from agents.validation import ValidationAgent
# from agents.clarification import ClarificationAgent
# from agents.confirmation import ConfirmationAgent
# from agents.pricing import PricingAgent
# from agents.fullfilment import FulfillmentAgent

# extract = ExtractionAgent()
# clarifier = ClarificationAgent()
# validate = ValidationAgent()
# price = PricingAgent()
# confirm = ConfirmationAgent()
# fulfill = FulfillmentAgent()

# def _after_missing(state): return "validation" if state["status"]=="ready_for_validation" else END
# def _after_validation(state): return "pricing" if state["status"]=="validated" else END
# def _after_pricing(state): return "confirmation" if state["status"] == "priced" else END

# def build_graph():
#     g = StateGraph(dict)
#     g.add_node("extraction", extract.run)
#     g.add_node("clarification", clarifier.run)
#     g.add_node("validation", validate.run)
#     g.add_node("pricing", price.run)
#     g.add_node("confirmation", confirm.run)
#     g.add_node("fulfillment", fulfill.run)

#     g.set_entry_point("extraction")

#     # Extraction → Clarification
#     g.add_edge("extraction", "clarification")

#     # Clarification → either back to extraction if info missing, or validation if ready
#     g.add_conditional_edges("clarification", _after_missing, {"extraction": "extraction", "validation": "validation", END: END})

#     # Validation → Pricing
#     g.add_conditional_edges("validation", _after_validation, {"pricing": "pricing", END: END})

#     # Pricing → Confirmation
#     g.add_conditional_edges("pricing", _after_pricing, {"confirmation": "confirmation", END: END})

#     # Confirmation → Fulfillment → END
#     g.add_edge("confirmation", "fulfillment")
#     g.add_edge("fulfillment", END)

#     return g.compile()

# GRAPH = build_graph()

# agents/orchestration.py
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from models.order import Order
from agents.extraction import ExtractionAgent
from agents.validation import ValidationAgent
from agents.clarification import ClarificationAgent
from agents.confirmation import ConfirmationAgent
from agents.pricing import PricingAgent
from agents.fullfilment import FulfillmentAgent

# Instantiate agents
extract = ExtractionAgent()
clarifier = ClarificationAgent()
validate = ValidationAgent()
price = PricingAgent()
confirm = ConfirmationAgent()
fulfill = FulfillmentAgent()

# ---- Transition functions ----
def _after_clarification(state: Dict[str, Any]):
    """
    Decide what to do after clarification.
    If ready → go to validation.
    If still missing → loop back to extraction (to reprocess next user reply).
    """
    if state.get("status") == "ready_for_validation":
        return "validation"
    return "extraction"

def _after_validation(state: Dict[str, Any]):
    """After validation, either move to pricing or stop."""
    return "pricing" if state.get("status") == "validated" else END

def _after_pricing(state: Dict[str, Any]):
    """After pricing, either move to confirmation or stop."""
    return "confirmation" if state.get("status") == "priced" else END

# ---- Build graph ----
def build_graph():
    g = StateGraph(dict)

    # Nodes
    g.add_node("extraction", extract.run)
    g.add_node("clarification", clarifier.run)
    g.add_node("validation", validate.run)
    g.add_node("pricing", price.run)
    g.add_node("confirmation", confirm.run)
    g.add_node("fulfillment", fulfill.run)

    # Entry
    g.set_entry_point("extraction")

    # Flow
    g.add_edge("extraction", "clarification")
    g.add_conditional_edges("clarification", _after_clarification,
        {"extraction": "extraction", "validation": "validation"}
    )
    g.add_conditional_edges("validation", _after_validation,
        {"pricing": "pricing", END: END}
    )
    g.add_conditional_edges("pricing", _after_pricing,
        {"confirmation": "confirmation"}
    )
    g.add_edge("confirmation", "fulfillment")
    g.add_edge("fulfillment", END)

    return g.compile()

# Compiled graph ready to use in FastAPI
GRAPH = build_graph()