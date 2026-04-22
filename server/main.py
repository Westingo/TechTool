from fastapi import FastAPI
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import random
import pigpio
from datetime import datetime
from server.event_bus import bus
from server.decoder import decode
from server.capture import start_capture
from server.transmit import transmit_wiegand

app = FastAPI()
pi = None

@app.on_event("startup")
def startup():
    global pi
    pi = pigpio.pi()
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

@app.post("/transmit")
def transmit(facility_code: int = 1, card_number: int = 1, format_type: str = "H10301"):
    if format_type == "H10301":
        fc_bits = format(facility_code & 0xFF, '08b')
        card_bits = format(card_number & 0xFFFF, '016b')
        middle = fc_bits + card_bits
        first_half = middle[:12]
        even_parity = '0' if first_half.count('1') % 2 == 0 else '1'
        second_half = middle[12:]
        odd_parity = '1' if second_half.count('1') % 2 == 0 else '0'
        bit_string = even_parity + middle + odd_parity
    else:
        return {"error": f"Format {format_type} not yet supported for transmit"}

    transmit_wiegand(pi, bit_string)
    return {
        "status": "transmitted",
        "format": format_type,
        "facility_code": facility_code,
        "card_number": card_number,
        "bits": bit_string
    }

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
