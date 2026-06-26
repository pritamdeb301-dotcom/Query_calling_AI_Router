"""Router for initiating an outbound voice call via an external provider (Vapi.ai / Bland.ai)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import httpx
import os
from dotenv import load_dotenv

# Force Python to read the .env file
load_dotenv()
router = APIRouter()
class TriggerCallRequest(BaseModel):
    name: str = Field(..., description="Patient's full name")
    phone_number: str = Field(..., description="E.164 formatted phone number, e.g. +15551234567")

class TriggerCallResponse(BaseModel):
    success: bool
    call_id: str | None = None
    error: str | None = None

@router.post("/trigger-call", response_model=TriggerCallResponse)
async def trigger_call(payload: TriggerCallRequest):
    """Kick off an outbound call using the configured Voice AI service.

    The real provider integration will differ; here we use a generic HTTP POST
    to illustrate the flow.  The provider should return a unique ``call_id``
    that later webhooks will reference.
    """
    api_key = os.getenv("VAPI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Voice API key not configured")

# Grab the Assistant ID you added to your .env file
    assistant_id = os.getenv("VAPI_ASSISTANT_ID") 

    # 1. The exact data layout Vapi requires
    provider_payload = {
        "assistantId": assistant_id,
        "phoneNumberId": "c34abed6-e06e-4ea7-9cd6-301cd7178182",  # <-- Paste your copied ID inside these quotes
        "customer": {
            "number": payload.phone_number
        }
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # 2. The exact URL Vapi uses for phone calls
            response = await client.post(
                "https://api.vapi.ai/call/phone", 
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=provider_payload
            )
            
            # This prints the exact response so you can see if it worked!
            print("VAPI RESPONSE:", response.text)
            response.raise_for_status()
            
            data = response.json()
            call_id = data.get("id")
            return TriggerCallResponse(success=True, call_id=call_id)
            
    except httpx.HTTPError as exc:
        return TriggerCallResponse(success=False, error=str(exc))