import asyncio
import httpx
import json

API_KEY = "cal_live_030551de67abe1bee4e39b4688202f72"

async def fetch_my_ids():
    url = "https://api.cal.com/v1/event-types"
    
    print("Asking Cal.com for your Event IDs...\n")
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params={"apiKey": API_KEY})
        
        # We are going to print the exact, raw response from the server
        try:
            data = response.json()
            print("--- EXACT CAL.COM RESPONSE ---")
            print(json.dumps(data, indent=2))
            print("------------------------------")
        except Exception as e:
            print("Failed to read JSON. Raw text:")
            print(response.text)

asyncio.run(fetch_my_ids())