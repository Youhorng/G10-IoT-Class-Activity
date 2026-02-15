import network
import time
import machine
import urequests as requests
from machine import Pin
import tm1637

# -------------------------
# CONFIG
# -------------------------
WIFI_SSID = "Nak"
WIFI_PASS = "25122005"

BLYNK_TOKEN = "V1D46o_2iZgLGqnhko-V-VcQvGBsjZ8c"
BLYNK_API = "http://blynk.cloud/external/api"

IR_PIN = 12
SERVO_PIN = 13

# Servo positions
SERVO_CLOSED = 0
SERVO_OPEN = 90
AUTO_DELAY = 1  # seconds

# TM1637 pins
TM_CLK = 17
TM_DIO = 16

# -------------------------
# HARDWARE
# -------------------------
ir = Pin(IR_PIN, Pin.IN)
servo = machine.PWM(Pin(SERVO_PIN), freq=50)
tm = tm1637.TM1637(Pin(TM_CLK), Pin(TM_DIO))
tm.set_brightness(7)

# -------------------------
# WIFI CONNECT
# -------------------------
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASS)

print("Connecting to WiFi...")
timeout = 10
start = time.time()
while not wifi.isconnected():
    if time.time() - start > timeout:
        print("Failed to connect!")
        break
    time.sleep(1)

if wifi.isconnected():
    print("Connected! IP:", wifi.ifconfig())

# -------------------------
# FUNCTIONS
# -------------------------
def send_ir_status(status):
    url = f"{BLYNK_API}/update?token={BLYNK_TOKEN}&V0={status}"
    try:
        r = requests.get(url)
        r.close()
    except:
        print("HTTP Error (IR)")

def read_slider_v1():
    url = f"{BLYNK_API}/get?token={BLYNK_TOKEN}&v1"
    try:
        r = requests.get(url)
        value = int(str(r.text).strip('[]"'))
        r.close()
        return value
    except Exception as e:
        print("Failed to read slider:", e)
        return None

def read_manual_override_v3():
    """Read Blynk switch for manual override (0 = automatic, 1 = manual)"""
    url = f"{BLYNK_API}/get?token={BLYNK_TOKEN}&v3"
    try:
        r = requests.get(url)
        val = int(str(r.text).strip('[]"'))
        r.close()
        return val == 1  # True if manual override active
    except Exception as e:
        print("Failed to read manual override:", e)
        return False

def send_counter_v2(counter):
    url = f"{BLYNK_API}/update?token={BLYNK_TOKEN}&V2={counter}"
    try:
        r = requests.get(url)
        r.close()
    except:
        print("HTTP Error (Counter)")

def set_angle(angle):
    duty = int((angle / 180) * 102 + 26)
    servo.duty(duty)

def auto_open_servo():
    print("Auto opening servo")
    set_angle(SERVO_OPEN)
    time.sleep(AUTO_DELAY)
    print("Closing servo")
    set_angle(SERVO_CLOSED)

def display_counter(value):
    try:
        tm.show_number(value)
    except Exception as e:
        print("TM1637 display error:", e)

# -------------------------
# MAIN LOOP
# -------------------------
prev_state = -1
last_angle = -1
auto_active = False
ir_counter = 0

while True:
    # --- Manual Override ---
    manual_override = read_manual_override_v3()  # True if manual mode

    # --- IR Sensor ---
    if not manual_override:
        current = ir.value()
        if current != prev_state:
            if current == 0:
                print("Detected")
                send_ir_status("Detected")
                
                # Task 4: increment counter
                ir_counter += 1
                print("IR Count:", ir_counter)
                display_counter(ir_counter)
                send_counter_v2(ir_counter)

                # Task 3: automatic servo
                auto_active = True
                auto_open_servo()
                auto_active = False
            else:
                print("Not Detected")
                send_ir_status("Not%20Detected")
            prev_state = current
    else:
        # Manual override active
        prev_state = -1  # reset IR sensor previous state
        print("Manual override active - IR ignored")

    # --- Servo Control via Slider (Task 2) ---
    angle = read_slider_v1()
    if angle is not None and angle != last_angle:
        angle = max(0, min(180, angle))
        print("Servo angle (manual):", angle)
        set_angle(angle)
        last_angle = angle

    time.sleep(0.2)
