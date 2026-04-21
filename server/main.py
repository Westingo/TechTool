from fastapi import FastAPI
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import random
from datetime import datetime
from server.event_bus import bus
from server.decoder import decode
from server.capture import start_capture

app = FastAPI()

@app.on_event("startup")
def startup():
    start_capture()

@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

@app.post("/fake-scan")
def fake_scan():
    fc = random.randint(1, 255)
    card = random.randint(1, 65535)
    fc_bits = format(fc, '08b')
    card_bits = format(card, '016b')
    middle = fc_bits + card_bits
    first_half = middle[:12]
    even_parity = '0' if first_half.count('1') % 2 == 0 else '1'
    second_half = middle[12:]
    odd_parity = '1' if second_half.count('1') % 2 == 0 else '0'
    bits = even_parity + middle + odd_parity

    scan = decode(bits)
    scan["timestamp"] = datetime.now().isoformat()
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
