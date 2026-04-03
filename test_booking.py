import asyncio
import httpx

API_KEY = "cal_live_030551de67abe1bee4e39b4688202f72"
EVENT_ID = 5223683

async def test_direct_booking():
    # We are picking 10:00 AM Karachi time on April 25th (a Saturday) 
    # NOTE: If you don't work Saturdays, change this to April 27th (Monday)!
    target_time = "2026-04-27T10:00:00+05:00" 
    
    print(f"Attempting to book for Monday morning: {target_time}...")
    
    url = "https://api.cal.com/v1/bookings"
    payload = {
        "eventTypeId": EVENT_ID,
        "start": target_time,
        "responses": {
            "name": "Final Success Test",
            "email": "imubashir994@gmail.com"
        },
        "timeZone": "Asia/Karachi",
        "language": "en",
        "metadata": {}
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, params={"apiKey": API_KEY}, json=payload)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Details: {response.text}")

asyncio.run(test_direct_booking())