# ── main.py — Smart IoT Parking System ────────────────────────
# Files on ESP32: config.py state.py hardware.py logic.py iot.py main.py
# Upload ALL files first, fill in config.py, then run this last.

import uasyncio as asyncio
import network, utime, gc

from config   import *
from state    import state
from hardware import (Ultrasonic, IRSensor, Servo, Relay, DHTSensor,
                      TM1637, LCD, sync_ntp, get_hms, get_time_str)
from logic    import (handle_entry_detected, handle_entry_clear,
                      handle_exit_detected,  handle_exit_clear,
                      auto_light_check)
from iot      import TelegramBot, WebServer, Blynk


# ── WiFi ──────────────────────────────────────────────────────
def connect_wifi():
    w=network.WLAN(network.STA_IF); w.active(True)
    if w.isconnected():
        print("[WIFI] "+w.ifconfig()[0]); return w.ifconfig()[0]
    print("[WIFI] Connecting...")
    w.connect(WIFI_SSID,WIFI_PASS)
    t=20
    while not w.isconnected() and t>0:
        utime.sleep(1); t-=1; print(".",end="")
    if w.isconnected():
        ip=w.ifconfig()[0]; print("\n[WIFI] "+ip); return ip
    print("\n[WIFI] Failed"); utime.sleep(3)
    import machine; machine.reset()


# ── Async tasks ───────────────────────────────────────────────
#async def task_sensors(slot_ir,ultra,exit_ir,esv,xsv,relay):
    #while True:
        #slot_ir.update(state)
        #auto_light_check(relay)
        #d=ultra.distance()
        #handle_entry_detected(esv) if d<ENTRY_TRIGGER_CM else handle_entry_clear()
        #handle_exit_detected(xsv)  if exit_ir.read_one() else handle_exit_clear()
        #if exit_ir.read_one():
            #handle_exit_detected(xsv)
        #else:
            #handle_exit_clear()
        #await asyncio.sleep_ms(T_SENSORS)
async def task_sensors(slir,ultra,exir,esv,xsv,relay,bot):
    while True:
        slir.update(state)
        #state._last_slots = state.slots[:]
        auto_light_check(relay)
        d=ultra.distance()
        handle_entry_detected(esv) if d<ENTRY_TRIGGER_CM else handle_entry_clear()
        handle_exit_detected(xsv)  if exir.read_one() else handle_exit_clear()

        # ── Real-time slot change notifications ──
        for i in range(state.total):
            prev = state._last_slots[i]
            curr = state.slots[i]
            if curr != prev:
                state._last_slots[i] = curr
                if curr:   # slot just became occupied
                    asyncio.create_task(_notify(bot, "Slot " + str(i+1) + " is taken!"))
                else:      # slot just became free
                    asyncio.create_task(_notify(bot, "Slot " + str(i+1) + " is now available"))

        # ── Gate entry/exit events ──
        if state.car_at_entry and state.gate_open and state._last_event != "entry":
            state._last_event = "entry"
            asyncio.create_task(_notify(bot, "Entry Gate: Open"))
            asyncio.create_task(_notify(bot, "Car Entered!"))
        elif state.car_at_exit and state.gate_open and state._last_event != "exit":
            state._last_event = "exit"
            asyncio.create_task(_notify(bot, "Exit Gate: Open"))
            asyncio.create_task(_notify(bot, "Car Exited!"))
        elif state.is_full and state._last_event != "full":
            state._last_event = "full"
            asyncio.create_task(_notify(bot, "Parking Full — all slots occupied"))
        elif not state.car_at_entry and not state.car_at_exit and not state.is_full:
            state._last_event = None   # reset for next event

        await asyncio.sleep_ms(T_SENSORS)

async def task_displays(tm,lcd):
    while True:
        try: tm.show(state.available); lcd.update(state)
        except Exception as e: print("[DISP] "+str(e))
        await asyncio.sleep_ms(T_DISPLAYS)

async def task_clock(tm_c):
    while True:
        try:
            h,m,s=get_hms(); tm_c.show_clock(h,m,s%2==0)
        except Exception as e: print("[CLK] "+str(e))
        await asyncio.sleep_ms(1000)

