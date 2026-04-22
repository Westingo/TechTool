import pigpio
import time

TX_D0_PIN = 22
TX_D1_PIN = 23
PULSE_US = 100
GAP_US = 2000

def transmit_wiegand(pi, bit_string, capture_ref=None):
    """Transmit a Wiegand bit string using hardware-timed pulses."""
    pi.set_mode(TX_D0_PIN, pigpio.OUTPUT)
    pi.set_mode(TX_D1_PIN, pigpio.OUTPUT)

    # Idle state: both lines high
    pi.write(TX_D0_PIN, 1)
    pi.write(TX_D1_PIN, 1)
    time.sleep(0.1)

    waveform = []

    # Settling period: hold both high for 10ms
    waveform.append(pigpio.pulse(
        (1 << TX_D0_PIN) | (1 << TX_D1_PIN), 0, 10000
    ))

    for bit in bit_string:
        if bit == '0':
            waveform.append(pigpio.pulse(0, 1 << TX_D0_PIN, PULSE_US))
            waveform.append(pigpio.pulse(1 << TX_D0_PIN, 0, GAP_US))
        else:
            waveform.append(pigpio.pulse(0, 1 << TX_D1_PIN, PULSE_US))
            waveform.append(pigpio.pulse(1 << TX_D1_PIN, 0, GAP_US))

    # End: hold both high
    waveform.append(pigpio.pulse(
        (1 << TX_D0_PIN) | (1 << TX_D1_PIN), 0, 10000
    ))

    pi.wave_clear()
    pi.wave_add_generic(waveform)
    wave_id = pi.wave_create()

    pi.wave_send_once(wave_id)

    while pi.wave_tx_busy():
        pass

    pi.wave_delete(wave_id)

    print(f"Transmitted {len(bit_string)} bits: {bit_string}")
