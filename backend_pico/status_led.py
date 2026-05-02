import time

import machine


def _create_led_pin():
    try:
        return machine.Pin("LED", machine.Pin.OUT)
    except Exception:
        return machine.Pin(25, machine.Pin.OUT)


LED = _create_led_pin()


def on():
    LED.value(1)


def off():
    LED.value(0)


def flash(count=1, on_time=0.08, off_time=0.08, leave_on=True):
    for _ in range(count):
        LED.value(1)
        time.sleep(on_time)
        LED.value(0)
        time.sleep(off_time)

    if leave_on:
        LED.value(1)


def waiting_for_network():
    flash(count=1, on_time=0.15, off_time=0.85, leave_on=False)


def ready():
    on()


def request_handled():
    flash(count=2, on_time=0.05, off_time=0.05, leave_on=True)


def error():
    flash(count=5, on_time=0.05, off_time=0.05, leave_on=False)
