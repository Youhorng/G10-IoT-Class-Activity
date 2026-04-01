# ── logic.py — all system decisions ───────────────────────────
import uasyncio as asyncio
from state  import state
from config import GATE_AUTO_CLOSE

def open_gate(servo,lbl="gate"):
    servo.open(); state.gate_open=True; print("[GATE] open "+lbl)

def close_gate(servo,lbl="gate"):
    servo.close(); state.gate_open=False; print("[GATE] close "+lbl)

async def auto_open_close(servo,lbl,delay=GATE_AUTO_CLOSE):
    open_gate(servo,lbl)
    await asyncio.sleep(delay)
    close_gate(servo,lbl)
    state.car_at_entry=False; state.car_at_exit=False
    print("[GATE] latches reset")

def handle_entry_detected(sv):
    if state.car_at_entry: return
    state.car_at_entry=True
    if state.is_full:
        print("[ENTRY] FULL — gate stays closed"); state.car_at_entry=False
    else:
        print("[ENTRY] "+str(state.available)+" free — opening")
        asyncio.create_task(auto_open_close(sv,"entry"))

def handle_entry_clear():
    if state.car_at_entry and not state.gate_open:
        state.car_at_entry=False; print("[ENTRY] clear")

def handle_exit_detected(sv):
    if state.car_at_exit: return
    state.car_at_exit=True; print("[EXIT] opening")
    asyncio.create_task(auto_open_close(sv,"exit"))

def handle_exit_clear():
    if state.car_at_exit and not state.gate_open:
        state.car_at_exit=False; print("[EXIT] clear")

def auto_light_check(relay):
    if state.is_occupied and not state.light_on:
        relay.on(); state.light_on=True; print("[LIGHT] auto ON")
    elif not state.is_occupied and state.light_on:
        relay.off(); state.light_on=False; print("[LIGHT] auto OFF")

def manual_open(sv):    open_gate(sv,"manual")
def manual_close(sv):   close_gate(sv,"manual")
def manual_light_on(rl):  rl.on();  state.light_on=True;  print("[LIGHT] manual ON")
def manual_light_off(rl): rl.off(); state.light_on=False; print("[LIGHT] manual OFF")

