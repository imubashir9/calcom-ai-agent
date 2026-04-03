import os
import httpx
import logging
from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from pathlib import Path

# --- INFRASTRUCTURE: Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("calcom-mcp")

# --- SETUP: Environment Variables ---
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

CAL_API_KEY = os.getenv("CAL_API_KEY")
BASE_URL = "https://api.cal.com/v1" # Locked to V1 for free personal accounts

if not CAL_API_KEY:
    raise ValueError("CAL_API_KEY is missing.")

mcp = FastMCP("CalComScheduler")

# --- V1 AUTHENTICATION HELPER ---
# async def make_cal_request(method: str, endpoint: str, data: dict = None, params: dict = None) -> Any:
#     """Helper function for Cal.com v1 - Keys MUST be clean strings."""
#     url = f"{BASE_URL}{endpoint}"
    
#     # Ensure the API Key is stripped of any accidental spaces or equal signs
#     clean_api_key = CAL_API_KEY.replace("CAL_API_KEY", "").replace("=", "").strip()
    
#     query_params = {"apiKey": clean_api_key}
#     if params:
#         query_params.update(params)

#     async with httpx.AsyncClient(timeout=30.0) as client:
#         try:
#             if method == "GET":
#                 response = await client.get(url, params=query_params)
#             elif method == "POST":
#                 response = await client.post(url, params=query_params, json=data)

#             response.raise_for_status()
#             return response.json()
#         except httpx.HTTPStatusError as e:
#             logger.error(f"API Error: {e.response.status_code} - {e.response.text}")
#             return {"error": f"API Error {e.response.status_code}", "details": e.response.text}
#         except Exception as e:
#             return {"error": "Internal server error", "details": str(e)}

async def make_cal_request(method: str, endpoint: str, data: dict = None, params: dict = None) -> Any:
    """Helper function for Cal.com v1 - Added DELETE support."""
    url = f"{BASE_URL}{endpoint}"
    clean_api_key = CAL_API_KEY.replace("CAL_API_KEY", "").replace("=", "").strip()
    
    query_params = {"apiKey": clean_api_key}
    if params:
        query_params.update(params)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if method == "GET":
                response = await client.get(url, params=query_params)
            elif method == "POST":
                response = await client.post(url, params=query_params, json=data)
            elif method == "DELETE": # <--- ADD THIS BLOCK
                # Cal.com V1 expects the cancellation reason in the JSON body
                response = await client.request("DELETE", url, params=query_params, json=data)

            response.raise_for_status()
            # DELETE requests sometimes return empty or simple strings
            if response.status_code == 204 or not response.text:
                return {"status": "success"}
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"API Error: {e.response.status_code} - {e.response.text}")
            return {"error": f"API Error {e.response.status_code}", "details": e.response.text}
        except Exception as e:
            return {"error": "Internal server error", "details": str(e)}

@mcp.tool()
async def book_meeting(event_type_id: int, start_time: str, name: str, email: str) -> str:
    """Create a booking. start_time: ISO 8601 (e.g., 2026-04-07T10:00:00+05:00)."""
    payload = {
        "eventTypeId": event_type_id,
        "start": start_time,
        "responses": {
            "name": name,
            "email": email
        },
        "timeZone": "Asia/Karachi",
        "language": "en",
        "metadata": {}
    }
    
    result = await make_cal_request("POST", "/bookings", data=payload)
    
    if "error" in result:
        return f"BOOKING_FAILED: {result.get('details', 'The slot might be taken or notice period is too short.')}"
    
    return "SUCCESS: The meeting is confirmed. Give the user the details."
# --- TOOLS ---

@mcp.tool()
async def get_my_id() -> Any:
    """Fetch profile to find the numeric User ID."""
    return await make_cal_request("GET", "/users")

@mcp.tool()
async def list_event_types() -> Any:
    """List all available event types."""
    return await make_cal_request("GET", "/event-types")

@mcp.tool()
async def get_availability(date_from: str, date_to: str) -> Any:
    """Check availability. Format dates as YYYY-MM-DD."""
    # Your verified ID from the logs
    USER_ID = 2312997 
    
    # Cal.com V1 strictly wants 'userId' as a single value, not 'userIds'
    params = {
        "userId": USER_ID,
        "dateFrom": f"{date_from}T00:00:00.000Z",
        "dateTo": f"{date_to}T23:59:59.000Z"
    }
    
    logger.info(f"Checking availability for User {USER_ID}")
    return await make_cal_request("GET", "/availability", params=params)

@mcp.tool()
async def list_bookings() -> str:
    """Fetch all upcoming bookings to see their IDs and times."""
    logger.info("Fetching all upcoming bookings...")
    
    # We ask Cal.com for the list
    result = await make_cal_request("GET", "/bookings")
    
    # Check if we got an error or empty result
    if not result or "error" in result:
        return "Could not find any bookings or there was an API error."
    
    # CRITICAL FIX: Cal.com V1 returns a dict with a "bookings" key
    # We need to extract that list to loop through it
    bookings_list = result.get("bookings", [])
    
    if not bookings_list:
        return "You have no upcoming bookings scheduled."
    
    # Format a nice list for the AI to read
    summary = "Here are your current bookings:\n"
    for b in bookings_list:
        # Use .get() to safely access fields
        b_id = b.get('id')
        title = b.get('title', 'Meeting')
        start = b.get('startTime', 'Unknown time')
        summary += f"- ID: {b_id} | Title: {title} | Time: {start}\n"
    
    return summary

@mcp.tool()
async def cancel_booking(booking_id: int, reason: str = "Requested by user") -> str:
    """Cancel/Delete a booking using its numeric ID."""
    logger.info(f"Attempting to cancel booking ID: {booking_id}")
    
    payload = {"reason": reason}
    
    # Cal.com V1 uses DELETE /bookings/{id}/cancel
    endpoint = f"/bookings/{booking_id}/cancel"
    result = await make_cal_request("DELETE", endpoint, data=payload)
    
    if "error" in result:
        return f"FAILED to cancel: {result.get('details', 'Unknown error')}"
    
    return f"SUCCESS: Booking {booking_id} has been canceled." 
    # Force the AI to read the success or failure in plain English!

if __name__ == "__main__":
    logger.info("Starting Cal.com MCP Server on SSE...")
    mcp.run(transport="sse")
