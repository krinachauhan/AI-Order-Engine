from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from models.order import ChatResponse, ChatRequest, STATE
from agents.orchestration import GRAPH
import uvicorn


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