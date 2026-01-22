# ==============================
# LAB 1: Temperature Sensor with Relay Control
# ESP32 + DHT22 + Telegram Bot
# ==============================

import time
import network
import urequests
import dht
from machine import Pin

# ---------- USER CONFIG ----------
WIFI_SSID = "AI WIFI"
WIFI_PASSWORD = "AIetl@2025"
BOT_TOKEN = "8367393613:AAEAqxm-Rh6VUrLZjy0eJFIr0a1FAeFdEA0"
CHAT_ID = "-5128585991"

DHT_PIN = 4
RELAY_PIN = 2
TEMP_THRESHOLD = 30.0
SAMPLE_INTERVAL = 5  # seconds
# ---------------------------------

# ---------- HARDWARE SETUP ----------
sensor = dht.DHT22(Pin(DHT_PIN))
relay = Pin(RELAY_PIN, Pin.OUT)
relay.off()
# -----------------------------------

# ---------- WIFI ----------
def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1

    if wlan.isconnected():
        print("WiFi connected:", wlan.ifconfig())
        return True
    else:
        print("WiFi failed")
        return False

wifi_connect()
# -----------------------------------

# ---------- TELEGRAM ----------
def send_message(text):
    try:
        url = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
        payload = {"chat_id": CHAT_ID, "text": text}
        r = urequests.post(url, json=payload)
        print("Telegram status:", r.status_code)
        r.close()
    except Exception as e:
        print("Telegram error:", e)

def get_updates(offset):
    try:
        url = "https://api.telegram.org/bot{}/getUpdates?offset={}".format(BOT_TOKEN, offset)
        r = urequests.get(url)
        data = r.json()
        r.close()
        return data
    except Exception as e:
        print("GetUpdates error:", e)
        return {"result": []}
# -----------------------------------

# ---------- STATE ----------
last_update_id = 0
alert_active = False
# -----------------------------------

# ---------- COMMAND HANDLER ----------
def handle_commands(temp, hum):
    global last_update_id

    updates = get_updates(last_update_id + 1)

    for item in updates["result"]:
        last_update_id = item["update_id"]
        text = item["message"]["text"]

        if text == "/status":
            state = "ON" if relay.value() else "OFF"
            msg = "Temp: {:.2f}°C\n Hum: {:.2f}%\n Relay: {}".format(temp, hum, state)
            send_message(msg)

        elif text == "/on":
            relay.on()
            send_message("Relay turned ON")

        elif text == "/off":
            relay.off()
            send_message("Relay turned OFF")
# -----------------------------------

# ---------- MAIN LOOP ----------
print("System started")

while True:
    try:
        # Reconnect WiFi if dropped
        if not network.WLAN(network.STA_IF).isconnected():
            wifi_connect()

        # Read sensor
        sensor.measure()
        temperature = sensor.temperature()
        humidity = sensor.humidity()

        print("Temp: {:.2f}C | Hum: {:.2f}%".format(temperature, humidity))

        # Handle Telegram commands
        handle_commands(temperature, humidity)

        # Alert logic
        if temperature >= TEMP_THRESHOLD and not relay.value():
            send_message("ALERT: Temperature {:.2f}°C".format(temperature))
            alert_active = True

        # Auto-OFF logic
        if temperature < TEMP_THRESHOLD and relay.value():
            relay.off()
            if alert_active:
                send_message("Temperature normal. Relay auto-OFF.")
                alert_active = False

    except OSError as e:
        print("Sensor error:", e)

    except Exception as e:
        print("Unexpected error:", e)

    time.sleep(SAMPLE_INTERVAL)
