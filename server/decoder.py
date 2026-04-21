import json
from pathlib import Path

formats_path = Path(__file__).parent / "formats.json"
with open(formats_path) as f:
    FORMATS = json.load(f)


def bits_to_int(bits, start, end):
    return int(bits[start:end + 1], 2)


def check_parity(bits, start, end, parity_type):
    ones = bits[start:end + 1].count("1")
    if parity_type == "even":
        return ones % 2 == 0
    else:
        return ones % 2 == 1


def decode(bit_string):
    bit_count = len(bit_string)

    matched_format = None
    format_name = None
    for name, fmt in FORMATS.items():
        if fmt["bits"] == bit_count:
            matched_format = fmt
            format_name = name
            break

    result = {
        "bit_count": bit_count,
        "raw_bits": bit_string,
        "format": format_name or "Unknown",
    }

    if not matched_format:
        return result

    for field_name, (start, end) in matched_format["fields"].items():
        result[field_name] = bits_to_int(bit_string, start, end)

    parity_ok = True
    for parity_type, (start, end) in matched_format["parity"].items():
        if not check_parity(bit_string, start, end, parity_type):
            parity_ok = False
    result["parity_ok"] = parity_ok

    return result
