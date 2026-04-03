Markdown
# Cal.com AI Scheduling Agent 🗓️🤖

A voice-activated, intelligent scheduling assistant that connects LLMs (like Claude and Vapi) to your Cal.com calendar using the Model Context Protocol (MCP).

## Features
This FastMCP server acts as a bridge between an AI agent and the Cal.com V1 API, giving the AI the ability to:
* **List Event Types:** Dynamically check available meeting lengths (e.g., 15-min, 30-min).
* **Check Availability:** Prevent double-booking by checking real-time free slots.
* **Book Meetings:** Create new calendar events with attendee names and emails.
* **List Bookings:** Look up upcoming appointments and their unique IDs.
* **Cancel Bookings:** Delete existing meetings directly from the calendar.

## Prerequisites
* Python 3.10+
* A [Cal.com](https://cal.com) account (with an API Key)
* [Ngrok](https://ngrok.com/) (for tunneling to cloud AI agents like Vapi)
* Claude Desktop (for local MCP testing)

## Setup Instructions

**1. Clone the repository and navigate to the folder:**
```bash
git clone [https://github.com/YOUR-USERNAME/calcom-ai-agent.git](https://github.com/YOUR-USERNAME/calcom-ai-agent.git)
cd calcom-ai-agent
2. Create a virtual environment and install dependencies:

Bash
python -m venv venv
venv\Scripts\activate  # On Windows
pip install mcp fastmcp httpx python-dotenv uvicorn
3. Configure Environment Variables:
Create a .env file in the root directory and add your Cal.com API key:

Code snippet
CAL_API_KEY=cal_live_your_api_key_here

How to Run
1. Start the FastMCP Server:

Bash
python server.py
The server will start locally on port 8000 using SSE (Server-Sent Events).

2. Expose to the Web (for Vapi):
In a new terminal window, use Ngrok to create a secure tunnel. The --host-header flag is required to bypass strict Host validation.

Bash
ngrok http 8000 --host-header="localhost:8000"
Take the resulting Ngrok URL and append /sse to it in your Vapi Tool settings.

3. Test locally with Claude Desktop:
Add the following to your claude_desktop_config.json:

JSON
"mcpServers": {
  "cal-com": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/transport-sse",
      "http://localhost:8000/sse"
    ]
  }
}
Security
All API requests to Cal.com enforce strict key parsing to prevent malformed headers. All local logging is redirected to stderr to ensure a clean JSON-RPC pipeline over stdout.
