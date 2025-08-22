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
    After clarification:
    - If ready → validation
    - If still incomplete → END (wait for user reply in next API call)
    """
    if state.get("status") == "ready_for_validation":
        return "validation"
    return END

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

    g.add_conditional_edges(
        "clarification", _after_clarification,
        {"validation": "validation", END: END}
    )

    g.add_conditional_edges(
        "validation", _after_validation,
        {"pricing": "pricing", END: END}
    )

    g.add_conditional_edges(
        "pricing", _after_pricing,
        {"confirmation": "confirmation", END: END}
    )

    g.add_edge("confirmation", "fulfillment")
    g.add_edge("fulfillment", END)

    return g.compile()

# Compiled graph ready to use in FastAPI
GRAPH = build_graph()