async def task_dht(dht):
    while True:
        try: state.temperature,state.humidity=dht.read()
        except Exception as e: print("[DHT] "+str(e))
        await asyncio.sleep_ms(T_DHT)

async def task_telegram(bot):
    await asyncio.sleep_ms(5000)
    while True:
        gc.collect(); await bot.poll(); gc.collect()
        await asyncio.sleep_ms(T_TELEGRAM)

async def task_blynk(blynk):
    await asyncio.sleep_ms(T_BLYNK_OFF)
    while True:
        gc.collect(); await blynk.sync(); gc.collect()
        await asyncio.sleep_ms(T_BLYNK)

async def task_web(web):
    while True:
        await web.handle(); await asyncio.sleep_ms(50)

async def task_notify(bot,ip):
    await asyncio.sleep_ms(8000); gc.collect()
    bot.send("Smart Parking ONLINE\nIP: "+ip+"\nTime: "+get_time_str()+" UTC+7\n"
             "Slots: "+str(state.available)+"/"+str(state.total)+" free\n/help for commands")
async def _notify(bot, text):
    """Send Telegram notification without blocking sensors."""
    import gc; gc.collect()
    bot.send(text)
    gc.collect()

# ── Boot ──────────────────────────────────────────────────────
async def main():
    gc.enable(); gc.collect()

    ip=connect_wifi(); gc.collect()
    sync_ntp();        gc.collect()

    print("[BOOT] Hardware...")
    esv  = Servo(SERVO_ENTRY_PIN, GATE_OPEN_DEG, GATE_CLOSE_DEG); gc.collect()
    xsv  = Servo(SERVO_EXIT_PIN,  GATE_OPEN_DEG, GATE_CLOSE_DEG); gc.collect()
    relay= Relay(RELAY_PIN)
    slir = IRSensor(IR_PINS,       IR_INVERT)
    exir = IRSensor([EXIT_IR_PIN], EXIT_IR_INVERT)
    ultra= Ultrasonic(TRIG_PIN, ECHO_PIN)
    dht  = DHTSensor(DHT_PIN);    gc.collect()
    tm   = TM1637(TM_CLK, TM_DIO)
    tmc  = TM1637(TM_CLOCK_CLK, TM_CLOCK_DIO)
    lcd  = LCD(LCD_SDA, LCD_SCL, LCD_ADDR); gc.collect()

    slir.update(state)   # read slots before boot message
    lcd.show_message("Smart Parking","Booting..."); utime.sleep(1)
    lcd.show_message("IP:"+ip[:13],"System Ready"); utime.sleep(1)

    print("[BOOT] IoT platforms...")
    bot   = TelegramBot(BOT_TOKEN,CHAT_ID,esv,relay); gc.collect()
    web = WebServer(esv, xsv, relay);                      gc.collect()
    blynk = Blynk(BLYNK_TOKEN, esv, xsv);                   gc.collect()

    print("[BOOT] Dashboard: http://"+ip)
    print("[BOOT] RAM: "+str(gc.mem_free())+" bytes")

    #asyncio.create_task(task_sensors(slir,ultra,exir,esv,xsv,relay))
    asyncio.create_task(task_sensors(slir,ultra,exir,esv,xsv,relay,bot))
    asyncio.create_task(task_displays(tm,lcd))
    asyncio.create_task(task_clock(tmc))
    asyncio.create_task(task_dht(dht))
    asyncio.create_task(task_telegram(bot))
    asyncio.create_task(task_blynk(blynk))
    asyncio.create_task(task_web(web))
    asyncio.create_task(task_notify(bot,ip))

    print("[BOOT] All tasks running.")
    while True:
        #gc.collect(); await asyncio.sleep_ms(100)
        while True:
            gc.collect()
            # Auto-reconnect if WiFi drops
            import network
            w = network.WLAN(network.STA_IF)
            if not w.isconnected():
                print("[WIFI] Reconnecting...")
                w.connect(WIFI_SSID, WIFI_PASS)
            await asyncio.sleep_ms(100)

asyncio.run(main())
