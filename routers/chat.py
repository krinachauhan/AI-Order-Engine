from fastapi import APIRouter
from models.order import ChatResponse, ChatRequest, STATE
from agents.orchestration import GRAPH
from typing import Dict

router = APIRouter()

# Store session states separately
SESSIONS: Dict[str, Dict] = {}


# from services.fuzzy_service import fuzzy_match_item

# def handle_order_item(user_input: str):
#     status, best_match, suggestions, msg = fuzzy_match_item(user_input)

#     if status == "high_confidence":
#         return {
#             "status": "accepted",
#             "item": best_match,
#             "message": f"Added {best_match['ItemName']} to your order."
#         }

#     elif status == "suggest":
#         return {
#             "status": "confirmation_needed",
#             "item": best_match,
#             "suggestions": suggestions,
#             "message": msg
#         }

#     else:  # none
#         return {
#             "status": "not_found",
#             "message": msg
#         }


@router.post("/{session_id}", response_model=ChatResponse)
async def chat(session_id: str, req: ChatRequest):
    # Get session state (or create fresh copy)
    state = SESSIONS.get(session_id, STATE.copy())
    
    # Add new user message
    # state["user_message"] = req.user_message
    # state.setdefault("transcript", []).append(req.user_message)

    STATE["transcript"].append(req.user_message)

    # Run graph
    new_state = await GRAPH.ainvoke(STATE)

    # Update session state
    SESSIONS[session_id] = new_state

    return ChatResponse(
        assistant_message=new_state.get("assistant_message", ""),
        state=new_state
    )
