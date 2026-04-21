from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import random
from datetime import datetime
from server.event_bus import bus

app = FastAPI()

@app.post("/fake-scan")
def fake_scan():
    scan = {
        "format": "26-bit Wiegand",
        "facility_code": random.randint(1, 255),
        "card_number": random.randint(1, 65535),
        "timestamp": datetime.now().isoformat(),
    }
    bus.publish(scan)
    return scan

async def scan_stream():
    queue = bus.subscribe()
    try:
        while True:
            scan = await queue.get()
            yield f"data: {json.dumps(scan)}\n\n"
    finally:
        bus.unsubscribe(queue)

@app.get("/scans")
async def scans():
    return StreamingResponse(scan_stream(), media_type="text/event-stream")

app.mount("/static", StaticFiles(directory="static"), name="static")
